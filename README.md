# ai-data-assistant

Brío Analyst: asistente de análisis comercial con IA. Arquitectura y decisiones en [docs/architecture.md](docs/architecture.md).

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

- `backend/src/analyst_backend/`: API (FastAPI, `POST /ask`) y agente.
- `frontend/src/analyst_frontend/`: interfaz del analista (Streamlit).
- `backend/tests/`, `frontend/tests/`, `tests/`: pruebas de cada aplicación y del repositorio.

## Comandos

| Comando | Qué hace |
|---------|----------|
| `make help` | Lista los objetivos disponibles. |
| `make test` | Pruebas sin LLM, modelo de embeddings, red ni credenciales (excluye `@pytest.mark.llm` y `@pytest.mark.embeddings`). |
| `make test-llm` | Solo pruebas marcadas `@pytest.mark.llm`; requieren red y credenciales en `ENV_FILE`. `LLM_TESTS` limita las rutas (por ejemplo, `LLM_TESTS=backend/tests/agent/test_gemini.py`). |
| `make test-embeddings` | Solo pruebas marcadas `@pytest.mark.embeddings`, con el modelo de embeddings real y sin red; requiere `make models`. |
| `make ingest` | Carga `data/raw/02_Ventas_2026.csv` en `data/processed/analytics.duckdb` aplicando las reglas de calidad. Rutas configurables con `SALES_CSV_PATH`, `DUCKDB_PATH`, `SEMANTIC_LAYER_PATH` y `DATA_QUALITY_PATH`. |
| `make models` | Descarga una vez el modelo de embeddings (~240 MB) en `MODELS_CACHE_DIR` (`.cache/models`) y comprueba su huella. |
| `make ingest-docs` | Convierte a Markdown y fragmenta los documentos de `data/raw/` y publica `data/processed/documents.duckdb` con sus embeddings. Rutas configurables con `DOCUMENTS_DIR`, `DOCUMENTS_DB_PATH`, `DOCUMENTS_CONFIG_PATH` y `MODELS_CACHE_DIR`. |
| `make ask Q="<pregunta>"` | Responde una pregunta con el agente e imprime hechos, hipótesis, contradicciones e información insuficiente con sus evidencias, los avisos y un resumen de la traza. Requiere `make ingest`, `make ingest-docs` y Gemini configurado (ver abajo). Carga `ENV_FILE` (por defecto `.env`) solo si existe. |
| `make eval` | Evaluación con el golden set (pendiente del change `add-evaluation-suite`). |
| `make up` | Comprueba las bases y el modelo (`make up-check`) y levanta backend (`:8000`) y frontend (`:8501`) con Docker Compose, solo en `127.0.0.1`. Ver "Usar la aplicación". |
| `make up-check` | Solo la comprobación previa de `make up`: si falta algo, nombra `make ingest`, `make ingest-docs` o `make models`. |

Los puertos publicados se cambian con `BACKEND_PORT` y `FRONTEND_PORT`.

## Preguntar al agente

El agente usa Gemini. En `.env` (nunca se versiona):

```bash
LLM_PROVIDER=gemini
GEMINI_MODEL=<modelo, por ejemplo uno de la familia Gemini Flash>
GEMINI_API_KEY=<tu clave de Google AI Studio>
```

Los límites del proveedor (peticiones por minuto, tiempo máximo, reintentos ante 5xx), el nivel de razonamiento de la planificación y de la síntesis (`plan_reasoning_by_prefix`, `synthesis_reasoning_by_prefix`; `low` en Gemini 3 para que las respuestas no pasen de minutos), los topes de consultas y el léxico de la verificación están en `backend/config/agent.yaml` (`AGENT_CONFIG_PATH`). Con la cuota gratuita, una pregunta de cifras hace normalmente 2 llamadas al LLM (plan y síntesis); una de contraste o de causalidad, 3 (además, la extracción dentro de la herramienta); como mucho 6.

Preguntas guía del equipo de ventas (ejemplos, no una lista cerrada):

- ¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026?
- ¿Son consistentes las principales conclusiones del reporte comercial con los datos de ventas? (contrasta cada afirmación del reporte con los datos y da un veredicto por afirmación)
- ¿Podemos afirmar que las promociones de la competencia causaron la caída de ventas? (evalúa la afirmación con cinco criterios y da un veredicto: contradicha, no sustentada o compatible como hipótesis; nunca la da por demostrada)

```bash
make ingest && make models && make ingest-docs   # una vez
make ask Q="¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026?"
```

Termina con código 1 si falta configuración (nombra la variable) y 2 si la respuesta tiene estado `error` (por ejemplo, `quota_exhausted`).

## Usar la aplicación

La interfaz del analista está en `http://localhost:8501`: se escribe la pregunta y la respuesta llega separada en hechos, hipótesis, contradicciones e información insuficiente. Cada cita se despliega para ver su evidencia (la tabla de la consulta, el texto del fragmento con su documento y página, la tabla de afirmaciones de un contraste con las descartadas aparte, o los criterios y el veredicto de una evaluación causal). También muestra los avisos y la traza. El historial es solo de la sesión del navegador: cada pregunta se responde de forma independiente.

```bash
make ingest && make models && make ingest-docs   # una vez, en el host
make up                                          # Gemini configurado en .env
```

- **Datos del host:** compose monta `data/processed` y `.cache/models` en **solo lectura**. Las bases deben llamarse `analytics.duckdb` y `documents.duckdb` (los nombres por defecto). Otros directorios: `make up DOCKER_DATA_DIR=... DOCKER_MODELS_DIR=...`. Son variables de `make`; con `docker compose up` directamente deben ser rutas absolutas o empezar por `./`. El contenedor lee los archivos con el uid 1000: deben ser legibles para ese usuario.
- **Datos cargados después:** si ejecutas `make ingest` con la aplicación en marcha, la siguiente pregunta ya los usa.
- **Configuración:** solo el backend recibe `.env`. Tras cambiar `.env`, vuelve a ejecutar `make up` para recrear el contenedor.
- **Puertos:** se publican solo en `127.0.0.1`, para que nadie más en la red use la API ni la cuota de Gemini. Se cambian con `BACKEND_PORT` y `FRONTEND_PORT`.
- **Tiempo de espera:** la interfaz espera la respuesta `BACKEND_TIMEOUT_S` segundos (300 por defecto). Si se agota, la pregunta puede seguir en curso en la API.
- **Una pregunta a la vez:** la API responde de una en una; las demás esperan su turno.

La API también se puede usar directamente:

```bash
curl -s -X POST http://localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026?"}'
```

Devuelve la respuesta del agente en JSON (`status`, `error_code`, `message`, `facts`, `hypotheses`, `contradictions`, `insufficient`, `warnings`, `evidence` y `trace`). El estado HTTP sigue al resultado: 200 si hay respuesta; 422 para una pregunta vacía o una petición inválida (solo admite `question`); 429 si se agotó la cuota; 503 si faltan datos o configuración; 502 o 504 ante fallos del proveedor; 500 ante un error interno.

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
