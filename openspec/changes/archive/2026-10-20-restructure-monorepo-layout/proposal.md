# Proposal

## Why

Brío Analyst tendrá dos aplicaciones desplegables por separado (API FastAPI y frontend Streamlit) con dependencias distintas, pero la decisión D2 de `docs/architecture.md` obliga a poner todo el código en `src/` raíz. Antes de escribir lógica de negocio hace falta una estructura que separe ambas aplicaciones y un esqueleto ejecutable (pruebas, contenedores, comandos comunes) sobre el que construir los changes siguientes del ROADMAP.

## What Changes

- **BREAKING (estructura):** D2 ("Código fuente solo en `src/`") se reemplaza por D2' ("Código fuente en `backend/src/` y `frontend/src/`"). Se elimina `src/` raíz (solo contiene `.gitkeep`).
- Se actualizan las referencias a la ubicación del código en `openspec/config.yaml` (context), `CLAUDE.md` y `docs/architecture.md`, para que ninguna contradiga D2'. Se registra D4 (Python 3.14 y workspace de uv).
- Entorno Python reproducible: versión 3.14 fijada y un workspace de uv con un único `uv.lock` versionado; cada aplicación tiene su propio `pyproject.toml` con dependencias de versión fija.
- Esqueleto del backend: paquete importable y un endpoint de salud.
- Esqueleto del frontend: paquete importable y una página mínima que muestra un título y la URL de la API, ambos configurables por variable de entorno.
- `Makefile` con `test`, `test-llm`, `eval` y `up`. `make eval` falla con un mensaje explícito hasta que exista la suite de evaluación (change 9).
- Contenedores: un Dockerfile por aplicación y `docker-compose.yml` que valida sin necesidad de `.env`.
- Pruebas mínimas aisladas (sin red ni credenciales), separadas de las marcadas como `llm`.

## Capabilities

### New Capabilities

- `project-layout`: ubicación del código, entorno reproducible, comandos comunes (`make`), separación y aislamiento de pruebas, servicios mínimos (salud del backend, página del frontend) y orquestación con contenedores.

### Modified Capabilities

Ninguna (no existen specs previas).

## Impact

- **Archivos nuevos:** `.python-version`, `pyproject.toml` raíz, `uv.lock`, `backend/` y `frontend/` (cada uno con `pyproject.toml`, `Dockerfile`, `src/` y `tests/`), `tests/` raíz y `conftest.py` para comprobaciones y aislamiento, `docker-compose.yml`, `.dockerignore` y `Makefile`.
- **Archivos modificados:** `docs/architecture.md` (D2 → D2', D4), `openspec/config.yaml` (línea del context), `CLAUDE.md` (línea inicial), `README.md` (requisitos y comandos), `.env.example` (`APP_TITLE`).
- **Archivos eliminados:** `src/.gitkeep` y `src/`.
- **Dependencias:** uv 0.13.4 (ya instalado en local), FastAPI, Uvicorn, Streamlit, httpx2 y pytest, todas con versión fija.
- **Herramientas:** graphify sigue indexando el repositorio completo, así que el cambio de carpetas no afecta al grafo.

## Fuera de alcance

- Lógica de negocio: ingesta, métricas, recuperación de documentos, agente, herramientas y evaluación (changes 2 a 9).
- Endpoints de consulta y pantallas de análisis (change 8). Aquí solo existen el endpoint de salud y una página mínima.
- Dependencias de datos y LLM (DuckDB, Pandera, LangGraph, fastembed, etc.): se agregan en el change que las usa.
- `data/raw/` y cualquier dato de ejemplo.
- CI remoto y publicación de imágenes.
