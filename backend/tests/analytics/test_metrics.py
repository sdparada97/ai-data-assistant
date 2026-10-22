"""Requisitos de consultar_metrica: Validación de la consulta, Consulta de métricas en un
período, Valores de las métricas, Comparación entre dos períodos, Orden y ranking, Datos
faltantes, Variación no definida, Avisos de calidad en el resultado y Trazabilidad."""

from __future__ import annotations

import re
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import (
    ComparisonCell,
    MetricCell,
    MetricQuery,
    MetricResult,
    QualityQuery,
    QueryError,
)
from analyst_backend.analytics.quality import calidad_datos
from analyst_backend.analytics.semantic import SemanticLayer, load_semantic_layer
from analyst_backend.ingestion.pipeline import ingest
from analyst_backend.settings import IngestionSettings

ROOT = Path(__file__).resolve().parents[3]
T1_T2 = {"base": "2026-T1", "target": "2026-T2"}


@pytest.fixture
def run(real_db: Any, layer: SemanticLayer) -> Callable[..., MetricResult]:
    def _run(**query: Any) -> MetricResult:
        return consultar_metrica(MetricQuery(**query), layer, real_db.path)

    return _run


def _by_group(result: MetricResult, dimension: str) -> dict[str, Any]:
    return {row.group[dimension]: row for row in result.rows}


def _single(cell: Any) -> MetricCell:
    assert isinstance(cell, MetricCell)
    return cell


def _comparison(cell: Any) -> ComparisonCell:
    assert isinstance(cell, ComparisonCell)
    return cell


# --- Validación de la consulta -----------------------------------------------------------------


def test_alias_gives_same_rows_and_evidence(run: Callable[..., MetricResult]) -> None:
    with_alias = run(metrics=["venta_neta"], filters={"marca": ["Brío"]}, group_by=["region"], period="2026-T1")
    plain = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, group_by=["region"], period="2026-T1")

    assert with_alias.rows == plain.rows
    assert with_alias.evidence_id == plain.evidence_id


