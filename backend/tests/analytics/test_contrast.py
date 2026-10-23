"""Requisitos "Veredicto de una variación", "Veredicto de un ranking y de una dirección" y
"Afirmaciones cualitativas", con la base de ventas real."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from analyst_backend.analytics.contrast import compare_claims, variation_verdict
from analyst_backend.analytics.models import ContrastResult, ValidatedClaim
from analyst_backend.analytics.semantic import SemanticLayer

from .conftest import RealDatabase

BRAND = {"marca": ["Brio"]}
TABLE = "05_Reporte_Comercial:003"


def variation(value: str, reported: str, decimals: int = 0, metric: str = "venta_neta",
              dimension: str = "region", filters: dict[str, list[str]] | None = None) -> ValidatedClaim:
    return ValidatedClaim(
        kind="variacion", chunk_id=TABLE, evidence_ref=TABLE, statement=f"{value}: {reported}",
        metric=metric, dimension=dimension, value=value, filters=filters if filters is not None else BRAND,
        base="2026-T1", target="2026-T2", reported=Decimal(reported), reported_decimals=decimals,
    )


def contrast(real_db: RealDatabase, layer: SemanticLayer, *claims: ValidatedClaim, approx: str = "1.0",
             **kwargs: Any) -> ContrastResult:
    return compare_claims(claims, doc_id="05_Reporte_Comercial", doc_title="Reporte", document_sha256="abc",
                          layer=layer, duckdb_path=real_db.path, approx_pp=Decimal(approx), **kwargs)


def by_value(result: ContrastResult) -> dict[str | None, Any]:
    return {c.claim.value: c for c in result.comparisons}


# --- Veredicto de una variación ----------------------------------------------------------------


def test_regional_table_of_the_report(real_db: RealDatabase, layer: SemanticLayer) -> None:
    rows = [("Centro", "-23"), ("Sur", "-7"), ("Norte", "-4"), ("Oriente", "4"), ("Occidente", "-6")]

    result = contrast(real_db, layer, *(variation(value, reported) for value, reported in rows))

    found = {v: (str(c.actual), str(c.difference), c.verdict) for v, c in by_value(result).items()}
    assert found == {
        "Centro": ("-9.03", "-13.97", "no coincide"),
        "Sur": ("-30.27", "23.27", "no coincide"),
        "Norte": ("-3.48", "-0.52", "aproximado"),
        "Oriente": ("4.65", "-0.65", "aproximado"),
        "Occidente": ("-5.27", "-0.73", "aproximado"),
    }
    assert len(result.queries) == 1
    assert {c.metric_evidence_id for c in result.comparisons} == {result.queries[0].evidence_id}


def test_match_by_rounding(real_db: RealDatabase, layer: SemanticLayer) -> None:
    [comparison] = contrast(real_db, layer, variation("Sur", "-30")).comparisons

    assert comparison.verdict == "coincide"


def test_different_sign(real_db: RealDatabase, layer: SemanticLayer) -> None:
    claim = variation("Sur", "-0.5", decimals=1, metric="precio_efectivo")

    [comparison] = contrast(real_db, layer, claim).comparisons

    assert (str(comparison.actual), comparison.verdict) == ("0.02", "no coincide")
    assert abs(comparison.difference) < 1  # type: ignore[arg-type]


def test_configurable_threshold(real_db: RealDatabase, layer: SemanticLayer) -> None:
    [comparison] = contrast(real_db, layer, variation("Norte", "-4"), approx="0.5").comparisons

    assert comparison.verdict == "no coincide"


@pytest.mark.parametrize(("reported", "decimals", "actual", "expected"), [
    ("-3", 0, "-2.5", "coincide"),        # el empate se aleja de cero: −2.5 → −3
    ("-2", 0, "-2.5", "aproximado"),
    ("0", 0, "0.4", "coincide"),
    ("-0.5", 1, "0.02", "no coincide"),   # signo distinto aunque esté a menos de 1 pp
])
def test_variation_verdict_rules(reported: str, decimals: int, actual: str, expected: str) -> None:
    assert variation_verdict(Decimal(reported), decimals, Decimal(actual), Decimal("1.0"))[1] == expected


# --- Veredicto de un ranking y de una dirección -------------------------------------------------


def ranking(value: str, chunk_id: str) -> ValidatedClaim:
    return ValidatedClaim(kind="ranking", chunk_id=chunk_id, evidence_ref=chunk_id, statement=f"{value} primero",
                          metric="venta_neta", dimension="region", value=value, filters=BRAND,
                          base="2026-T1", target="2026-T2", direction="mayor_caida")


@pytest.mark.parametrize("chunk_id", ["05_Reporte_Comercial:004", "04_Observaciones_Canales:004"])
def test_largest_drop_claimed_for_centro(real_db: RealDatabase, layer: SemanticLayer, chunk_id: str) -> None:
    [comparison] = contrast(real_db, layer, ranking("Centro", chunk_id)).comparisons

    assert comparison.verdict == "falsa"
    assert (comparison.leader, str(comparison.leader_value)) == ("Sur", "-30.27")


def test_ranking_shares_the_query_with_the_variations(real_db: RealDatabase, layer: SemanticLayer) -> None:
    result = contrast(real_db, layer, variation("Centro", "-23"), ranking("Centro", "05_Reporte_Comercial:004"))

    assert len(result.queries) == 1


def test_contraction_of_the_brand(real_db: RealDatabase, layer: SemanticLayer) -> None:
    claim = ValidatedClaim(kind="direccion", chunk_id="05_Reporte_Comercial:002", evidence_ref="05_Reporte_Comercial:002",
                           statement="Brío se contrae", metric="venta_neta", filters=BRAND,
                           base="2026-T1", target="2026-T2", direction="contraccion")

    [comparison] = contrast(real_db, layer, claim).comparisons

    assert (comparison.verdict, str(comparison.actual)) == ("verdadera", "-10.50")


# --- Afirmaciones cualitativas -----------------------------------------------------------------


def test_qualitative_claim_without_query(real_db: RealDatabase, layer: SemanticLayer) -> None:
    claim = ValidatedClaim(kind="cualitativa", chunk_id="05_Reporte_Comercial:006", evidence_ref="REP-03",
                           statement="REP-03: afirmación cualitativa")

    result = contrast(real_db, layer, claim)

    assert [c.verdict for c in result.comparisons] == ["no verificable con los datos"]
    assert result.queries == []


# --- Resultado trazable -------------------------------------------------------------------------


def test_same_input_same_result(real_db: RealDatabase, layer: SemanticLayer) -> None:
    claims = [variation("Centro", "-23"), variation("Sur", "-7")]

    first, second = contrast(real_db, layer, *claims), contrast(real_db, layer, *claims)

    assert first.evidence_id == second.evidence_id
    assert [c.verdict for c in first.comparisons] == [c.verdict for c in second.comparisons]
    assert first.evidence_id != contrast(real_db, layer, *claims, approx="0.5").evidence_id
