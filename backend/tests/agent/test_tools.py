"""Herramientas del agente: resumen (content), resultado completo (artifact), errores y entradas tolerantes."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from analyst_backend.agent.tool_errors import ERROR_PREFIX, format_tool_error
from analyst_backend.agent.tools import (
    DocumentToolInput,
    MetricToolInput,
    QualityToolInput,
    ToolContext,
    build_tools,
)
from analyst_backend.analytics.models import MetricResult, QualityResult, QueryError
from analyst_backend.documents.models import DocumentResult

# `EV-d5c128c22542` depende de la huella de semantic_layer.yaml y del CSV real.
LARGEST_DROP = {
    "metrics": ["venta_neta"],
    "filters": {"marca": ["Brío"]},
    "group_by": ["region"],
    "compare": {"base": "2026-T1", "target": "2026-T2"},
    "sort": {"metric": "venta_neta", "field": "var_pct", "order": "asc"},
}


def _call(tool_context: ToolContext, name: str, args: dict[str, Any]) -> ToolMessage:
    tools = {t.name: t for t in build_tools(tool_context)}
    return tools[name].invoke({"type": "tool_call", "name": name, "args": args, "id": "c1"})


def test_metric_summary_and_full_artifact(tool_context: ToolContext) -> None:
    message = _call(tool_context, "consultar_metrica", LARGEST_DROP)

    summary = json.loads(message.content)
    assert isinstance(message.artifact, MetricResult)
    assert summary["evidence_id"] == message.artifact.evidence_id == "EV-d5c128c22542"
    assert summary["rows"][0]["group"] == {"region": "Sur"}
    assert summary["rows"][0]["values"]["venta_neta"]["var_pct"] == -30.27
    assert set(summary) == {"evidence_id", "periods", "rows", "total", "warnings", "quality_notes", "corrections_count"}
    assert "sql" not in message.content  # el SQL solo va en el artifact
    assert message.artifact.sql


def test_quality_summary_is_capped(tool_context: ToolContext) -> None:
    message = _call(tool_context, "calidad_datos", {})

    summary = json.loads(message.content)
    assert isinstance(message.artifact, QualityResult)
    assert summary["issue_count"] == message.artifact.issue_count
    assert len(summary["issues"]) <= tool_context.max_quality_issues
    assert summary["by_rule_action"]


def test_document_summary_has_citable_fragments(tool_context: ToolContext) -> None:
    message = _call(tool_context, "buscar_documentos", {"query": "nota técnica importada del proveedor externo"})

    summary = json.loads(message.content)
    assert isinstance(message.artifact, DocumentResult)
    assert len(summary["fragments"]) == len(message.artifact.hits) == tool_context.docs_top_k
    assert {"id", "chunk_id", "doc_id", "page", "evidence_ids", "text"} <= set(summary["fragments"][0])


def test_query_error_is_propagated(tool_context: ToolContext) -> None:
    with pytest.raises(QueryError) as error:
        _call(tool_context, "consultar_metrica", {"metrics": ["venta_neta"], "filters": {"marca": ["Zeta"]}, "period": "2026"})

    assert error.value.field == "filters.marca"


def test_tolerant_inputs_wrap_single_values() -> None:
    metric = MetricToolInput.model_validate({"metrics": "venta_neta", "filters": {"marca": "Brío"}, "group_by": "region"})
    quality = QualityToolInput.model_validate({"filters": {"region": "Sur"}, "periods": "2026-T1", "rule_codes": "DQ05"})
    documents = DocumentToolInput.model_validate({"query": "x", "doc_ids": "05_Reporte_Comercial", "source_types": "pdf"})

    assert (metric.metrics, metric.filters, metric.group_by) == (["venta_neta"], {"marca": ["Brío"]}, ["region"])
    assert (quality.filters, quality.periods, quality.rule_codes) == ({"region": ["Sur"]}, ["2026-T1"], ["DQ05"])
    assert (documents.doc_ids, documents.source_types) == (["05_Reporte_Comercial"], ["pdf"])


def _run_tool_node(tool_context: ToolContext, calls: list[dict[str, Any]]) -> list[ToolMessage]:
    graph = StateGraph(MessagesState)
    graph.add_node("tools", ToolNode(build_tools(tool_context), handle_tool_errors=format_tool_error))
    graph.add_edge(START, "tools")
    graph.add_edge("tools", END)
    out = graph.compile().invoke({"messages": [AIMessage(content="", tool_calls=calls)]})
    return [m for m in out["messages"] if isinstance(m, ToolMessage)]


def test_handler_reports_invalid_arguments_and_query_errors(tool_context: ToolContext) -> None:
    messages = _run_tool_node(
        tool_context,
        [
            {"name": "consultar_metrica", "args": {"metrics": [5]}, "id": "a", "type": "tool_call"},
            {"name": "consultar_metrica", "args": {**LARGEST_DROP, "period": "2026"}, "id": "b", "type": "tool_call"},
            {"name": "consultar_metrica", "args": {"metrics": ["venta_neta"], "filters": {"marca": "Zeta"}, "period": "2026"}, "id": "c", "type": "tool_call"},
        ],
    )

    invalid_type, period_and_compare, unknown_brand = messages
    assert all(m.status == "error" and m.content.startswith(ERROR_PREFIX) for m in messages)
    assert "metrics.0" in invalid_type.content
    assert "period" in period_and_compare.content and "compare" in period_and_compare.content
    assert all(word in unknown_brand.content for word in ("filters.marca", "Zeta", "Brio, Luma, Nativa, Rizo, Senda"))


def test_format_tool_error_for_query_error() -> None:
    text = format_tool_error(QueryError("filters.marca", "Valor desconocido", "Zeta", ["Brio"]))

    assert json.loads(text.removeprefix(ERROR_PREFIX)) == {
        "field": "filters.marca", "message": "Valor desconocido", "invalid_value": "Zeta", "valid_options": ["Brio"],
    }


# --- Descripciones sin valores escritos a mano ----------------------------------------------------


def test_tool_descriptions_come_from_configuration(tool_context: ToolContext) -> None:
    first = next(iter(tool_context.layer.metrics))
    only_one = replace(tool_context, layer=replace(tool_context.layer, metrics={first: tool_context.layer.metrics[first]}))

    full = {t.name: t.description for t in build_tools(tool_context)}
    reduced = {t.name: t.description for t in build_tools(only_one)}

    assert all(name in full["consultar_metrica"] for name in tool_context.layer.metrics)
    assert first in reduced["consultar_metrica"]
    assert not any(name in reduced["consultar_metrica"] for name in tool_context.layer.metrics if name != first)
    assert "reporte comercial" not in full["buscar_documentos"].lower()
