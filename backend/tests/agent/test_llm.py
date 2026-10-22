"""Requisitos de llm-provider: selección del proveedor, parámetros, errores y clave nunca expuesta."""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_google_genai.chat_models import GoogleAPIError, GoogleAuthenticationError, GoogleRateLimitError
from pydantic import SecretStr

from analyst_backend.agent.config import AgentConfig, load_agent_config
from analyst_backend.agent.llm import LLMClient, ProviderError, build_chat_model, make_rate_limiter
from analyst_backend.settings import LLMSettings, SettingsError, load_llm_settings

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def config() -> AgentConfig:
    return load_agent_config(ROOT / "backend/config/agent.yaml")


# --- Selección del proveedor -------------------------------------------------------------------


def test_unsupported_provider() -> None:
    with pytest.raises(SettingsError) as error:
        load_llm_settings({"LLM_PROVIDER": "ollama", "GEMINI_MODEL": "m", "GEMINI_API_KEY": "k"})

    assert all(word in str(error.value) for word in ("LLM_PROVIDER", "ollama", "gemini"))


def test_missing_provider() -> None:
    with pytest.raises(SettingsError) as error:
        load_llm_settings({"GEMINI_MODEL": "m", "GEMINI_API_KEY": "k"})

    assert "LLM_PROVIDER" in str(error.value) and "gemini" in str(error.value)


def test_missing_key() -> None:
    with pytest.raises(SettingsError, match="GEMINI_API_KEY"):
        load_llm_settings({"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-x", "GEMINI_API_KEY": "  "})


# --- Parámetros del modelo en configuración ----------------------------------------------------


def test_temperature_by_model_family(config: AgentConfig) -> None:
    gemini3 = build_chat_model(LLMSettings("gemini", "gemini-3-flash", SecretStr("k")), config)
    gemini25 = build_chat_model(LLMSettings("gemini", "gemini-2.5-flash", SecretStr("k")), config)

    assert (gemini3.temperature, gemini25.temperature) == (1.0, 0.0)
    assert gemini3.max_retries == 0
    assert gemini3.max_output_tokens == config.provider.gemini.max_output_tokens
    assert gemini3.timeout == config.provider.gemini.timeout_s
    limiter = gemini3.rate_limiter
    assert limiter is not None
    assert limiter.requests_per_second == config.provider.gemini.requests_per_minute / 60
    assert limiter.max_bucket_size == config.provider.gemini.burst


def test_request_rate_limit(config: AgentConfig) -> None:
    gemini = config.provider.gemini.model_copy(update={"requests_per_minute": 60, "burst": 1})
    model = GenericFakeChatModel(messages=iter(["uno", "dos"]), rate_limiter=make_rate_limiter(gemini))

    model.invoke("a")
    first = time.monotonic()
    model.invoke("b")
    second = time.monotonic()

    assert second - first >= 0.95


# --- Errores del proveedor ---------------------------------------------------------------------


def _client(retries: int = 2, secret: str = "") -> LLMClient:
    return LLMClient(GenericFakeChatModel(messages=iter([])), model_name="m", unavailable_retries=retries,
                     backoff_s=0, secrets=(secret,))


def _failing(errors: Iterator[BaseException], calls: list[int]) -> RunnableLambda:
    def run(_: Any) -> AIMessage:
        calls.append(1)
        error = next(errors, None)
        if error is not None:
            raise error
        return AIMessage(content="bien")

    return RunnableLambda(run)


def _unavailable() -> GoogleAPIError:
    return GoogleAPIError(code=503, response_json={"error": {"code": 503, "status": "UNAVAILABLE"}})


def test_quota_exhausted_is_not_retried() -> None:
    calls: list[int] = []
    client = _client()

    with pytest.raises(ProviderError) as error:
        client.invoke(_failing(iter([GoogleRateLimitError("429 RESOURCE_EXHAUSTED")]), calls), ["hola"])

    assert error.value.code == "quota_exhausted"
    assert len(calls) == 1 and client.attempts == 1 and client.calls == 1


def test_transient_unavailability() -> None:
    calls: list[int] = []
    client = _client(retries=2)

    result = client.invoke(_failing(iter([_unavailable()]), calls), ["hola"])

    assert result.content == "bien"
    assert len(calls) == 2 and client.attempts == 2 and client.calls == 1


def test_persistent_unavailability() -> None:
    calls: list[int] = []
    client = _client(retries=2)

    with pytest.raises(ProviderError) as error:
        client.invoke(_failing(iter([_unavailable()] * 5), calls), ["hola"])

    assert error.value.code == "provider_unavailable"
    assert len(calls) == 3


def test_timeout() -> None:
    with pytest.raises(ProviderError) as error:
        _client().invoke(_failing(iter([httpx.ReadTimeout("tiempo agotado")]), []), ["hola"])

    assert error.value.code == "timeout"


def test_rejected_key_is_not_retried() -> None:
    calls: list[int] = []

    with pytest.raises(ProviderError) as error:
        _client().invoke(_failing(iter([GoogleAuthenticationError("401 API key not valid")]), calls), ["hola"])

    assert error.value.code == "provider_error"
    assert len(calls) == 1


# --- Clave nunca expuesta ----------------------------------------------------------------------


def test_key_never_exposed_in_provider_errors() -> None:
    secret = "clave-de-prueba-123"
    client = _client(secret=secret)

    with pytest.raises(ProviderError) as error:
        client.invoke(_failing(iter([GoogleAuthenticationError(f"API key {secret} not valid")]), []), ["hola"])

    assert secret not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert "***" in str(error.value)


def test_programming_errors_are_not_provider_errors() -> None:
    """Un fallo del propio código no se disfraza de error del proveedor: el grafo lo da como internal_error."""
    calls: list[int] = []

    with pytest.raises(KeyError):
        _client().invoke(_failing(iter([KeyError("campo")]), calls), ["hola"])

    assert len(calls) == 1
