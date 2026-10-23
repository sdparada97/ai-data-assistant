"""Grafo LangGraph del agente: plan con herramientas → ejecución → corrección → síntesis → verificación.

check_question → load_context → plan → execute → [repair → execute] → collect → synthesize → verify
→ [synthesize → verify] → respond. Cualquier excepción de un nodo (salvo `respond`) termina en
`respond` con estado `error` y un código estable.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from decimal import Decimal
from typing import Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import NodeError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from pydantic import BaseModel

from analyst_backend.agent.context import PlanningContext, build_planning_context
from analyst_backend.agent.llm import ProviderError
from analyst_backend.agent.models import AgentDeps, AgentResponse, Evidence, Synthesis, ToolRun, Trace
from analyst_backend.agent.prompts import (
    NO_EVIDENCE_MESSAGE,
    OMITTED_RESULT,
    REPAIR_INSTRUCTION,
    UNPARSEABLE_INSTRUCTION,
    UNPARSEABLE_MESSAGE,
    evidence_block,
    planning_system_prompt,
    retry_instruction,
    synthesis_prompt,
    synthesis_system_prompt,
)
from analyst_backend.agent.tool_errors import DISCARDED_PREFIX, ERROR_PREFIX, format_tool_error
from analyst_backend.agent.evidence import evidence_items, evidence_views, index, metric_has_values
from analyst_backend.agent.extraction import llm_extractor
from analyst_backend.agent.tools import (
    DOCUMENTS_TOOL,
    EXTRACTION_TOOLS,
    METRIC_TOOL,
    QUALITY_TOOL,
    ToolContext,
    build_tools,
)
from analyst_backend.agent.verify import Consulted, drop_failing, removed_note, verify_synthesis
from analyst_backend.analytics.database import DatabaseError
from analyst_backend.analytics.models import CausalResult, ContrastResult, MetricResult, QualityResult
from analyst_backend.documents.models import DocumentResult

RECURSION_LIMIT = 30
MAX_SYNTHESIS_ATTEMPTS = 2  # la síntesis y un reintento (por verificación o por salida no interpretable)


class AgentState(TypedDict, total=False):
    question: str
    status: str
    error_code: str | None
    message: str | None
    context: PlanningContext
    messages: list[BaseMessage]
    plan_message: AIMessage
    pending: AIMessage | None
    round: int
    round_messages: dict[int, list[ToolMessage]]
    runs: list[ToolRun]
    extractions: dict[str, int]  # ejecuciones que llegaron a llamar al LLM de extracción, por herramienta
    artifacts: dict[str, Any]
    evidence: dict[str, Evidence]
    aliases: dict[str, list[str]]
    warnings: list[str]
    notes: list[str]
    plan_text: str
    synthesis: Synthesis | None
    synthesis_attempts: int
    synthesis_messages: list[BaseMessage]
    parse_failed: bool
    problems: list[str]
    problem_log: list[str]
    response: AgentResponse
    started: float
    llm_start: tuple[int, int]  # contadores del LLMClient al empezar: la traza cuenta solo esta pregunta


# --- Utilidades ----------------------------------------------------------------------------------


def _error_detail(content: str) -> str:
    """Resumen legible de un error de herramienta: campo = valor (mensaje)."""
    body = content.removeprefix(ERROR_PREFIX)
    try:
        payload = json.loads(body)
    except ValueError:
        return body[:300]
    if "field" in payload:
        return f"{payload['field']} = {payload.get('invalid_value')} ({payload.get('message', '')})"
    if "validation_errors" in payload:
        return "; ".join(f"{item['field']}: {item['message']}" for item in payload["validation_errors"])
    return str(payload.get("message", body))[:300]


def _failure_notes(runs: list[ToolRun]) -> list[str]:
    """Consultas que fallaron y no se resolvieron, agrupadas por herramienta.

    Una corrección no indica a qué consulta fallida sustituye, así que por herramienta quedan sin
    resolver `max(fallos de la ronda 1, consultas de la ronda 2) - correctas de la ronda 2`. El detalle
    es el de la última ronda en que esa herramienta falló (incluidas las consultas descartadas).
    """
    notes: list[str] = []
    for tool in dict.fromkeys(run.tool for run in runs):
        failed_first = sum(1 for run in runs if run.tool == tool and run.round == 1 and run.status == "error")
        second = [run for run in runs if run.tool == tool and run.round == 2]
        fixed = sum(1 for run in second if run.status == "ok")
        pending = max(failed_first, len(second)) - fixed
        if pending <= 0:
            continue
        failures = [run for run in runs if run.tool == tool and run.status != "ok"]
        last_round = max(run.round for run in failures)
        details = "; ".join(dict.fromkeys(_error_detail(run.error or "") for run in failures if run.round == last_round))
        subject = "una consulta" if pending == 1 else f"{pending} consultas"
        notes.append(f"No se pudo completar {subject} a {tool}: {details}")
    return notes


def _discarded_warning(tool: str, count: int, maximum: int) -> str:
    if count == 1:
        return f"Se descartó 1 consulta a {tool} (máximo {maximum})"
    return f"Se descartaron {count} consultas a {tool} (máximo {maximum})"


# --- Grafo ---------------------------------------------------------------------------------------


def build_graph(deps: AgentDeps) -> CompiledStateGraph:
    cfg = deps.config
    tools = build_tools(
        ToolContext(
            layer=deps.layer,
            duckdb_path=deps.duckdb_path,
            documents_config=deps.documents_config,
            documents_db_path=deps.documents_db_path,
            embedder=deps.embedder,
            docs_top_k=cfg.limits.docs_top_k,
            max_quality_issues=cfg.limits.max_quality_issues,
            contrast=cfg.contrast,
            causal=cfg.causal,
            metric_synonyms=cfg.metric_synonyms,
            extractor=llm_extractor(deps.llm),
        )
    )
    tool_node = ToolNode(tools, handle_tool_errors=format_tool_error)
    planner = deps.llm.with_tools(tools)

    consulted = Consulted.build(
        absence_markers=cfg.absence_markers, absence_exceptions=cfg.absence_exceptions, metrics=deps.layer.metrics,
        metric_synonyms=cfg.metric_synonyms, dimensions=deps.layer.dimensions,
    )

    def limit_of(tool: str) -> int:
        return cfg.limits.max_calls_by_tool.get(tool, cfg.limits.max_calls_per_tool)

    def check_question(state: AgentState) -> dict[str, Any]:
        question = state["question"].strip()
        if not question or len(question) > cfg.limits.max_question_chars:
            return {
                "status": "error",
                "error_code": "invalid_question",
                "message": f"La pregunta debe tener entre 1 y {cfg.limits.max_question_chars} caracteres.",
            }
        return {"question": question}

    def load_context(state: AgentState) -> dict[str, Any]:
        return {"context": build_planning_context(deps.layer, deps.duckdb_path, deps.documents_db_path)}

    def plan(state: AgentState) -> dict[str, Any]:
        messages: list[BaseMessage] = [
            SystemMessage(planning_system_prompt(state["context"], cfg.assistant_name, cfg.causal.cause_kind_examples)),
            HumanMessage(state["question"]),
        ]
        message: AIMessage = deps.llm.invoke(planner, messages)
        if not message.tool_calls:
            return {"status": "fuera_de_alcance", "message": cfg.out_of_scope_message, "plan_text": message.text}
        return {"messages": messages, "plan_message": message, "pending": message, "round": 1, "plan_text": message.text}

    def execute(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        """Ejecuta las consultas de una en una (DuckDB: una conexión a la vez por base).

        Máximos: el general cuenta las consultas correctas (corregir una que falló no consume otro
        hueco); el propio de las herramientas con extracción cuenta las ejecuciones que llegaron a
        llamar al LLM de extracción, correctas o fallidas. Si el proveedor falla dentro de una
        herramienta, se conserva lo ejecutado y las llamadas siguientes quedan descartadas.
        """
        pending = state["pending"]
        round_number = state["round"]
        runs = list(state.get("runs", []))
        artifacts = dict(state.get("artifacts", {}))
        extractions: Counter[str] = Counter(state.get("extractions", {}))
        used = Counter(run.tool for run in runs if run.status == "ok" and run.tool not in EXTRACTION_TOOLS)
        used.update(extractions)
        dropped: Counter[str] = Counter()
        failure: ProviderError | None = None
        ordered: list[ToolMessage] = []

        def discard(call: dict[str, Any], reason: str) -> None:
            message = ToolMessage(f"{DISCARDED_PREFIX}{reason}", tool_call_id=call["id"], name=call["name"],
                                  status="error")
            runs.append(ToolRun(tool=call["name"], args=call["args"], status="descartada", round=round_number,
                                error=message.content))
            ordered.append(message)

        for call in pending.tool_calls:
            name = call["name"]
            if failure is not None:
                discard(call, f"no se ejecutó por el fallo del proveedor ({failure.code})")
                continue
            if used[name] >= limit_of(name):
                dropped[name] += 1
                discard(call, f"máximo {limit_of(name)} consultas a {name}")
                continue
            if name not in EXTRACTION_TOOLS:
                used[name] += 1
            calls_before = deps.llm.calls
            try:
                out = tool_node.invoke({"messages": [AIMessage(content="", tool_calls=[call])]}, config=config)
            except ProviderError as error:
                failure = error
                runs.append(ToolRun(tool=name, args=call["args"], status="error", round=round_number,
                                    error=str(error)))
                continue
            finally:
                if name in EXTRACTION_TOOLS and deps.llm.calls > calls_before:
                    extractions[name] += 1
                    used[name] += 1
            message = out["messages"][0]
            if message.status == "error":
                runs.append(ToolRun(tool=name, args=call["args"], status="error", round=round_number,
                                    error=message.content))
            else:
                artifact = message.artifact
                runs.append(ToolRun(tool=name, args=call["args"], status="ok", round=round_number,
                                    evidence_id=artifact.evidence_id, result=artifact.model_dump(mode="json")))
                artifacts[artifact.evidence_id] = artifact
            ordered.append(message)
        warnings = list(state.get("warnings", []))
        warnings += [_discarded_warning(tool, count, limit_of(tool)) for tool, count in dropped.items()]
        round_messages = dict(state.get("round_messages", {}))
        round_messages[round_number] = ordered
        update: dict[str, Any] = {"runs": runs, "artifacts": artifacts, "warnings": warnings,
                                  "round_messages": round_messages, "pending": None, "extractions": dict(extractions)}
        if failure is not None:
            update.update({"status": "error", "error_code": failure.code, "message": str(failure)})
        return update

    def after_execute(state: AgentState) -> str:
        if state.get("status"):
            return "respond"
        failed = any(run.status == "error" for run in state["runs"] if run.round == state["round"])
        return "repair" if failed and state["round"] == 1 else "collect"

    def repair(state: AgentState) -> dict[str, Any]:
        replies = [
            message if message.status == "error"
            else ToolMessage(OMITTED_RESULT, tool_call_id=message.tool_call_id, name=message.name)
            for message in state["round_messages"][1]
        ]
        messages = [*state["messages"], state["plan_message"], *replies, HumanMessage(REPAIR_INSTRUCTION)]
        message: AIMessage = deps.llm.invoke(planner, messages)
        return {"pending": message if message.tool_calls else None, "round": 2}

    def after_repair(state: AgentState) -> str:
        return "execute" if state.get("pending") is not None else "collect"

    def collect(state: AgentState) -> dict[str, Any]:
        artifacts = state.get("artifacts", {})
        warnings = list(state.get("warnings", []))
        summaries = {
            id(m.artifact): m.content
            for messages in state.get("round_messages", {}).values()
            for m in messages
            if m.artifact is not None
        }
        items: list[Evidence] = []
        valid = False
        for run in state.get("runs", []):
            if run.status != "ok":
                continue
            artifact = artifacts[run.evidence_id]
            items += evidence_items(artifact, summaries.get(id(artifact), ""))
            if isinstance(artifact, MetricResult):
                valid = valid or metric_has_values(artifact)
                warnings += artifact.warnings
            elif isinstance(artifact, QualityResult):
                valid = True
            elif isinstance(artifact, DocumentResult):
                valid = valid or bool(artifact.hits)
                warnings += [warning.message for warning in artifact.warnings]
            elif isinstance(artifact, ContrastResult):
                valid = valid or bool(artifact.comparisons)
                warnings += artifact.warnings
            elif isinstance(artifact, CausalResult):
                valid = True
                warnings += artifact.warnings
        evidence, aliases = index(items)
        notes = _failure_notes(state.get("runs", []))
        update = {"evidence": evidence, "aliases": aliases, "warnings": list(dict.fromkeys(warnings)), "notes": notes}
        if not valid:
            return {**update, "status": "insuficiente", "message": NO_EVIDENCE_MESSAGE}
        return update

    def synthesize(state: AgentState) -> dict[str, Any]:
        attempts = state.get("synthesis_attempts", 0)
        if attempts == 0:
            blocks = [
                evidence_block(item.id, item.kind, item.prompt_text, item.extra)
                for item in state["evidence"].values()
                if item.kind != "busqueda" and not item.internal
            ]
            messages: list[BaseMessage] = [
                SystemMessage(synthesis_system_prompt(cfg.assistant_name)),
                HumanMessage(synthesis_prompt(state["question"], blocks, cfg.hedges)),
            ]
        else:
            previous = state.get("synthesis")
            feedback = UNPARSEABLE_INSTRUCTION if state.get("parse_failed") else retry_instruction(state["problems"])
            messages = [
                *state["synthesis_messages"],
                AIMessage(previous.model_dump_json() if previous is not None else "(respuesta no interpretable)"),
                HumanMessage(feedback),
            ]
        result = deps.llm.invoke(deps.llm.structured(Synthesis), messages)
        parsed = result.get("parsed") if isinstance(result, dict) else result
        update: dict[str, Any] = {"synthesis_attempts": attempts + 1, "parse_failed": parsed is None}
        if attempts == 0:
            update["synthesis_messages"] = messages
        if parsed is not None:
            update["synthesis"] = parsed
        return update

    def after_synthesize(state: AgentState) -> str:
        if not state.get("parse_failed"):
            return "verify"
        if state["synthesis_attempts"] < MAX_SYNTHESIS_ATTEMPTS:
            return "synthesize"
        # Sin reintentos: si hubo una síntesis anterior se aplica el fallo cerrado sobre ella.
        return "verify" if state.get("synthesis") is not None else "unparseable"

    def unparseable(state: AgentState) -> dict[str, Any]:
        return {"status": "error", "error_code": "invalid_output", "message": UNPARSEABLE_MESSAGE}

    def verify(state: AgentState) -> dict[str, Any]:
        synthesis = state["synthesis"]
        problems = verify_synthesis(
            synthesis,
            state["evidence"],
            state["aliases"],
            years=state["context"].data_range.years,
            causal_lexicon=cfg.causal_lexicon,
            hedges=cfg.hedges,
            id_pattern=deps.documents_config.id_regex,
            document_ids=state["context"].document_ids,
            consulted=consulted,
        )
        messages = [problem.message for problem in problems]
        log = list(dict.fromkeys([*state.get("problem_log", []), *messages]))  # sin repetir si se reverifica
        if not problems:
            return {"problems": [], "problem_log": log, "status": "ok"}
        if state["synthesis_attempts"] < MAX_SYNTHESIS_ATTEMPTS:
            return {"problems": messages, "problem_log": log}
        kept, removed = drop_failing(synthesis, problems)  # fallo cerrado
        notes = [*state.get("notes", []), removed_note(removed)]
        status = "ok" if (kept.facts or kept.contradictions) else "insuficiente"
        return {"synthesis": kept, "notes": notes, "problems": messages, "problem_log": log, "status": status}

    def after_verify(state: AgentState) -> str:
        return "respond" if state.get("status") else "synthesize"

    def respond(state: AgentState) -> dict[str, Any]:
        status = state.get("status") or "ok"
        synthesis = state.get("synthesis") or Synthesis()
        error = status == "error"
        trace = Trace(
            question=state.get("question", ""),
            plan_text=state.get("plan_text", ""),
            tool_runs=state.get("runs", []),
            repairs=1 if state.get("round", 1) == 2 else 0,
            synthesis_retries=max(state.get("synthesis_attempts", 0) - 1, 0),
            verification_problems=state.get("problem_log", []),
            llm_calls=deps.llm.calls - state.get("llm_start", (0, 0))[0],
            llm_attempts=deps.llm.attempts - state.get("llm_start", (0, 0))[1],
            model=deps.llm.model_name,
            duration_ms=int((time.monotonic() - state.get("started", time.monotonic())) * 1000),
        )
        response = AgentResponse(
            status=status,
            error_code=state.get("error_code"),
            message=deps.llm.redact(state["message"]) if state.get("message") else None,
            facts=[] if error else synthesis.facts,
            hypotheses=[] if error else synthesis.hypotheses,
            contradictions=[] if error else synthesis.contradictions,
            insufficient=[] if error else [*synthesis.insufficient, *state.get("notes", [])],
            warnings=state.get("warnings", []),
            evidence=evidence_views(state.get("artifacts", {})),
            trace=trace,
        )
        return {"response": response}

    def on_error(state: AgentState, error: NodeError) -> Command:
        exc = error.error
        if isinstance(exc, ProviderError):
            code, message = exc.code, str(exc)
        elif isinstance(exc, DatabaseError):
            code, message = "data_unavailable", str(exc)
        else:
            code, message = "internal_error", f"Error interno en {error.node}: {type(exc).__name__}"
        return Command(update={"status": "error", "error_code": code, "message": message}, goto="respond")

    graph = StateGraph(AgentState)
    for name, node in (
        ("check_question", check_question),
        ("load_context", load_context),
        ("plan", plan),
        ("execute", execute),
        ("repair", repair),
        ("collect", collect),
        ("synthesize", synthesize),
        ("unparseable", unparseable),
        ("verify", verify),
    ):
        graph.add_node(name, node, error_handler=on_error)
    graph.add_node("respond", respond)  # sin manejador: un fallo aquí no debe reenviarse a sí mismo
    def unless_finished(next_node: str):  # noqa: ANN202 - devuelve el router de una arista condicional
        def route(state: AgentState) -> str:
            return "respond" if state.get("status") else next_node

        return route

    graph.add_edge(START, "check_question")
    graph.add_conditional_edges("check_question", unless_finished("load_context"), ["load_context", "respond"])
    graph.add_edge("load_context", "plan")
    graph.add_conditional_edges("plan", unless_finished("execute"), ["execute", "respond"])
    graph.add_conditional_edges("execute", after_execute, ["repair", "collect", "respond"])
    graph.add_conditional_edges("repair", after_repair, ["execute", "collect"])
    graph.add_conditional_edges("collect", unless_finished("synthesize"), ["synthesize", "respond"])
    graph.add_conditional_edges("synthesize", after_synthesize, ["verify", "synthesize", "unparseable"])
    graph.add_edge("unparseable", "respond")
    graph.add_conditional_edges("verify", after_verify, ["synthesize", "respond"])
    graph.add_edge("respond", END)
    return graph.compile()


def run_graph(question: str, deps: AgentDeps) -> AgentResponse:
    state = build_graph(deps).invoke(
        {"question": question, "started": time.monotonic(), "llm_start": (deps.llm.calls, deps.llm.attempts)},
        config={"recursion_limit": RECURSION_LIMIT},
    )
    return state["response"]


__all__ = ["AgentState", "build_graph", "run_graph", "METRIC_TOOL", "QUALITY_TOOL", "DOCUMENTS_TOOL"]
