"""Requisitos de la base publicada: Estructura de las incidencias, Validación de la
entrada (base previa intacta), Validación final con Pandera, Esquema de la tabla de
ventas, Descripción del esquema, Carga atómica, Trazabilidad de la carga y Cuadre de filas."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest

from analyst_backend.ingestion import pipeline, rules, storage
from analyst_backend.ingestion.catalog import load_catalog
from analyst_backend.ingestion.errors import InputError, ReconciliationError, ValidationFailedError
from analyst_backend.ingestion.pipeline import IngestionSummary, ingest
from analyst_backend.ingestion.schema import validate_sales
from analyst_backend.settings import IngestionSettings

WriteCsv = Callable[..., Path]
TABLES = ("sales", "sales_review", "dq_issues", "ingestion_runs")


def _settings(paths: Any, csv: Path, db: Path) -> IngestionSettings:
    return IngestionSettings(csv, db, paths.semantic_layer, paths.data_quality)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def real_db(paths: Any, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, IngestionSummary]:
    db = tmp_path_factory.mktemp("real") / "analytics.duckdb"
    return db, ingest(_settings(paths, paths.real_csv, db))


@pytest.fixture
def con(real_db: tuple[Path, IngestionSummary]) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(str(real_db[0]), read_only=True)
    yield connection
    connection.close()


@pytest.fixture
def previous_db(paths: Any, tmp_path: Path) -> Path:
    """Base publicada por una carga anterior correcta."""
    db = tmp_path / "db" / "analytics.duckdb"
    ingest(_settings(paths, paths.real_csv, db))
    return db


# --- Estructura de las incidencias --------------------------------------------------


def test_dq_issues_columns_and_details(con: duckdb.DuckDBPyConnection) -> None:
    columns = [row[0] for row in con.execute("DESCRIBE dq_issues").fetchall()]
    details = [row[0] for row in con.execute("SELECT details FROM dq_issues").fetchall()]

    assert tuple(columns) == rules.ISSUE_COLUMNS
    for value in details:
        assert value is None or isinstance(json.loads(value), dict)


# --- Validación de la entrada: base previa intacta ------------------------------------


def test_invalid_input_keeps_previous_database(
    previous_db: Path, write_csv: WriteCsv, paths: Any
) -> None:
    before = _sha(previous_db)
    broken = write_csv([{}], header=paths.header.replace(",venta_neta_cop", ""))

    with pytest.raises(InputError, match="venta_neta_cop"):
        ingest(_settings(paths, broken, previous_db))

    assert _sha(previous_db) == before


def test_missing_file_creates_no_database(paths: Any, tmp_path: Path) -> None:
    db = tmp_path / "analytics.duckdb"

    with pytest.raises(InputError, match="no_existe.csv"):
        ingest(_settings(paths, tmp_path / "no_existe.csv", db))

    assert not db.exists()


# --- Validación final con Pandera ------------------------------------------------------


def test_pandera_names_the_failing_column(paths: Any) -> None:
    frame = pd.DataFrame(
        [{"registro_id": "V1", "mes": "2026-01", "marca": "Brio", "region": "Sur", "canal": "Moderno",
          "punto_venta_id": "X", "presentacion": "Individual", "unidades": -1, "venta_neta_cop": 10,
          "source_line": 2, "ingestion_id": "abc"}]
    )

    with pytest.raises(ValidationFailedError, match="unidades"):
        validate_sales(frame, load_catalog(paths.semantic_layer))


def test_row_escaping_the_rules_stops_the_load(
    monkeypatch: pytest.MonkeyPatch, write_csv: WriteCsv, paths: Any, tmp_path: Path
) -> None:
    def no_negative_rule(frame: pd.DataFrame) -> rules.RuleResult:
        return rules.RuleResult(mask=pd.Series(False, index=frame.index))

    monkeypatch.setattr(rules, "check_negative", no_negative_rule)
    db = tmp_path / "analytics.duckdb"

    with pytest.raises(ValidationFailedError, match="unidades"):
        ingest(_settings(paths, write_csv([{"unidades": "-5"}]), db))

    assert not db.exists()


def test_empty_registro_id_stops_the_load(write_csv: WriteCsv, paths: Any, tmp_path: Path) -> None:
    db = tmp_path / "analytics.duckdb"

    with pytest.raises(ValidationFailedError, match="registro_id"):
        ingest(_settings(paths, write_csv([{"registro_id": ""}]), db))

    assert not db.exists()


# --- Esquema de la tabla de ventas -----------------------------------------------------------


def test_sales_types_and_constraints(con: duckdb.DuckDBPyConnection) -> None:
    types = dict(con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE table_name = 'sales'").fetchall())
    bad = con.execute(
        "SELECT count(*) FROM sales WHERE unidades IS NULL OR venta_neta_cop IS NULL "
        "OR unidades < 0 OR venta_neta_cop < 0"
    ).fetchone()
    distinct, total = con.execute("SELECT count(DISTINCT registro_id), count(*) FROM sales").fetchone() or (0, 0)

    assert types["unidades"] == "INTEGER"
    assert types["venta_neta_cop"] == "BIGINT"
    assert bad == (0,)
    assert distinct == total == 3995


# --- Descripción del esquema ------------------------------------------------------------------


def test_every_table_and_column_has_a_comment(con: duckdb.DuckDBPyConnection) -> None:
    table_comments = dict(con.execute("SELECT table_name, comment FROM duckdb_tables() WHERE NOT internal").fetchall())
    column_comments = con.execute(
        "SELECT table_name, column_name, comment FROM duckdb_columns() WHERE NOT internal"
    ).fetchall()

    assert set(table_comments) == set(TABLES)
    assert all(table_comments[t] for t in TABLES)
    assert len(column_comments) == 11 + 14 + 13 + 9
    assert all(comment for _, _, comment in column_comments)
    assert "Única fuente de cifras" in table_comments["sales"]


# --- Carga atómica ---------------------------------------------------------------------------------


def test_failure_after_writing_keeps_previous_database(
    monkeypatch: pytest.MonkeyPatch, previous_db: Path, paths: Any
) -> None:
    before = _sha(previous_db)
    original = storage.write_tables

    def write_then_fail(connection: duckdb.DuckDBPyConnection, tables: Any) -> None:
        original(connection, tables)
        raise RuntimeError("fallo simulado tras escribir")

    monkeypatch.setattr(storage, "write_tables", write_then_fail)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        ingest(_settings(paths, paths.real_csv, previous_db))

    assert _sha(previous_db) == before
    assert sorted(p.name for p in previous_db.parent.iterdir()) == [previous_db.name]


def test_orphan_temporary_file_is_removed(paths: Any, tmp_path: Path) -> None:
    db = tmp_path / "analytics.duckdb"
    orphan = tmp_path / "analytics.duckdb.tmp-99999"
    orphan.write_bytes(b"resto de una carga interrumpida")

    ingest(_settings(paths, paths.real_csv, db))

    assert not orphan.exists()
    assert db.exists()


# --- Trazabilidad de la carga -------------------------------------------------------------------------


def test_single_run_with_source_hash_and_shared_id(
    con: duckdb.DuckDBPyConnection, real_db: tuple[Path, IngestionSummary], paths: Any
) -> None:
    runs = con.execute("SELECT ingestion_id, source_sha256 FROM ingestion_runs").fetchall()
    ids = {
        table: {row[0] for row in con.execute(f"SELECT DISTINCT ingestion_id FROM {table}").fetchall()}
        for table in ("sales", "sales_review", "dq_issues")
    }

    assert runs == [(real_db[1].ingestion_id, _sha(paths.real_csv))]
    assert all(found == {real_db[1].ingestion_id} for found in ids.values())


# --- Cuadre de filas ------------------------------------------------------------------------------------


def test_real_file_reconciliation(con: duckdb.DuckDBPyConnection) -> None:
    row = con.execute(
        "SELECT rows_read, rows_sales, rows_review, rows_excluded, rows_removed FROM ingestion_runs"
    ).fetchone()

    assert row == (4000, 3995, 2, 2, 1)
    assert row[1] + row[2] + row[3] + row[4] == row[0]


def test_broken_reconciliation_stops_the_load(
    monkeypatch: pytest.MonkeyPatch, paths: Any, tmp_path: Path
) -> None:
    original = pipeline._sales_frame
    monkeypatch.setattr(pipeline, "_sales_frame", lambda rows: original(rows).iloc[:-1])
    db = tmp_path / "analytics.duckdb"

    with pytest.raises(ReconciliationError) as error:
        ingest(_settings(paths, paths.real_csv, db))

    message = str(error.value)
    assert all(name in message for name in ("rows_read=4000", "rows_sales=3994", "rows_review=2", "rows_excluded=2", "rows_removed=1"))
    assert not db.exists()
