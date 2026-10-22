"""Respuesta con el modelo real (Gemini). Solo con `make test-llm`: requiere red y GEMINI_* en ENV_FILE.

Bases de prueba (ingesta real con el embedder de prueba) y el LLM configurado. Dos preguntas,
como mucho 8 llamadas al LLM en total (plan, corrección, síntesis y reintento por pregunta).
"""

from __future__ import annotations

import re

import pytest

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.graph import run_graph
from analyst_backend.agent.llm import build_llm_client
from analyst_backend.agent.models import AgentDeps, AgentResponse
from analyst_backend.settings import SettingsError, load_llm_settings

from .conftest import Bases, fake_embedder

pytestmark = pytest.mark.llm

MAX_CALLS_PER_QUESTION = 4
REPORT_DOC = "05_Reporte_Comercial"
EVIDENCE_ID = re.compile(r"^EV-[0-9a-f]{12}$")


@pytest.fixture(scope="module")
def ask(bases: Bases, agent_config: AgentConfig):  # noqa: ANN201
    try:
        settings = load_llm_settings()
    except SettingsError as error:
        pytest.fail(f"make test-llm necesita el LLM configurado en ENV_FILE: {error}")

    def run(question: str) -> AgentResponse:
        deps = AgentDeps(config=agent_config, layer=bases.layer, duckdb_path=bases.sales,
                         documents_config=bases.documents_config, documents_db_path=bases.documents,
                         embedder=fake_embedder(), llm=build_llm_client(settings, agent_config))
        response = run_graph(question, deps)
        assert response.trace.llm_calls <= MAX_CALLS_PER_QUESTION
        return response

    return run


def _sales_ids(response: AgentResponse) -> set[str]:
    return {run.evidence_id for run in response.trace.tool_runs
            if run.tool == "consultar_metrica" and run.status == "ok" and run.evidence_id}


def _report_ids(response: AgentResponse) -> set[str]:
    """Ids citables de los fragmentos del reporte recuperados en esta ejecución."""
    ids: set[str] = set()
    for run in response.trace.tool_runs:
        if run.tool == "buscar_documentos" and run.status == "ok" and run.result:
            for hit in run.result["hits"]:
                if hit["doc_id"] == REPORT_DOC:
                    ids |= {hit["chunk_id"], *hit["evidence_ids"]} | ({hit["primary_evidence_id"]} - {None})
    return ids


def test_largest_drop_with_gemini(ask) -> None:  # noqa: ANN001
    response = ask("¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026?")

    assert response.status == "ok", (response.error_code, response.message, response.trace.verification_problems)
    sales_ids = _sales_ids(response)
    assert any(
        "Sur" in fact.statement and ("30.27" in fact.statement or "30,27" in fact.statement)
        and sales_ids & set(fact.evidence)
        for fact in response.facts
    ), response.facts


def test_report_consistency_with_gemini(ask) -> None:  # noqa: ANN001
    response = ask(
        "El reporte comercial afirma que Centro fue la región con mayor caída de ventas de Brío entre T1 y T2 "
        "de 2026. ¿Es consistente con los datos?"
    )

    assert response.status == "ok", (response.error_code, response.message, response.trace.verification_problems)
    sales_ids, report_ids = _sales_ids(response), _report_ids(response)
    assert all(EVIDENCE_ID.match(evidence_id) for evidence_id in sales_ids)
    assert any(
        "Sur" in claim.statement and sales_ids & set(claim.evidence) and report_ids & set(claim.evidence)
        for claim in response.contradictions
    ), response.contradictions
