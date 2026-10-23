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


# --- Herramientas de contraste y causalidad (extracción de prueba) --------------------------------


def _with_extraction(tool_context: ToolContext, *script: Any) -> tuple[ToolContext, Any]:
    from analyst_backend.agent.extraction import llm_extractor
    from analyst_backend.agent.llm import LLMClient

    from .fakes import ScriptedChatModel

    model = ScriptedChatModel.from_script(*script)
    llm = LLMClient(model, model_name="modelo-de-prueba", unavailable_retries=0, backoff_s=0)
    return replace(tool_context, extractor=llm_extractor(llm)), model


def test_five_tools(tool_context: ToolContext) -> None:
    from analyst_backend.agent.tools import TOOL_NAMES

    assert [t.name for t in build_tools(tool_context)] == list(TOOL_NAMES)
    assert {"contrastar_afirmaciones", "evaluar_causalidad"} <= set(TOOL_NAMES)


def test_contrast_of_the_report(tool_context: ToolContext) -> None:
    from analyst_backend.analytics.models import ContrastResult

    from .extraction_scripts import REPORT, report_extraction

    context, _ = _with_extraction(tool_context, report_extraction())

    message = _call(context, "contrastar_afirmaciones", {"doc_id": REPORT})

    result = message.artifact
    assert isinstance(result, ContrastResult) and result.discarded == []
    verdicts = {c.claim.value: c.verdict for c in result.comparisons if c.claim.kind == "variacion"}
    assert verdicts == {"Centro": "no coincide", "Sur": "no coincide", "Norte": "aproximado",
                        "Oriente": "aproximado", "Occidente": "aproximado"}
    [ranking] = [c for c in result.comparisons if c.claim.kind == "ranking"]
    assert (ranking.verdict, ranking.leader, ranking.claim.evidence_ref) == ("falsa", "Sur", "REP-01")
    assert len(result.queries) == 1
    summary = json.loads(message.content)
    assert summary["claims"][1]["statement"] == "Sur: venta neta -7 % (2026-T1 frente a 2026-T2)"
    assert summary["claims"][1]["difference"] == 23.27


def test_discarded_claims_are_not_a_plan_error(tool_context: ToolContext) -> None:
    from .extraction_scripts import MOSTLY_INVALID, REPORT
    from .fakes import json_message

    context, _ = _with_extraction(tool_context, json_message(MOSTLY_INVALID))

    message = _call(context, "contrastar_afirmaciones", {"doc_id": REPORT})

    assert message.status != "error"
    assert len(message.artifact.comparisons) == 1 and len(message.artifact.discarded) == 3


def test_unparseable_extraction_names_the_tool_without_text(tool_context: ToolContext) -> None:
    context, model = _with_extraction(tool_context, "salida libre del modelo con OC-EXT-06")

    with pytest.raises(QueryError) as error:
        _call(context, "contrastar_afirmaciones", {"doc_id": "04_Observaciones_Canales"})

    text = format_tool_error(error.value)
    assert "contrastar_afirmaciones" in text
    assert "OC-EXT-06" not in text and "salida libre" not in text and len(model.received) == 1


def test_unknown_document_does_not_reach_the_extraction(tool_context: ToolContext) -> None:
    with pytest.raises(QueryError) as error:
        _call(tool_context, "contrastar_afirmaciones", {"doc_id": "06_Inexistente"})

    assert "06_Inexistente" in error.value.message and "05_Reporte_Comercial" in error.value.message


def test_causal_assessment_of_promotions(tool_context: ToolContext) -> None:
    from analyst_backend.analytics.models import CausalResult

    from .extraction_scripts import CAUSAL_ARGS, promotions_extraction

    context, model = _with_extraction(tool_context, promotions_extraction())

    message = _call(context, "evaluar_causalidad", CAUSAL_ARGS)

    result = message.artifact
    assert isinstance(result, CausalResult) and result.verdict == "no sustentada"
    assert [o.evidence_ref for o in result.observations] == ["OC-CEN-02", "REP-02"]
    assert f'id="04_Observaciones_Canales:004"' in str(model.received[0][-1].content)
    summary = json.loads(message.content)
    assert summary["verdict"] == "no sustentada" and len(summary["criteria"]) == 5


@pytest.mark.parametrize(("override", "field"), [
    ({"locate_by": "ciudad"}, "locate_by"),
    ({"cause_kind": "metrica_propia"}, "cause_metric"),
])
def test_invalid_causal_input_does_not_reach_the_extraction(tool_context: ToolContext, override: dict[str, Any],
                                                            field: str) -> None:
    from .extraction_scripts import CAUSAL_ARGS

    with pytest.raises(QueryError) as error:
        _call(tool_context, "evaluar_causalidad", {**CAUSAL_ARGS, **override})

    assert error.value.field == field


def test_no_effect_is_rejected_before_the_extraction(tool_context: ToolContext) -> None:
    from .extraction_scripts import CAUSAL_ARGS

    same_period = {**CAUSAL_ARGS, "compare": {"base": "2026-T1", "target": "2026-T1"}}

    with pytest.raises(QueryError, match="No hay efecto"):  # el extractor de tool_context fallaría si se llamara
        _call(tool_context, "evaluar_causalidad", same_period)
