"""Evaluación de una afirmación causal con criterios fijos (Python puro, sin LLM).

El veredicto nunca afirma causalidad: "contradicha", "no sustentada" o "compatible (hipótesis)",
según el tipo de causa:
- `competencia`: compatible si la localización encaja y los competidores muestran efecto diferencial;
- `disponibilidad`: compatible si la localización encaja;
- `metrica_propia`: contradicha si la métrica de la causa no cambió o cambió al revés de lo esperado;
  no sustentada si no hay datos de esa métrica.
Si la afirmación localiza el efecto en un segmento que no encaja, es "contradicha" en cualquier tipo.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from analyst_backend.analytics.evidence import causal_evidence_id
from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import (
    CausalResult,
    CausalVerdict,
    CauseDirection,
    CauseKind,
    Comparison,
    CriterionResult,
    DiscardedItem,
    MetricQuery,
    MetricResult,
    MetricRow,
    QueryError,
    SourceFragment,
    ValidatedObservation,
)
from analyst_backend.analytics.semantic import SemanticLayer

NO_OBSERVATIONS = "sin observaciones"


@dataclass(frozen=True)
class CausalThresholds:
    locate_margin_pp: Decimal
    differential_pp: Decimal
    step_share: Decimal
    uniform_spread_pp: Decimal
    cause_change_pct: Decimal
    open_dimensions: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {key: str(value) if isinstance(value, Decimal) else list(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class CausalRequest:
    """Entrada ya validada contra el catálogo (valores con la escritura del catálogo)."""

    cause: str
    cause_kind: CauseKind
    metric: str
    filters: dict[str, list[str]]
    compare: Comparison
    locate_by: str
    cause_metric: str | None = None
    cause_direction: CauseDirection | None = None
    claimed_segment: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["compare"] = self.compare.model_dump()
        return data


def _time_dimension(layer: SemanticLayer) -> str | None:
    return next((name for name, dimension in layer.dimensions.items() if dimension.time), None)


def locatable_dimensions(layer: SemanticLayer, filtered: Sequence[str], open_dimensions: Sequence[str]) -> list[str]:
    """Dimensiones por las que se puede localizar: con valores o abiertas, no filtradas ni temporales."""
    return [
        name for name, dimension in layer.dimensions.items()
        if (dimension.values or name in open_dimensions) and not dimension.time and name not in filtered
    ]


def validate_request(
    *,
    cause: str,
    cause_kind: CauseKind,
    metric: str,
    filters: dict[str, list[str]],
    compare: Comparison,
    locate_by: str,
    cause_metric: str | None,
    cause_direction: CauseDirection | None,
    claimed_segment: str | None,
    layer: SemanticLayer,
    thresholds: CausalThresholds,
) -> CausalRequest:
    """Valida la entrada contra el catálogo. Lanza `QueryError` con el campo y las opciones válidas."""
    if not cause.strip():
        raise QueryError("cause", "Indica la causa que se evalúa", cause)
    layer.metric(metric)
    resolved: dict[str, list[str]] = {}
    for name, values in filters.items():
        dimension = layer.dimension(name, f"filters.{name}")
        resolved[name] = [dimension.resolve(value, f"filters.{name}") for value in values]
    allowed = locatable_dimensions(layer, list(resolved), thresholds.open_dimensions)
    if locate_by in resolved:
        raise QueryError("locate_by", f"La dimensión de localización {locate_by!r} no puede estar filtrada",
                         locate_by, allowed)
    if locate_by not in allowed:
        raise QueryError("locate_by", f"No se puede localizar por {locate_by!r}. Dimensiones válidas: {', '.join(allowed)}",
                         locate_by, allowed)
    segment = None
    if claimed_segment is not None:
        segment = layer.dimensions[locate_by].resolve(claimed_segment, "claimed_segment")
    if cause_kind == "competencia":
        single = [name for name, values in resolved.items() if len(values) == 1]
        if len(resolved) != 1 or not single or not layer.dimensions[single[0]].values:
            raise QueryError("filters", "Con el tipo competencia hace falta filtrar un solo valor de una dimensión "
                             "con catálogo, para compararlo con los demás valores", filters)
    if cause_kind == "metrica_propia":
        if cause_metric is None:
            raise QueryError("cause_metric", "Con el tipo metrica_propia hace falta la métrica de la causa", None,
                             tuple(layer.metrics))
        layer.metric(cause_metric)
        if cause_direction is None:
            raise QueryError("cause_direction", "Con el tipo metrica_propia hace falta el sentido esperado del cambio",
                             None, ("sube", "baja"))
    return CausalRequest(cause.strip(), cause_kind, metric, resolved, compare, locate_by, cause_metric,
                         cause_direction, segment)


# --- Consultas ----------------------------------------------------------------------------------


def _effect_query(request: CausalRequest) -> MetricQuery:
    return MetricQuery(metrics=[request.metric], filters=request.filters, group_by=[request.locate_by],
                       compare=request.compare)


def _require_effect(result: MetricResult, request: CausalRequest) -> Decimal:
    total = _pct(result.total, request.metric)
    if total is None or total == 0:
        raise QueryError("compare", "No hay efecto que evaluar: la variación total es nula o cero",
                         request.compare.model_dump())
    return total


def check_effect(request: CausalRequest, *, layer: SemanticLayer, duckdb_path: Path) -> None:
    """Lanza `QueryError` si no hay efecto que evaluar. Se llama antes de la búsqueda y la extracción,
    para que un período sin datos no consuma la extracción y la corrección pueda arreglarlo."""
    _require_effect(consultar_metrica(_effect_query(request), layer, duckdb_path), request)


@dataclass
class _Queries:
    layer: SemanticLayer
    duckdb_path: Path
    done: list[MetricResult] = field(default_factory=list)

    def run(self, query: MetricQuery) -> MetricResult:
        result = consultar_metrica(query, self.layer, self.duckdb_path)
        if all(result.evidence_id != previous.evidence_id for previous in self.done):
            self.done.append(result)
        return result


def _pct(row: MetricRow | None, metric: str) -> Decimal | None:
    return None if row is None else getattr(row.metrics.get(metric), "var_pct", None)


def _value(row: MetricRow, metric: str) -> Decimal | None:
    return getattr(row.metrics.get(metric), "value", None)


def _by_group(result: MetricResult, dimension: str, metric: str) -> dict[str, Decimal]:
    return {row.group[dimension]: value for row in result.rows if (value := _pct(row, metric)) is not None}


def _sign(value: Decimal) -> int:
    return (value > 0) - (value < 0)


# --- Criterios ----------------------------------------------------------------------------------


def _localization(observed: list[ValidatedObservation], segments: dict[str, Decimal], worst: str, total: Decimal,
                  beyond: Any, evidence: str) -> CriterionResult:
    values: dict[str, Decimal | None] = {"total": total, f"{worst}": segments[worst]}
    places = sorted({obs.value for obs in observed if obs.value is not None})
    for place in places:
        values[place] = segments.get(place)
    supports = [evidence, *dict.fromkeys(obs.evidence_ref for obs in observed)]
    if not places:
        return CriterionResult(name="localizacion", result=NO_OBSERVATIONS, values=values, supports=[evidence],
                               detail=f"No hay observaciones de la causa; el segmento más afectado es {worst} ({segments[worst]}).")
    fits = any(place == worst or (place in segments and beyond(segments[place])) for place in places)
    observed_text = ", ".join(f"{place} ({segments.get(place)})" for place in places)
    return CriterionResult(
        name="localizacion", result="encaja" if fits else "no encaja", values=values, supports=supports,
        detail=f"Causa observada en {observed_text}; total {total}; más afectado {worst} ({segments[worst]}).",
    )


def _comparison(request: CausalRequest, worst: str, direction: int, queries: _Queries,
                thresholds: CausalThresholds) -> CriterionResult:
    if request.cause_kind != "competencia":
        return CriterionResult(name="comparacion", result="no aplica",
                               detail="Solo se evalúa con causas de tipo competencia.")
    group, [own] = next(iter(request.filters.items()))
    others = [value for value in queries.layer.dimensions[group].values or () if value != own]
    by_segment = queries.run(MetricQuery(metrics=[request.metric], filters={group: others},
                                         group_by=[group, request.locate_by], compare=request.compare))
    totals_result = queries.run(MetricQuery(metrics=[request.metric], filters={group: others}, group_by=[group],
                                            compare=request.compare))
    totals = _by_group(totals_result, group, request.metric)
    values: dict[str, Decimal | None] = {}
    differential = False
    parts = []
    for row in by_segment.rows:
        if row.group.get(request.locate_by) != worst:
            continue
        name = row.group[group]
        segment_value, total_value = _pct(row, request.metric), totals.get(name)
        values[f"{name} en {worst}"], values[f"{name} total"] = segment_value, total_value
        if segment_value is not None and total_value is not None:
            parts.append(f"{name} {segment_value} en {worst} y {total_value} en total")
            if (segment_value - total_value) * -direction >= thresholds.differential_pp:
                differential = True
    return CriterionResult(
        name="comparacion", result="efecto diferencial" if differential else "sin efecto diferencial",
        values=values, supports=[by_segment.evidence_id, totals_result.evidence_id],
        detail="; ".join(parts) + ".",
    )


def _timing(request: CausalRequest, worst: str, direction: int, observed: list[ValidatedObservation],
            queries: _Queries, thresholds: CausalThresholds) -> CriterionResult:
    time = _time_dimension(queries.layer)
    if time is None:
        return CriterionResult(name="temporalidad", result="sin serie", detail="El catálogo no tiene dimensión temporal.")
    filters = {**request.filters, request.locate_by: [worst]}
    series: list[tuple[str, Decimal, str]] = []
    supports = []
    for label, period in (("base", request.compare.base), ("objetivo", request.compare.target)):
        result = queries.run(MetricQuery(metrics=[request.metric], filters=filters, group_by=[time], period=period))
        supports.append(result.evidence_id)
        series += [(row.group[time], value, label) for row in result.rows if (value := _value(row, request.metric)) is not None]
    series.sort()
    base = [value for _, value, label in series if label == "base"]
    target = [value for _, value, label in series if label == "objetivo"]
    if len(series) < 2 or not base or not target:
        return CriterionResult(name="temporalidad", result="sin serie suficiente", supports=supports,
                               detail="No hay meses con datos en los dos períodos.")
    mean_base, mean_target = sum(base) / len(base), sum(target) / len(target)
    changes = [(series[i][0], series[i][1] - series[i - 1][1]) for i in range(1, len(series))]
    month, step = (min if direction < 0 else max)(changes, key=lambda item: item[1])
    gap = abs(mean_target - mean_base)
    share = (abs(step) / gap).quantize(Decimal("0.001")) if gap else Decimal(0)
    concentrated = _sign(step) == direction and gap > 0 and share >= thresholds.step_share
    dates = sorted({obs.date for obs in observed if obs.value == worst and obs.date})
    detail = f"Mayor cambio entre meses consecutivos en {month}: {step} ({share} de la diferencia de medias)."
    if dates:
        detail += f" Observaciones de la causa en {worst}: {', '.join(dates)}."
    return CriterionResult(
        name="temporalidad", result=f"cambio concentrado en {month}" if concentrated else "cambio gradual",
        values={"cambio": step, "proporcion": share, "media base": mean_base.quantize(Decimal("0.01")),
                "media objetivo": mean_target.quantize(Decimal("0.01"))},
        supports=supports, detail=detail,
    )


def _alternatives(request: CausalRequest, worst: str, queries: _Queries,
                  thresholds: CausalThresholds) -> tuple[CriterionResult, str | None]:
    layer = queries.layer
    filters = {**request.filters, request.locate_by: [worst]}
    dimensions = [
        name for name, dimension in layer.dimensions.items()
        if name not in filters and not dimension.time
        and (dimension.values or name in thresholds.open_dimensions)
    ]
    values: dict[str, Decimal | None] = {}
    parts, supports, uniform = [], [], True
    for name in dimensions:
        result = queries.run(MetricQuery(metrics=[request.metric], filters=filters, group_by=[name], compare=request.compare))
        supports.append(result.evidence_id)
        variations = _by_group(result, name, request.metric)
        if not variations:
            continue
        spread = max(variations.values()) - min(variations.values())
        uniform = uniform and spread <= thresholds.uniform_spread_pp
        if layer.dimensions[name].values:
            values.update({f"{name} {value}": pct for value, pct in variations.items()})
            parts.append(f"{name}: " + ", ".join(f"{value} {pct}" for value, pct in variations.items()))
        else:
            values.update({f"{name} mínimo": min(variations.values()), f"{name} máximo": max(variations.values())})
            parts.append(f"{name}: {len(variations)} valores entre {min(variations.values())} y {max(variations.values())}")
        values[f"{name} amplitud"] = spread
    cause_status = None
    if request.cause_kind == "metrica_propia" and request.cause_metric:
        result = queries.run(MetricQuery(metrics=[request.cause_metric], filters=filters, compare=request.compare))
        supports.append(result.evidence_id)
        change = _pct(result.total, request.cause_metric)
        values[f"{request.cause_metric} en {worst}"] = change
        expected = 1 if request.cause_direction == "sube" else -1
        if change is None:
            cause_status = "sin datos"
        elif abs(change) <= thresholds.cause_change_pct:
            cause_status = "sin cambio"
        elif _sign(change) != expected:
            cause_status = "en sentido contrario"
        else:
            cause_status = "cambió en el sentido esperado"
        parts.append(f"{request.cause_metric} en {worst}: {change} ({cause_status})")
    result_text = "uniforme" if uniform else "no uniforme"
    if cause_status:
        result_text += f"; {request.cause_metric} {cause_status}"
    return (CriterionResult(name="alternativas", result=result_text, values=values, supports=supports,
                            detail="; ".join(parts) + "."), cause_status)


def _design(observations: list[ValidatedObservation]) -> CriterionResult:
    attributions = [obs for obs in observations if obs.kind == "atribucion"]
    limitations = [obs for obs in observations if obs.kind == "limitacion"]
    with_design = any(obs.declares_design for obs in attributions)
    result = "con diseño declarado" if with_design and not limitations else "sin diseño que permita atribuir"
    refs = list(dict.fromkeys(obs.evidence_ref for obs in [*attributions, *limitations]))
    detail = (f"Atribuciones: {', '.join(o.evidence_ref for o in attributions) or 'ninguna'}; "
              f"limitaciones: {', '.join(o.evidence_ref for o in limitations) or 'ninguna'}.")
    return CriterionResult(name="diseno", result=result, supports=refs, detail=detail)


def _verdict(request: CausalRequest, criteria: dict[str, CriterionResult], cause_status: str | None,
             claimed_fits: bool | None) -> CausalVerdict:
    if claimed_fits is False:
        return "contradicha"
    fits = criteria["localizacion"].result == "encaja"
    if request.cause_kind == "competencia":
        return "compatible (hipótesis)" if fits and criteria["comparacion"].result == "efecto diferencial" else "no sustentada"
    if request.cause_kind == "disponibilidad":
        return "compatible (hipótesis)" if fits else "no sustentada"
    if cause_status in ("sin cambio", "en sentido contrario"):
        return "contradicha"
    if cause_status == "sin datos":
        return "no sustentada"
    return "compatible (hipótesis)" if fits else "no sustentada"


def assess_cause(
    request: CausalRequest,
    observations: Sequence[ValidatedObservation],
    *,
    layer: SemanticLayer,
    duckdb_path: Path,
    thresholds: CausalThresholds,
    search: dict[str, Any] | None = None,
    discarded: Sequence[DiscardedItem] = (),
    warnings: Sequence[str] = (),
    fragments: Sequence[SourceFragment] = (),
) -> CausalResult:
    """Calcula los cinco criterios y el veredicto. Lanza `QueryError` si no hay efecto que evaluar."""
    queries = _Queries(layer, duckdb_path)
    by_segment = queries.run(_effect_query(request))
    total = _require_effect(by_segment, request)
    direction = _sign(total)
    segments = _by_group(by_segment, request.locate_by, request.metric)
    worst_value = (min if direction < 0 else max)(segments.values())
    worst = sorted(name for name, value in segments.items() if value == worst_value)[0]

    def beyond(value: Decimal) -> bool:
        return (value - total) * direction >= thresholds.locate_margin_pp

    observed = [obs for obs in observations if obs.kind == "segmento" and obs.dimension == request.locate_by]
    localization = _localization(observed, segments, worst, total, beyond, by_segment.evidence_id)
    comparison = _comparison(request, worst, direction, queries, thresholds)
    timing = _timing(request, worst, direction, observed, queries, thresholds)
    alternatives, cause_status = _alternatives(request, worst, queries, thresholds)
    design = _design(list(observations))
    criteria = {c.name: c for c in (localization, comparison, timing, alternatives, design)}
    claimed_fits = None
    if request.claimed_segment is not None:
        claimed = segments.get(request.claimed_segment)
        claimed_fits = request.claimed_segment == worst or (claimed is not None and beyond(claimed))
    verdict = _verdict(request, criteria, cause_status, claimed_fits)
    all_warnings = list(dict.fromkeys([*warnings, *(w for q in queries.done for w in q.warnings)]))
    return CausalResult(
        evidence_id=causal_evidence_id(
            request.as_dict(), thresholds.as_dict(), search or {},
            [obs.model_dump(mode="json") for obs in observations], [q.evidence_id for q in queries.done],
        ),
        cause=request.cause, cause_kind=request.cause_kind, metric=request.metric, filters=request.filters,
        compare=request.compare, locate_by=request.locate_by, cause_metric=request.cause_metric,
        cause_direction=request.cause_direction, claimed_segment=request.claimed_segment,
        criteria=list(criteria.values()), verdict=verdict, observations=list(observations),
        discarded=list(discarded), warnings=all_warnings, queries=queries.done, fragments=list(fragments),
    )
