"""Requisitos: Métricas definidas en configuración, Expresiones de métricas seguras,
Dimensiones consultables y Alias y escritura de los valores."""

from __future__ import annotations

from pathlib import Path

import pytest

from analyst_backend.analytics.models import QueryError
from analyst_backend.analytics.semantic import (
    AggregateMetric,
    RatioMetric,
    SemanticLayerError,
    load_semantic_layer,
)

ROOT = Path(__file__).resolve().parents[3]
REPO_LAYER = ROOT / "backend/config/semantic_layer.yaml"

BASE_DIMENSIONS = """
dimensions:
  marca:
    description: Marca
    values: [Brio, Luma]
    aliases:
      Brío: Brio
"""


def _layer(tmp_path: Path, metrics: str, dimensions: str = BASE_DIMENSIONS) -> Path:
    path = tmp_path / "semantic_layer.yaml"
    path.write_text(dimensions + "metrics:\n" + metrics, encoding="utf-8")
    return path


def _metric(name: str, body: str) -> str:
    return f"  {name}:\n    description: d\n    unit: u\n    decimals: 0\n{body}"


# --- Métricas definidas en configuración ----------------------------------------------------


def test_repository_metrics() -> None:
    layer = load_semantic_layer(REPO_LAYER)

    assert set(layer.metrics) == {"venta_neta", "unidades", "precio_efectivo", "registros"}
    for name in ("venta_neta", "unidades", "registros"):
        assert isinstance(layer.metrics[name], AggregateMetric)
    ratio = layer.metrics["precio_efectivo"]
    assert isinstance(ratio, RatioMetric)
    assert (ratio.numerator, ratio.denominator) == ("venta_neta", "unidades")
    assert all(m.description and m.unit and m.decimals >= 0 for m in layer.metrics.values())


def test_ratio_with_unknown_metric_is_rejected(tmp_path: Path) -> None:
    metrics = _metric("venta", "    expression: SUM(venta_neta_cop)\n") + _metric(
        "precio", "    ratio:\n      numerator: venta\n      denominator: margen\n"
    )

    with pytest.raises(SemanticLayerError, match="margen"):
        load_semantic_layer(_layer(tmp_path, metrics))


def test_fingerprint_changes_with_the_file(tmp_path: Path) -> None:
    first = load_semantic_layer(_layer(tmp_path, _metric("venta", "    expression: SUM(venta_neta_cop)\n")))
    second = load_semantic_layer(
        _layer(tmp_path, _metric("venta", "    expression: SUM(venta_neta_cop)\n").replace("d\n", "otra\n", 1))
    )

    assert len(first.fingerprint) == 64
    assert first.fingerprint != second.fingerprint


# --- Expresiones de métricas seguras -----------------------------------------------------------


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ('"SUM(unidades); DROP TABLE sales"', "mala"),
        ('"SUM(unidades) /*"', "mala"),
        ('"SUM(unidades) -- comentario"', "mala"),
        ('"SUM(descuento)"', "descuento"),
        ('"unidades * 2"', "mala"),
        ('"lower(marca)"', "mala"),
        ('"SUM(unidades"', "mala"),
        ('"SUM(SUM(unidades))"', "anidadas"),
    ],
)
def test_unsafe_expressions_are_rejected(tmp_path: Path, expression: str, expected: str) -> None:
    with pytest.raises(SemanticLayerError, match=expected):
        load_semantic_layer(_layer(tmp_path, _metric("mala", f"    expression: {expression}\n")))


@pytest.mark.parametrize("expression", ["SUM(venta_neta_cop)", "COUNT(*)", "SUM(venta_neta_cop) / SUM(unidades) * 100"])
def test_safe_expressions_are_accepted(tmp_path: Path, expression: str) -> None:
    layer = load_semantic_layer(_layer(tmp_path, _metric("ok", f'    expression: "{expression}"\n')))

    assert isinstance(layer.metrics["ok"], AggregateMetric)


# --- Dimensiones consultables ----------------------------------------------------------------------


def test_repository_dimensions() -> None:
    layer = load_semantic_layer(REPO_LAYER)

    assert set(layer.dimensions) == {"marca", "region", "canal", "presentacion", "punto_venta_id", "mes"}
    assert layer.dimensions["punto_venta_id"].values is None
    assert layer.dimensions["mes"].time


def test_column_that_is_not_a_dimension_is_rejected() -> None:
    layer = load_semantic_layer(REPO_LAYER)

    with pytest.raises(QueryError) as error:
        layer.dimension("unidades", "group_by")

    assert error.value.field == "group_by"
    assert set(error.value.valid_options) == set(layer.dimensions)


def test_yaml_cannot_declare_other_columns_as_dimensions(tmp_path: Path) -> None:
    dimensions = BASE_DIMENSIONS + "  unidades:\n    description: no\n"

    with pytest.raises(SemanticLayerError, match="unidades"):
        load_semantic_layer(_layer(tmp_path, _metric("v", "    expression: SUM(unidades)\n"), dimensions))


# --- Alias y escritura de los valores ----------------------------------------------------------------


def test_brand_alias() -> None:
    assert load_semantic_layer(REPO_LAYER).dimensions["marca"].resolve("Brío", "filters.marca") == "Brio"


def test_case_insensitive_value() -> None:
    assert load_semantic_layer(REPO_LAYER).dimensions["region"].resolve("sur", "filters.region") == "Sur"


def test_unknown_value_lists_valid_options() -> None:
    region = load_semantic_layer(REPO_LAYER).dimensions["region"]

    with pytest.raises(QueryError) as error:
        region.resolve("Caribe", "filters.region")

    assert error.value.field == "filters.region"
    assert set(error.value.valid_options) == {"Norte", "Centro", "Sur", "Oriente", "Occidente"}


def test_alias_to_unknown_value_is_rejected(tmp_path: Path) -> None:
    dimensions = BASE_DIMENSIONS.replace("Brío: Brio", "Bryo: Brioo")

    with pytest.raises(SemanticLayerError, match="Brioo"):
        load_semantic_layer(_layer(tmp_path, _metric("v", "    expression: SUM(unidades)\n"), dimensions))
