"""Carga y validación de `agent.yaml`."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveInt, ValidationError, field_validator

from analyst_backend.analytics.models import CauseKind

# Nombres de las herramientas del agente (aquí para validar `limits.max_calls_by_tool` sin importar tools.py).
METRIC_TOOL = "consultar_metrica"
QUALITY_TOOL = "calidad_datos"
DOCUMENTS_TOOL = "buscar_documentos"
CONTRAST_TOOL = "contrastar_afirmaciones"
CAUSAL_TOOL = "evaluar_causalidad"
TOOL_NAMES = (METRIC_TOOL, QUALITY_TOOL, DOCUMENTS_TOOL, CONTRAST_TOOL, CAUSAL_TOOL)
EXTRACTION_TOOLS = (CONTRAST_TOOL, CAUSAL_TOOL)
DEFAULT_EXTRACTION_MAXIMUM = 1

ReasoningEffort = Literal["minimal", "low", "medium", "high"]
Direction = Literal["contraccion", "crecimiento"]


class AgentConfigError(RuntimeError):
    """`agent.yaml` ausente o inválido."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GeminiConfig(_Strict):
    requests_per_minute: PositiveInt
    burst: PositiveInt
    timeout_s: PositiveInt
    max_output_tokens: PositiveInt
    unavailable_retries: int = Field(ge=0)
    backoff_s: NonNegativeFloat
    temperature_by_prefix: dict[str, float] = Field(default_factory=dict)
    default_temperature: float
    plan_reasoning_by_prefix: dict[str, ReasoningEffort] = Field(default_factory=dict)
    synthesis_reasoning_by_prefix: dict[str, ReasoningEffort] = Field(default_factory=dict)

    def temperature_for(self, model: str) -> float:
        """Temperatura del prefijo más largo que coincide con el modelo, o la de por defecto."""
        matches = [prefix for prefix in self.temperature_by_prefix if model.startswith(prefix)]
        return self.temperature_by_prefix[max(matches, key=len)] if matches else self.default_temperature

    @staticmethod
    def _longest_prefix(values: dict[str, ReasoningEffort], model: str) -> ReasoningEffort | None:
        matches = [prefix for prefix in values if model.startswith(prefix)]
        return values[max(matches, key=len)] if matches else None

    def plan_reasoning_for(self, model: str) -> ReasoningEffort | None:
        """Razonamiento de la planificación y la corrección; `None` deja el del modelo."""
        return self._longest_prefix(self.plan_reasoning_by_prefix, model)

    def synthesis_reasoning_for(self, model: str) -> ReasoningEffort | None:
        """Razonamiento de la síntesis del prefijo más largo que coincide; `None` deja el del modelo."""
        return self._longest_prefix(self.synthesis_reasoning_by_prefix, model)


class ProviderConfig(_Strict):
    gemini: GeminiConfig


class LimitsConfig(_Strict):
    max_question_chars: PositiveInt
    max_calls_per_tool: PositiveInt
    max_quality_issues: PositiveInt
    docs_top_k: PositiveInt
    # Máximo propio por herramienta; en las de extracción cuenta las ejecuciones que llamaron al LLM
    # (1 por defecto). Las demás herramientas usan `max_calls_per_tool` si no aparecen aquí.
    max_calls_by_tool: dict[str, PositiveInt] = Field(
        default_factory=lambda: dict.fromkeys(EXTRACTION_TOOLS, DEFAULT_EXTRACTION_MAXIMUM)
    )

    @field_validator("max_calls_by_tool")
    @classmethod
    def _known_tools(cls, value: dict[str, int]) -> dict[str, int]:
        unknown = sorted(set(value) - set(TOOL_NAMES))
        if unknown:
            raise ValueError(f"herramientas desconocidas: {', '.join(unknown)}. Válidas: {', '.join(TOOL_NAMES)}")
        return {**dict.fromkeys(EXTRACTION_TOOLS, DEFAULT_EXTRACTION_MAXIMUM), **value}


def _non_blank_items(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if any(not item.strip() for item in values):
        raise ValueError("no puede haber expresiones vacías")
    return tuple(item.strip() for item in values)


class ContrastConfig(_Strict):
    """Umbrales y límites de `contrastar_afirmaciones`."""

    approx_pp: Decimal = Field(gt=0, description="Diferencia máxima, en pp, para 'aproximado'")
    max_claims: PositiveInt
    max_document_chars: PositiveInt
    direction_words: dict[Direction, tuple[str, ...]] = Field(description="Palabras de sentido de una dirección")

    @field_validator("direction_words")
    @classmethod
    def _words(cls, value: dict[Direction, tuple[str, ...]]) -> dict[Direction, tuple[str, ...]]:
        if set(value) != {"contraccion", "crecimiento"}:
            raise ValueError("hacen falta palabras para 'contraccion' y 'crecimiento'")
        return {key: _non_blank_items(words) for key, words in value.items()}


class CausalConfig(_Strict):
    """Umbrales de los criterios de `evaluar_causalidad`."""

    locate_margin_pp: Decimal = Field(ge=0)
    differential_pp: Decimal = Field(gt=0)
    step_share: Decimal = Field(gt=0, le=1)
    uniform_spread_pp: Decimal = Field(gt=0)
    cause_change_pct: Decimal = Field(ge=0)
    open_dimensions: tuple[str, ...] = ()
    search_top_k: PositiveInt
    cause_kind_examples: dict[CauseKind, tuple[str, ...]]

    @field_validator("cause_kind_examples")
    @classmethod
    def _examples(cls, value: dict[CauseKind, tuple[str, ...]]) -> dict[CauseKind, tuple[str, ...]]:
        if set(value) != {"competencia", "disponibilidad", "metrica_propia"}:
            raise ValueError("hacen falta ejemplos para competencia, disponibilidad y metrica_propia")
        return {key: _non_blank_items(examples) for key, examples in value.items()}


class AgentConfig(_Strict):
    assistant_name: str = Field(min_length=1, description="Nombre con el que el asistente se presenta en los prompts")
    provider: ProviderConfig
    limits: LimitsConfig
    out_of_scope_message: str = Field(min_length=1)
    causal_lexicon: tuple[str, ...] = Field(min_length=1)
    hedges: tuple[str, ...] = Field(min_length=1)
    contrast: ContrastConfig
    causal: CausalConfig
    # Coherencia de "información insuficiente" con lo consultado.
    absence_markers: tuple[str, ...] = Field(min_length=1)
    absence_exceptions: tuple[str, ...] = ()
    metric_synonyms: dict[str, str] = Field(default_factory=dict, description="Término → métrica del catálogo")

    @field_validator("causal_lexicon", "hedges", "absence_markers", "absence_exceptions")
    @classmethod
    def _non_blank(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _non_blank_items(value)


def load_agent_config(path: Path) -> AgentConfig:
    if not path.is_file():
        raise AgentConfigError(f"No existe la configuración del agente: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise AgentConfigError(f"YAML inválido en {path}: {error}") from error
    if not isinstance(data, dict):
        raise AgentConfigError(f"{path} debe contener un objeto YAML")
    try:
        return AgentConfig.model_validate(data)
    except ValidationError as error:
        raise AgentConfigError(f"Configuración inválida en {path}: {error}") from error
