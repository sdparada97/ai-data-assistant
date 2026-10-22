"""Manejador de errores de `ToolNode`.

Este módulo NO usa `from __future__ import annotations`: `ToolNode` deduce de la
anotación del parámetro qué excepciones maneja, y con anotaciones diferidas (texto)
falla en Python 3.14. Las demás excepciones (por ejemplo, una base ausente) se
propagan al manejador de errores del grafo.
"""

import json
from typing import Any

from langgraph.prebuilt.tool_node import ToolInvocationError
from pydantic import ValidationError

from analyst_backend.analytics.models import QueryError

ERROR_PREFIX = "ERROR: "
DISCARDED_PREFIX = "DESCARTADA: "


def _validation_details(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"field": ".".join(str(part) for part in error.get("loc", ())), "message": error.get("msg", "")}
        for error in errors
    ]


def format_tool_error(error: QueryError | ValidationError | ToolInvocationError) -> str:
    """Error legible por el LLM: campo, valor rechazado y opciones válidas, o campo y motivo."""
    if isinstance(error, QueryError):
        payload: dict[str, Any] = error.to_dict()
    elif isinstance(error, ValidationError):
        payload = {"validation_errors": _validation_details(error.errors())}
    else:
        source = error.source
        if isinstance(source, ValidationError):
            payload = {"validation_errors": _validation_details(source.errors())}
        else:
            payload = {"message": error.message}
    return ERROR_PREFIX + json.dumps(payload, ensure_ascii=False, default=str)
