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
    uv sync --locked --no-dev --no-install-workspace --package analyst-frontend

# Capa del paquete: instalación no editable (la imagen no depende del código fuente).
COPY frontend/ frontend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --package analyst-frontend

FROM python:3.14-slim
RUN useradd --create-home --uid 1000 app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app
WORKDIR /home/app
EXPOSE 8501
CMD ["analyst-frontend", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
