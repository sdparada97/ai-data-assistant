# Design

## Context

Ver proposal.md (Why). Estado actual:
- `data/raw/` tiene 4 documentos:
  - `01_Contexto_Negocio.md`: secciones con `##` (a veces sin línea en blanco tras el título) y una tabla.
  - `03_Investigacion_Consumidor.pdf` y `05_Reporte_Comercial.pdf`: un título por página (17 pt), secciones numeradas de unos 11,2 pt, cabecera y pie repetidos en cada página, y tablas **sin bordes**: cada fila es un rectángulo de fondo y hay celdas de dos líneas centradas en vertical.
  - `04_Observaciones_Canales.docx`: estilos `Title`, `Heading 1`, `Heading 2`, viñetas y 2 tablas; la segunda tiene una fila por registro `CAM-*`. Contiene además `OC-EXT-06`, un texto importado con instrucciones dirigidas a "el asistente de IA".
- Pruebas de conversión a Markdown con los archivos reales:
  - `pymupdf4llm` 1.28.2: buenos títulos, pero desordena la tabla de la sección 3 de la investigación (asigna "Centro" a la línea equivocada), parte el encabezado de la tabla del reporte y añade `pymupdf-layout`.
  - `markitdown` 0.1.9: en PDF no produce títulos ni quita cabeceras; añade `magika`, `requests` y `onnxruntime`.
  - `page.find_tables()` de PyMuPDF: no sirve, porque las tablas no tienen líneas.
  - Conversión propia (prototipo de unas 150 líneas con PyMuPDF y python-docx): tablas correctas, títulos correctos y 55 fragmentos (4/18/21/12).
- Prueba de recuperación con esos 55 fragmentos y 10 preguntas en español: el híbrido BM25 + MiniLM con título y sección dio hit@3 10/10 y MRR 0,90; MiniLM solo, MRR 0,80; BM25 solo, 9/10 y 0,68. Esas cifras son del prototipo con el IDF de Okapi; la implementación final (sin fragmentos de puntuación 0 en el ranking BM25 e IDF de Lucene) da híbrido 10/10 y MRR 0,95, y BM25 solo 7/10 y 0,72.
- fastembed 0.9.0 carga `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` sin red desde la caché (`local_files_only=True`). El modelo pesa 0,22 GB y se obtiene de `Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q`; el archivo `model_optimized.onnx` tiene una huella SHA-256 fija.
- El change 2 ya tiene publicación atómica (`ingestion.storage.publish`) y el change 3 el `evidence_id` determinista (`analytics.evidence.evidence_id`).
- La suite de pruebas bloquea toda conexión de red.

## Goals / Non-Goals

**Goals:**
- Un único formato intermedio (Markdown) y un único fragmentador, de modo que PDF, Word y Markdown se fragmenten con las mismas reglas.
- Fragmentos alineados con las unidades que el asistente debe citar (`REP-02`, `INV-04`…), con las tablas legibles.
- Una búsqueda que funcione sin el modelo, en modo léxico y avisándolo.

**Non-Goals:**
- OCR, re-ranking, el modelo dentro de la imagen Docker (change 8) y el wrapper de LangChain (change 5).
- Volúmenes grandes: con 55 fragmentos, BM25 y el coseno se calculan en memoria en cada consulta.

## Decisions

### D7a: convertir PDF y Word a Markdown con código propio, y fragmentar solo Markdown
`documents/markdown.py` tiene `pdf_to_markdown(path, config)` y `docx_to_markdown(path)`. Convenciones del Markdown normalizado: `#` título, `##` sección, `###` subsección, `- ` listas, tablas GFM (con `|` escapado en las celdas) y `<!-- page: N -->` en PDF. En PDF y Word los espacios repetidos se reducen a uno (`CAM-101  2026-04-09` → `CAM-101 2026-04-09`).
- **PDF:**
  - se leen las líneas con su tamaño de letra y su caja; el título y las secciones se detectan con `pdf.title_min_size` (16), `pdf.section_min_size` (11) y `pdf.section_pattern` (`^\d+\.\s+\S`);
  - con 2 o más páginas, se quitan las líneas presentes en todas las páginas (contadas una vez por página); siempre, las que cumplen `pdf.page_label_pattern` (`^Página \d+$`);
  - un párrafo se corta cuando el salto vertical supera `pdf.paragraph_gap_ratio` (0,8) veces la altura de la línea, en un título o en una línea que empieza por un ID con separador;
  - **tablas:** dos o más rectángulos con relleno, de altura mínima `pdf.min_row_height_pt` (5), del mismo ancho y apilados sin hueco, con tolerancia `pdf.row_stack_tolerance_pt` (1). Cada rectángulo es una fila y el primero el encabezado. Las columnas salen de la fila con más posiciones horizontales distintas; cada línea va a la última columna que empieza a su izquierda (tolerancia `pdf.column_tolerance_pt`, 3) y las líneas de una misma celda se unen en orden.
