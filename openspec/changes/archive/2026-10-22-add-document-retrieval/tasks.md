# Tasks

## 1. Dependencias, configuración y suite

- [x] 1.1 (~20 min) Añadir pymupdf==1.28.2, python-docx==1.2.0, rank-bm25==0.2.2, fastembed==0.9.0 y numpy==2.5.4 a `backend/pyproject.toml`; regenerar `uv.lock`; verificar con `uv sync --all-packages --locked` y `make test`
- [x] 1.2 (~45 min) Crear `backend/config/documents.yaml` (`extensions`, `id_patterns`, `id_separators`, `pdf` con umbrales, patrones y tolerancias, `model` con nombre, origen, archivo, huella y dimensión 384, `embedding_template`, `rrf_k`, `default_top_k`, `max_top_k`, `max_query_chars`) y `documents/config.py` (carga y validación con pydantic), con tests de configuración; verificar que pasan
- [x] 1.3 (~30 min) Añadir `load_documents_settings()` a `settings.py` (`DOCUMENTS_DIR`, `DOCUMENTS_DB_PATH`, `DOCUMENTS_CONFIG_PATH`, `MODELS_CACHE_DIR`), las variables a `.env.example` y al `Makefile`, y `.cache/` a `.gitignore`, con tests de settings; verificar que pasan
- [x] 1.4 (~45 min) Implementar el delta de `project-layout`: marca `embeddings` en `pyproject.toml`, filtro `not llm and not embeddings` en `make test`, objetivo `make test-embeddings` (comprueba el modelo con `models_cli --check` antes de pytest) y exención de `MODELS_CACHE_DIR` en `conftest.py` para las pruebas `embeddings`
- [x] 1.5 (~30 min) Tests de los requisitos modificados "Suite de pruebas sin servicios externos" (pruebas `embeddings` excluidas; actualizar `test_default_filter_excludes_llm_tests`) y "Aislamiento de la suite por defecto" (caché de modelos en pruebas `embeddings`) en `tests/`; verificar que pasan

## 2. Documentos a cargar

- [x] 2.1 (~30 min) Implementar en `documents/sources.py` la selección de archivos: primer nivel, extensión sin distinguir mayúsculas, sin ocultos ni `~$*`, orden alfabético, `doc_id` sin extensión, error por `doc_id` duplicado y por directorio sin documentos válidos
- [x] 2.2 (~30 min) Tests del requisito "Documentos a cargar" (directorio real; archivos que se ignoran; `doc_id` duplicado y sin documentos válidos → error) en `backend/tests/documents/test_sources.py`; la parte "no publica la base" y el escenario "Archivo dañado" se prueban en 6.3; verificar que pasan

## 3. Conversión a Markdown

- [x] 3.1 (~1 h 30 min) Implementar en `documents/markdown.py` `pdf_to_markdown`: líneas con tamaño de letra, título y secciones por umbral, cabeceras repetidas (solo con 2 o más páginas, una vez por página) y número de página eliminados, unión de párrafos, espacios colapsados y marcas de página
- [x] 3.2 (~1 h 30 min) Implementar en `documents/markdown.py` la reconstrucción de tablas de PDF a partir de los rectángulos de fondo (filas, columnas, celdas de varias líneas, tolerancias de configuración) y su salida como tabla GFM
- [x] 3.3 (~45 min) Implementar `docx_to_markdown` (cuerpo en orden, niveles de título, listas, tablas, celdas combinadas una sola vez, espacios colapsados) y el error con el nombre del archivo cuando PDF o Word no se pueden abrir
- [x] 3.4 (~45 min) Tests de los requisitos "Conversión a Markdown" (niveles de título en Word; celda combinada con un `.docx` sintético; espacios repetidos; "Markdown guardado" se prueba en 6.4), "Estructura de los PDF" (cabeceras y pies eliminados; PDF sintético de una página; línea repetida en una sola página) y "Tablas de PDF" (tabla sin bordes del reporte; celda de varias líneas) en `backend/tests/documents/test_markdown.py`; verificar que pasan

## 4. Fragmentación

