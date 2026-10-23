"""Configuración del frontend leída de variables de entorno."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

DEFAULT_APP_TITLE = "Asistente de análisis"
DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_BACKEND_TIMEOUT_S = 300.0
TIMEOUT_WARNING = (
    "BACKEND_TIMEOUT_S no es un número positivo de segundos; se usan "
    f"{DEFAULT_BACKEND_TIMEOUT_S:g} segundos."
)


@dataclass(frozen=True)
class Settings:
    app_title: str
    backend_url: str
    backend_timeout_s: float = DEFAULT_BACKEND_TIMEOUT_S
    timeout_warning: str | None = None  # aviso para la página si BACKEND_TIMEOUT_S no es válida


def _timeout(raw: str | None) -> tuple[float, str | None]:
    if raw is None or not raw.strip():
        return DEFAULT_BACKEND_TIMEOUT_S, None
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_BACKEND_TIMEOUT_S, TIMEOUT_WARNING
    if not math.isfinite(value) or value <= 0:
        return DEFAULT_BACKEND_TIMEOUT_S, TIMEOUT_WARNING
    return value, None


def load_settings() -> Settings:
    """Lee ``APP_TITLE``, ``BACKEND_URL`` y ``BACKEND_TIMEOUT_S``; usa valores por defecto si faltan o están vacías."""
    timeout, warning = _timeout(os.environ.get("BACKEND_TIMEOUT_S"))
    return Settings(
        app_title=os.environ.get("APP_TITLE") or DEFAULT_APP_TITLE,
        backend_url=os.environ.get("BACKEND_URL") or DEFAULT_BACKEND_URL,
        backend_timeout_s=timeout,
        timeout_warning=warning,
    )
