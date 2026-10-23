"""Pintado de las respuestas del agente.

Todo texto que viene de la API (afirmaciones, mensajes, avisos, fragmentos, traza) se pinta con
`st.text` o `st.json`, que no interpretan Markdown, HTML, fórmulas, colores ni emojis abreviados.
`st.error`, `st.warning` y `st.info` solo llevan textos fijos de esta interfaz. Las cifras se
muestran tal como llegan, sin calcularlas ni redondearlas.
"""

from __future__ import annotations

import string
from typing import Any

import streamlit as st

from analyst_frontend.client import AskOutcome
from analyst_frontend.config import Settings

SECTIONS = (
    ("facts", "Hechos"),
    ("hypotheses", "Hipótesis"),
    ("contradictions", "Contradicciones"),
)
INSUFFICIENT_TITLE = "Información insuficiente"
WARNINGS_TITLE = "Avisos sobre los datos"
NO_PAGE = "sin página"
MISSING_EVIDENCE = "Esta evidencia no viene en la respuesta."

QUOTA_MESSAGE = "Se agotó la cuota del LLM. Espera un minuto y vuelve a preguntar."
DATA_MESSAGE = "Faltan datos en el backend."
CONFIGURATION_MESSAGE = (
    "La configuración del backend no es válida. Corrígela en .env y vuelve a ejecutar make up."
)
OTHER_ERROR_MESSAGE = "No se pudo responder la pregunta."
OUT_OF_SCOPE_MESSAGE = "La pregunta está fuera del alcance del asistente."
INSUFFICIENT_MESSAGE = "No hay evidencia suficiente para responder del todo."
UNREACHABLE_MESSAGE = "No se pudo contactar con la API."
TIMEOUT_MESSAGE = "La API no respondió a tiempo."
UNRECOGNIZED_MESSAGE = "La API devolvió una respuesta no reconocible."

_MARKDOWN_PUNCTUATION = frozenset(string.punctuation)


def escape_label(text: str) -> str:
    """Escapa la puntuación ASCII de una etiqueta de `st.expander`, que Streamlit interpreta como Markdown."""
    return "".join(f"\\{char}" if char in _MARKDOWN_PUNCTUATION else char for char in text)


# --- Evidencias -------------------------------------------------------------------------------------