def test_unknown_metric_lists_metrics(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(QueryError) as error:
        run(metrics=["margen"], period="2026-T1")

    assert error.value.field == "metrics"
    assert set(error.value.valid_options) == {"venta_neta", "unidades", "precio_efectivo", "registros"}


def test_unknown_catalog_value(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(QueryError) as error:
        run(metrics=["venta_neta"], filters={"region": ["Caribe"]}, period="2026-T1")

    assert error.value.field == "filters.region"
    assert set(error.value.valid_options) == {"Norte", "Centro", "Sur", "Oriente", "Occidente"}


def test_unknown_dimension(run: Callable[..., MetricResult], layer: SemanticLayer) -> None:
    with pytest.raises(QueryError) as error:
        run(metrics=["venta_neta"], group_by=["ciudad"], period="2026-T1")

    assert error.value.field == "group_by"
    assert set(error.value.valid_options) == set(layer.dimensions)


def test_period_and_compare_together_are_rejected(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(ValidationError, match="excluyentes"):
        run(metrics=["venta_neta"], period="2026-T1", compare=T1_T2)


def test_invalid_period(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(QueryError, match="AAAA-T1") as error:
        run(metrics=["venta_neta"], period="2026-T5")

    assert error.value.field == "period"


def test_month_cannot_be_a_filter(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(QueryError) as error:
        run(metrics=["venta_neta"], filters={"mes": ["2026-01"]}, period="2026-T1")

    assert error.value.field == "filters.mes"


def test_variation_sort_requires_comparison(run: Callable[..., MetricResult]) -> None:
    with pytest.raises(QueryError) as error:
        run(metrics=["venta_neta"], period="2026-T1", sort={"metric": "venta_neta", "field": "var_pct"})

    assert error.value.field == "sort.field"


# --- Consulta de métricas en un período ------------------------------------------------------------


def test_brand_by_region_in_t1(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brío"]}, group_by=["region"], period="2026-T1")
    rows = _by_group(result, "region")

    assert len(rows) == 5
    assert _single(rows["Sur"].metrics["venta_neta"]).value == 363431600
    assert _single(rows["Centro"].metrics["venta_neta"]).value == 314314900


def test_total_without_grouping(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, period="2026-T2")

    assert len(result.rows) == 1
    assert _single(result.rows[0].metrics["venta_neta"]).value == 1282713700


# --- Valores de las métricas -----------------------------------------------------------------------


def test_effective_price_rounded_and_exact(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["precio_efectivo"], filters={"marca": ["Brio"], "region": ["Sur"]}, period="2026-T1")
    cell = _single(result.rows[0].metrics["precio_efectivo"])

    assert cell.value == Decimal("9973.42")
    assert cell.value_exact == Decimal(363431600) / Decimal(36440)


# --- Comparación entre dos períodos ------------------------------------------------------------------


def test_reference_value_by_region(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, group_by=["region"], compare=T1_T2)
    south = _comparison(_by_group(result, "region")["Sur"].metrics["venta_neta"])

    assert (south.base, south.target, south.var_abs, south.var_pct) == (363431600, 253404600, -110027000, Decimal("-30.27"))
    assert south.var_pct_exact == (Decimal(253404600) / Decimal(363431600) - 1) * 100
    assert _comparison(result.total.metrics["venta_neta"]).var_pct == Decimal("-10.50")


def test_effective_price_variation(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["precio_efectivo"], filters={"marca": ["Brio"], "region": ["Sur"]}, compare=T1_T2)
    cell = _comparison(result.rows[0].metrics["precio_efectivo"])

    assert (cell.base, cell.target, cell.var_pct) == (Decimal("9973.42"), Decimal("9974.99"), Decimal("0.02"))


# --- Orden y ranking ---------------------------------------------------------------------------------

SORT_BY_DROP = {"metric": "venta_neta", "field": "var_pct", "order": "asc"}


def test_region_with_largest_drop(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, group_by=["region"], compare=T1_T2, sort=SORT_BY_DROP)
    ranks = {row.group["region"]: row.rank for row in result.rows}

    assert ranks["Sur"] == 1
    assert ranks["Oriente"] == 5
    assert [row.group["region"] for row in result.rows][0] == "Sur"


def test_limit_keeps_total(run: Callable[..., MetricResult]) -> None:
    result = run(
        metrics=["venta_neta"], filters={"marca": ["Brio"]}, group_by=["region"], compare=T1_T2, sort=SORT_BY_DROP, limit=1
    )

    assert [row.group for row in result.rows] == [{"region": "Sur"}]
    assert result.total.is_total
    assert _comparison(result.total.metrics["venta_neta"]).var_pct == Decimal("-10.50")


def test_ties_share_rank(layer: SemanticLayer, tmp_path: Path) -> None:
    header = "registro_id,mes,marca,region,canal,punto_venta_id,presentacion,unidades,venta_neta_cop"
    rows = [
        "V1,2026-01,Brio,Norte,Tradicional,NO-T-001,Individual,10,100",
        "V2,2026-01,Brio,Sur,Tradicional,SU-T-001,Individual,10,100",
        "V3,2026-01,Brio,Centro,Tradicional,CE-T-001,Individual,10,50",
    ]
    csv = tmp_path / "empate.csv"
    csv.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    db = tmp_path / "empate.duckdb"
    ingest(IngestionSettings(csv, db, ROOT / "backend/config/semantic_layer.yaml", ROOT / "backend/config/data_quality.yaml"))

    result = consultar_metrica(
        MetricQuery(metrics=["venta_neta"], group_by=["region"], period="2026-01", sort={"metric": "venta_neta"}),
        layer,
        db,
    )

    assert {row.group["region"]: row.rank for row in result.rows} == {"Norte": 1, "Sur": 1, "Centro": 3}


# --- Datos faltantes -----------------------------------------------------------------------------------


def test_period_without_data_returns_nulls(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta", "registros"], filters={"marca": ["Brio"]}, period="2025-T1")
    metrics = result.rows[0].metrics

    assert _single(metrics["venta_neta"]).value is None
    assert _single(metrics["registros"]).value is None
    assert "El período 2025-T1 no tiene datos en la base" in result.warnings


def test_partial_period_lists_missing_months(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, period="2026")
    (warning,) = [w for w in result.warnings if "2026-07" in w]

    assert _single(result.rows[0].metrics["venta_neta"]).value == 2715963700
    assert all(f"2026-{m:02d}" in warning for m in range(7, 13))


def test_empty_slice_returns_null(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"punto_venta_id": ["XX-T-999"]}, period="2026-T1")

    assert _single(result.rows[0].metrics["venta_neta"]).value is None
    assert any("Sin datos" in w and "2026-T1" in w for w in result.warnings)


# --- Variación no definida -------------------------------------------------------------------------------


def test_comparison_against_period_without_data(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, compare={"base": "2025-T4", "target": "2026-T1"})
    cell = _comparison(result.rows[0].metrics["venta_neta"])

    assert cell.base is None and cell.var_abs is None and cell.var_pct is None
    assert cell.target == 1433250000
    assert any("2025-T4" in w for w in result.warnings)
    assert any("Variación no definida" in w for w in result.warnings)


# --- Avisos de calidad en el resultado --------------------------------------------------------------------


def test_missing_sales_note_in_south(run: Callable[..., MetricResult], layer: SemanticLayer, real_db: Any) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"], "region": ["Sur"]}, compare=T1_T2)
    (note,) = [n for n in result.quality_notes if n.rule_code == "DQ07"]

    assert (note.registro_id, note.action, note.mes, note.region) == ("V03997", "excluida", "2026-05", "Sur")
    assert not note.outside_periods
    assert result.corrections_count == 1
    corrections = calidad_datos(
        QualityQuery(filters={"marca": ["Brio"], "region": ["Sur"]}, periods=["2026-T1", "2026-T2"], include_corrections=True),
        layer,
        real_db.path,
    )
    assert [n.registro_id for n in corrections.issues if n.severity == "correccion"] == ["V02929"]


def test_invalid_month_note_in_centre(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"], "region": ["Centro"]}, compare=T1_T2)
    (note,) = [n for n in result.quality_notes if n.rule_code == "DQ05"]

    assert note.registro_id == "V03999"
    assert note.outside_periods


def test_slice_without_issues(run: Callable[..., MetricResult]) -> None:
    result = run(metrics=["venta_neta"], filters={"marca": ["Brio"], "region": ["Oriente"]}, period="2026-T1")

    assert result.quality_notes == []


# --- Trazabilidad de los resultados ------------------------------------------------------------------------


def test_equivalent_queries_share_evidence(run: Callable[..., MetricResult]) -> None:
    first = run(metrics=["venta_neta"], filters={"marca": ["Brío"], "region": ["Sur", "Norte"]}, period="2026-T1")
    second = run(metrics=["venta_neta"], filters={"region": ["norte", "Sur"], "marca": ["Brio"]}, period="2026-t1")

    assert re.fullmatch(r"EV-[0-9a-f]{12}", first.evidence_id)
    assert first.evidence_id == second.evidence_id


def test_metric_and_group_order_do_not_change_evidence(run: Callable[..., MetricResult]) -> None:
    first = run(metrics=["unidades", "venta_neta"], group_by=["region", "canal"], period="2026-T1")
    second = run(metrics=["venta_neta", "unidades"], group_by=["canal", "region"], period="2026-T1")

    assert first.evidence_id == second.evidence_id
    assert first.query["metrics"] == ["unidades", "venta_neta"]


def test_different_queries_have_different_evidence(run: Callable[..., MetricResult], real_db: Any) -> None:
    t1 = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, period="2026-T1")
    t2 = run(metrics=["venta_neta"], filters={"marca": ["Brio"]}, period="2026-T2")

    assert t1.evidence_id != t2.evidence_id
    assert t1.periods == {"2026-T1": ["2026-01", "2026-02", "2026-03"]}
    assert t2.periods == {"2026-T2": ["2026-04", "2026-05", "2026-06"]}
    assert "FROM sales" in t1.sql and "?" in t1.sql
    assert t1.sql_params == ["2026-01", "2026-02", "2026-03", "Brio"]
    assert "FROM sales" in t2.sql and "?" in t2.sql
    assert t2.sql_params == ["2026-04", "2026-05", "2026-06", "Brio"]
    assert t1.ingestion_id == real_db.ingestion_id


def test_semantic_layer_change_changes_evidence(real_db: Any, layer: SemanticLayer, tmp_path: Path) -> None:
    changed = tmp_path / "semantic_layer.yaml"
    changed.write_text(
        real_db.semantic_layer_path.read_text(encoding="utf-8").replace(
            "Venta neta en pesos colombianos.", "Venta neta en COP (descripción revisada)."
        ),
        encoding="utf-8",
    )
    query = MetricQuery(metrics=["venta_neta"], filters={"marca": ["Brio"]}, period="2026-T1")

    original = consultar_metrica(query, layer, real_db.path)
    revised = consultar_metrica(query, load_semantic_layer(changed), real_db.path)

    assert original.rows == revised.rows
    assert original.evidence_id != revised.evidence_id
