# syntax=docker/dockerfile:1
# Contexto de build: raíz del repositorio (necesita uv.lock y el workspace).
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/uv
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Capa de dependencias: solo cambia si cambian los pyproject o el lock.
COPY pyproject.toml uv.lock .python-version ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY frontend/pyproject.toml frontend/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-workspace --package analyst-backend

# Capa del paquete: instalación no editable (la imagen no depende del código fuente).
COPY backend/ backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --package analyst-backend

FROM python:3.14-slim
RUN useradd --create-home --uid 1000 app
COPY --from=builder /app/.venv /app/.venv
# Configuración del agente, la capa semántica y los documentos (rutas fijadas en docker-compose.yml).
COPY backend/config /app/config
ENV PATH="/app/.venv/bin:$PATH"
USER app
WORKDIR /home/app
EXPOSE 8000
CMD ["uvicorn", "analyst_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
