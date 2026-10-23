"""Página de preguntas: apartados, texto tal cual, evidencias, avisos y traza, historial, pregunta en
curso, mensajes de error, respuesta no reconocible, API inaccesible y tiempo de espera."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from analyst_frontend import cli, client, render
from analyst_frontend.app import INDEPENDENCE_NOTICE, PENDING_TEXT
from analyst_frontend.client import AskOutcome
from analyst_frontend.config import DEFAULT_BACKEND_URL, TIMEOUT_WARNING
from analyst_frontend.render import escape_label

APP_FILE = str(cli.APP_PATH)
EV = "EV-d5c128c22542"
SEARCH_EV = "EV-0000000000aa"
QUALITY_EV = "EV-0000000000bb"

METRIC = {
    "id": EV, "kind": "metricas", "citable_ids": [EV], "tool": "consultar_metrica",
    "title": "Venta neta por region · marca Brio · 2026-T1 frente a 2026-T2",
    "result": {
        "rows": [
            {"group": {"region": "Sur"}, "rank": 1, "metrics": {"venta_neta": {
                "base": "363431600", "base_exact": "363431600", "target": "253404600", "target_exact": "253404600",
                "var_abs": "-110027000", "var_abs_exact": "-110027000", "var_pct": "-30.27",
                "var_pct_exact": "-30.27447255549599979748596435"}}},
            {"group": {"region": "Centro"}, "rank": 2, "metrics": {"venta_neta": {"var_pct": "-9.03"}}},
        ],
        "total": {"group": {}, "is_total": True, "metrics": {"venta_neta": {"var_pct": "-10.50"}}},
    },
}
REP01 = {
    "id": "REP-01", "kind": "documento", "citable_ids": ["05_Reporte_Comercial:004", "REP-01"],
    "title": "Reporte ejecutivo | Desempeño de Brío · 3. Interpretación preliminar · p. 1",
    "tool": "buscar_documentos", "doc_id": "05_Reporte_Comercial", "chunk_id": "05_Reporte_Comercial:004", "page": 1,
    "text": "REP-01 | Localización de la presión comercial. El reporte considera a Centro la región con mayor caída.",
}
INV01 = {
    "id": "INV-01", "kind": "documento", "citable_ids": ["03_Investigacion_Consumidor:003", "INV-01"],
    "title": "Estudio exploratorio de consumidores de Brío · 2. Hallazgos · p. 1",
    "tool": "buscar_documentos", "doc_id": "03_Investigacion_Consumidor", "chunk_id": "03_Investigacion_Consumidor:003",
    "page": 1, "text": "INV-01 | Sensibilidad al precio en Sur.",
}
INV_INDEX = {
    "id": "03_Investigacion_Consumidor:018", "kind": "documento",
    "citable_ids": ["03_Investigacion_Consumidor:018", "INV-01", "INV-02"], "tool": "buscar_documentos",
    "title": "Estudio exploratorio de consumidores de Brío · 8. Referencias internas de evidencia · p. 3",
    "doc_id": "03_Investigacion_Consumidor", "chunk_id": "03_Investigacion_Consumidor:018", "page": 3,
    "text": "ID: INV-01 | Descripción: Percepción de precio en Sur",
}
CONTEXT = {
    "id": "01_Contexto_Negocio:001", "kind": "documento", "citable_ids": ["01_Contexto_Negocio:001"],
    "title": "Almena Foods | Contexto de negocio · Situación · sin página",
    "tool": "buscar_documentos", "doc_id": "01_Contexto_Negocio", "chunk_id": "01_Contexto_Negocio:001", "page": None,
    "text": "Contexto de negocio de la compañía.",
}
SEARCH = {
    "id": SEARCH_EV, "kind": "busqueda", "citable_ids": [SEARCH_EV], "tool": "buscar_documentos",
    "title": "Búsqueda en documentos: «presión comercial por región»",
    "query": "presión comercial por región", "fragment_ids": ["REP-01", "05_Reporte_Comercial:003"],
}
QUALITY = {
    "id": QUALITY_EV, "kind": "calidad", "citable_ids": [QUALITY_EV], "tool": "calidad_datos",
    "title": "Calidad de datos · reglas DQ11",
    "result": {"issues": [
        {"rule_code": "DQ11", "action": "ninguna", "severity": "aviso", "issue_type": "t", "registro_id": f"R{i}",
         "canal": "Moderno", "details": f"detalle {i}"}
        for i in range(3)
    ]},
}
TRACE = {
    "question": "q", "model": "gemini-de-prueba", "llm_calls": 2, "llm_attempts": 2, "duration_ms": 1234,
    "tool_runs": [{"tool": "consultar_metrica", "status": "ok", "evidence_id": EV, "args": {}, "round": 1}],
    "verification_problems": [],
}


def answer(**fields: Any) -> AskOutcome:
    body = {"status": "ok", "error_code": None, "message": None, "facts": [], "hypotheses": [],
            "contradictions": [], "insufficient": [], "warnings": [], "evidence": [], "trace": TRACE, **fields}
    status = {"quota_exhausted": 429, "data_unavailable": 503, "configuration_error": 503,
              "invalid_output": 502}.get(fields.get("error_code") or "", 200)
    return AskOutcome("answer", status, body)


def claim(statement: str, *evidence: str) -> dict[str, Any]:
    return {"statement": statement, "evidence": list(evidence)}


@pytest.fixture
def asked(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    return []


def page(monkeypatch: pytest.MonkeyPatch, asked: list[str], *outcomes: AskOutcome | Callable[[], AskOutcome]) -> AppTest:
    queue = list(outcomes)

    def fake(url: str, question: str, timeout: float, transport: object = None) -> AskOutcome:
        asked.append(question)
        item = queue.pop(0)
        return item() if callable(item) else item

    monkeypatch.setattr(client, "ask_backend", fake)
    app = AppTest.from_file(APP_FILE, default_timeout=30)
    app.run()
    return app


def send(app: AppTest, question: str) -> AppTest:
    app.chat_input[0].set_value(question).run()
    assert not app.exception, app.exception
    return app


def texts(app: AppTest) -> list[str]:
    return [element.value for element in app.text]


def joined(app: AppTest) -> str:
    return "\n".join(texts(app))


def evidence_expanders(app: AppTest) -> list[Any]:
    return [expander for expander in app.expander if expander.label != "Traza"]


def labels(app: AppTest) -> list[str]:
    """Etiquetas de los desplegables de evidencia, sin el escape de Markdown."""
    return [expander.label.replace("\\", "") for expander in evidence_expanders(app)]


# --- Pregunta y respuesta por apartados ----------------------------------------------------------


def test_sections_with_their_evidence(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    outcome = answer(
        facts=[claim("Sur tuvo la mayor caída, -30.27 %", EV)],
        contradictions=[claim("El reporte prioriza Centro; los datos dicen Sur", "REP-01", EV)],
        evidence=[METRIC, REP01],
    )
    app = send(page(monkeypatch, asked, outcome), "¿Qué región cayó más?")

    headers = [element.value for element in app.subheader]
    assert headers == ["Hechos", "Contradicciones"]
    assert "• Sur tuvo la mayor caída, -30.27 %" in texts(app)
    assert "• El reporte prioriza Centro; los datos dicen Sur" in texts(app)
    assert labels(app) == [METRIC["title"], REP01["title"], METRIC["title"]]


# --- Texto mostrado tal cual ---------------------------------------------------------------------


def test_text_is_shown_verbatim(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    statement = "Entre $1.000 y $2.000 **x** :red[y]"
    fragment = {**REP01, "text": "**negrita** y <b>etiqueta</b>"}
    app = send(page(monkeypatch, asked, answer(facts=[claim(statement, "REP-01")], evidence=[fragment])), "q")

    assert f"• {statement}" in texts(app)
    assert "**negrita** y <b>etiqueta</b>" in texts(app)
    markdown = "\n".join(element.value for element in app.markdown)
    assert statement not in markdown and "<b>etiqueta</b>" not in markdown


# --- Detalle de las evidencias --------------------------------------------------------------------


def test_metric_evidence_table(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Sur cayó", EV)], evidence=[METRIC])), "q")

    assert labels(app) == [METRIC["title"]]
    assert f"Id: {EV} · se cita como: {EV}" in texts(app)
    table = app.dataframe[0].value
    assert table.iloc[0]["region"] == "Sur" and table.iloc[0]["venta_neta.var_pct"] == "-30.27"
    assert "venta_neta.var_pct_exact" not in table.columns


def test_document_evidence(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("El reporte prioriza Centro", "REP-01")], evidence=[REP01])), "q")

    assert "05_Reporte_Comercial · 05_Reporte_Comercial:004 · página 1" in texts(app)
    assert REP01["text"] in texts(app)


def test_id_with_two_evidences(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    outcome = answer(hypotheses=[claim("El precio podría pesar en Sur", "INV-01")], evidence=[INV01, INV_INDEX])
    app = send(page(monkeypatch, asked, outcome), "q")

    assert labels(app) == [INV01["title"], INV_INDEX["title"]]
    assert INV01["text"] in texts(app) and INV_INDEX["text"] in texts(app)


def test_search_evidence(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Se buscó el reporte", SEARCH_EV)], evidence=[SEARCH])), "q")

    assert "Búsqueda: presión comercial por región" in texts(app)
    assert any("REP-01" in text and text.startswith("Fragmentos:") for text in texts(app))


def test_quality_evidence(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Hay avisos de calidad", QUALITY_EV)], evidence=[QUALITY])), "q")

    table = app.dataframe[0].value
    assert len(table) == 3 and set(table["rule_code"]) == {"DQ11"}
    assert set(table["canal"]) == {"Moderno"} and list(table["details"]) == ["detalle 0", "detalle 1", "detalle 2"]


def test_fragment_without_page(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Contexto", "01_Contexto_Negocio:001")], evidence=[CONTEXT])), "q")

    assert "01_Contexto_Negocio · 01_Contexto_Negocio:001 · sin página" in texts(app)
    assert CONTEXT["text"] in texts(app)


def test_citation_without_evidence(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Sur cayó", "REP-77")], evidence=[METRIC])), "q")

    assert not evidence_expanders(app)
    assert any(text.startswith("REP-77:") and "no viene en la respuesta" in text for text in texts(app))


def test_title_with_symbols_is_shown_verbatim(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    title = "Informe **Q2** $1.000 :red[x]"
    app = send(page(monkeypatch, asked, answer(facts=[claim("Hecho", "REP-01")], evidence=[{**REP01, "title": title}])), "q")

    [expander] = evidence_expanders(app)
    assert expander.label == escape_label(title) and labels(app) == [title]


# --- Avisos y traza -------------------------------------------------------------------------------


def test_warnings_and_trace(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    warning = "El período 2025-T1 no tiene datos en la base"
    app = send(page(monkeypatch, asked, answer(facts=[claim("Sur cayó", EV)], evidence=[METRIC], warnings=[warning])), "q")

    assert "Avisos sobre los datos" in [element.value for element in app.warning]
    assert warning in texts(app)
    order = [node.value for node in app if type(node).__name__ in ("Warning", "Text")
             and node.value in ("Avisos sobre los datos", warning)]
    assert order == ["Avisos sobre los datos", warning]  # el aviso va debajo del encabezado fijo
    assert any(text.startswith("Modelo: gemini-de-prueba · 2 llamadas al LLM") and "1234 ms" in text for text in texts(app))
    assert f"consultar_metrica · ok · {EV}" in texts(app)


# --- Historial de la sesión ------------------------------------------------------------------------


def test_history_in_order_and_only_the_new_question(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = page(monkeypatch, asked, answer(facts=[claim("Primera respuesta", EV)], evidence=[METRIC]),
               answer(facts=[claim("Segunda respuesta", EV)], evidence=[METRIC]))
    send(app, "Primera pregunta")
    send(app, "Segunda pregunta")

    assert asked == ["Primera pregunta", "Segunda pregunta"]
    order = [text for text in texts(app) if "Primera" in text or "Segunda" in text]
    assert order == ["Primera pregunta", "• Primera respuesta", "Segunda pregunta", "• Segunda respuesta"]


def test_independence_notice(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = page(monkeypatch, asked)

    assert INDEPENDENCE_NOTICE in [element.value for element in app.info]


# --- Pregunta en curso ------------------------------------------------------------------------------


def test_input_disabled_while_waiting(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    def still_waiting() -> AskOutcome:
        st.stop()  # la página se queda como está mientras espera la respuesta
        raise AssertionError("st.stop no detuvo la página")

    app = send(page(monkeypatch, asked, still_waiting), "¿Qué región cayó más?")

    assert app.chat_input[0].disabled
    assert "¿Qué región cayó más?" in texts(app) and PENDING_TEXT in texts(app)


def test_answer_is_saved_and_input_enabled(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, answer(facts=[claim("Sur cayó", EV)], evidence=[METRIC])), "q")

    [entry] = app.session_state["history"]
    assert entry["outcome"] is not None and not app.chat_input[0].disabled


# --- Mensajes de estado y de error --------------------------------------------------------------------


def test_quota_exhausted_does_not_block(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = page(monkeypatch, asked, answer(status="error", error_code="quota_exhausted", message="429"),
               answer(facts=[claim("Sur cayó", EV)], evidence=[METRIC]))
    send(app, "q1")

    assert any("cuota" in element.value for element in app.error)
    assert not app.chat_input[0].disabled
    send(app, "q2")
    assert "• Sur cayó" in texts(app)


@pytest.mark.parametrize(("code", "message"), [
    ("data_unavailable", "No existe la base de ventas data/x.duckdb. Ejecuta `make ingest` para crearla."),
    ("configuration_error", "Faltan variables de entorno para el proveedor gemini: GEMINI_API_KEY."),
])
def test_api_message_is_shown(monkeypatch: pytest.MonkeyPatch, asked: list[str], code: str, message: str) -> None:
    app = send(page(monkeypatch, asked, answer(status="error", error_code=code, message=message)), "q")

    assert message in texts(app)


def test_out_of_scope(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    message = "Solo puedo responder preguntas sobre las ventas y los documentos cargados."
    app = send(page(monkeypatch, asked, answer(status="fuera_de_alcance", message=message)), "¿Lloverá?")

    assert message in texts(app) and not app.subheader


def test_insufficient_answer(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    note = "No se pudo completar una consulta a consultar_metrica: filters.marca = Zeta"
    outcome = answer(status="insuficiente", message="No hay evidencia suficiente para responder la pregunta.",
                     insufficient=[note])
    app = send(page(monkeypatch, asked, outcome), "Ventas de Zeta")

    assert render.INSUFFICIENT_MESSAGE in [element.value for element in app.warning]
    assert "No hay evidencia suficiente para responder la pregunta." in texts(app)
    assert "Información insuficiente" in [element.value for element in app.subheader]
    assert f"• {note}" in texts(app)


def test_other_error_shows_code_and_message(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    outcome = answer(status="error", error_code="invalid_output", message="El modelo no devolvió el formato esperado.")
    app = send(page(monkeypatch, asked, outcome), "q")

    assert "invalid_output: El modelo no devolvió el formato esperado." in texts(app)


# --- Respuesta no reconocible y API inaccesible ----------------------------------------------------------


def test_unrecognized_response(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    app = send(page(monkeypatch, asked, AskOutcome("unrecognized", 500)), "q")

    assert any("500" in text for text in texts(app)) and not app.chat_input[0].disabled


def test_unreachable_api(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    monkeypatch.delenv("BACKEND_URL", raising=False)
    app = send(page(monkeypatch, asked, AskOutcome("unreachable")), "q")

    assert app.error and any(DEFAULT_BACKEND_URL in text for text in texts(app))


def test_timeout_message(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    monkeypatch.delenv("BACKEND_TIMEOUT_S", raising=False)
    app = send(page(monkeypatch, asked, AskOutcome("timeout")), "q")

    [text] = [text for text in texts(app) if "segundos" in text]
    assert DEFAULT_BACKEND_URL in text and "300 segundos" in text and "puede seguir en curso" in text


def test_invalid_timeout_setting_is_warned(monkeypatch: pytest.MonkeyPatch, asked: list[str]) -> None:
    monkeypatch.setenv("BACKEND_TIMEOUT_S", "abc")
    app = page(monkeypatch, asked)

    assert TIMEOUT_WARNING in [element.value for element in app.warning]
