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
| `make test` | Pruebas sin LLM, modelo de embeddings, red ni credenciales (excluye `@pytest.mark.llm` y `@pytest.mark.embeddings`). |
| `make test-llm` | Solo pruebas marcadas `@pytest.mark.llm`; requieren red y credenciales. |
| `make test-embeddings` | Solo pruebas marcadas `@pytest.mark.embeddings`, con el modelo de embeddings real y sin red; requiere `make models`. |
| `make ingest` | Carga `data/raw/02_Ventas_2026.csv` en `data/processed/analytics.duckdb` aplicando las reglas de calidad. Rutas configurables con `SALES_CSV_PATH`, `DUCKDB_PATH`, `SEMANTIC_LAYER_PATH` y `DATA_QUALITY_PATH`. |
| `make models` | Descarga una vez el modelo de embeddings (~240 MB) en `MODELS_CACHE_DIR` (`.cache/models`) y comprueba su huella. |
| `make ingest-docs` | Convierte a Markdown y fragmenta los documentos de `data/raw/` y publica `data/processed/documents.duckdb` con sus embeddings. Rutas configurables con `DOCUMENTS_DIR`, `DOCUMENTS_DB_PATH`, `DOCUMENTS_CONFIG_PATH` y `MODELS_CACHE_DIR`. |
| `make eval` | Evaluación con el golden set (pendiente del change `add-evaluation-suite`). |
| `make up` | Construye y levanta backend (`:8000`) y frontend (`:8501`) con Docker Compose. |

Los puertos publicados se cambian con `BACKEND_PORT` y `FRONTEND_PORT`.

## Consultar la base desde Python

Tras `make ingest`, las herramientas `consultar_metrica` y `calidad_datos` se pueden probar directamente:

```bash
DUCKDB_PATH=data/processed/analytics.duckdb SEMANTIC_LAYER_PATH=backend/config/semantic_layer.yaml \
uv run --all-packages python -c '
from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import MetricQuery
from analyst_backend.analytics.semantic import load_semantic_layer
from analyst_backend.settings import load_analytics_settings

settings = load_analytics_settings()
layer = load_semantic_layer(settings.semantic_layer_path)
query = MetricQuery(
    metrics=["venta_neta"], filters={"marca": ["Brío"]}, group_by=["region"],
    compare={"base": "2026-T1", "target": "2026-T2"},
    sort={"metric": "venta_neta", "field": "var_pct", "order": "asc"},
)
result = consultar_metrica(query, layer, settings.duckdb_path)
for row in result.rows:
    cell = row.metrics["venta_neta"]
    print(row.rank, row.group["region"], cell.base, cell.target, cell.var_pct)
print(result.evidence_id, [(n.registro_id, n.rule_code) for n in result.quality_notes])
'
```

Tras `make models` y `make ingest-docs`, `buscar_documentos` devuelve los fragmentos más pertinentes con sus IDs de evidencia:

```bash
DOCUMENTS_DIR=data/raw DOCUMENTS_DB_PATH=data/processed/documents.duckdb \
DOCUMENTS_CONFIG_PATH=backend/config/documents.yaml MODELS_CACHE_DIR=.cache/models \
uv run --all-packages python -c '
from analyst_backend.documents.config import load_documents_config
from analyst_backend.documents.embeddings import FastEmbedEmbedder
from analyst_backend.documents.models import DocumentQuery
from analyst_backend.documents.retrieval import buscar_documentos
from analyst_backend.settings import load_documents_settings

settings = load_documents_settings()
config = load_documents_config(settings.documents_config_path)
embedder = FastEmbedEmbedder(config.model, settings.models_cache_dir)
query = DocumentQuery.model_validate({"query": "faltantes de Brío en Sur", "top_k": 3}, context={"config": config})
result = buscar_documentos(query, config, settings.documents_db_path, embedder)
for hit in result.hits:
    print(hit.rank, hit.primary_evidence_id or hit.chunk_id, hit.doc_id, hit.page, hit.text[:70])
print(result.mode, result.evidence_id, [w.code for w in result.warnings])
'
```

Sin el modelo descargado, la búsqueda funciona solo por palabras (`mode = lexico`) y lo avisa.

Sin Docker, cada aplicación se puede lanzar en local:

```bash
uv run --all-packages uvicorn analyst_backend.main:app --reload
uv run --all-packages analyst-frontend
```
