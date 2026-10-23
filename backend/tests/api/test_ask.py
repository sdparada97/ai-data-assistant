"""API de consulta: `POST /ask`, cuerpo, estados HTTP, fallos, dependencias, datos y una pregunta a la vez."""

from __future__ import annotations

import shutil
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_google_genai.chat_models import GoogleRateLimitError

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.models import AgentDeps, AgentResponse, Trace
from analyst_backend.agent.service import build_deps
from analyst_backend.api import ask as ask_module
from analyst_backend.api.ask import http_status
from analyst_backend.main import create_app

from ..agent.conftest import Bases, make_deps
from ..agent.fakes import plan_message
from ..agent.test_graph import LARGEST_DROP, LARGEST_DROP_ID, QUESTION, SYNTHESIS, metric


@contextmanager
def client_for(factory: Callable[[], AgentDeps]) -> Iterator[TestClient]:
    with TestClient(create_app(deps_factory=factory)) as client:  # `with`: ejecuta el lifespan
        yield client


def ask(client: TestClient, body: Any) -> Any:
    return client.post("/ask", json=body)


# --- Pregunta por la API -------------------------------------------------------------------------


def test_figures_question(bases: Bases, agent_config: AgentConfig) -> None:
    deps = make_deps(bases, agent_config, plan_message(metric(LARGEST_DROP)), SYNTHESIS)

    with client_for(lambda: deps) as client:
        response = ask(client, {"question": QUESTION})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["facts"][0]["evidence"] == [LARGEST_DROP_ID]
    assert body["facts"][0]["statement"] == "Sur tuvo la mayor caída, -30.27 %"
    assert LARGEST_DROP_ID in {item["id"] for item in body["evidence"]}
    [run] = body["trace"]["tool_runs"]
    assert (run["tool"], run["evidence_id"]) == ("consultar_metrica", LARGEST_DROP_ID)


# --- Cuerpo de la petición -----------------------------------------------------------------------


@pytest.mark.parametrize("body", [{}, {"question": 123}, {"question": "hola", "history": ["pregunta anterior"]}])
def test_invalid_body(bases: Bases, agent_config: AgentConfig, body: dict[str, Any]) -> None:
    deps = make_deps(bases, agent_config)

    with client_for(lambda: deps) as client:
        response = ask(client, body)

    assert response.status_code == 422
    assert "detail" in response.json()
    assert deps.llm.calls == 0


# --- Estado HTTP según el resultado ----------------------------------------------------------------


def test_quota_exhausted_is_429(bases: Bases, agent_config: AgentConfig) -> None:
    deps = make_deps(bases, agent_config, GoogleRateLimitError("429 RESOURCE_EXHAUSTED"))

    with client_for(lambda: deps) as client:
        response = ask(client, {"question": QUESTION})

    assert response.status_code == 429
    assert (response.json()["status"], response.json()["error_code"]) == ("error", "quota_exhausted")


def test_blank_question_is_422_with_agent_body(bases: Bases, agent_config: AgentConfig) -> None:
    with client_for(lambda: make_deps(bases, agent_config)) as client:
        response = ask(client, {"question": "   "})

    assert response.status_code == 422
    assert (response.json()["status"], response.json()["error_code"]) == ("error", "invalid_question")


def test_out_of_scope_is_200(bases: Bases, agent_config: AgentConfig) -> None:
    deps = make_deps(bases, agent_config, plan_message(text="No aplica."))

    with client_for(lambda: deps) as client:
        response = ask(client, {"question": "¿Qué tiempo hará mañana?"})

    assert (response.status_code, response.json()["status"]) == (200, "fuera_de_alcance")


def test_unknown_error_code_is_500() -> None:
    response = AgentResponse(status="error", error_code="codigo_nuevo", trace=Trace(question="q"))

    assert http_status(response) == 500


# --- Fallos no controlados -------------------------------------------------------------------------


