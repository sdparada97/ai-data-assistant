"""Fragmentador único de Markdown (PDF y Word llegan ya convertidos).

Reglas:
- El primer ``#`` es el título del documento (si no hay, el ``doc_id``); los ``#``
  posteriores son títulos de página y no entran al texto.
- ``##`` y ``###`` abren un fragmento cuya ``section`` es el título. ``####`` y las
  líneas dentro de bloques de código son texto.
- El texto anterior a la primera sección forma un fragmento con ``section`` nula.
- Un párrafo, elemento de lista o título que empieza por un ID de evidencia seguido
  de un separador abre un fragmento con ese ID principal; los párrafos siguientes
  sin ID siguen en él hasta el siguiente ID o título.
- Las tablas se escriben fila a fila como ``encabezado: valor | …``. Una tabla con
  IDs en la primera columna de todas sus filas produce un fragmento por fila,
  salvo que alguno de esos IDs ya sea principal en el documento.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.errors import ConversionError
from analyst_backend.documents.markdown import PAGE_MARKER_RE

_TITLE_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
_SECTION_RE = re.compile(r"^#{2,3}\s+(.+?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
_BOLD = "**"


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    source_type: str
    title: str
    section: str | None
    page: int | None
    primary_evidence_id: str | None
    evidence_ids: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class _Table:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    page: int | None


@dataclass
class _Draft:
    section: str | None
    page: int | None
    primary: str | None
    parts: list[str | _Table] = field(default_factory=list)


def _strip_bold(text: str) -> str:
    return text.replace(_BOLD, "")


def _blocks(markdown: str) -> list[str]:
    """Bloques separados por líneas en blanco; cada título y cada marca de página es un bloque.

    Un bloque de código se conserva entero (con sus líneas en blanco) y nunca se interpreta.
    """
    blocks: list[str] = []
    current: list[str] = []
    fence: str | None = None

    def flush() -> None:
        if current:
            blocks.append("\n".join(current))
            current.clear()

    for line in markdown.splitlines():
        match = _FENCE_RE.match(line)
        if fence is not None:
            current.append(line)
            if match and match.group(1) == fence:
                fence = None
                flush()
            continue
        if match:
            flush()
            fence = match.group(1)
            current.append(line)
        elif not line.strip():
            flush()
        elif _TITLE_RE.match(line) or _SECTION_RE.match(line) or PAGE_MARKER_RE.match(line.strip()):
            flush()
            blocks.append(line.strip())
        else:
            current.append(line.rstrip())
    flush()
    return blocks


def _is_code(block: str) -> bool:
    return _FENCE_RE.match(block) is not None


def _is_table(block: str) -> bool:
    lines = block.splitlines()
    return (
        len(lines) >= 2
        and all(line.lstrip().startswith("|") for line in lines)
        and _TABLE_SEPARATOR_RE.match(lines[1].strip()) is not None
    )


def _cells(line: str) -> tuple[str, ...]:
    inner = line.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return tuple(_strip_bold(cell.strip().replace("\\|", "|")) for cell in _CELL_SPLIT_RE.split(inner))


def _parse_table(block: str, page: int | None) -> _Table:
    lines = block.splitlines()
    return _Table(header=_cells(lines[0]), rows=tuple(_cells(line) for line in lines[2:]), page=page)


def _row_text(header: tuple[str, ...], row: tuple[str, ...]) -> str:
    return " | ".join(f"{name}: {value}" for name, value in zip(header, row, strict=False))


def _table_text(table: _Table) -> str:
    if not table.rows:
        return " | ".join(cell for cell in table.header if cell)
    return "\n".join(_row_text(table.header, row) for row in table.rows)


def chunk_markdown(
    markdown: str, doc_id: str, source_type: str, config: DocumentsConfig
) -> tuple[str, list[Chunk]]:
    """Devuelve el título del documento y sus fragmentos, en orden de aparición."""
    id_start = config.id_start_regex
    title: str | None = None
    section: str | None = None
    page: int | None = None
    drafts: list[_Draft] = []
    current: _Draft | None = None

    def open_draft(primary: str | None) -> _Draft:
        draft = _Draft(section=section, page=page, primary=primary)
        drafts.append(draft)
        return draft

    def starting_id(text: str) -> str | None:
        match = id_start.match(_strip_bold(_LIST_ITEM_RE.sub("", text, count=1)).strip())
        return match.group("id") if match else None

    for block in _blocks(markdown):
        if marker := PAGE_MARKER_RE.match(block):
            page = int(marker.group(1))
            continue
        if _is_code(block):
            current = current or open_draft(None)
            current.parts.append(block)
            continue
        if heading := _TITLE_RE.match(block):
            if title is None:
                title = _strip_bold(heading.group(1)).strip()
            continue
        if heading := _SECTION_RE.match(block):
            section = _strip_bold(heading.group(1)).strip()
            current = open_draft(starting_id(section))
            continue
        if _is_table(block):
            current = current or open_draft(None)
            current.parts.append(_parse_table(block, page))
            continue
        if _LIST_ITEM_RE.match(block):
            for item in block.splitlines():
                primary = starting_id(item) if _LIST_ITEM_RE.match(item) else None
                if primary is not None or current is None:
                    current = open_draft(primary)
                current.parts.append(_strip_bold(item))
            continue
        primary = starting_id(block)
        if primary is not None or current is None:
            current = open_draft(primary)
        current.parts.append(_strip_bold(block))

    primaries = {draft.primary for draft in drafts if draft.primary}
    document_title = title or doc_id
    rendered: list[tuple[_Draft, str | None, str, int | None]] = []
    for draft in drafts:
        texts: list[str] = []
        rows: list[tuple[str, str, int | None]] = []
        for part in draft.parts:
            if isinstance(part, _Table):
                matches = [config.id_regex.match(row[0]) if row else None for row in part.rows]
                ids = [match.group(0) for match in matches if match]
                # Se divide solo si todas las filas tienen ID, sin repetidos y sin ninguno ya principal
                # (en títulos, párrafos o filas de tablas anteriores). Gana la primera aparición.
                if part.rows and len(ids) == len(part.rows) and len(set(ids)) == len(ids) and not set(ids) & primaries:
                    primaries.update(ids)
                    rows.extend(
                        (evidence_id, _row_text(part.header, row), part.page)
                        for evidence_id, row in zip(ids, part.rows, strict=True)
                    )
                    continue
                texts.append(_table_text(part))
            else:
                texts.append(part)
        if texts:
            rendered.append((draft, draft.primary, "\n".join(texts), draft.page))
        rendered.extend((draft, primary, text, row_page) for primary, text, row_page in rows)

    chunks: list[Chunk] = []
    for position, (draft, primary, text, chunk_page) in enumerate(rendered, start=1):
        found = config.id_regex.findall(text)
        evidence_ids = tuple(dict.fromkeys([primary, *found] if primary else found))
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}:{position:03d}",
                doc_id=doc_id,
                source_type=source_type,
                title=document_title,
                section=draft.section,
                page=chunk_page,
                primary_evidence_id=primary,
                evidence_ids=evidence_ids,
                text=text,
            )
        )
    if not chunks:
        raise ConversionError(f"El documento {doc_id} no produce ningún fragmento (¿sin texto o solo títulos?)")
    return document_title, chunks
