"""Carga y validación de `agent.yaml`."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveInt, ValidationError, field_validator


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

    def temperature_for(self, model: str) -> float:
        """Temperatura del prefijo más largo que coincide con el modelo, o la de por defecto."""
        matches = [prefix for prefix in self.temperature_by_prefix if model.startswith(prefix)]
        return self.temperature_by_prefix[max(matches, key=len)] if matches else self.default_temperature


class ProviderConfig(_Strict):
    gemini: GeminiConfig


class LimitsConfig(_Strict):
    max_question_chars: PositiveInt
    max_calls_per_tool: PositiveInt
    max_quality_issues: PositiveInt
    docs_top_k: PositiveInt


class AgentConfig(_Strict):
    assistant_name: str = Field(min_length=1, description="Nombre con el que el asistente se presenta en los prompts")
    provider: ProviderConfig
    limits: LimitsConfig
    out_of_scope_message: str = Field(min_length=1)
    causal_lexicon: tuple[str, ...] = Field(min_length=1)
    hedges: tuple[str, ...] = Field(min_length=1)

    @field_validator("causal_lexicon", "hedges")
    @classmethod
    def _non_blank(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("no puede haber expresiones vacías")
        return tuple(item.strip() for item in value)


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