def test_exception_outside_the_nodes(bases: Bases, agent_config: AgentConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(question: str, deps: AgentDeps) -> AgentResponse:
        raise RuntimeError("detalle-secreto")

    monkeypatch.setattr(ask_module, "run_graph", explode)
    with client_for(lambda: make_deps(bases, agent_config)) as client:
        response = ask(client, {"question": QUESTION})

    assert response.status_code == 500
    assert (response.json()["status"], response.json()["error_code"]) == ("error", "internal_error")
    assert "detalle-secreto" not in response.text


def test_failure_in_the_api_outside_the_agent(bases: Bases, agent_config: AgentConfig,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_status(response: AgentResponse) -> int:
        raise RuntimeError("detalle-secreto")

    monkeypatch.setattr(ask_module, "http_status", broken_status)
    deps = make_deps(bases, agent_config, plan_message(text="No aplica."))
    app = create_app(deps_factory=lambda: deps)
    with TestClient(app, raise_server_exceptions=False) as client:  # el manejador global responde
        response = ask(client, {"question": "hola"})

    assert response.status_code == 500
    assert (response.json()["status"], response.json()["error_code"]) == ("error", "internal_error")
    assert "detalle-secreto" not in response.text


def test_unexpected_error_at_startup() -> None:
    def broken() -> AgentDeps:
        raise ValueError("detalle-secreto")

    with client_for(broken) as client:
        health = client.get("/health")
        response = ask(client, {"question": "hola"})

    assert health.status_code == 200
    assert (response.status_code, response.json()["error_code"]) == (500, "internal_error")
    assert "detalle-secreto" not in response.text


def test_missing_runtime_is_internal_error() -> None:
    client = TestClient(create_app(deps_factory=build_deps))  # sin `with`: el lifespan no se ejecuta

    response = ask(client, {"question": "hola"})

    assert (response.status_code, response.json()["error_code"]) == (500, "internal_error")


# --- Dependencias del agente al arrancar ------------------------------------------------------------


def test_dependencies_are_built_once(bases: Bases, agent_config: AgentConfig) -> None:
    deps = make_deps(bases, agent_config, plan_message(metric(LARGEST_DROP)), SYNTHESIS,
                     plan_message(metric(LARGEST_DROP)), SYNTHESIS)
    built: list[AgentDeps] = []

    def factory() -> AgentDeps:
        built.append(deps)
        return deps

    with client_for(factory) as client:
        first = ask(client, {"question": QUESTION})
        second = ask(client, {"question": QUESTION})

    assert (first.status_code, second.status_code) == (200, 200)
    assert len(built) == 1 and deps.llm.calls == 4  # el mismo cliente del LLM en las dos preguntas


def test_invalid_configuration_at_startup() -> None:
    with client_for(lambda: build_deps({"LLM_PROVIDER": ""})) as client:
        health = client.get("/health")
        response = ask(client, {"question": "hola"})

    assert health.status_code == 200
    assert (response.status_code, response.json()["error_code"]) == (503, "configuration_error")
    assert "LLM_PROVIDER" in response.json()["message"]


# --- Datos cargados después de arrancar ---------------------------------------------------------------


def test_sales_database_created_after_start(bases: Bases, agent_config: AgentConfig, tmp_path: Path) -> None:
    sales = tmp_path / "ventas.duckdb"
    deps = replace(make_deps(bases, agent_config, plan_message(metric(LARGEST_DROP)), SYNTHESIS), duckdb_path=sales)

    with client_for(lambda: deps) as client:
        before = ask(client, {"question": QUESTION})
        shutil.copy(bases.sales, sales)
        after = ask(client, {"question": QUESTION})

    assert (before.status_code, before.json()["error_code"]) == (503, "data_unavailable")
    assert "make ingest" in before.json()["message"]
    assert (after.status_code, after.json()["status"]) == (200, "ok")


def test_documents_database_missing(bases: Bases, agent_config: AgentConfig, tmp_path: Path) -> None:
    deps = replace(make_deps(bases, agent_config), documents_db_path=tmp_path / "documentos.duckdb")

    with client_for(lambda: deps) as client:
        response = ask(client, {"question": QUESTION})

    assert (response.status_code, response.json()["error_code"]) == (503, "data_unavailable")
    assert "make ingest-docs" in response.json()["message"]


# --- Una pregunta a la vez -----------------------------------------------------------------------------


def test_one_question_at_a_time(bases: Bases, agent_config: AgentConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    active = 0
    peak = 0
    counter = threading.Lock()
    started = threading.Event()
    release = threading.Event()

    def slow_answer(question: str, deps: AgentDeps) -> AgentResponse:
        nonlocal active, peak
        with counter:
            active += 1
            peak = max(peak, active)
        started.set()
        release.wait(timeout=10)
        with counter:
            active -= 1
        return AgentResponse(status="ok", trace=Trace(question=question))

    monkeypatch.setattr(ask_module, "run_graph", slow_answer)
    statuses: list[int] = []
    with client_for(lambda: make_deps(bases, agent_config)) as client:
        threads = [threading.Thread(target=lambda: statuses.append(ask(client, {"question": "q"}).status_code))
                   for _ in range(2)]
        for thread in threads:
            thread.start()
        assert started.wait(timeout=10)
        time.sleep(0.3)  # sin candado, la segunda pregunta entraría en este intervalo
        health_started = time.monotonic()
        health = client.get("/health")  # con una pregunta en curso y otra esperando
        health_seconds = time.monotonic() - health_started
        release.set()
        for thread in threads:
            thread.join(timeout=10)

    assert peak == 1 and statuses == [200, 200]
    assert health.status_code == 200 and health_seconds < 2
