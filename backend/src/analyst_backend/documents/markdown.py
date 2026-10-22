"""Conversión de PDF y Word a un Markdown normalizado.

Convenciones del Markdown que produce: ``#`` título del documento, ``##`` sección,
``###`` subsección, ``- `` listas, tablas GFM y, en PDF, ``<!-- page: N -->`` al
inicio de cada página. Los espacios repetidos se reducen a uno. Todos los
umbrales salen de ``documents.yaml``.
"""

from __future__ import annotations

import re
import zipfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import docx
import pymupdf
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from analyst_backend.documents.config import DocumentsConfig, PdfConfig
from analyst_backend.documents.errors import ConversionError
from analyst_backend.documents.sources import SourceFile

PAGE_MARKER = "<!-- page: {} -->"
PAGE_MARKER_RE = re.compile(r"^<!-- page: (\d+) -->$")
_SPACES = re.compile(r"\s+")
_WORD_HEADINGS = {"Title": "# ", "Heading 1": "## ", "Heading 2": "### "}


def collapse_spaces(text: str) -> str:
    return _SPACES.sub(" ", text).strip()


def markdown_table(rows: Sequence[Sequence[str]]) -> str:
    """Tabla GFM: la primera fila es el encabezado. Escapa ``|`` dentro de las celdas."""
    width = max(len(row) for row in rows)
    padded = [[*(cell.replace("|", "\\|") for cell in row), *[""] * (width - len(row))] for row in rows]
    lines = ["| " + " | ".join(padded[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(row) + " |" for row in padded[1:]]
    return "\n".join(lines)


def to_markdown(source: SourceFile, config: DocumentsConfig) -> str:
    """Markdown del documento. Los ``.md`` se devuelven tal cual."""
    if source.source_type == "pdf":
        return pdf_to_markdown(source.path, config.pdf, config.id_start_regex)
    if source.source_type == "docx":
        return docx_to_markdown(source.path)
    if source.source_type == "md":
        try:
            return source.path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ConversionError(f"No se puede leer {source.path.name}: no es UTF-8 ({error})") from error
    raise ConversionError(f"Tipo de documento no admitido: {source.path.name}")


# --- PDF -----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Line:
    rect: pymupdf.Rect
    size: float
    text: str

    @property
    def center(self) -> pymupdf.Point:
        return pymupdf.Point((self.rect.x0 + self.rect.x1) / 2, (self.rect.y0 + self.rect.y1) / 2)


def _page_lines(page: pymupdf.Page) -> list[_Line]:
    lines: list[_Line] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = collapse_spaces("".join(span["text"] for span in line["spans"]))
            if text:
                size = max(span["size"] for span in line["spans"])
                lines.append(_Line(pymupdf.Rect(line["bbox"]), size, text))
    return lines


def _table_rows(page: pymupdf.Page, config: PdfConfig) -> list[list[pymupdf.Rect]]:
    """Tablas sin bordes: dos o más rectángulos de fondo del mismo ancho, apilados sin hueco."""
    tolerance = config.row_stack_tolerance_pt
    rects = sorted(
        (
            pymupdf.Rect(drawing["rect"])
            for drawing in page.get_drawings()
            if drawing.get("fill") is not None and drawing["rect"].height >= config.min_row_height_pt
        ),
        key=lambda rect: (rect.y0, rect.x0),
    )
    groups: list[list[pymupdf.Rect]] = []
    for rect in rects:
        last = groups[-1][-1] if groups else None
        if (
            last is not None
            and abs(last.x0 - rect.x0) <= tolerance
            and abs(last.x1 - rect.x1) <= tolerance
            and abs(last.y1 - rect.y0) <= tolerance
        ):
            groups[-1].append(rect)
        else:
            groups.append([rect])
    return [group for group in groups if len(group) >= 2]


def _table_cells(rows: list[pymupdf.Rect], lines: Iterable[_Line], config: PdfConfig) -> list[list[str]]:
    by_row: list[list[_Line]] = [[line for line in lines if row.contains(line.center)] for row in rows]
    reference = max(by_row, key=lambda row: len({round(line.rect.x0) for line in row}))
    starts = sorted({round(line.rect.x0) for line in reference}) or [0]

    def column(x0: float) -> int:
        candidates = [i for i, start in enumerate(starts) if start <= x0 + config.column_tolerance_pt]
        return max(candidates) if candidates else 0

    cells: list[list[str]] = []
    for row in by_row:
        values = [""] * len(starts)
        for line in sorted(row, key=lambda item: (item.rect.y0, item.rect.x0)):
            index = column(line.rect.x0)
            values[index] = collapse_spaces(f"{values[index]} {line.text}")
        if any(values):
            cells.append(values)
    return cells


def pdf_to_markdown(path: Path, config: PdfConfig, id_start: re.Pattern[str]) -> str:
    try:
        with pymupdf.open(path) as document:
            if not document.is_pdf:
                raise ConversionError(f"No se puede abrir {path.name}: no es un PDF")
            pages = [(page.number + 1, _page_lines(page), _table_rows(page, config)) for page in document]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError, RuntimeError) as error:
        if isinstance(error, ConversionError):
            raise
        raise ConversionError(f"No se puede abrir {path.name}: {error}") from error

    repeated: set[str] = set()
    if len(pages) >= 2:
        pages_per_text = Counter(text for _, lines, _ in pages for text in {line.text for line in lines})
        repeated = {text for text, count in pages_per_text.items() if count == len(pages)}
    section_re = re.compile(config.section_pattern)
    page_label_re = re.compile(config.page_label_pattern)

    blocks: list[str] = []
    for number, page_lines, tables in pages:
        blocks.append(PAGE_MARKER.format(number))
        lines = [line for line in page_lines if line.text not in repeated and not page_label_re.match(line.text)]
        regions = [pymupdf.Rect(rows[0].x0, rows[0].y0, rows[-1].x1, rows[-1].y1) for rows in tables]

        def table_of(line: _Line) -> int | None:
            return next((i for i, region in enumerate(regions) if region.contains(line.center)), None)

        emitted: set[int] = set()
        paragraph: list[str] = []
        previous: _Line | None = None
        title_open = False

        def flush() -> None:
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph.clear()

        for line in lines:
            table = table_of(line)
            if table is not None:
                if table not in emitted:
                    flush()
                    emitted.add(table)
                    members = [item for item in lines if table_of(item) == table]
                    cells = _table_cells(tables[table], members, config)
                    if cells:
                        blocks.append(markdown_table(cells))
                previous, title_open = None, False
                continue
            if line.size >= config.title_min_size:
                flush()
                if title_open:  # un título en varias líneas
                    blocks[-1] = f"{blocks[-1]} {line.text}"
                else:
                    blocks.append(f"# {line.text}")
                previous, title_open = None, True
                continue
            title_open = False
            if line.size >= config.section_min_size and section_re.match(line.text):
                flush()
                blocks.append(f"## {line.text}")
                previous = None
                continue
            gap = line.rect.y0 - previous.rect.y1 if previous is not None else 0.0
            if previous is None or gap > config.paragraph_gap_ratio * line.rect.height or id_start.match(line.text):
                flush()
            paragraph.append(line.text)
            previous = line
        flush()
    return "\n\n".join(blocks) + "\n"


# --- Word ----------------------------------------------------------------------------------------


def _docx_table_rows(table: Table) -> list[list[str]]:
    """Filas de la tabla. Una celda combinada aparece una sola vez: python-docx repite su elemento.

    Se guardan los elementos vistos (no solo su ``id``): así siguen vivos y lxml
    devuelve el mismo objeto para el mismo nodo, sin reutilizar identificadores.
    """
    seen: dict[int, object] = {}
    rows: list[list[str]] = []
    for row in table.rows:
        values: list[str] = []
        for cell in row.cells:
            element = cell._tc
            values.append("" if seen.get(id(element)) is element else collapse_spaces(cell.text))
            seen[id(element)] = element
        if any(values):
            rows.append(values)
    return rows


def docx_to_markdown(path: Path) -> str:
    try:
        document = docx.Document(str(path))
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError) as error:
        raise ConversionError(f"No se puede abrir {path.name}: no es un documento de Word válido ({error})") from error

    blocks: list[str] = []
    for element in document.element.body.iterchildren():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(element, document)
            text = collapse_spaces(paragraph.text)
            if not text:
                continue
            style = paragraph.style.name if paragraph.style is not None else ""
            if style in _WORD_HEADINGS:
                blocks.append(_WORD_HEADINGS[style] + text)
            elif "List" in style:
                item = f"- {text}"
                if blocks and blocks[-1].startswith("- "):
                    blocks[-1] = f"{blocks[-1]}\n{item}"
                else:
                    blocks.append(item)
            else:
                blocks.append(text)
        elif tag == "tbl":
            rows = _docx_table_rows(Table(element, document))
            if rows:
                blocks.append(markdown_table(rows))
    return "\n\n".join(blocks) + "\n"
