"""Fixtures del agente: bases reales cargadas en un directorio temporal, sin red.

- Ventas: la ingesta real de `data/raw/` (los `evidence_id` fijos de las pruebas dependen
  de la huella de `semantic_layer.yaml` y del CSV).
- Documentos: la ingesta real con un embedder de prueba (sin modelo descargado).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

from analyst_backend.agent.config import AgentConfig, load_agent_config
from analyst_backend.agent.tools import ToolContext
from analyst_backend.analytics.semantic import SemanticLayer, load_semantic_layer
from analyst_backend.documents.config import DocumentsConfig, load_documents_config
from analyst_backend.documents.embeddings import FakeEmbedder
from analyst_backend.documents.ingest import ingest_documents
from analyst_backend.ingestion.pipeline import ingest
from analyst_backend.settings import DocumentsSettings, IngestionSettings

if TYPE_CHECKING:
    from analyst_backend.agent.models import AgentDeps

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/raw"
SEMANTIC = ROOT / "backend/config/semantic_layer.yaml"
AGENT_CONFIG = ROOT / "backend/config/agent.yaml"
FAKE_MODEL = {"name": "pruebas/fake-embedder", "sha256": "f" * 64, "dimension": 384}


def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder(FAKE_MODEL["name"], FAKE_MODEL["sha256"], FAKE_MODEL["dimension"])


@dataclass(frozen=True)
class Bases:
    sales: Path
    documents: Path
    documents_config_path: Path
    layer: SemanticLayer
    documents_config: DocumentsConfig


@pytest.fixture(scope="session")
def bases(tmp_path_factory: pytest.TempPathFactory) -> Bases:
    folder = tmp_path_factory.mktemp("agent-bases")
    sales = folder / "analytics.duckdb"
    ingest(IngestionSettings(RAW / "02_Ventas_2026.csv", sales, SEMANTIC, ROOT / "backend/config/data_quality.yaml"))
    data = yaml.safe_load((ROOT / "backend/config/documents.yaml").read_text(encoding="utf-8"))
    data["model"].update(FAKE_MODEL)
    documents_config_path = folder / "documents.yaml"
    documents_config_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    documents = folder / "documents.duckdb"
    ingest_documents(DocumentsSettings(RAW, documents, documents_config_path, folder / "sin-modelos"), fake_embedder())
    return Bases(sales, documents, documents_config_path, load_semantic_layer(SEMANTIC),
                 load_documents_config(documents_config_path))


@pytest.fixture(scope="session")
def agent_config() -> AgentConfig:
    return load_agent_config(AGENT_CONFIG)


@pytest.fixture(scope="session")
def tool_context(bases: Bases, agent_config: AgentConfig) -> ToolContext:
    return ToolContext(
        layer=bases.layer,
        duckdb_path=bases.sales,
        documents_config=bases.documents_config,
        documents_db_path=bases.documents,
        embedder=fake_embedder(),
        docs_top_k=agent_config.limits.docs_top_k,
        max_quality_issues=agent_config.limits.max_quality_issues,
    )


def make_deps(bases: Bases, config: AgentConfig, *script: object, secret: str = "") -> AgentDeps:
    """Dependencias del agente con un modelo de chat con guion (sin red)."""
    from analyst_backend.agent.llm import LLMClient
    from analyst_backend.agent.models import AgentDeps

    from .fakes import ScriptedChatModel

    llm = LLMClient(ScriptedChatModel.from_script(*script), model_name="modelo-de-prueba", unavailable_retries=0,
                    backoff_s=0, secrets=(secret,))
    return AgentDeps(config=config, layer=bases.layer, duckdb_path=bases.sales,
                     documents_config=bases.documents_config, documents_db_path=bases.documents,
                     embedder=fake_embedder(), llm=llm)
