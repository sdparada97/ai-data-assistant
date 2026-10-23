"""Cliente HTTP de la API del agente (`POST /ask`).

Clasifica el resultado en cuatro casos para que la página nunca reciba una excepción:
respuesta del agente (con cualquier estado HTTP), tiempo agotado, API inaccesible y
respuesta no reconocible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

OutcomeKind = Literal["answer", "timeout", "unreachable", "unrecognized"]


@dataclass(frozen=True)
class AskOutcome:
    kind: OutcomeKind
    http_status: int | None = None
    body: dict[str, Any] | None = None  # la respuesta del agente, si `kind == "answer"`


def _is_agent_response(body: Any) -> bool:
    return isinstance(body, dict) and "status" in body and "trace" in body


def ask_backend(
    url: str, question: str, timeout: float, transport: httpx.BaseTransport | None = None
) -> AskOutcome:
    """Envía solo la pregunta nueva: el agente no tiene memoria."""
    try:
        with httpx.Client(base_url=url, timeout=timeout, transport=transport) as client:
            response = client.post("/ask", json={"question": question})
    except httpx.TimeoutException:
        return AskOutcome("timeout")
    except (httpx.HTTPError, httpx.InvalidURL):  # sin conexión, conexión cortada, URL inválida…
        return AskOutcome("unreachable")
    try:
        body = response.json()
    except ValueError:
        body = None
    if _is_agent_response(body):
        return AskOutcome("answer", response.status_code, body)
    return AskOutcome("unrecognized", response.status_code)
