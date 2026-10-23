"""Comparación de afirmaciones ya validadas con los datos (Python puro, sin LLM).

- Variación: diferencia = reportado − real (pp) y veredicto "coincide" (redondeo del real a los
  decimales del reportado, el empate se aleja de cero), "aproximado" (|diferencia| ≤ umbral y mismo
  signo) o "no coincide".
- Ranking: "verdadera" si el valor afirmado está entre los primeros empatados en la dirección pedida.
- Dirección: "verdadera" si el signo de la variación total es el afirmado.
- Cualitativa: "no verificable con los datos", sin consulta.

Las afirmaciones que comparten métrica, dimensión, filtros y períodos usan una sola consulta.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from analyst_backend.analytics.evidence import contrast_evidence_id
from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import (
    ClaimComparison,
    ClaimVerdict,
    Comparison,
    ContrastResult,
    DiscardedItem,
    MetricQuery,
    MetricResult,
    MetricRow,
    SortSpec,
    SourceFragment,
    ValidatedClaim,
)
from analyst_backend.analytics.semantic import SemanticLayer

UNVERIFIABLE: ClaimVerdict = "no verificable con los datos"

QueryKey = tuple[str, str | None, tuple[tuple[str, tuple[str, ...]], ...], str, str]


def _sign(value: Decimal) -> int:
    return (value > 0) - (value < 0)


def variation_verdict(
    reported: Decimal, decimals: int, actual: Decimal, approx_pp: Decimal
) -> tuple[Decimal, ClaimVerdict]:
    """Diferencia (reportado − real) y veredicto de una variación."""
    difference = reported - actual
    if actual.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP) == reported:
        return difference, "coincide"
    if abs(difference) <= approx_pp and _sign(reported) == _sign(actual):
        return difference, "aproximado"
    return difference, "no coincide"


def _key(claim: ValidatedClaim) -> QueryKey:
    filters = tuple(sorted((dimension, tuple(sorted(values))) for dimension, values in claim.filters.items()))
    assert claim.metric is not None and claim.base is not None and claim.target is not None
    return claim.metric, claim.dimension, filters, claim.base, claim.target


def _query(key: QueryKey, layer: SemanticLayer, duckdb_path: Path) -> MetricResult:
    metric, dimension, filters, base, target = key
    return consultar_metrica(
        MetricQuery(
            metrics=[metric],
            filters={name: list(values) for name, values in filters},
            group_by=[dimension] if dimension else [],
            compare=Comparison(base=base, target=target),
            sort=SortSpec(metric=metric, field="var_pct", order="asc") if dimension else None,
        ),
        layer,
        duckdb_path,
    )


def _var_pct(row: MetricRow | None, metric: str) -> Decimal | None:
    if row is None:
        return None
    return getattr(row.metrics.get(metric), "var_pct", None)


def _compare(claim: ValidatedClaim, result: MetricResult, approx_pp: Decimal) -> ClaimComparison:
    assert claim.metric is not None
    if claim.dimension is None:
        actual = _var_pct(result.total, claim.metric)
    else:
        row = next((r for r in result.rows if r.group.get(claim.dimension) == claim.value), None)
        actual = _var_pct(row, claim.metric)
    if actual is None:
        return ClaimComparison(claim=claim, verdict=UNVERIFIABLE, metric_evidence_id=result.evidence_id)

    if claim.kind == "variacion":
        assert claim.reported is not None
        difference, verdict = variation_verdict(claim.reported, claim.reported_decimals, actual, approx_pp)
        return ClaimComparison(claim=claim, verdict=verdict, actual=actual, difference=difference,
                               metric_evidence_id=result.evidence_id)

    if claim.kind == "direccion":
        expected = -1 if claim.direction == "contraccion" else 1
        verdict = "verdadera" if _sign(actual) == expected else "falsa"
        return ClaimComparison(claim=claim, verdict=verdict, actual=actual, metric_evidence_id=result.evidence_id)

    # Ranking: el primero en la dirección pedida, con empates.
    assert claim.dimension is not None
    ranked = [(row.group[claim.dimension], value) for row in result.rows
              if (value := _var_pct(row, claim.metric)) is not None]
    best = min(v for _, v in ranked) if claim.direction == "mayor_caida" else max(v for _, v in ranked)
    leaders = sorted(name for name, value in ranked if value == best)
    verdict = "verdadera" if claim.value in leaders else "falsa"
    return ClaimComparison(claim=claim, verdict=verdict, actual=actual, leader=leaders[0], leader_value=best,
                           metric_evidence_id=result.evidence_id)


def compare_claims(
    claims: Sequence[ValidatedClaim],
    *,
    doc_id: str,
    doc_title: str,
    document_sha256: str,
    layer: SemanticLayer,
    duckdb_path: Path,
    approx_pp: Decimal,
    discarded: Sequence[DiscardedItem] = (),
    omitted: int = 0,
    warnings: Sequence[str] = (),
    fragments: Sequence[SourceFragment] = (),
) -> ContrastResult:
    """Compara las afirmaciones validadas con los datos. Una consulta por combinación de datos pedidos."""
    results: dict[QueryKey, MetricResult] = {}
    comparisons: list[ClaimComparison] = []
    for claim in claims:
        if claim.kind == "cualitativa" or claim.metric is None:
            comparisons.append(ClaimComparison(claim=claim, verdict=UNVERIFIABLE))
            continue
        key = _key(claim)
        if key not in results:
            results[key] = _query(key, layer, duckdb_path)
        comparisons.append(_compare(claim, results[key], approx_pp))
    queries = list(results.values())
    all_warnings = list(dict.fromkeys([*warnings, *(w for q in queries for w in q.warnings)]))
    return ContrastResult(
        evidence_id=contrast_evidence_id(
            doc_id,
            document_sha256,
            {"approx_pp": str(approx_pp)},
            [claim.model_dump(mode="json") for claim in claims],
            [query.evidence_id for query in queries],
        ),
        doc_id=doc_id,
        doc_title=doc_title,
        document_sha256=document_sha256,
        comparisons=comparisons,
        discarded=list(discarded),
        omitted=omitted,
        warnings=all_warnings,
        queries=queries,
        fragments=list(fragments),
    )
