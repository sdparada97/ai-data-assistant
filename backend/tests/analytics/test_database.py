"""Requisito: Acceso de solo lectura."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

import duckdb
import pytest

from analyst_backend.analytics.database import DatabaseError, open_readonly, published_ingestion_id


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_is_rejected_and_database_unchanged(real_db: Any) -> None:
    before = _sha(real_db.path)

    with open_readonly(real_db.path) as connection:
        with pytest.raises(duckdb.Error):
            connection.execute("DELETE FROM sales")
        with pytest.raises(duckdb.Error):
            connection.execute("CREATE TABLE intruso (a INTEGER)")

    assert _sha(real_db.path) == before


@pytest.mark.parametrize(
    "statement",
    ["SELECT * FROM read_csv('/etc/passwd')", "INSTALL httpfs", "SET enable_external_access = true"],
)
def test_external_access_and_configuration_are_rejected(real_db: Any, statement: str) -> None:
    with open_readonly(real_db.path) as connection:
        with pytest.raises(duckdb.Error):
            connection.execute(statement)


def test_reads_published_ingestion(real_db: Any) -> None:
    with open_readonly(real_db.path) as connection:
        assert published_ingestion_id(connection) == real_db.ingestion_id
        assert connection.execute("SELECT count(*) FROM sales").fetchone() == (3995,)


def test_missing_database_asks_for_ingest(tmp_path: Path) -> None:
    with pytest.raises(DatabaseError, match="make ingest"):
        with open_readonly(tmp_path / "no_existe.duckdb"):
            pass


def test_old_database_without_issue_dimensions_asks_for_ingest(real_db: Any, tmp_path: Path) -> None:
    old = tmp_path / "vieja.duckdb"
    shutil.copy(real_db.path, old)
    with duckdb.connect(str(old)) as writer:
        writer.execute("ALTER TABLE dq_issues DROP COLUMN marca")

    with pytest.raises(DatabaseError, match=r"dq_issues\.marca.*make ingest"):
        with open_readonly(old):
            pass
