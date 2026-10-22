"""Selección de los documentos a cargar."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from analyst_backend.documents.errors import SourceError

# Prefijo de los archivos de bloqueo que crea Office al abrir un documento.
_OFFICE_LOCK_PREFIX = "~$"


@dataclass(frozen=True)
class SourceFile:
    doc_id: str
    path: Path
    source_type: str  # extensión sin punto y en minúsculas: pdf, docx o md


def list_documents(directory: Path, extensions: Sequence[str]) -> list[SourceFile]:
    """Documentos del primer nivel de ``directory``, en orden alfabético.

    Ignora subdirectorios, archivos ocultos, archivos de bloqueo de Office y las
    extensiones no configuradas. Falla si el directorio no existe, si no queda
    ningún documento o si dos archivos comparten ``doc_id``.
    """
    if not directory.is_dir():
        raise SourceError(f"No existe el directorio de documentos: {directory}")
    allowed = {extension.lower() for extension in extensions}
    selected = [
        path
        for path in sorted(directory.iterdir(), key=lambda p: p.name)
        if path.is_file()
        and not path.name.startswith((".", _OFFICE_LOCK_PREFIX))
        and path.suffix.lower() in allowed
    ]
    if not selected:
        raise SourceError(
            f"No hay documentos que cargar en {directory} (extensiones admitidas: {', '.join(sorted(allowed))})"
        )
    by_id: dict[str, list[Path]] = {}
    for path in selected:
        by_id.setdefault(path.stem, []).append(path)
    duplicated = {doc_id: paths for doc_id, paths in by_id.items() if len(paths) > 1}
    if duplicated:
        detail = "; ".join(f"{doc_id}: {', '.join(p.name for p in paths)}" for doc_id, paths in duplicated.items())
        raise SourceError(f"Hay documentos con el mismo doc_id: {detail}")
    return [SourceFile(doc_id=path.stem, path=path, source_type=path.suffix.lower().lstrip(".")) for path in selected]
