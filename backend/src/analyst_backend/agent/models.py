"""Modelos del agente: síntesis que produce el LLM, evidencias, traza y respuesta."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.llm import LLMClient
from analyst_backend.analytics.semantic import SemanticLayer
from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import Embedder

Status = Literal["ok", "insuficiente", "fuera_de_alcance", "error"]


# --- Lo que escribe el LLM (descripciones en español: es lo que lee) ---------------------------


class Claim(BaseModel):
    statement: str = Field(description="Afirmación en español")
    evidence: list[str] = Field(
        default_factory=list,
        description="Ids exactos de la evidencia que la sustenta: evidence_id (EV-...), id de fragmento o ID de documento",
    )


class Synthesis(BaseModel):
    facts: list[Claim] = Field(default_factory=list, description="Hechos comprobados por la evidencia")
    hypotheses: list[Claim] = Field(default_factory=list, description="Hipótesis atenuadas (podría, es compatible con…)")
    contradictions: list[Claim] = Field(default_factory=list, description="Contradicciones entre fuentes")
    insufficient: list[str] = Field(default_factory=list, description="Qué información falta, sin cifras")


# --- Evidencia y traza (código) ----------------------------------------------------------------


EvidenceKind = Literal["metricas", "calidad", "documento", "busqueda", "contraste", "causalidad"]


@dataclass(frozen=True)
class Evidence:
    """Una evidencia citable de esta ejecución.

    `numbers` son las cifras citables (de métricas y calidad, todas las del resultado; de contraste
    y causalidad, solo las explícitas); `text` es el texto literal de un fragmento. `aliases` son
    todos los ids por los que se puede citar. `internal` marca las consultas internas de un contraste
    o una evaluación causal: se pueden citar pero no van como bloques a la síntesis.
    """

    id: str
    kind: EvidenceKind
    prompt_text: str
    aliases: frozenset[str]
    numbers: tuple[Decimal, ...] = ()
    text: str = ""
    extra: str = ""
    # Origen estructurado (para la respuesta): herramienta; documento, fragmento y página; búsqueda.
    tool: str = ""
    doc_id: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    query: str | None = None
    fragment_ids: tuple[str, ...] = ()
    title: str = ""  # título legible para la interfaz, generado en código
    internal: bool = False
    verdict: str | None = None  # veredicto de una evaluación causal
    metrics: tuple[str, ...] = ()  # métricas y agrupación de una consulta de métricas
    group_by: tuple[str, ...] = ()


class ToolRun(BaseModel):
    tool: str
    args: dict[str, Any]
    status: Literal["ok", "error", "descartada"]
    round: int = Field(description="1 = plan, 2 = corrección")
    evidence_id: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = Field(default=None, description="Resultado completo (artifact)")


class Trace(BaseModel):
    question: str
    plan_text: str = ""
    tool_runs: list[ToolRun] = Field(default_factory=list)
    repairs: int = 0
    synthesis_retries: int = 0
    verification_problems: list[str] = Field(default_factory=list)
    llm_calls: int = 0
    llm_attempts: int = 0
    model: str = ""
    duration_ms: int = 0


class EvidenceView(BaseModel):
    """Una evidencia de la ejecución tal como la recibe quien lee la respuesta (la interfaz)."""

    id: str
    kind: EvidenceKind
    title: str = Field(description="Título legible, generado en código a partir de la consulta o del documento")
    citable_ids: list[str] = Field(description="Ids por los que una afirmación puede citarla")
    tool: str
    doc_id: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    text: str | None = Field(default=None, description="Texto literal del fragmento")
    result: dict[str, Any] | None = Field(
        default=None, description="Resultado completo de métricas, calidad, contraste o causalidad"
    )
    query: str | None = Field(default=None, description="Consulta de la búsqueda")
    fragment_ids: list[str] = Field(default_factory=list, description="Fragmentos de la búsqueda")


class AgentResponse(BaseModel):
    status: Status
    error_code: str | None = None
    message: str | None = None
    facts: list[Claim] = Field(default_factory=list)
    hypotheses: list[Claim] = Field(default_factory=list)
    contradictions: list[Claim] = Field(default_factory=list)
    insufficient: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence: list[EvidenceView] = Field(default_factory=list)
    trace: Trace


@dataclass
class AgentDeps:
    """Dependencias de una ejecución. `answer_question` las crea desde settings salvo en las pruebas."""

    config: AgentConfig
    layer: SemanticLayer
    duckdb_path: Path
    documents_config: DocumentsConfig
    documents_db_path: Path
    embedder: Embedder
    llm: LLMClient
