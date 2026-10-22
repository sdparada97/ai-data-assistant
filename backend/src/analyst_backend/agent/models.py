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


@dataclass(frozen=True)
class Evidence:
    """Una evidencia citable de esta ejecución.

    `numbers` son los valores de los resultados de métricas y calidad; `text` es el texto
    literal de un fragmento. `aliases` son todos los ids por los que se puede citar.
    """

    id: str
    kind: Literal["metricas", "calidad", "documento", "busqueda"]
    prompt_text: str
    aliases: frozenset[str]
    numbers: tuple[Decimal, ...] = ()
    text: str = ""
    extra: str = ""


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


class AgentResponse(BaseModel):
    status: Status
    error_code: str | None = None
    message: str | None = None
    facts: list[Claim] = Field(default_factory=list)
    hypotheses: list[Claim] = Field(default_factory=list)
    contradictions: list[Claim] = Field(default_factory=list)
    insufficient: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
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
