# Proposal

## Why

Preguntas como "¿qué hallazgos de consumidor podrían explicar el deterioro?" necesitan evidencia de los documentos, no solo cifras, y hoy el asistente solo consulta ventas. Hace falta convertir el PDF, el Word y el Markdown de `data/raw/` en fragmentos citables por su ID de evidencia (`REP-02`, `INV-04`…) y recuperarlos de forma fiable en español.

## What Changes

- **Ingesta de documentos** (`make ingest-docs`):
  - conversión de PDF (PyMuPDF) y Word (python-docx) a un Markdown normalizado: títulos como `#`/`##`/`###`, tablas como tablas Markdown (también las de PDF, que no tienen bordes) y marcas de página;
  - un único fragmentador de Markdown para los tres formatos: fragmentos por sección y por ID de evidencia, con metadatos (documento, tipo, título, sección, página, IDs, `chunk_id`);
  - las filas de tabla se escriben como `encabezado: valor | …`, y una tabla de registros con ID se divide en un fragmento por fila;
  - todo se guarda, con el Markdown de cada documento, en una base DuckDB propia, con publicación atómica y trazabilidad de la carga.
- **Embeddings locales con fastembed** (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones) detrás de una interfaz `Embedder`, fijados por la huella del archivo del modelo. Se embebe título, sección y texto. Sin red tras `make models`.
- **`buscar_documentos`** (función Python pura, pydantic): híbrido BM25 + embeddings con RRF, filtros por documento y tipo, resultados citables con `evidence_id` y contenido devuelto como evidencia, nunca como instrucciones.
- **Degradación explícita**: si el modelo no está disponible o no coincide con el de la carga, la búsqueda usa solo BM25 y lo avisa.
- **Configuración** en `backend/config/documents.yaml`: extensiones, patrones de IDs, modelo y su huella, parámetros de recuperación.

Prueba de elección del modelo (55 fragmentos reales, 10 preguntas en español): el híbrido BM25 + MiniLM con título y sección obtuvo hit@3 10/10 y MRR 0,90 (0,95 en la implementación final), y BM25 solo 9/10 y 0,68. Ollama `nomic-embed-text` no superó a MiniLM en una prueba previa. Es una prueba exploratoria; la evaluación formal es el change 9.

## Capabilities

### New Capabilities

- `document-ingestion`: conversión a Markdown, fragmentación, tablas, metadatos, embeddings y publicación de la base de documentos.
- `document-retrieval`: búsqueda híbrida, degradación a BM25, resultados citables y trazabilidad.

### Modified Capabilities

- `project-layout`: `make test` excluye también la marca `embeddings`, que tiene su propio `make test-embeddings`.

## Impact

- **Código nuevo:** `backend/src/analyst_backend/documents/` y pruebas.
- **Reutiliza:** la publicación atómica de `ingestion/storage.py`, el `evidence_id` de `analytics/evidence.py` y la conexión de solo lectura de `analytics/database.py`, que pasa a recibir el esquema esperado.
- **Dependencias del backend (versión fija):** pymupdf 1.28.2, python-docx 1.2.0, rank-bm25 0.2.2, fastembed 0.9.0 y numpy 2.5.4.
- **Configuración:** `DOCUMENTS_DIR`, `DOCUMENTS_DB_PATH`, `DOCUMENTS_CONFIG_PATH` y `MODELS_CACHE_DIR`.
- **Documentación:** `docs/architecture.md` (D7) y `docs/EXPLORACION_DATOS.md`.

## Fuera de alcance

- Wrapper de LangChain y defensa del agente frente a instrucciones en los documentos (change 5); contraste con los datos (change 6).
- Embeddings con Ollama (la interfaz lo permite después) y el modelo en la imagen Docker (change 8).
- OCR, re-ranking y evaluación formal (change 9).
