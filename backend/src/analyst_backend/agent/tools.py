"""Herramientas del agente: `@tool` con `content_and_artifact` sobre las funciones puras.

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

from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import Comparison, MetricQuery, MetricResult, QualityQuery, QualityResult, SortSpec
from analyst_backend.analytics.quality import calidad_datos
from analyst_backend.analytics.semantic import SemanticLayer
from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import Embedder
from analyst_backend.documents.models import DocumentQuery, DocumentResult
from analyst_backend.documents.retrieval import buscar_documentos

METRIC_TOOL = "consultar_metrica"
QUALITY_TOOL = "calidad_datos"
DOCUMENTS_TOOL = "buscar_documentos"
TOOL_NAMES = (METRIC_TOOL, QUALITY_TOOL, DOCUMENTS_TOOL)


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


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def metric_description(layer: SemanticLayer) -> str:
    """Descripción de `consultar_metrica` con las métricas de la capa semántica (nada escrito a mano)."""
    return (
        f"Consulta métricas de ventas de la capa semántica ({', '.join(layer.metrics)}), con filtros por dimensión, "
        "agrupación, un período o una comparación entre dos períodos y orden. Devuelve cifras exactas con su evidence_id."
    )


def build_tools(context: ToolContext) -> list[BaseTool]:
    """Las tres herramientas, ligadas a las bases y configuraciones de esta ejecución."""

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

    return [metric_tool, quality_tool, documents_tool]
