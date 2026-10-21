"""Aplicación FastAPI del backend."""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Construye la aplicación con sus rutas."""
    application = FastAPI(title="analyst-backend")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
