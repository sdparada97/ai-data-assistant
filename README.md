# ai-data-assistant

Brío Analyst: asistente de análisis comercial con IA. Arquitectura y decisiones en [docs/architecture.md](docs/architecture.md); avance en [openspec/ROADMAP.md](openspec/ROADMAP.md).

## Requisitos

- Python 3.14 (fijado en `.python-version`; por ejemplo con `pyenv install 3.14`)
- [uv](https://docs.astral.sh/uv/) 0.13.4: `curl -LsSf https://astral.sh/uv/0.13.4/install.sh | sh`
- Docker con Compose ≥ 2.24
- GNU Make

## Instalación

```bash
uv sync --all-packages
cp .env.example .env   # completa las variables; .env nunca se versiona
```

## Estructura

- `backend/src/analyst_backend/`: API (FastAPI).
- `frontend/src/analyst_frontend/`: interfaz (Streamlit).
- `backend/tests/`, `frontend/tests/`, `tests/`: pruebas de cada aplicación y del repositorio.

## Comandos

| Comando | Qué hace |
|---------|----------|
| `make help` | Lista los objetivos disponibles. |
| `make test` | Pruebas sin LLM, red ni credenciales (excluye `@pytest.mark.llm`). |
| `make test-llm` | Solo pruebas marcadas `@pytest.mark.llm`; requieren red y credenciales. |
| `make ingest` | Carga `data/raw/02_Ventas_2026.csv` en `data/processed/analytics.duckdb` aplicando las reglas de calidad. Rutas configurables con `SALES_CSV_PATH`, `DUCKDB_PATH`, `SEMANTIC_LAYER_PATH` y `DATA_QUALITY_PATH`. |
| `make eval` | Evaluación con el golden set (pendiente del change `add-evaluation-suite`). |
| `make up` | Construye y levanta backend (`:8000`) y frontend (`:8501`) con Docker Compose. |

Los puertos publicados se cambian con `BACKEND_PORT` y `FRONTEND_PORT`.

Sin Docker, cada aplicación se puede lanzar en local:

```bash
uv run --all-packages uvicorn analyst_backend.main:app --reload
uv run --all-packages analyst-frontend
```
