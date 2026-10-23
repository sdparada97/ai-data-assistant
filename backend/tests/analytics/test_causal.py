"""Evaluación causal con criterios fijos, sobre la base de ventas real y observaciones construidas a mano."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from analyst_backend.analytics.causal import CausalThresholds, assess_cause, validate_request
from analyst_backend.analytics.models import CausalResult, Comparison, QueryError, ValidatedObservation
from analyst_backend.analytics.semantic import SemanticLayer

from .conftest import RealDatabase

THRESHOLDS = CausalThresholds(Decimal("1.0"), Decimal("1.0"), Decimal("0.8"), Decimal("1.5"), Decimal("1.0"),
                              ("punto_venta_id",))
T1_T2 = Comparison(base="2026-T1", target="2026-T2")


def request(layer: SemanticLayer, **overrides: Any) -> Any:
    args: dict[str, Any] = {
        "cause": "promociones de la competencia", "cause_kind": "competencia", "metric": "venta_neta",
        "filters": {"marca": ["Brío"]}, "compare": T1_T2, "locate_by": "region",
        "cause_metric": None, "cause_direction": None, "claimed_segment": None,
    }
    args.update(overrides)
    return validate_request(**args, layer=layer, thresholds=THRESHOLDS)


def segment(value: str, ref: str = "OC-CEN-02", date: str | None = None) -> ValidatedObservation:
    return ValidatedObservation(kind="segmento", chunk_id=f"doc:{ref}", evidence_ref=ref, quote="cita",
                                dimension="region", value=value, date=date)


DESIGN = [
    ValidatedObservation(kind="atribucion", chunk_id="05_Reporte_Comercial:005", evidence_ref="REP-02", quote="70 %"),
    ValidatedObservation(kind="limitacion", chunk_id="03_Investigacion_Consumidor:011", evidence_ref="INV-04",
                         quote="sin causalidad atribuible"),
]


def assess(real_db: RealDatabase, layer: SemanticLayer, observations: list[ValidatedObservation],
           **overrides: Any) -> CausalResult:
    return assess_cause(request(layer, **overrides), observations, layer=layer, duckdb_path=real_db.path,
                        thresholds=THRESHOLDS)


def criterion(result: CausalResult, name: str) -> Any:
    return next(c for c in result.criteria if c.name == name)


# --- Evaluación de una afirmación causal y dimensiones -------------------------------------------


def test_valid_input_and_comparison_group(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Centro"), *DESIGN])

    keys = criterion(result, "comparacion").values
    assert {key.split(" ")[0] for key in keys} == {"Luma", "Nativa", "Rizo", "Senda"}


@pytest.mark.parametrize(("overrides", "field", "text"), [
    ({"locate_by": "ciudad"}, "locate_by", "ciudad"),
    ({"locate_by": "marca"}, "locate_by", "filtrada"),
    ({"filters": {}}, "filters", "competencia"),
    ({"claimed_segment": "Atlántico"}, "claimed_segment", "Atlántico"),
    ({"cause_kind": "metrica_propia"}, "cause_metric", "métrica de la causa"),
    ({"cause_kind": "metrica_propia", "cause_metric": "precio_efectivo"}, "cause_direction", "sentido"),
])
def test_invalid_inputs(layer: SemanticLayer, overrides: dict[str, Any], field: str, text: str) -> None:
    with pytest.raises(QueryError) as error:
        request(layer, **overrides)

    assert error.value.field == field and text in error.value.message


def test_invalid_location_lists_valid_dimensions(layer: SemanticLayer) -> None:
    with pytest.raises(QueryError) as error:
        request(layer, locate_by="ciudad")

    assert "region" in error.value.valid_options and "mes" not in error.value.valid_options
    assert "marca" not in error.value.valid_options


# --- Segmento más afectado ------------------------------------------------------------------------


def test_most_affected_segment(real_db: RealDatabase, layer: SemanticLayer) -> None:
    values = criterion(assess(real_db, layer, []), "localizacion").values

    assert (str(values["total"]), str(values["Sur"])) == ("-10.50", "-30.27")


def test_no_effect_to_evaluate(real_db: RealDatabase, layer: SemanticLayer) -> None:
    with pytest.raises(QueryError, match="No hay efecto"):
        assess(real_db, layer, [], compare=Comparison(base="2026-T1", target="2026-T1"))


# --- Criterios ------------------------------------------------------------------------------------


def test_localization_only_in_centro(real_db: RealDatabase, layer: SemanticLayer) -> None:
    assert criterion(assess(real_db, layer, [segment("Centro")]), "localizacion").result == "no encaja"


def test_localization_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    assert criterion(assess(real_db, layer, [segment("Sur", "OC-SUR-01")]), "localizacion").result == "encaja"


def test_localization_without_observations(real_db: RealDatabase, layer: SemanticLayer) -> None:
    assert criterion(assess(real_db, layer, []), "localizacion").result == "sin observaciones"


def test_competitors_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    comparison = criterion(assess(real_db, layer, []), "comparacion")

    assert comparison.result == "sin efecto diferencial"
    assert {k: str(v) for k, v in comparison.values.items()} == {
        "Luma en Sur": "6.22", "Luma total": "6.13", "Nativa en Sur": "3.71", "Nativa total": "3.63",
        "Rizo en Sur": "-0.78", "Rizo total": "-0.89", "Senda en Sur": "-0.42", "Senda total": "-0.28",
    }


def test_step_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    timing = criterion(assess(real_db, layer, [segment("Sur", "CAM-103", "2026-04-18")]), "temporalidad")

    assert timing.result == "cambio concentrado en 2026-04"
    assert str(timing.values["proporcion"]) == "0.965"
    assert "2026-04-18" in timing.detail


def test_uniform_drop_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    alternatives = criterion(assess(real_db, layer, []), "alternativas")

    assert alternatives.result == "uniforme"
    values = {k: str(v) for k, v in alternatives.values.items()}
    assert values["canal Moderno"] == "-30.26" and values["canal Tradicional"] == "-30.28"
    assert values["presentacion Familiar"] == "-30.33" and values["presentacion Individual"] == "-30.26"
    assert values["punto_venta_id mínimo"] == "-31.01" and values["punto_venta_id máximo"] == "-29.70"
    assert "24 valores" in alternatives.detail


def test_own_price_did_not_change(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [], cause="subida del precio de la marca", cause_kind="metrica_propia",
                    cause_metric="precio_efectivo", cause_direction="sube")

    alternatives = criterion(result, "alternativas")
    assert str(alternatives.values["precio_efectivo en Sur"]) == "0.02"
    assert "sin cambio" in alternatives.result


def test_design_without_attribution_design(real_db: RealDatabase, layer: SemanticLayer) -> None:
    design = criterion(assess(real_db, layer, DESIGN), "diseno")

    assert design.result == "sin diseño que permita atribuir" and design.supports == ["REP-02", "INV-04"]


# --- Veredictos -------------------------------------------------------------------------------------


def test_promotions_only_in_centro(real_db: RealDatabase, layer: SemanticLayer) -> None:
    assert assess(real_db, layer, [segment("Centro"), *DESIGN]).verdict == "no sustentada"


def test_promotions_also_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Centro"), segment("Sur", "CAM-103", "2026-04-18"), *DESIGN])

    assert criterion(result, "localizacion").result == "encaja"
    assert result.verdict == "no sustentada"  # sin efecto diferencial


def test_relative_price(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Sur", "INV-01")], cause="precios de la competencia más bajos")

    assert result.verdict == "no sustentada"


def test_shortages_in_sur(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Sur", "OC-SUR-01")], cause="faltantes de producto",
                    cause_kind="disponibilidad")

    assert result.verdict == "compatible (hipótesis)"
    assert criterion(result, "comparacion").result == "no aplica"


def test_own_price_rise_is_contradicted(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Sur", "INV-01")], cause="subida del precio de la marca",
                    cause_kind="metrica_propia", cause_metric="precio_efectivo", cause_direction="sube")

    assert result.verdict == "contradicha"


def test_own_metric_in_the_opposite_direction(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Sur", "OC-SUR-01")], cause="aumento de unidades",
                    cause_kind="metrica_propia", cause_metric="unidades", cause_direction="sube")

    assert str(criterion(result, "alternativas").values["unidades en Sur"]) == "-30.29"
    assert result.verdict == "contradicha"


def test_effect_located_in_centro(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Sur", "CAM-103")], cause="promociones de la competencia en Centro",
                    claimed_segment="Centro", cause_kind="disponibilidad")

    assert result.verdict == "contradicha"  # prevalece sobre "compatible" por localización


# --- Resultado causal trazable ------------------------------------------------------------------------


def test_every_criterion_has_its_support(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = assess(real_db, layer, [segment("Centro"), *DESIGN])

    assert [c.name for c in result.criteria] == ["localizacion", "comparacion", "temporalidad", "alternativas", "diseno"]
    assert all(c.supports for c in result.criteria)
    assert result.evidence_id == assess(real_db, layer, [segment("Centro"), *DESIGN]).evidence_id


def test_cause_metric_without_data_is_not_supported(layer: SemanticLayer) -> None:
    from analyst_backend.analytics.causal import _verdict
    from analyst_backend.analytics.models import CriterionResult

    own = request(layer, cause="subida del precio de la marca", cause_kind="metrica_propia",
                  cause_metric="precio_efectivo", cause_direction="sube")
    criteria = {name: CriterionResult(name=name, result=result, detail="", values={}, supports=[])
                for name, result in [("localizacion", "sin observaciones"), ("comparacion", "no aplica")]}

    assert _verdict(own, criteria, "sin datos", None) == "no sustentada"
    assert _verdict(own, criteria, "sin cambio", None) == "contradicha"
