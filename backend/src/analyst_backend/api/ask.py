"""`POST /ask`: responde una pregunta con el agente.

Las dependencias del agente se construyen una vez al arrancar (`start_runtime`) y se comparten:
así el límite de peticiones al LLM vale para todas las preguntas. Las preguntas se responden de
una en una (un candado). El cuerpo de la respuesta siempre es la respuesta del agente, salvo el
422 de una petición inválida; el estado HTTP sale de su estado y su código.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from analyst_backend.agent.graph import run_graph
from analyst_backend.agent.models import AgentDeps, AgentResponse
from analyst_backend.agent.service import CONFIGURATION_ERROR, CONFIGURATION_ERRORS, error_response

logger = logging.getLogger(__name__)

INTERNAL_ERROR = "internal_error"
INTERNAL_MESSAGE = "Error interno al responder la pregunta. Revisa los registros del backend."
NOT_READY_MESSAGE = "El agente no está preparado: el backend no completó el arranque."
STARTUP_MESSAGE = "No se pudieron preparar las dependencias del agente ({kind}). Revisa los registros del backend."

# Estado HTTP de una respuesta `error` según su código; cualquier otro código da 500.
ERROR_STATUS: dict[str, int] = {
    "invalid_question": 422,
    "quota_exhausted": 429,
    CONFIGURATION_ERROR: 503,
    "data_unavailable": 503,
    "provider_unavailable": 503,
    "timeout": 504,
    "provider_error": 502,
    "invalid_output": 502,
    INTERNAL_ERROR: 500,
}


class AskRequest(BaseModel):
    """Solo la pregunta: el agente no tiene memoria, así que no se admite historial."""

    model_config = ConfigDict(extra="forbid")

    question: StrictStr = Field(description="Pregunta en lenguaje natural")


@dataclass
class AgentRuntime:
    """Lo que el arranque deja preparado: las dependencias o el error que impidió crearlas."""

    deps: AgentDeps | None = None
    error: tuple[str, str] | None = None  # (código, mensaje)
    lock: threading.Lock = field(default_factory=threading.Lock)


def start_runtime(deps_factory: Callable[[], AgentDeps]) -> AgentRuntime:
    """Construye las dependencias. Un fallo no impide arrancar: queda guardado para cada pregunta."""
    try:
        return AgentRuntime(deps=deps_factory())
    except CONFIGURATION_ERRORS as error:
        return AgentRuntime(error=(CONFIGURATION_ERROR, str(error)))
    except Exception as error:  # cualquier otro fallo: se registra aquí y no se expone su texto
        logger.exception("No se pudieron construir las dependencias del agente")
        return AgentRuntime(error=(INTERNAL_ERROR, STARTUP_MESSAGE.format(kind=type(error).__name__)))


def http_status(response: AgentResponse) -> int:
    if response.status != "error":
        return 200
    return ERROR_STATUS.get(response.error_code or "", 500)


def answer(runtime: AgentRuntime | None, question: str) -> AgentResponse:
    if runtime is None or (runtime.deps is None and runtime.error is None):
        return error_response(question, INTERNAL_ERROR, NOT_READY_MESSAGE)
    if runtime.error is not None:
        return error_response(question, *runtime.error)
    with runtime.lock:  # una pregunta a la vez
        try:
            return run_graph(question, runtime.deps)  # type: ignore[arg-type]  # deps existe si no hay error
        except Exception:  # un fallo fuera de los nodos del grafo: sin su texto en la respuesta
            logger.exception("Fallo no controlado al responder una pregunta")
            return error_response(question, INTERNAL_ERROR, INTERNAL_MESSAGE)


async def unhandled_error(request: Request, error: Exception) -> JSONResponse:
    """Cualquier fallo de la API fuera del agente: respuesta del agente con `internal_error`, sin su texto."""
    logger.exception("Fallo no controlado en la API", exc_info=error)
    response = error_response("", INTERNAL_ERROR, INTERNAL_MESSAGE)
    return JSONResponse(status_code=500, content=response.model_dump(mode="json"))


router = APIRouter()


@router.post("/ask", response_model=AgentResponse)
def ask(body: AskRequest, request: Request) -> JSONResponse:
    """Síncrono: FastAPI lo ejecuta en su pool de hilos; el candado ordena las preguntas."""
    response = answer(getattr(request.app.state, "agent", None), body.question)
    return JSONResponse(status_code=http_status(response), content=response.model_dump(mode="json"))
