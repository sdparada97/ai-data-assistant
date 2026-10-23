"""Proveedor de LLM: crea el modelo de chat de Gemini y centraliza sus llamadas.

`LLMClient.invoke` aplica los reintentos ante saturación (500/503/504), nunca ante
cuota agotada (429), convierte los errores en `ProviderError` con código y elimina la
clave de cualquier texto. Cuenta las llamadas lógicas y los intentos al proveedor.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx
from langchain_core.exceptions import ModelAPIError
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_google_genai.chat_models import GoogleAPIError, GoogleGenerativeAIError, GoogleRateLimitError

from analyst_backend.agent.config import AgentConfig, GeminiConfig
from analyst_backend.settings import LLMSettings

RETRYABLE_STATUS = frozenset({500, 503, 504})
# Excepciones del proveedor: las de langchain-google-genai, las de langchain-core de las que
# heredan (incluido el 5xx de google-genai, `GoogleAPIError`) y las de red. Cualquier otra es un fallo del
# propio código y llega al grafo como `internal_error`, sin su texto.
PROVIDER_ERRORS: tuple[type[BaseException], ...] = (
    GoogleGenerativeAIError,
    ModelAPIError,
    httpx.HTTPError,
    TimeoutError,
)
_REDACTED = "***"


class ProviderError(RuntimeError):
    """Fallo del proveedor de LLM con un código estable para la respuesta del agente."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _is_retryable(error: BaseException) -> bool:
    return isinstance(error, GoogleAPIError) and getattr(error, "code", None) in RETRYABLE_STATUS


def _error_code(error: BaseException) -> str:
    if isinstance(error, GoogleRateLimitError):
        return "quota_exhausted"
    if _is_retryable(error):
        return "provider_unavailable"
    if isinstance(error, httpx.TimeoutException | TimeoutError):
        return "timeout"
    return "provider_error"


class LLMClient:
    """Modelo de chat con límites, reintentos acotados, errores con código y contadores."""

    def __init__(
        self,
        chat_model: BaseChatModel,
        *,
        model_name: str,
        unavailable_retries: int,
        backoff_s: float,
        secrets: Sequence[str] = (),
        plan_reasoning: str | None = None,
        synthesis_reasoning: str | None = None,
    ) -> None:
        self.chat_model = chat_model
        self.plan_reasoning = plan_reasoning  # razonamiento con herramientas (planificación y corrección)
        self.synthesis_reasoning = synthesis_reasoning  # razonamiento de la salida estructurada (síntesis)
        self.model_name = model_name
        self._retries = unavailable_retries
        self._backoff_s = backoff_s
        self._secrets = tuple(secret for secret in secrets if secret)
        self.calls = 0
        self.attempts = 0

    def _with_reasoning(self, reasoning: str | None) -> BaseChatModel:
        """Copia del modelo con el nivel de razonamiento del paso; el modelo compartido no cambia."""
        if reasoning is None:
            return self.chat_model
        return self.chat_model.model_copy(update={"reasoning_effort": reasoning})

    def with_tools(self, tools: Sequence[Any]) -> Runnable:
        return self._with_reasoning(self.plan_reasoning).bind_tools(list(tools))

    def structured(self, schema: type) -> Runnable:
        """Salida estructurada; devuelve `{raw, parsed, parsing_error}` en lugar de lanzar al no poder interpretar."""
        model = self._with_reasoning(self.synthesis_reasoning)
        return model.with_structured_output(schema, method="json_schema", include_raw=True)

    def redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, _REDACTED)
        return text

    def invoke(self, runnable: Runnable, messages: Sequence[Any]) -> Any:
        self.calls += 1

        def attempt(payload: Any) -> Any:
            self.attempts += 1  # dentro de la parte reintentada: with_retry no expone los intentos
            return runnable.invoke(payload)

        retrying = RunnableLambda(attempt).with_retry(
            retry_if_exception_type=_is_retryable,
            stop_after_attempt=self._retries + 1,
            wait_exponential_jitter=self._backoff_s > 0,
            exponential_jitter_params={"initial": self._backoff_s} if self._backoff_s > 0 else None,
        )
        try:
            return retrying.invoke(list(messages))
        except ProviderError:
            raise
        except PROVIDER_ERRORS as error:  # los fallos del proveedor se convierten en un código estable
            code = _error_code(error)
            message = self.redact(f"{type(error).__name__}: {error}")[:500]
        # Fuera del `except`: el ProviderError no conserva la excepción original (ni causa ni contexto),
        # cuyo texto podría contener la clave.
        raise ProviderError(code, f"{code}: {message}")


def make_rate_limiter(gemini: GeminiConfig) -> InMemoryRateLimiter:
    return InMemoryRateLimiter(
        requests_per_second=gemini.requests_per_minute / 60,
        check_every_n_seconds=0.05,
        max_bucket_size=gemini.burst,
    )


def build_chat_model(settings: LLMSettings, config: AgentConfig) -> BaseChatModel:
    """Modelo de chat del proveedor configurado. Solo Gemini en esta versión (lo valida `load_llm_settings`)."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    gemini = config.provider.gemini
    return ChatGoogleGenerativeAI(
        model=settings.model,
        api_key=settings.api_key,
        temperature=gemini.temperature_for(settings.model),
        max_output_tokens=gemini.max_output_tokens,
        timeout=gemini.timeout_s,
        max_retries=0,  # los reintentos los decide LLMClient: nunca ante cuota agotada
        rate_limiter=make_rate_limiter(gemini),
    )


def build_llm_client(settings: LLMSettings, config: AgentConfig, chat_model: BaseChatModel | None = None) -> LLMClient:
    gemini = config.provider.gemini
    return LLMClient(
        chat_model if chat_model is not None else build_chat_model(settings, config),
        model_name=settings.model,
        unavailable_retries=gemini.unavailable_retries,
        backoff_s=gemini.backoff_s,
        secrets=(settings.api_key.get_secret_value(),),
        plan_reasoning=gemini.plan_reasoning_for(settings.model),
        synthesis_reasoning=gemini.synthesis_reasoning_for(settings.model),
    )
