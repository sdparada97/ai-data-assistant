"""Aplicación FastAPI del backend: salud y preguntas al agente."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from analyst_backend.agent.models import AgentDeps
from analyst_backend.agent.service import build_deps
from analyst_backend.api.ask import router, start_runtime, unhandled_error


def create_app(deps_factory: Callable[[], AgentDeps] = build_deps) -> FastAPI:
    """Construye la aplicación. Las dependencias del agente se crean al arrancar (`lifespan`)."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.agent = start_runtime(deps_factory)
        yield

    application = FastAPI(title="analyst-backend", lifespan=lifespan)

    @application.get("/health")
    async def health() -> dict[str, str]:  # asíncrona: responde aunque haya preguntas esperando
        return {"status": "ok"}

    application.add_exception_handler(Exception, unhandled_error)
    application.include_router(router)
    return application


app = create_app()
