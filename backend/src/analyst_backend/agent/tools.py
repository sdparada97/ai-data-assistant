"""Herramientas del agente: `@tool` con `content_and_artifact` sobre las funciones puras.

`contrastar_afirmaciones` y `evaluar_causalidad` llaman dentro al LLM de extracción (esquema
cerrado); lo extraído se valida en código antes de consultar los datos (ver `extraction.py`).

- **Entradas tolerantes:** un valor suelto donde se espera una lista se convierte en lista
  de un elemento. Después se construye el modelo estricto (`MetricQuery`, …), que valida el resto.
- **Content:** resumen JSON breve para el LLM.
- **Artifact:** el resultado completo (modelo pydantic), para la verificación y la traza; no va al LLM.

Los `QueryError` y `ValidationError` se propagan; `ToolNode` los convierte en mensajes de error
(ver `tool_errors.py`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, ConfigDict, Field, field_validator

from analyst_backend.agent.config import (  # los nombres se reexportan para graph.py y evidence.py
    CAUSAL_TOOL,
    CONTRAST_TOOL,
    DOCUMENTS_TOOL,
    EXTRACTION_TOOLS,
    METRIC_TOOL,
    QUALITY_TOOL,
    TOOL_NAMES,
    CausalConfig,
    ContrastConfig,
)
from analyst_backend.agent.context import data_range
from analyst_backend.agent.extraction import (
    Extractor,
    extract_claims,
    extract_observations,
    load_document,
    search_cause,
    validate_claims,
    validate_observations,
)
from analyst_backend.analytics.causal import CausalThresholds, assess_cause, check_effect, validate_request
from analyst_backend.analytics.contrast import compare_claims
from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import (
    CausalResult,
    CauseDirection,
    CauseKind,
    Comparison,
    ContrastResult,
    MetricQuery,
    MetricResult,
    QualityQuery,
    QualityResult,
    SortSpec,
)
from analyst_backend.analytics.quality import calidad_datos
from analyst_backend.analytics.semantic import SemanticLayer
from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import Embedder
from analyst_backend.documents.models import DocumentQuery, DocumentResult
from analyst_backend.documents.retrieval import buscar_documentos



def _as_list(value: Any) -> Any:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _as_list_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _as_list(item) for key, item in value.items()}
    return value


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MetricToolInput(_Tolerant):
    metrics: list[str] = Field(min_length=1, description="Métricas de la capa semántica")
    filters: dict[str, list[str]] = Field(default_factory=dict, description="Dimensión → valores aceptados")
    group_by: list[str] = Field(default_factory=list, description="Dimensiones por las que agrupar")
    period: str | None = Field(default=None, description="Período único (AAAA, AAAA-Sn, AAAA-Tn o AAAA-MM)")
    compare: Comparison | None = Field(default=None, description="Comparación entre dos períodos (base y target)")
    sort: SortSpec | None = Field(default=None, description="Orden de las filas (métrica, campo y sentido)")
    limit: int | None = Field(default=None, ge=1, description="Número máximo de filas")

    @field_validator("metrics", "group_by", mode="before")
    @classmethod
    def _lists(cls, value: Any) -> Any:
        return _as_list(value)

    @field_validator("filters", mode="before")
    @classmethod
    def _filters(cls, value: Any) -> Any:
        return _as_list_values(value)


class QualityToolInput(_Tolerant):
    filters: dict[str, list[str]] = Field(default_factory=dict, description="Dimensión → valores aceptados")
    periods: list[str] = Field(default_factory=list, description="Períodos (AAAA, AAAA-Sn, AAAA-Tn o AAAA-MM)")
    rule_codes: list[str] = Field(default_factory=list, description="Códigos de regla de calidad (DQnn)")
    include_corrections: bool = Field(default=False, description="Incluir también las correcciones aplicadas")

    @field_validator("periods", "rule_codes", mode="before")
    @classmethod
    def _lists(cls, value: Any) -> Any:
        return _as_list(value)

    @field_validator("filters", mode="before")
    @classmethod
    def _filters(cls, value: Any) -> Any:
        return _as_list_values(value)


class DocumentToolInput(_Tolerant):
    query: str = Field(description="Texto a buscar en los documentos")
    top_k: int | None = Field(default=None, ge=1, description="Número de fragmentos")
    doc_ids: list[str] = Field(default_factory=list, description="Solo estos documentos (doc_id)")
    source_types: list[str] = Field(default_factory=list, description="Solo estos tipos: pdf, docx o md")

    @field_validator("doc_ids", "source_types", mode="before")
    @classmethod
    def _lists(cls, value: Any) -> Any:
        return _as_list(value)


class ContrastToolInput(_Tolerant):
    doc_id: str = Field(description="doc_id del documento cargado cuyas afirmaciones se contrastan con los datos")


class CausalToolInput(_Tolerant):
    cause: str = Field(description="Causa que se evalúa, en texto (por ejemplo, la de la pregunta)")
    cause_kind: CauseKind = Field(description="competencia, disponibilidad o metrica_propia")
    metric: str = Field(description="Métrica del efecto")
    filters: dict[str, list[str]] = Field(default_factory=dict, description="Filtros del efecto (por ejemplo, la marca)")
    compare: Comparison = Field(description="Períodos del efecto (base y target)")
    locate_by: str = Field(description="Dimensión donde localizar el efecto (por ejemplo, region)")
    cause_metric: str | None = Field(default=None, description="Solo metrica_propia: métrica de la causa")
    cause_direction: CauseDirection | None = Field(default=None, description="Solo metrica_propia: sube o baja")
    claimed_segment: str | None = Field(
        default=None, description="Segmento donde la pregunta localiza el efecto (no es un filtro)"
    )

    @field_validator("filters", mode="before")
    @classmethod
    def _filters(cls, value: Any) -> Any:
        return _as_list_values(value)


@dataclass(frozen=True)
class ToolContext:
    """Lo que necesitan las herramientas para ejecutarse."""

    layer: SemanticLayer
    duckdb_path: Path
    documents_config: DocumentsConfig
    documents_db_path: Path
    embedder: Embedder
    docs_top_k: int
    max_quality_issues: int
    contrast: ContrastConfig
    causal: CausalConfig
    metric_synonyms: dict[str, str]
    extractor: Extractor


def _number(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(round(value, 2))
    return value


def _cells(metrics: dict[str, Any]) -> dict[str, Any]:
    keep = ("value", "base", "target", "var_abs", "var_pct")
    return {
        name: {key: _number(getattr(cell, key)) for key in keep if hasattr(cell, key)} for name, cell in metrics.items()
    }


def metric_summary(result: MetricResult) -> dict[str, Any]:
    return {
        "evidence_id": result.evidence_id,
        "periods": result.periods,
        "rows": [{"group": row.group, "rank": row.rank, "values": _cells(row.metrics)} for row in result.rows],
        "total": _cells(result.total.metrics),
        "warnings": result.warnings,
        "quality_notes": {
            "count": len(result.quality_notes),
            "rules": sorted({note.rule_code for note in result.quality_notes}),
        },
        "corrections_count": result.corrections_count,
    }


def quality_summary(result: QualityResult, max_issues: int) -> dict[str, Any]:
    issues = [
        {
            "rule_code": issue.rule_code,
            "issue_type": issue.issue_type,
            "action": issue.action,
            "mes": issue.mes,
            "region": issue.region,
            "affected_net_sales_cop": issue.affected_net_sales_cop,
        }
        for issue in result.issues[:max_issues]
    ]
    return {
        "evidence_id": result.evidence_id,
        "issue_count": result.issue_count,
        "by_rule_action": [item.model_dump(mode="json") for item in result.by_rule_action],
        "issues": issues,
        "corrections_count": result.corrections_count,
    }


def document_summary(result: DocumentResult) -> dict[str, Any]:
    return {
        "evidence_id": result.evidence_id,
        "warnings": [warning.code for warning in result.warnings],
        "fragments": [
            {
                "id": hit.primary_evidence_id or hit.chunk_id,
                "chunk_id": hit.chunk_id,
                "doc_id": hit.doc_id,
                "page": hit.page,
                "evidence_ids": hit.evidence_ids,
                "text": hit.text,
            }
            for hit in result.hits
        ],
    }


def contrast_summary(result: ContrastResult) -> dict[str, Any]:
    """Tabla compacta: enunciados generados en código, cifras redondeadas y veredictos."""
    return {
        "evidence_id": result.evidence_id,
        "doc_id": result.doc_id,
        "claims": [
            {
                "statement": c.claim.statement,
                "evidence": c.claim.evidence_ref,
                "verdict": c.verdict,
                "reported": _number(c.claim.reported),
                "actual": _number(c.actual),
                "difference": _number(c.difference),
                "leader": c.leader,
                "leader_value": _number(c.leader_value),
                "default_periods": c.claim.default_periods,
                "query": c.metric_evidence_id,
            }
            for c in result.comparisons
        ],
        "discarded": len(result.discarded),
        "omitted": result.omitted,
        "warnings": result.warnings,
    }


def causal_summary(result: CausalResult) -> dict[str, Any]:
    return {
        "evidence_id": result.evidence_id,
        "cause": result.cause,
        "cause_kind": result.cause_kind,
        "verdict": result.verdict,
        "criteria": [
            {
                "name": c.name,
                "result": c.result,
                "detail": c.detail,
                "values": {key: _number(value) for key, value in c.values.items()},
                "supports": c.supports,
            }
            for c in result.criteria
        ],
        "observations": [
            {"kind": o.kind, "value": o.value, "date": o.date, "evidence": o.evidence_ref} for o in result.observations
        ],
        "discarded": len(result.discarded),
        "warnings": result.warnings,
    }


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def metric_description(layer: SemanticLayer) -> str:
    """Descripción de `consultar_metrica` con las métricas de la capa semántica (nada escrito a mano)."""
    return (
        f"Consulta métricas de ventas de la capa semántica ({', '.join(layer.metrics)}), con filtros por dimensión, "
        "agrupación, un período o una comparación entre dos períodos y orden. Devuelve cifras exactas con su evidence_id."
    )


def build_tools(context: ToolContext) -> list[BaseTool]:
    """Las cinco herramientas, ligadas a las bases y configuraciones de esta ejecución."""

    @tool(METRIC_TOOL, args_schema=MetricToolInput, response_format="content_and_artifact",
          description=metric_description(context.layer))
    def metric_tool(**kwargs: Any) -> tuple[str, MetricResult]:
        query = MetricQuery.model_validate(MetricToolInput.model_validate(kwargs).model_dump())
        result = consultar_metrica(query, context.layer, context.duckdb_path)
        return _json(metric_summary(result)), result

    @tool(QUALITY_TOOL, args_schema=QualityToolInput, response_format="content_and_artifact")
    def quality_tool(**kwargs: Any) -> tuple[str, QualityResult]:
        """Devuelve las incidencias de calidad de datos detectadas al cargar las ventas, con filtros opcionales por dimensión, período y regla."""
        query = QualityQuery.model_validate(QualityToolInput.model_validate(kwargs).model_dump())
        result = calidad_datos(query, context.layer, context.duckdb_path)
        return _json(quality_summary(result, context.max_quality_issues)), result

    @tool(DOCUMENTS_TOOL, args_schema=DocumentToolInput, response_format="content_and_artifact")
    def documents_tool(**kwargs: Any) -> tuple[str, DocumentResult]:
        """Busca fragmentos citables en los documentos cargados (la lista está en las instrucciones). Devuelve el texto literal de cada fragmento con sus IDs de evidencia."""
        data = DocumentToolInput.model_validate(kwargs).model_dump()
        if data["top_k"] is None:
            data["top_k"] = context.docs_top_k
        query = DocumentQuery.model_validate(data, context={"config": context.documents_config})
        result = buscar_documentos(query, context.documents_config, context.documents_db_path, context.embedder)
        return _json(document_summary(result)), result

    @tool(CONTRAST_TOOL, args_schema=ContrastToolInput, response_format="content_and_artifact")
    def contrast_tool(**kwargs: Any) -> tuple[str, ContrastResult]:
        """Contrasta con los datos de ventas las afirmaciones de un documento cargado (por su doc_id): variaciones, rankings y direcciones, con un veredicto calculado en código por afirmación. Úsala para preguntas sobre la consistencia de un documento con los datos."""
        args = ContrastToolInput.model_validate(kwargs)
        document = load_document(context.documents_db_path, args.doc_id, context.contrast.max_document_chars)
        dates = data_range(context.duckdb_path)
        claims = extract_claims(context.extractor, document, context.layer, dates, CONTRAST_TOOL)
        checked = validate_claims(claims, document, context.layer, dates, context.contrast, context.metric_synonyms)
        result = compare_claims(
            checked.valid, doc_id=document.doc_id, doc_title=document.title, document_sha256=document.sha256,
            layer=context.layer, duckdb_path=context.duckdb_path, approx_pp=context.contrast.approx_pp,
            discarded=checked.discarded, omitted=checked.omitted, warnings=checked.warnings,
            fragments=list(checked.fragments.values()),
        )
        return _json(contrast_summary(result)), result

    @tool(CAUSAL_TOOL, args_schema=CausalToolInput, response_format="content_and_artifact")
    def causal_tool(**kwargs: Any) -> tuple[str, CausalResult]:
        """Evalúa una afirmación causal con cinco criterios fijos (localización, grupo de comparación, temporalidad, explicaciones alternativas y diseño de la evidencia) y da un veredicto: contradicha, no sustentada o compatible (hipótesis). Nunca demuestra una causa."""
        args = CausalToolInput.model_validate(kwargs)
        causal = context.causal
        thresholds = CausalThresholds(causal.locate_margin_pp, causal.differential_pp, causal.step_share,
                                      causal.uniform_spread_pp, causal.cause_change_pct, causal.open_dimensions)
        request = validate_request(**args.model_dump(exclude={"compare"}), compare=args.compare,
                                   layer=context.layer, thresholds=thresholds)
        check_effect(request, layer=context.layer, duckdb_path=context.duckdb_path)  # antes de la extracción
        search = search_cause(request.cause, causal.search_top_k, context.documents_config,
                              context.documents_db_path, context.embedder)
        extracted = extract_observations(context.extractor, request.cause, list(search.fragments.values()),
                                         context.layer, CAUSAL_TOOL)
        checked = validate_observations(extracted, search.fragments, context.layer)
        result = assess_cause(
            request, checked.valid, layer=context.layer, duckdb_path=context.duckdb_path, thresholds=thresholds,
            search=search.summary(), discarded=checked.discarded,
            warnings=[warning.message for warning in search.result.warnings],
            fragments=list(checked.fragments.values()),
        )
        return _json(causal_summary(result)), result

    return [metric_tool, quality_tool, documents_tool, contrast_tool, causal_tool]
