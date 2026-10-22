"""Conexión de solo lectura para las herramientas de consulta."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb

from analyst_backend.ingestion.rules import ROW_DIMENSIONS

READ_ONLY_CONFIG = {
    "enable_external_access": False,
    "autoinstall_known_extensions": False,
    "autoload_known_extensions": False,
}
# Columnas mínimas que las herramientas necesitan. Una base anterior sin ellas debe recargarse.
REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "sales": ("registro_id", "mes", "unidades", "venta_neta_cop", "ingestion_id"),
    "dq_issues": ("rule_code", "severity", "action", "affected_net_sales_cop", *ROW_DIMENSIONS),
    "sales_review": ("source_line", "rule_codes", "reason"),
    "ingestion_runs": ("ingestion_id", "rows_read", "rows_sales", "rows_review", "rows_excluded", "rows_removed"),
}
RELOAD_HINT = "Ejecuta `make ingest` para crearla o actualizarla."


class DatabaseError(RuntimeError):
    """La base no existe o no tiene el esquema que esperan las herramientas."""


def _check_schema(connection: duckdb.DuckDBPyConnection, path: Path) -> None:
    present: dict[str, set[str]] = {}
    for table, column in connection.execute(
        "SELECT table_name, column_name FROM duckdb_columns() WHERE NOT internal"
    ).fetchall():
        present.setdefault(table, set()).add(column)
    missing = [
        f"{table}.{column}"
        for table, columns in REQUIRED_COLUMNS.items()
        for column in columns
        if column not in present.get(table, set())
    ]
    if missing:
        raise DatabaseError(f"La base {path} no tiene el esquema esperado (faltan {', '.join(missing)}). {RELOAD_HINT}")


@contextmanager
def open_readonly(path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    """Abre la base en solo lectura, sin acceso externo ni extensiones, con la configuración bloqueada."""
    if not path.is_file():
        raise DatabaseError(f"No existe la base de ventas {path}. {RELOAD_HINT}")
    connection = duckdb.connect(str(path), read_only=True, config=READ_ONLY_CONFIG)
    try:
        connection.execute("SET lock_configuration = true")
        _check_schema(connection, path)
        yield connection
    finally:
        connection.close()


def published_ingestion_id(connection: duckdb.DuckDBPyConnection) -> str:
    row = connection.execute("SELECT ingestion_id FROM ingestion_runs").fetchone()
    if row is None:
        raise DatabaseError(f"La base no tiene una carga registrada en ingestion_runs. {RELOAD_HINT}")
    return str(row[0])
