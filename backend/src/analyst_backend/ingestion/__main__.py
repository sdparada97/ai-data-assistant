"""Punto de entrada de `make ingest`: `python -m analyst_backend.ingestion`."""

from __future__ import annotations

import sys

from analyst_backend.ingestion.errors import IngestionError
from analyst_backend.ingestion.pipeline import ingest
from analyst_backend.settings import SettingsError, load_ingestion_settings


def main() -> int:
    try:
        summary = ingest(load_ingestion_settings())
    except (IngestionError, SettingsError) as error:
        print(f"Error de ingesta: {error}", file=sys.stderr)
        return 1
    counts = summary.counts
    print(
        f"Ingesta publicada en {summary.duckdb_path} (ingestion_id {summary.ingestion_id}): "
        f"{counts['rows_read']} leídas → {counts['rows_sales']} en sales, {counts['rows_review']} en revisión, "
        f"{counts['rows_excluded']} excluidas, {counts['rows_removed']} eliminadas."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