- **Word:** se recorre el cuerpo en orden (párrafos y tablas). `Title` → `#`, `Heading 1` → `##`, `Heading 2` → `###`, estilos de lista → `- `, tabla → tabla GFM. python-docx repite el texto de una celda combinada en cada posición; se detecta por el mismo elemento `<w:tc>` y se deja vacía la repetición.
- **Archivos:** primer nivel de `DOCUMENTS_DIR`, sin ocultos ni `~$*`; un archivo que PyMuPDF o python-docx no pueden abrir produce un error con su nombre.
- **Markdown:** se usa el archivo tal cual.
- *Descartada: `pymupdf4llm`.* Falla en la tabla con celdas de dos líneas y añade `pymupdf-layout`.
- *Descartada: `markitdown`.* No detecta títulos en estos PDF y trae dependencias de red y de ML que no necesitamos.
- *Descartada: un parser distinto por formato (versión anterior de este design).* Tres juegos de reglas de fragmentación que mantener; con Markdown hay uno.

### D7b: fragmentador de Markdown
`documents/chunking.py` recorre el Markdown línea a línea, separando bloques por líneas en blanco y siempre antes y después de cada título.
- El primer `#` es el título del documento (si no hay, el `doc_id`); los `#` posteriores son títulos de página y no entran al texto. `####` y las líneas dentro de bloques de código delimitados con ``` son texto.
- `##` y `###` abren un fragmento cuya `section` es el título; si el título empieza por un ID con separador, ese ID es el principal.
- El texto anterior a la primera sección forma un fragmento con `section` nula.
- Un párrafo o elemento de lista que empieza por un ID seguido de un separador de `id_separators` (`|`, `:`), ignorando `**` y la viñeta, abre un fragmento con ese ID principal. Los párrafos siguientes sin ID siguen en ese fragmento hasta el siguiente ID o título (así, la nota de trazabilidad queda con `OC-EXT-06`).
- `evidence_ids` empieza por el ID principal, aunque solo esté en el título.
- Las tablas se escriben fila a fila como `encabezado: valor | …`. Si todas las filas empiezan por un ID, sin repetidos, y ninguno es ya principal en el documento, cada fila es un fragmento (se comprueba en una segunda pasada, en orden de aparición, añadiendo a los principales los IDs de cada tabla dividida: gana la primera aparición). Si no, la tabla queda en el fragmento de su sección. Así el índice de referencias de la investigación no duplica `INV-01`…`INV-05`.
- Si una sección tiene texto antes y después de una tabla que se divide, ese texto queda en un fragmento colocado antes de las filas. No ocurre en los documentos actuales; se acepta para no partir la sección.
- Los fragmentos sin texto aparte de su título se descartan y se quitan las marcas `**`, salvo en los bloques de código, que se conservan literales.
- Patrones de IDs en `documents.yaml`: `REP-\d{2}`, `INV-LIM(?:-\d{2})?`, `INV-\d{2}`, `ENT-[A-Z]{3}-\d{2}`, `OC-[A-Z]{3}-\d{2}`, `CAM-\d{3}`. Con patrones por prefijo, `OC-T-001` no es un ID.
- *Descartada: fragmentos de tamaño fijo con solapamiento.* Partirían las afirmaciones citables y mezclarían IDs.

### D7c: embeddings con fastembed MiniLM detrás de `Embedder`
Interfaz `Embedder` con `model_name`, `fingerprint()` (SHA-256 del archivo del modelo, calculada una vez por instancia), `dimension`, `embed_documents()` y `embed_query()`. Implementaciones:
- `FastEmbedEmbedder`: localiza el archivo del modelo en `MODELS_CACHE_DIR` (estructura de caché de Hugging Face) y, si no está, lanza un error que cita `make models` y `MODELS_CACHE_DIR`. Carga `TextEmbedding(model_name, cache_dir=MODELS_CACHE_DIR, local_files_only=True)` de forma perezosa; nunca descarga en la ingesta ni en la consulta. Comprobado: no intenta conexiones de red.
- `FakeEmbedder` determinista (hash de palabras) con nombre, huella y dimensión configurables, y `FailingEmbedder`, que falla al cargar. Las pruebas usan un `documents.yaml` con los valores del falso.

La ingesta compara `model_name`, `fingerprint()` y `dimension` del embedder con `documents.yaml`; la consulta, con `doc_ingestion_runs`. La huella cubre `model_optimized.onnx`, que es lo que cambia los vectores; el tokenizador viene en la misma revisión de la caché.

