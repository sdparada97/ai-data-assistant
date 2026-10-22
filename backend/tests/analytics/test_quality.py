"""Requisitos: Filtros de calidad de datos, Resultado de calidad de datos y el escenario
"Evidencia de calidad_datos" de Trazabilidad de los resultados."""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from typing import Any

import duckdb
import pytest

from analyst_backend.analytics import quality
from analyst_backend.analytics.database import DatabaseError

from analyst_backend.analytics.models import QualityQuery, QualityResult, QueryError
from analyst_backend.analytics.quality import calidad_datos
from analyst_backend.analytics.semantic import SemanticLayer


@pytest.fixture
def run(real_db: Any, layer: SemanticLayer) -> Callable[..., QualityResult]:
    def _run(**query: Any) -> QualityResult:
        return calidad_datos(QualityQuery(**query), layer, real_db.path)

    return _run


def _ids(result: QualityResult, rule_code: str | None = None) -> list[str | None]:
    return [n.registro_id for n in result.issues if rule_code is None or n.rule_code == rule_code]


# --- Filtros de calidad de datos -------------------------------------------------------------


def test_period_filter_includes_invalid_months(run: Callable[..., QualityResult]) -> None:
    result = run(filters={"marca": ["Brio"]}, periods=["2026-T2"])
    by_id = {(n.registro_id, n.rule_code): n for n in result.issues}

    assert by_id[("V03997", "DQ07")].mes == "2026-05"
    assert by_id[("V03999", "DQ05")].outside_periods
    t2_months = {"2026-04", "2026-05", "2026-06"}
    assert all(n.mes in t2_months or n.outside_periods for n in result.issues)
    assert not any(n.mes in {"2026-01", "2026-02", "2026-03"} for n in result.issues)


def test_unknown_rule_code_is_rejected(run: Callable[..., QualityResult]) -> None:
    with pytest.raises(QueryError) as error:
        run(rule_codes=["X1"])

    assert error.value.field == "rule_codes"


# --- Resultado de calidad de datos -------------------------------------------------------------


def test_without_filters(run: Callable[..., QualityResult]) -> None:
    result = run()

    assert (result.issue_count, result.corrections_count, len(result.issues), len(result.review_rows)) == (11, 3, 8, 2)
    assert result.ingestion.model_dump() == {
        "rows_read": 4000,
        "rows_sales": 3995,
        "rows_review": 2,
        "rows_excluded": 2,
        "rows_removed": 1,
    }
    assert result.affected_by_action["excluida"] == 935000
    assert sum(item.count for item in result.by_rule_action) == 11


def test_brand_in_south(run: Callable[..., QualityResult]) -> None:
    result = run(filters={"marca": ["Brío"], "region": ["Sur"]})

    assert "V03997" in _ids(result, "DQ07")
    assert result.corrections_count == 1


def test_rule_filter(run: Callable[..., QualityResult]) -> None:
    result = run(rule_codes=["dq05"])

    assert _ids(result) == ["V03999"]
    assert [row["registro_id"] for row in result.review_rows] == ["V03999"]


def test_corrections_listed_on_request(run: Callable[..., QualityResult]) -> None:
    result = run(include_corrections=True)

    assert len(result.issues) == 11


def test_missing_ingestion_counts_raise_instead_of_zeros(
    real_db: Any, layer: SemanticLayer, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy = tmp_path / "sin_carga.duckdb"
    shutil.copy(real_db.path, copy)
    with duckdb.connect(str(copy)) as writer:
        writer.execute("DELETE FROM ingestion_runs")
    monkeypatch.setattr(quality, "published_ingestion_id", lambda connection: "id-de-prueba")

    with pytest.raises(DatabaseError, match="make ingest"):
        calidad_datos(QualityQuery(), layer, copy)


# --- Evidencia de calidad_datos -------------------------------------------------------------------


def test_quality_evidence_is_deterministic(run: Callable[..., QualityResult], real_db: Any) -> None:
    first = run(filters={"marca": ["Brio"]}, periods=["2026-T2"])
    second = run(filters={"marca": ["brío"]}, periods=["2026-t2"])

    assert re.fullmatch(r"EV-[0-9a-f]{12}", first.evidence_id)
    assert first.evidence_id == second.evidence_id
    assert first.ingestion_id == second.ingestion_id == real_db.ingestion_id
