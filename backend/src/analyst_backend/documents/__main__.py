"""Punto de entrada de `make ingest-docs`: `python -m analyst_backend.documents`."""

from __future__ import annotations

import sys

from analyst_backend.documents.errors import DocumentsError
from analyst_backend.documents.ingest import ingest_documents
from analyst_backend.settings import SettingsError, load_documents_settings


def main() -> int:
    try:
        summary = ingest_documents(load_documents_settings())
    except (DocumentsError, SettingsError) as error:
        print(f"Error de ingesta de documentos: {error}", file=sys.stderr)
        return 1
    detail = ", ".join(f"{doc_id}: {count}" for doc_id, count in summary.chunks_per_document.items())
    print(
        f"Documentos publicados en {summary.documents_db_path} (ingestion_id {summary.ingestion_id}): "
        f"{summary.chunk_count} fragmentos ({detail}) con el modelo {summary.model_name}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