El texto a embeber sale de `embedding_template` (`{title} — {section}: {text}`, y `{title}: {text}` sin sección): en la prueba, añadir título y sección mejoró el híbrido de MRR 0,75 a 0,90. `documents.yaml` guarda el nombre del modelo, el repositorio de origen (`model.source`: `Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q`), que permite localizar el archivo en la caché sin red, su archivo, su huella y la dimensión (384).

La ingesta va por etapas: lee todos los archivos (huellas), los convierte todos a Markdown, los fragmenta todos y solo entonces comprueba el modelo; así un archivo dañado se informa antes que un documento sin fragmentos, aunque vaya después en orden alfabético. `FastEmbedEmbedder` convierte cualquier fallo de inferencia de fastembed u onnxruntime en `EmbedderError`, y la búsqueda solo degrada a modo léxico ante `EmbedderError` u `OSError`: un error de programación no se disfraza de "búsqueda semántica no disponible".

`make models` (`python -m analyst_backend.documents.models_cli`): si el archivo ya está con la huella correcta, no hace nada; si está con otra huella, falla mostrando ambas sin descargar; si no está, descarga con `local_files_only=False` y comprueba la huella. Con `--check`, solo comprueba; lo usa `make test-embeddings` antes de ejecutar pytest.
- *Descartada: Ollama `nomic-embed-text`.* En la prueba no superó a MiniLM y obliga a tener un servidor en marcha para cargar documentos. La interfaz permite añadirlo después.
- *Descartada: descargar el modelo en la primera ingesta.* Rompería la ejecución sin red y haría la ingesta no reproducible.

### Almacenamiento
Base propia `data/processed/documents.duckdb` (`DOCUMENTS_DB_PATH`), publicada con `ingestion.storage.publish`. Tablas, todas con `COMMENT ON`:
- `documents`: `doc_id`, `source_type`, `title`, `file_name`, `sha256`, `chunk_count` y `markdown`.
- `doc_chunks`: los metadatos de la spec, `evidence_ids` como `VARCHAR[]` y `embedding` como `FLOAT[<dimensión>]`.
- `doc_ingestion_runs`: una fila con `ingestion_id`, modelo, huella del modelo, dimensión, fecha, total de fragmentos y una lista de archivos con nombre, SHA-256 y fragmentos. El `ingestion_id` es el SHA-256 de los nombres y contenidos de los archivos, de `documents.yaml` y de la huella del modelo.
- *Descartada: guardar los documentos en `analytics.duckdb`.* `make ingest` reconstruye esa base solo desde el CSV.
- *Descartada: un almacén vectorial.* Otra dependencia para 55 vectores.

### Recuperación
- **BM25:** `rank-bm25` sobre el `text` de cada fragmento (sin título ni sección: con ellos, `brio` coincidiría con todo el contexto de negocio), con tokens `\w+` en minúsculas y sin tildes (NFKD). `LuceneBM25` sustituye el IDF de Okapi, `log((N − n + 0,5)/(n + 0,5))`, que vale 0 cuando una palabra está en justo la mitad de los fragmentos filtrados (p. ej. `brio` en 2 de los 4 del contexto de negocio) y es negativo por encima, por el de Lucene, `log(1 + (N − n + 0,5)/(n + 0,5))`, siempre positivo. Los fragmentos con puntuación 0 (sin ninguna palabra de la consulta) no entran en su ranking.
  - *Descartada: Qdrant en modo local (evaluado tras la verificación).* Con estos 55 fragmentos da exactamente la misma calidad que `rank-bm25` con el IDF de Lucene (híbrido 10/10, MRR 0,95), añade 4 dependencias y, si guarda los datos en una carpeta, solo un proceso puede abrirla a la vez. Su BM25 (`Qdrant/bm25`) además necesita otro modelo y no trata `ñ`/`n` igual sin normalizar antes.
- **Similitud:** coseno con numpy sobre los embeddings guardados; ranking de todos los fragmentos filtrados.
- **Fusión:** RRF con `k = 60` (`rrf_k`). Empates por `chunk_id` en cada ranking y en la fusión.
- **Filtros:** `doc_ids` y `source_types`, aplicados antes de puntuar; si no queda ningún fragmento, resultado vacío con aviso `filters_empty`.
- **Modo híbrido:** solo si el embedder carga, embebe la consulta y su modelo, huella y dimensión coinciden con `doc_ingestion_runs`. Si BM25 no tiene ninguna coincidencia, se devuelven los resultados semánticos con el aviso `no_lexical_matches`, para que el agente sepa que pueden no ser pertinentes.
- **Modo léxico:** si no, con aviso `semantic_unavailable` o `model_mismatch`; solo puntuaciones BM25 > 0 y, sin resultados, aviso `no_matches`.
- **Avisos:** objetos `{code, message}`; las pruebas comparan el código.
- *Descartada: solo embeddings.* MiniLM solo se quedó en MRR 0,80 frente a 0,90 del híbrido en el prototipo (0,95 en la implementación final), y BM25 es el respaldo sin modelo.

