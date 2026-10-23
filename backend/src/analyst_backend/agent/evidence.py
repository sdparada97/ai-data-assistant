"""Evidencias citables a partir de los resultados de las herramientas (los artifacts).

- Métricas y calidad: una evidencia por resultado, citada por su `evidence_id`, con las cifras
  del resultado (sin identificadores ni SQL).
- Documentos: una evidencia por fragmento, citable por su `chunk_id`, su ID principal o
  cualquier ID que contenga, con el texto literal; y otra por la búsqueda.
- Contraste y causalidad: una evidencia con cifras explícitas (no todas las del resultado), más
  sus consultas internas (evidencias `metricas` que no van como bloques a la síntesis) y los
  fragmentos de sus afirmaciones u observaciones validadas (evidencias `documento`).

Cada evidencia lleva un título legible, generado en código a partir de la consulta o del
documento (sin el LLM y sin traducciones escritas aquí).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from analyst_backend.agent.models import Evidence, EvidenceView
from analyst_backend.agent.tools import (
    CAUSAL_TOOL,
    CONTRAST_TOOL,
    DOCUMENTS_TOOL,
    METRIC_TOOL,
    QUALITY_TOOL,
    metric_summary,
)
from analyst_backend.analytics.models import CausalResult, ContrastResult, MetricResult, QualityResult, SourceFragment
from analyst_backend.documents.models import DocumentResult

Artifact = MetricResult | QualityResult | DocumentResult | ContrastResult | CausalResult

# Campos de los resultados que no son cifras de negocio (no cuentan como evidencia numérica).
_NON_FIGURE_FIELDS = frozenset(
    {"periods", "sql", "sql_params", "query", "source_line", "evidence_id", "ingestion_id", "registro_id"}
)


def figures(value: Any) -> list[Decimal]:
    """Cifras de un resultado (modelo pydantic, dict o lista), sin identificadores ni SQL."""
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, Decimal):
        return [value]
    if isinstance(value, int | float):
        return [Decimal(str(value))]
    if isinstance(value, BaseModel):
        return [n for name in type(value).model_fields if name not in _NON_FIGURE_FIELDS for n in figures(getattr(value, name))]
    if isinstance(value, dict):
        return [n for key, item in value.items() if key not in _NON_FIGURE_FIELDS for n in figures(item)]
    if isinstance(value, list | tuple):
        return [n for item in value for n in figures(item)]
    return []


def metric_has_values(result: MetricResult) -> bool:
    for row in [*result.rows, result.total]:
        for cell in row.metrics.values():
            if any(getattr(cell, key, None) is not None for key in ("value", "base", "target")):
                return True
    return False


TITLE_SEPARATOR = " · "


def _words(name: str) -> str:
    return name.replace("_", " ")


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"


def _filters(filters: dict[str, Any]) -> list[str]:
    return [f"{_words(dimension)} {', '.join(map(str, values))}" for dimension, values in filters.items() if values]


def metric_title(result: MetricResult) -> str:
    """`<Métricas> por <dimensiones> · <dimensión> <valores> · <base> frente a <objetivo>` (o `<período>`)."""
    query = result.query
    metrics = _join([_words(name) for name in query.get("metrics") or []]) or "Métricas"
    head = metrics[:1].upper() + metrics[1:]
    if query.get("group_by"):
        head += " por " + ", ".join(_words(name) for name in query["group_by"])
    parts = [head, *_filters(query.get("filters") or {})]
    compare = query.get("compare")
    if compare:
        parts.append(f"{compare['base']} frente a {compare['target']}")
    elif query.get("period"):
        parts.append(str(query["period"]))
    return TITLE_SEPARATOR.join(parts)


def quality_title(result: QualityResult) -> str:
    """`Calidad de datos · reglas <códigos> · <dimensión> <valores> · <períodos>`."""
    query = result.query
    parts = ["Calidad de datos"]
    if query.get("rule_codes"):
        parts.append("reglas " + ", ".join(query["rule_codes"]))
    parts += _filters(query.get("filters") or {})
    if query.get("periods"):
        parts.append(", ".join(query["periods"]))
    return TITLE_SEPARATOR.join(parts)


def fragment_title(title: str, section: str | None, page: int | None) -> str:
    """`<Título del documento> · <sección> · p. <página>` (o `sin página`)."""
    parts = [title, *([section] if section else []), f"p. {page}" if page is not None else "sin página"]
    return TITLE_SEPARATOR.join(parts)


def search_title(query: str) -> str:
    return f"Búsqueda en documentos: «{query}»"


def contrast_title(result: ContrastResult) -> str:
    return f"Contraste de {result.doc_title}"


def causal_title(result: CausalResult) -> str:
    return f"Evaluación causal: «{result.cause}»"


def contrast_figures(result: ContrastResult) -> list[Decimal]:
    """Por afirmación comparada: reportado, real y diferencia; en un ranking, el real del afirmado y el del primero."""
    values = [v for c in result.comparisons for v in (c.claim.reported, c.actual, c.difference, c.leader_value)]
    return [value for value in values if value is not None]


def causal_figures(result: CausalResult) -> list[Decimal]:
    return [value for criterion in result.criteria for value in criterion.values.values() if value is not None]


def _grouping(result: MetricResult) -> dict[str, tuple[str, ...]]:
    """Métricas y agrupación de la consulta (para comprobar lo que la ejecución consultó)."""
    return {"metrics": tuple(result.query.get("metrics") or ()), "group_by": tuple(result.query.get("group_by") or ())}


def _fragment_evidence(fragment: SourceFragment, tool: str) -> Evidence:
    fragment_id = fragment.primary_evidence_id or fragment.chunk_id
    return Evidence(
        fragment_id, "documento", fragment.text,
        frozenset({fragment.chunk_id, fragment_id, *fragment.evidence_ids}),
        text=fragment.text,
        extra=f'doc="{fragment.doc_id}" fragmento="{fragment.chunk_id}" pagina="{fragment.page or ""}"',
        tool=tool, doc_id=fragment.doc_id, chunk_id=fragment.chunk_id, page=fragment.page,
        title=fragment_title(fragment.title, fragment.section, fragment.page),
    )


def _related(result: ContrastResult | CausalResult, tool: str) -> list[Evidence]:
    """Consultas internas (citables, sin bloque en la síntesis) y fragmentos validados."""
    queries = [
        Evidence(query.evidence_id, "metricas", json.dumps(metric_summary(query), ensure_ascii=False, default=str),
                 frozenset({query.evidence_id}), tuple(figures(query)), tool=tool, title=metric_title(query),
                 internal=True, **_grouping(query))
        for query in result.queries
    ]
    return [*queries, *(_fragment_evidence(fragment, tool) for fragment in result.fragments)]


def evidence_items(artifact: Artifact, summary: str = "") -> list[Evidence]:
    """Evidencias de un resultado. `summary` es el resumen que recibió el LLM (salvo en documentos)."""
    if isinstance(artifact, ContrastResult):
        main = Evidence(artifact.evidence_id, "contraste", summary, frozenset({artifact.evidence_id}),
                        tuple(contrast_figures(artifact)), tool=CONTRAST_TOOL, doc_id=artifact.doc_id,
                        title=contrast_title(artifact))
        return [main, *_related(artifact, CONTRAST_TOOL)]
    if isinstance(artifact, CausalResult):
        main = Evidence(artifact.evidence_id, "causalidad", summary, frozenset({artifact.evidence_id}),
                        tuple(causal_figures(artifact)), tool=CAUSAL_TOOL, title=causal_title(artifact),
                        verdict=artifact.verdict)
        return [main, *_related(artifact, CAUSAL_TOOL)]
    if isinstance(artifact, MetricResult):
        return [Evidence(artifact.evidence_id, "metricas", summary, frozenset({artifact.evidence_id}),
                         tuple(figures(artifact)), tool=METRIC_TOOL, title=metric_title(artifact),
                         **_grouping(artifact))]
    if isinstance(artifact, QualityResult):
        return [Evidence(artifact.evidence_id, "calidad", summary, frozenset({artifact.evidence_id}),
                         tuple(figures(artifact)), tool=QUALITY_TOOL, title=quality_title(artifact))]
    items: list[Evidence] = []
    for hit in artifact.hits:
        fragment_id = hit.primary_evidence_id or hit.chunk_id
        items.append(Evidence(
            fragment_id, "documento", hit.text,
            frozenset({hit.chunk_id, fragment_id, *hit.evidence_ids}),
            text=hit.text,
            extra=f'doc="{hit.doc_id}" fragmento="{hit.chunk_id}" pagina="{hit.page or ""}"',
            tool=DOCUMENTS_TOOL, doc_id=hit.doc_id, chunk_id=hit.chunk_id, page=hit.page,
            title=fragment_title(hit.title, hit.section, hit.page),
        ))
    fragment_ids = tuple(item.id for item in items)
    items.append(Evidence(artifact.evidence_id, "busqueda", f"Fragmentos: {', '.join(fragment_ids)}",
                          frozenset({artifact.evidence_id}), tool=DOCUMENTS_TOOL, query=artifact.query,
                          fragment_ids=fragment_ids, title=search_title(artifact.query)))
    return items


def index(items: Iterable[Evidence]) -> tuple[dict[str, Evidence], dict[str, list[str]]]:
    """Evidencias por id y, para cada id citable, las evidencias a las que apunta."""
    evidence: dict[str, Evidence] = {}
    aliases: dict[str, list[str]] = {}
    for item in items:
        evidence.setdefault(item.id, item)
        for alias in item.aliases:
            targets = aliases.setdefault(alias, [])
            if item.id not in targets:
                targets.append(item.id)
    return evidence, aliases


def _results(artifacts: Mapping[str, Artifact]) -> dict[str, BaseModel]:
    """Resultados completos por `evidence_id`, incluidas las consultas internas de contraste y causalidad."""
    results: dict[str, BaseModel] = {}
    for artifact in artifacts.values():
        if isinstance(artifact, ContrastResult | CausalResult):
            for query in artifact.queries:
                results.setdefault(query.evidence_id, query)
        if not isinstance(artifact, DocumentResult):
            results[artifact.evidence_id] = artifact
    return results


def evidence_views(artifacts: Mapping[str, Artifact]) -> list[EvidenceView]:
    """Evidencias de las consultas correctas para la respuesta, con el resultado completo o el texto.

    Se construyen desde los artifacts (no desde lo que reunió `collect`), así que también salen
    cuando la ejecución falla antes de reunirlas.
    """
    items: list[Evidence] = []
    for artifact in artifacts.values():
        items += evidence_items(artifact)
    evidence, _ = index(items)
    results = _results(artifacts)
    views: list[EvidenceView] = []
    for item in evidence.values():
        artifact = results.get(item.id) if item.kind in ("metricas", "calidad", "contraste", "causalidad") else None
        views.append(EvidenceView(
            id=item.id, kind=item.kind, title=item.title, citable_ids=sorted(item.aliases), tool=item.tool,
            doc_id=item.doc_id, chunk_id=item.chunk_id, page=item.page,
            text=item.text or None,
            result=artifact.model_dump(mode="json") if artifact is not None else None,
            query=item.query, fragment_ids=list(item.fragment_ids),
        ))
    return views
