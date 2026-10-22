"""Requisitos: Carga del CSV a DuckDB, Idempotencia y Comando de ingesta."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import duckdb
import pytest

from analyst_backend.ingestion.pipeline import ingest
from analyst_backend.settings import INGESTION_VARIABLES, IngestionSettings, load_ingestion_settings

TABLES = ("sales", "sales_review", "dq_issues", "ingestion_runs")
MAKE = shutil.which("make")


def _settings(paths: Any, csv: Path, db: Path) -> IngestionSettings:
    return IngestionSettings(csv, db, paths.semantic_layer, paths.data_quality)


def _rows(db: Path, table: str, exclude: tuple[str, ...] = ()) -> list[tuple[Any, ...]]:
    with duckdb.connect(str(db), read_only=True) as connection:
        columns = [c[0] for c in connection.execute(f"DESCRIBE {table}").fetchall() if c[0] not in exclude]
        return connection.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY ALL").fetchall()


# --- Carga del CSV a DuckDB ---------------------------------------------------------------


def test_real_file_creates_all_tables_without_touching_the_csv(paths: Any, tmp_path: Path) -> None:
    before = hashlib.sha256(paths.real_csv.read_bytes()).hexdigest()
    db = tmp_path / "analytics.duckdb"

    ingest(_settings(paths, paths.real_csv, db))

    with duckdb.connect(str(db), read_only=True) as connection:
        tables = {row[0] for row in connection.execute("SELECT table_name FROM duckdb_tables()").fetchall()}
    assert tables == set(TABLES)
    assert hashlib.sha256(paths.real_csv.read_bytes()).hexdigest() == before


def test_csv_without_bom_gives_same_sales(paths: Any, tmp_path: Path) -> None:
    raw = paths.real_csv.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    no_bom = tmp_path / "sin_bom.csv"
    no_bom.write_bytes(raw[3:])

    ingest(_settings(paths, paths.real_csv, tmp_path / "con_bom.duckdb"))
    ingest(_settings(paths, no_bom, tmp_path / "sin_bom.duckdb"))

    assert _rows(tmp_path / "con_bom.duckdb", "sales", exclude=("ingestion_id",)) == _rows(
        tmp_path / "sin_bom.duckdb", "sales", exclude=("ingestion_id",)
    )


def test_paths_come_from_environment_variables(
    paths: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    csv_copy = tmp_path / "entrada" / "ventas.csv"
    csv_copy.parent.mkdir()
    csv_copy.write_bytes(paths.real_csv.read_bytes())
    db = tmp_path / "otra" / "ruta" / "base.duckdb"
    monkeypatch.setenv("SALES_CSV_PATH", str(csv_copy))
    monkeypatch.setenv("DUCKDB_PATH", str(db))
    monkeypatch.setenv("SEMANTIC_LAYER_PATH", str(paths.semantic_layer))
    monkeypatch.setenv("DATA_QUALITY_PATH", str(paths.data_quality))
    assert len(INGESTION_VARIABLES) == 4

    summary = ingest(load_ingestion_settings())

    assert summary.duckdb_path == db
    assert db.is_file()
    assert summary.counts["rows_sales"] == 3995


def test_columns_in_another_order_load_completely(paths: Any, tmp_path: Path, valid_row: dict[str, str]) -> None:
    columns = list(reversed(paths.header.split(",")))
    csv = tmp_path / "ventas.csv"
    csv.write_text(",".join(columns) + "\n" + ",".join(valid_row[c] for c in columns) + "\n", encoding="utf-8")
    db = tmp_path / "analytics.duckdb"

    summary = ingest(_settings(paths, csv, db))

    assert summary.counts["rows_sales"] == 1
    with duckdb.connect(str(db), read_only=True) as connection:
        row = connection.execute(
            "SELECT registro_id, mes, marca, region, canal, punto_venta_id, presentacion, unidades, venta_neta_cop "
            "FROM sales"
        ).fetchone()
    expected = [valid_row[c] for c in ("registro_id", "mes", "marca", "region", "canal", "punto_venta_id", "presentacion")]
    assert row == (*expected, int(valid_row["unidades"]), int(valid_row["venta_neta_cop"]))


def test_stale_wal_of_destination_is_removed(paths: Any, tmp_path: Path) -> None:
    db = tmp_path / "analytics.duckdb"
    stale = tmp_path / "analytics.duckdb.wal"
    stale.write_bytes(b"wal de una base anterior")

    ingest(_settings(paths, paths.real_csv, db))

    assert not stale.exists()
    with duckdb.connect(str(db), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM sales").fetchone() == (3995,)


# --- Idempotencia ------------------------------------------------------------------------------


def test_two_loads_produce_identical_tables(paths: Any, tmp_path: Path) -> None:
    first, second = tmp_path / "a.duckdb", tmp_path / "b.duckdb"

    ingest(_settings(paths, paths.real_csv, first))
    ingest(_settings(paths, paths.real_csv, second))

    for table in ("sales", "sales_review", "dq_issues"):
        assert _rows(first, table) == _rows(second, table), table
    assert _rows(first, "ingestion_runs", exclude=("started_at",)) == _rows(
        second, "ingestion_runs", exclude=("started_at",)
    )


# --- Comando de ingesta ----------------------------------------------------------------------------


def _make_ingest(paths: Any, **overrides: str) -> subprocess.CompletedProcess[str]:
    assert MAKE is not None
    env = {**os.environ, **overrides}
    return subprocess.run([MAKE, "ingest"], cwd=paths.root, env=env, capture_output=True, text=True)


@pytest.mark.skipif(MAKE is None, reason="make no está instalado")
def test_make_ingest_publishes_the_database(paths: Any, tmp_path: Path) -> None:
    db = tmp_path / "analytics.duckdb"

    result = _make_ingest(paths, DUCKDB_PATH=str(db))

    assert result.returncode == 0, result.stderr
    assert db.is_file()
    assert "3995 en sales" in result.stdout


@pytest.mark.skipif(MAKE is None, reason="make no está instalado")
def test_make_ingest_reports_errors(paths: Any, tmp_path: Path) -> None:
    missing = tmp_path / "no_existe.csv"

    result = _make_ingest(paths, SALES_CSV_PATH=str(missing), DUCKDB_PATH=str(tmp_path / "x.duckdb"))

    assert result.returncode != 0
    assert str(missing) in result.stderr


def test_failed_replace_restores_previous_wal(
    paths: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "analytics.duckdb"
    ingest(_settings(paths, paths.real_csv, db))
    wal = tmp_path / "analytics.duckdb.wal"
    wal.write_bytes(b"wal de la base anterior")
    real_replace = os.replace

    def failing_replace(source: Any, target: Any) -> None:
        if str(target) == str(db):
            raise OSError("reemplazo simulado fallido")
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError, match="reemplazo simulado"):
        ingest(_settings(paths, paths.real_csv, db))

    assert wal.read_bytes() == b"wal de la base anterior"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["analytics.duckdb", "analytics.duckdb.wal"]