### Herramienta y contrato
`buscar_documentos(DocumentQuery, DocumentsConfig, documents_db_path, embedder) -> DocumentResult`, con pydantic y el `QueryError` estructurado del change 3. `DocumentQuery.query` admite hasta `max_query_chars` (500). Como los límites salen de la configuración, `DocumentQuery` se valida con ella mediante el contexto de validación de pydantic (`model_validate(data, context={"config": ...})`); `buscar_documentos` recibe la consulta ya validada. La búsqueda y el `evidence_id` usan el mismo texto normalizado. Cada resultado lleva `content_kind = "evidencia_documental"` y el texto literal; ningún dato del texto altera la consulta. El `evidence_id` usa `analytics.evidence.evidence_id("buscar_documentos", consulta normalizada, ingestion_id, huella de documents.yaml)`; la consulta normalizada es el texto con los espacios colapsados (conserva mayúsculas y tildes, porque cambian el embedding), `top_k`, filtros ordenados y modo.

`analytics.database.open_readonly` pasa a recibir las columnas requeridas, el nombre de la base para los mensajes (`ventas` o `documentos`) y la pista de recarga (`make ingest` o `make ingest-docs`), con los valores actuales por defecto para ventas; las pruebas de `sales-metrics` siguen pasando sin cambios.

### Configuración y comandos
- **`backend/config/documents.yaml`:** `extensions`, `id_patterns`, `id_separators`, `pdf` (umbrales, patrones y tolerancias anteriores), `model` (nombre, archivo, huella, dimensión), `embedding_template`, `rrf_k`, `default_top_k`, `max_top_k` y `max_query_chars`.
- **Rutas:** `DOCUMENTS_DIR`, `DOCUMENTS_DB_PATH`, `DOCUMENTS_CONFIG_PATH` y `MODELS_CACHE_DIR`, leídas en `settings.py` y con valores por defecto en el `Makefile` y en `.env.example` (`MODELS_CACHE_DIR=.cache/models`, ignorado por git). Los embeddings ya no usan `OLLAMA_BASE_URL`; esa variable sigue siendo del LLM alternativo (change 5).
- **`make models`** descarga el modelo; **`make ingest-docs`** ejecuta la carga.

### Pruebas
- **Sin modelo real** (`make test`): `FakeEmbedder` (384) y `FailingEmbedder` para el modo léxico.
- **Con el modelo real:** nueva marca `@pytest.mark.embeddings`, excluida de `make test` y ejecutada por `make test-embeddings` tras `make models`. Sigue sin red; `conftest.py` conserva solo `MODELS_CACHE_DIR` en esas pruebas (delta de `project-layout`). Estas pruebas usan siempre `backend/config/documents.yaml`: `DOCUMENTS_CONFIG_PATH` solo cambia el modelo que comprueba `make test-embeddings` antes de ejecutarlas.
- **PDF sintéticos** (una página, línea repetida, sin texto) se generan en la prueba con PyMuPDF.

### Arquitectura
`docs/architecture.md` registra D7 (Markdown intermedio, fragmentador único y modelo fijado por huella) y cambia `tipo_fuente` por `source_type`. `docs/EXPLORACION_DATOS.md` documenta la estructura verificada de los documentos: IDs (incluidos `ENT-*`, `OC-EXT-06` e `INV-LIM` suelto), tamaños de letra, un título por página, tablas con rectángulos de fondo, `INSUMO DE NEGOCIO` antes del título del Word y la columna `ID / fecha`.

## Risks / Trade-offs

- [La conversión de PDF depende del formato de estos archivos (tamaños de letra, tablas con rectángulos de fondo)] → Umbrales en configuración; los tests de tablas y de los 55 fragmentos detectan cambios.
- [Una tabla de PDF sin rectángulos de fondo no se reconoce] → Su texto queda como párrafos de la sección y sigue siendo recuperable.
- [Una versión nueva del modelo cambia los vectores] → Huella verificada al descargar, al cargar y al consultar; si no coincide, la ingesta falla y la consulta pasa a modo léxico con aviso.
- [El modelo ocupa 0,22 GB y no está en la imagen] → `make models` explícito; en Docker, change 8.
- [Las consultas de los escenarios son las mismas que sirvieron para elegir el modelo] → Sirven para fijar el comportamiento, no para medir calidad; el change 9 evaluará con preguntas distintas.

## Migration Plan

Base nueva, sin migración. Requiere `make models` antes de `make ingest-docs`. Rollback: borrar `data/processed/documents.duckdb` y revertir el commit.
