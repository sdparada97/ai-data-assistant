"""Configuración del frontend leída de variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_APP_TITLE = "Asistente de análisis"
DEFAULT_BACKEND_URL = "http://localhost:8000"


@dataclass(frozen=True)
class Settings:
    app_title: str
    backend_url: str


def load_settings() -> Settings:
    """Lee ``APP_TITLE`` y ``BACKEND_URL``; usa valores por defecto si faltan o están vacías."""
    return Settings(
        app_title=os.environ.get("APP_TITLE") or DEFAULT_APP_TITLE,
        backend_url=os.environ.get("BACKEND_URL") or DEFAULT_BACKEND_URL,
    )