- [x] 4.1 (~1 h 30 min) Implementar en `documents/chunking.py` el fragmentador de Markdown: título (o `doc_id`), títulos de página fuera del texto, secciones `##`/`###`, `####` y bloques de código como texto, preámbulo con `section` nula, IDs con separador en párrafos, listas y títulos, párrafos posteriores en el fragmento abierto, descarte de secciones vacías, error por documento sin fragmentos, marcas `**` eliminadas y metadatos (`chunk_id`, página, `evidence_ids` empezando por el principal)
- [x] 4.2 (~45 min) Implementar en `documents/chunking.py` las tablas: filas como `encabezado: valor | …` y división por filas con la comprobación de IDs ya principales en segunda pasada
- [x] 4.3 (~45 min) Tests de los requisitos "Fragmentos por sección" (55 fragmentos 4/18/21/12; preámbulo; sección vacía descartada; `.md` solo con títulos → error) y "Títulos en el Markdown" (títulos que no abren sección; título de página fuera del texto con `REP-04` en la página 2) en `backend/tests/documents/test_chunking.py`; verificar que pasan
- [x] 4.4 (~20 min) Tests del requisito "Fragmentos por ID de evidencia" (`REP-01` a `REP-06`; `OC-*` por título con sus viñetas; párrafo posterior sin ID en `OC-EXT-06`); verificar que pasan
- [x] 4.5 (~20 min) Tests del requisito "Tablas en los fragmentos" (10 `CAM-*` con `Región: Occidente` en `CAM-145`; índice de referencias como un fragmento; tabla regional del reporte); verificar que pasan
- [x] 4.6 (~20 min) Tests del requisito "Patrones de IDs en configuración" (`OC-T-001` no es ID; sin el patrón `CAM-*` la tabla queda en su sección); verificar que pasan
- [x] 4.7 (~20 min) Tests del requisito "Metadatos de cada fragmento" (fragmento de `REP-02`; ID principal solo en el título de `OC-SUR-01`; fragmentos de Markdown); verificar que pasan

## 5. Embeddings y modelo

- [x] 5.1 (~1 h) Implementar en `documents/embeddings.py` la interfaz `Embedder`, `FastEmbedEmbedder` (localización en la caché, `local_files_only`, carga perezosa, huella calculada una vez, error con `make models` y `MODELS_CACHE_DIR`), `FakeEmbedder` configurable, `FailingEmbedder`, la plantilla de texto y la comprobación de nombre, huella y dimensión frente a `documents.yaml`
- [x] 5.2 (~30 min) Tests del requisito "Embeddings de los fragmentos" (55 embeddings de 384 con `FakeEmbedder`; caché vacía → error con `make models` y `MODELS_CACHE_DIR`; huella distinta y dimensión distinta → error con ambos valores); la parte "no se crea la base" se prueba en 6.3; verificar que pasan
- [x] 5.3 (~45 min) Implementar `documents/models_cli.py` (descarga solo si falta, error sin descargar si la huella no coincide, modo `--check`) y el objetivo `make models`
- [x] 5.4 (~30 min) Tests de los requisitos "Descarga del modelo" (caché con otra huella → código distinto de 0 con ambas huellas) y "Pruebas con el modelo de embeddings separadas" (filtro de `make test-embeddings`; caché vacía → código distinto de 0 con `make models`); verificar que pasan

## 6. Base de documentos

- [x] 6.1 (~1 h) Implementar en `documents/storage.py` el DDL de `documents` (con `markdown`), `doc_chunks` y `doc_ingestion_runs` con `COMMENT ON`, y en `documents/ingest.py` la carga en el orden de la spec: archivos → Markdown → fragmentos → comprobación del modelo → embeddings → `ingestion_id` (nombres, contenidos, configuración y huella) → publicación atómica con `ingestion.storage.publish`
- [x] 6.2 (~30 min) Tests del requisito "Publicación atómica e idempotente" (doble carga idéntica; fallo forzado con base previa intacta y sin temporales); verificar que pasan
- [x] 6.3 (~45 min) Tests de que ningún error de ingesta publica la base: `doc_id` duplicado, sin documentos válidos, archivo dañado (`.pdf` y `.docx` con texto plano), documento sin fragmentos (`.md` solo con títulos y PDF sintético sin texto) y modelo no descargado; verificar que pasan
- [x] 6.4 (~30 min) Tests del requisito "Trazabilidad de la carga de documentos" (una fila con 4 archivos, huellas, modelo y 55 fragmentos; archivo renombrado → `ingestion_id` distinto) y del escenario "Markdown guardado"; verificar que pasan
- [x] 6.5 (~30 min) Implementar `documents/__main__.py` y `make ingest-docs` (resumen de la carga; código 1 con mensaje claro ante errores)
- [x] 6.6 (~20 min) Tests del requisito "Comando de ingesta de documentos" (`DOCUMENTS_DIR` inexistente con caché de modelos vacía → código distinto de 0 con la ruta); verificar que pasan

## 7. buscar_documentos

