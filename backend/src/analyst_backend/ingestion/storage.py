"""Almacenamiento en DuckDB: esquema, descripciones y publicación atómica."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable, Mapping
from pathlib import Path

import duckdb
import pandas as pd

# Sin red: la ingesta no necesita extensiones y no debe descargarlas.
CONNECTION_CONFIG = {"autoinstall_known_extensions": False, "autoload_known_extensions": False}

TABLE_DDL: dict[str, str] = {
    "sales": """
        CREATE TABLE sales (
            registro_id VARCHAR PRIMARY KEY,
            mes VARCHAR NOT NULL,
            marca VARCHAR NOT NULL,
            region VARCHAR NOT NULL,
            canal VARCHAR NOT NULL,
            punto_venta_id VARCHAR NOT NULL,
            presentacion VARCHAR NOT NULL,
            unidades INTEGER NOT NULL CHECK (unidades >= 0),
            venta_neta_cop BIGINT NOT NULL CHECK (venta_neta_cop >= 0),
            source_line INTEGER NOT NULL,
            ingestion_id VARCHAR NOT NULL
        )""",
    "sales_review": """
        CREATE TABLE sales_review (
            registro_id VARCHAR,
            mes VARCHAR,
            marca VARCHAR,
            region VARCHAR,
            canal VARCHAR,
            punto_venta_id VARCHAR,
            presentacion VARCHAR,
            unidades VARCHAR,
            venta_neta_cop VARCHAR,
            source_line INTEGER NOT NULL,
            rule_codes VARCHAR NOT NULL,
            reason VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            ingestion_id VARCHAR NOT NULL
        )""",
    "dq_issues": """
        CREATE TABLE dq_issues (
            issue_id INTEGER PRIMARY KEY,
            registro_id VARCHAR,
            source_line INTEGER NOT NULL,
            rule_code VARCHAR NOT NULL,
            issue_type VARCHAR NOT NULL,
            severity VARCHAR NOT NULL,
            column_name VARCHAR,
            original_value VARCHAR,
            new_value VARCHAR,
            action VARCHAR NOT NULL,
            affected_net_sales_cop BIGINT,
            details VARCHAR,
            ingestion_id VARCHAR NOT NULL
        )""",
    "ingestion_runs": """
        CREATE TABLE ingestion_runs (
            ingestion_id VARCHAR PRIMARY KEY,
            source_path VARCHAR NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            started_at TIMESTAMP NOT NULL,
            rows_read INTEGER NOT NULL,
            rows_sales INTEGER NOT NULL,
            rows_review INTEGER NOT NULL,
            rows_excluded INTEGER NOT NULL,
            rows_removed INTEGER NOT NULL
        )""",
}

TABLE_COMMENTS: dict[str, str] = {
    "sales": (
        "Ventas limpias. Única fuente de cifras del asistente: no incluye filas en revisión "
        "(sales_review) ni filas excluidas o eliminadas por las reglas de calidad (ver dq_issues)."
    ),
    "sales_review": (
        "Filas retenidas para revisión humana (reglas DQ04 fuera de catálogo, DQ05, DQ08, DQ13), "
        "tal como llegaron en el CSV. No cuentan en ninguna cifra."
    ),
    "dq_issues": "Cada actuación de una regla de calidad (corrección, error o aviso) sobre una fila del CSV.",
    "ingestion_runs": "Carga publicada: archivo de origen, su huella y cuántas filas fueron a cada destino.",
}

_RAW = "Valor tal como llegó en el CSV (texto, sin recortar)"
COLUMN_COMMENTS: dict[str, dict[str, str]] = {
    "sales": {
        "registro_id": "Identificador único del registro comercial",
        "mes": "Mes del registro, formato AAAA-MM",
        "marca": "Marca comercial, escrita como en el catálogo de semantic_layer.yaml",
        "region": "Región comercial, escrita como en el catálogo",
        "canal": "Canal de venta, escrito como en el catálogo",
        "punto_venta_id": "Identificador operativo del punto de venta",
        "presentacion": "Presentación del producto, escrita como en el catálogo",
        "unidades": "Unidades registradas (entero >= 0)",
        "venta_neta_cop": "Venta neta en pesos colombianos (entero >= 0, sin decimales)",
        "source_line": "Línea física del CSV de origen (encabezado = línea 1)",
        "ingestion_id": "Carga que produjo la fila (ver ingestion_runs)",
    },
    "sales_review": {
        "registro_id": _RAW,
        "mes": _RAW,
        "marca": _RAW,
        "region": _RAW,
        "canal": _RAW,
        "punto_venta_id": _RAW,
        "presentacion": _RAW,
        "unidades": _RAW,
        "venta_neta_cop": _RAW,
        "source_line": "Línea física del CSV de origen",
        "rule_codes": "Reglas que retuvieron la fila, ordenadas y separadas por comas",
        "reason": "Motivo legible de la retención",
        "status": "Estado de la revisión (en_revision)",
        "ingestion_id": "Carga que produjo la fila",
    },
    "dq_issues": {
        "issue_id": "Identificador de la incidencia dentro de la carga",
        "registro_id": "registro_id de la fila afectada (recortado)",
        "source_line": "Línea física del CSV de la fila afectada",
        "rule_code": "Código de la regla (DQ01..DQ13)",
        "issue_type": "Tipo de incidencia (por ejemplo mes_invalido)",
        "severity": "correccion, error o aviso",
        "column_name": "Columna afectada, si aplica",
        "original_value": "Valor original, si aplica",
        "new_value": "Valor corregido, si la regla corrige",
        "action": "corregida, ninguna o el destino final de la fila (eliminada, excluida, en_revision)",
        "affected_net_sales_cop": "Venta neta registrada en la fila si es un entero; nula si no es cuantificable",
        "details": "JSON con datos propios de la regla (diferencias, columnas, mediana, precio)",
        "ingestion_id": "Carga que produjo la incidencia",
    },
    "ingestion_runs": {
        "ingestion_id": "Identificador determinista de la carga (huella del CSV y de la configuración)",
        "source_path": "Ruta del CSV cargado",
        "source_sha256": "Huella SHA-256 del CSV cargado",
        "started_at": "Fecha y hora de la carga (UTC)",
        "rows_read": "Filas de datos leídas del CSV",
        "rows_sales": "Filas publicadas en sales",
        "rows_review": "Filas retenidas en sales_review",
        "rows_excluded": "Filas excluidas (DQ06, DQ07)",
        "rows_removed": "Filas eliminadas por duplicado (DQ01)",
    },
}


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def write_tables(connection: duckdb.DuckDBPyConnection, tables: Mapping[str, pd.DataFrame]) -> None:
    """Crea las cuatro tablas, inserta los datos y añade las descripciones."""
    for name, ddl in TABLE_DDL.items():
        connection.execute(ddl)
        frame = tables[name]
        columns = list(COLUMN_COMMENTS[name])
        connection.register("incoming", frame[columns])
        try:
            connection.execute(f"INSERT INTO {name} SELECT {', '.join(columns)} FROM incoming")
        finally:
            connection.unregister("incoming")
        connection.execute(f"COMMENT ON TABLE {name} IS {_quote(TABLE_COMMENTS[name])}")
        for column, comment in COLUMN_COMMENTS[name].items():
            connection.execute(f"COMMENT ON COLUMN {name}.{column} IS {_quote(comment)}")


def _temporary_files(destination: Path) -> list[Path]:
    return sorted(destination.parent.glob(f"{destination.name}.tmp-*"))


def _replace_keeping_old_wal_until_done(temporary: Path, destination: Path) -> None:
    """Publica ``temporary`` en ``destination``.

    Un WAL antiguo del destino se aplicaría a la base nueva al abrirla, así que se
    aparta antes del reemplazo y se borra después. Si el reemplazo falla, vuelve a
    su sitio y la base anterior queda completa.
    """
    old_wal = destination.with_name(f"{destination.name}.wal")
    parked = destination.with_name(f"{destination.name}.wal.old-{os.getpid()}")
    if old_wal.exists():
        os.replace(old_wal, parked)
    try:
        os.replace(temporary, destination)
    except BaseException:
        if parked.exists():
            os.replace(parked, old_wal)
        raise
    parked.unlink(missing_ok=True)


def publish(destination: Path, writer: Callable[[duckdb.DuckDBPyConnection], None]) -> None:
    """Construye la base en un temporal del mismo directorio y la publica con ``os.replace``.

    Si ``writer`` o cualquier paso falla, el destino anterior queda intacto y el
    temporal se borra. Al empezar se borran temporales huérfanos de cargas interrumpidas.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    for orphan in _temporary_files(destination):
        orphan.unlink(missing_ok=True)
    temporary = destination.with_name(f"{destination.name}.tmp-{os.getpid()}")
    connection = duckdb.connect(str(temporary), config=CONNECTION_CONFIG)
    try:
        writer(connection)
        connection.execute("CHECKPOINT")
        connection.close()
        _replace_keeping_old_wal_until_done(temporary, destination)
    except BaseException:
        with contextlib.suppress(duckdb.Error):
            connection.close()
        for leftover in _temporary_files(destination):
            leftover.unlink(missing_ok=True)
        raise