def _metric_table(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Una fila por grupo (y el total) con los valores tal como vienen, sin los `*_exact`."""
    rows = [*result.get("rows", []), result.get("total")]
    table: list[dict[str, Any]] = []
    for row in rows:
        if not row:
            continue
        line: dict[str, Any] = dict(row.get("group") or {}) or {"grupo": "Total"}
        for metric, cell in (row.get("metrics") or {}).items():
            for field, value in (cell or {}).items():
                if not field.endswith("_exact"):
                    line[f"{metric}.{field}"] = value
        table.append(line)
    return table


def _quality_table(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Cada incidencia con todos sus campos, tal como llega: las dimensiones no se escriben aquí."""
    return [dict(issue) for issue in result.get("issues", [])]


def render_evidence(item: dict[str, Any]) -> None:
    kind = item.get("kind")
    if kind == "metricas":
        st.text(f"Consulta {item['id']} ({item.get('tool', '')})")
        st.dataframe(_metric_table(item.get("result") or {}))
    elif kind == "calidad":
        st.text(f"Consulta {item['id']} ({item.get('tool', '')})")
        st.dataframe(_quality_table(item.get("result") or {}))
    elif kind == "documento":
        page = item.get("page")
        place = f"página {page}" if page is not None else NO_PAGE
        st.text(f"{item.get('doc_id')} · {item.get('chunk_id')} · {place}")
        st.text(item.get("text") or "")
    elif kind == "busqueda":
        st.text(f"Búsqueda: {item.get('query') or ''}")
        st.text(f"Fragmentos: {', '.join(item.get('fragment_ids') or [])}")


def render_claim_evidence(evidence: list[dict[str, Any]], cited: list[str]) -> None:
    """Un desplegable por evidencia citada, titulado con su título; dentro, su id y el detalle."""
    shown: set[str] = set()
    for ident in cited:
        matches = [item for item in evidence if ident in item.get("citable_ids", [])]
        if not matches:
            st.text(f"{ident}: {MISSING_EVIDENCE}")
        for item in matches:
            if item["id"] in shown:  # citada por dos de sus ids en la misma afirmación
                continue
            shown.add(item["id"])
            with st.expander(escape_label(item.get("title") or item["id"])):
                st.text(f"Id: {item['id']} · se cita como: {', '.join(item.get('citable_ids') or [])}")
                render_evidence(item)


# --- Respuesta del agente -------------------------------------------------------------------------


def _render_claims(body: dict[str, Any]) -> None:
    evidence = body.get("evidence") or []
    for field, title in SECTIONS:
        claims = body.get(field) or []
        if not claims:
            continue
        st.subheader(title)
        for claim in claims:
            st.text(f"• {claim.get('statement', '')}")
            render_claim_evidence(evidence, claim.get("evidence") or [])
    insufficient = body.get("insufficient") or []
    if insufficient:
        st.subheader(INSUFFICIENT_TITLE)
        for text in insufficient:
            st.text(f"• {text}")


def _render_warnings(body: dict[str, Any]) -> None:
    warnings = body.get("warnings") or []
    if warnings:
        st.warning(WARNINGS_TITLE)
        for text in warnings:
            st.text(text)


def _render_trace(body: dict[str, Any]) -> None:
    trace = body.get("trace") or {}
    with st.expander("Traza"):
        st.text(
            f"Modelo: {trace.get('model') or '-'} · {trace.get('llm_calls', 0)} llamadas al LLM "
            f"({trace.get('llm_attempts', 0)} intentos) · {trace.get('duration_ms', 0)} ms"
        )
        for run in trace.get("tool_runs") or []:
            st.text(f"{run.get('tool')} · {run.get('status')} · {run.get('evidence_id') or '-'}")
        for problem in trace.get("verification_problems") or []:
            st.text(f"Problema de verificación: {problem}")
        st.json(trace, expanded=False)


def _render_error(body: dict[str, Any]) -> None:
    code = body.get("error_code") or ""
    message = body.get("message") or ""
    if code == "quota_exhausted":
        st.error(QUOTA_MESSAGE)
    elif code == "data_unavailable":
        st.error(DATA_MESSAGE)
        st.text(message)
    elif code == "configuration_error":
        st.error(CONFIGURATION_MESSAGE)
        st.text(message)
    else:
        st.error(OTHER_ERROR_MESSAGE)
        st.text(f"{code}: {message}")


def render_response(body: dict[str, Any]) -> None:
    status = body.get("status")
    if status == "error":
        _render_error(body)
    elif status == "fuera_de_alcance":
        st.info(OUT_OF_SCOPE_MESSAGE)
        st.text(body.get("message") or "")
    else:
        if status == "insuficiente":
            st.warning(INSUFFICIENT_MESSAGE)
            if body.get("message"):
                st.text(body["message"])
        _render_claims(body)
    _render_warnings(body)
    _render_trace(body)


def render_outcome(outcome: AskOutcome, settings: Settings) -> None:
    if outcome.kind == "answer" and outcome.body is not None:
        render_response(outcome.body)
    elif outcome.kind == "timeout":
        st.error(TIMEOUT_MESSAGE)
        st.text(
            f"{settings.backend_url} no respondió en {settings.backend_timeout_s:g} segundos. "
            "La pregunta puede seguir en curso en la API: espera antes de repetirla."
        )
    elif outcome.kind == "unreachable":
        st.error(UNREACHABLE_MESSAGE)
        st.text(f"Comprueba que la API está en marcha en {settings.backend_url}.")
    else:
        st.error(UNRECOGNIZED_MESSAGE)
        st.text(f"Estado HTTP {outcome.http_status}.")
