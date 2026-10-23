"""Punto de entrada del agente: `answer_question(pregunta)`.

Sin `deps`, las dependencias salen de `settings`: primero se valida la configuración del LLM
(proveedor, modelo y clave) y después las rutas y la configuración; las bases no se abren
hasta ejecutar el grafo. Una configuración inválida vuelve como respuesta con estado `error` y
código `configuration_error`, nunca como excepción.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from analyst_backend.agent.config import AgentConfigError, load_agent_config
from analyst_backend.agent.graph import run_graph
from analyst_backend.agent.llm import build_llm_client
from analyst_backend.agent.models import AgentDeps, AgentResponse, Trace
from analyst_backend.analytics.semantic import SemanticLayerError, load_semantic_layer
from analyst_backend.documents.config import load_documents_config
from analyst_backend.documents.embeddings import FastEmbedEmbedder
from analyst_backend.documents.errors import DocumentsError
from analyst_backend.settings import SettingsError, load_agent_settings, load_llm_settings

CONFIGURATION_ERROR = "configuration_error"
CONFIGURATION_ERRORS = (SettingsError, AgentConfigError, SemanticLayerError, DocumentsError)


def build_deps(environ: Mapping[str, str] | None = None, base_dir: Path | None = None) -> AgentDeps:
    """Dependencias reales. Lanza `SettingsError` o el error de la configuración que falle."""
    llm_settings = load_llm_settings(environ)  # antes que nada: sin LLM no se abre ninguna base
    settings = load_agent_settings(environ, base_dir)
    config = load_agent_config(settings.agent_config_path)
    documents_config = load_documents_config(settings.documents_config_path)
    return AgentDeps(
        config=config,
        layer=load_semantic_layer(settings.semantic_layer_path),
        duckdb_path=settings.duckdb_path,
        documents_config=documents_config,
        documents_db_path=settings.documents_db_path,
        embedder=FastEmbedEmbedder(documents_config.model, settings.models_cache_dir),
        llm=build_llm_client(llm_settings, config),
    )


def error_response(question: str, code: str, message: str) -> AgentResponse:
    """Respuesta `error` sin ejecutar el agente (configuración inválida o fallo fuera del grafo)."""
    return AgentResponse(status="error", error_code=code, message=message, trace=Trace(question=question))


def answer_question(question: str, deps: AgentDeps | None = None) -> AgentResponse:
    """Responde la pregunta. Los fallos de configuración, datos y proveedor vuelven como respuesta `error`."""
    if deps is None:
        try:
            deps = build_deps()
        except CONFIGURATION_ERRORS as error:
            return error_response(question, CONFIGURATION_ERROR, str(error))
    return run_graph(question, deps)
