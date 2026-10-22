"""Evidencias citables a partir de los resultados de las herramientas (los artifacts).

- Métricas y calidad: una evidencia por resultado, citada por su `evidence_id`, con las cifras
  del resultado (sin identificadores ni SQL).
- Documentos: una evidencia por fragmento, citable por su `chunk_id`, su ID principal o
  cualquier ID que contenga, con el texto literal; y otra por la búsqueda.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from analyst_backend.agent.models import Evidence
from analyst_backend.analytics.models import MetricResult, QualityResult
from analyst_backend.documents.models import DocumentResult

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


def evidence_items(artifact: MetricResult | QualityResult | DocumentResult, summary: str = "") -> list[Evidence]:
    """Evidencias de un resultado. `summary` es el resumen que recibió el LLM (métricas y calidad)."""
    if isinstance(artifact, MetricResult):
        return [Evidence(artifact.evidence_id, "metricas", summary, frozenset({artifact.evidence_id}),
                         tuple(figures(artifact)))]
    if isinstance(artifact, QualityResult):
        return [Evidence(artifact.evidence_id, "calidad", summary, frozenset({artifact.evidence_id}),
                         tuple(figures(artifact)))]
    items: list[Evidence] = []
    for hit in artifact.hits:
        fragment_id = hit.primary_evidence_id or hit.chunk_id
        items.append(Evidence(
            fragment_id, "documento", hit.text,
            frozenset({hit.chunk_id, fragment_id, *hit.evidence_ids}),
            text=hit.text,
            extra=f'doc="{hit.doc_id}" fragmento="{hit.chunk_id}" pagina="{hit.page or ""}"',
        ))
    fragment_ids = ", ".join(item.id for item in items)
    items.append(Evidence(artifact.evidence_id, "busqueda", f"Fragmentos: {fragment_ids}",
                          frozenset({artifact.evidence_id})))
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