- [x] 7.1 (~45 min) Implementar `documents/models.py` (`DocumentQuery` con `query` normalizada en espacios y límites `max_query_chars` y `max_top_k` validados con la configuración en el contexto de pydantic, `top_k`, `doc_ids`, `source_types`; `DocumentHit`; `Warning` con `code` y `message`; `DocumentResult`)
- [x] 7.2 (~20 min) Tests del requisito "Validación de la consulta de documentos" (vacía, 501 caracteres, `top_k` 0 y mayor que el máximo) en `backend/tests/documents/test_retrieval.py`; verificar que pasan
- [x] 7.3 (~45 min) Parametrizar `analytics.database.open_readonly` (columnas requeridas, nombre de la base y pista de recarga, con los valores de ventas por defecto) y abrir con ella la base de documentos con su esquema y la pista `make ingest-docs`; verificar que las pruebas de `sales-metrics` siguen pasando
- [x] 7.4 (~20 min) Tests del requisito "Acceso de solo lectura a la base de documentos" (base inexistente; sin `doc_chunks`; intento de escritura; acceso externo y configuración); verificar que pasan
- [x] 7.5 (~1 h 30 min) Implementar en `documents/retrieval.py` la tokenización normalizada, BM25 sobre `text` sin puntuaciones 0, coseno, RRF, empates por `chunk_id` en cada ranking, filtros, modo léxico (embedder que falla; modelo, huella o dimensión distintos) y los avisos `semantic_unavailable`, `model_mismatch`, `no_matches`, `no_lexical_matches` y `filters_empty`, con `content_kind = "evidencia_documental"`
- [x] 7.6 (~30 min) Tests del requisito "Búsqueda híbrida" (RRF 1/61 + 1/63; BM25 0 → 1/61; empate en BM25; `zzzz` en modo híbrido con `FakeEmbedder` → `no_lexical_matches`) y prueba `@pytest.mark.embeddings` con el modelo real (`limitaciones de la muestra del estudio` → `INV-LIM-*` primero, modo `hibrido`); verificar que pasan
- [x] 7.7 (~15 min) Tests del requisito "Normalización del texto para BM25" (`FORMATOS PEQUENOS en norte`; `brio` frente a `BRÍO`); verificar que pasan
- [x] 7.8 (~30 min) Tests del requisito "Degradación a BM25" (con `FailingEmbedder`: `REP-02`, `OC-CEN-02` e `INV-04` en ese orden y `semantic_unavailable` — orden sustituido por la tarea 10.1: `INV-04`, `REP-02`, `OC-CEN-02`; huella distinta → `model_mismatch` con ambas huellas; `zzzz` → vacío con `no_matches`); verificar que pasan
- [x] 7.9 (~20 min) Tests del requisito "Resultados citables" (`REP-01` primero en modo léxico, página 1, texto completo, posición en similitud nula); verificar que pasan
- [x] 7.10 (~20 min) Tests del requisito "Filtros" (solo `05_Reporte_Comercial`; `doc_id` y `source_type` desconocidos con sus opciones; filtros sin fragmentos → `filters_empty`); verificar que pasan
- [x] 7.11 (~20 min) Tests del requisito "Contenido documental como evidencia" (`OC-EXT-06` primero, literal y marcado, con 3 resultados y filtros intactos); verificar que pasan
- [x] 7.12 (~30 min) Añadir al resultado el `evidence_id` (texto con espacios colapsados, `top_k`, filtros ordenados y modo), el `ingestion_id`, el modo y el modelo
- [x] 7.13 (~20 min) Tests del requisito "Trazabilidad de la búsqueda" (misma búsqueda; cambio de modo; espacios frente a tildes); verificar que pasan

## 8. Documentación

- [x] 8.1 (~45 min) Registrar D7 en `docs/architecture.md` (y `tipo_fuente` → `source_type`); documentar en `docs/EXPLORACION_DATOS.md` la estructura verificada de los documentos; documentar en `README.md` `make models`, `make ingest-docs`, `make test-embeddings` y un ejemplo de `buscar_documentos`; verificar que el ejemplo se ejecuta

## 9. Cierre

- [x] 9.1 (~15 min) Ejecutar `make models`, `make ingest-docs`, `make test` y `make test-embeddings`; verificar que todo pasa
- [x] 9.2 (~10 min) Actualizar `openspec/ROADMAP.md` (change 4 implementado; nota para el change 9: evaluar con preguntas distintas de las usadas para elegir el modelo)
- [x] 9.3 (~10 min) Ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores

## 10. Correcciones de la verificación

- [x] 10.1 (~30 min) BM25 con el IDF de Lucene (`LuceneBM25`) y test "Palabra en la mitad de los fragmentos"; actualizar el orden de "Modelo no disponible" (`INV-04`, `REP-02`, `OC-CEN-02`); verificar que pasan
- [x] 10.2 (~30 min) Tablas: no dividir si un ID se repite en la tabla o ya es principal (incluidas tablas anteriores); tests "Tabla con IDs ya divididos" e "ID repetido en una tabla"; verificar que pasan
- [x] 10.3 (~15 min) Test "Filtros antes de puntuar"; verificar que pasa
- [x] 10.4 (~45 min) Ingesta por etapas (archivos → Markdown → fragmentos) con test de orden; base anterior intacta sin modelo; extensiones sin conversor rechazadas en `documents.yaml`; tabla de cargas vacía → `DatabaseError` con test; errores de inferencia como `EmbedderError` y degradación solo ante `EmbedderError`/`OSError`, con tests de fallo al embeber la consulta y de otro nombre de modelo; aserciones literales en lugar de recalculadas; verificar que pasan
- [x] 10.5 (~15 min) Actualizar specs, design y proposal; ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores
