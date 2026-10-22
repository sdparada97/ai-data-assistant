# Graph Report - ai-data-assistant  (2026-10-22)

## Corpus Check
- 123 files · ~102,789 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 1969 nodes · 4134 edges · 128 communities (106 shown, 22 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 574 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f0b28e64`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- Arquitectura de Brío Analyst
- ADDED Requirements
- markdown.py
- explore_data.py
- explore.md
- test_models_cli.py
- conftest.py
- Requirements
- Exploración de datos
- load_documents_config
- test_health.py
- test_app.py
- Requirements
- Decisions
- Proposal
- analyst-backend
- analyst-frontend
- Tasks
- Almena Foods | Contexto de negocio
- rules.py
- ADDED Requirements
- test_rules.py
- ingest
- test_pipeline.py
- Requirements
- test_metrics.py
- Decisions
- .action
- ADDED Requirements
- Proposal
- catalog.py
- semantic.py
- ADDED Requirements
- Requirements
- ADDED Requirements
- Requirements
- evidence_id
- ADDED Requirements
- Requirements
- ingest_documents
- Requirement: Estructura de las incidencias
- open_readonly
- settings.py
- publish
- documents/errors.py
- Requirement: Aislamiento de la suite por defecto
- metrics.py
- pathlib
- test_settings.py
- retrieval.py
- test_chunking.py
- Decisions
- test_quality.py
- DocumentsConfig
- pipeline.py
- Tasks
- ingest.py
- Requirement: DQ04 catálogo de valores válidos
- pipeline.py
- Proposal
- documents/config.py
- chunking.py
- pdf_to_markdown
- Requirement: DQ08 valores negativos
- EmbedderError
- apply_rules
- QueryError
- re
- resolve_period
- _query
- Embedder
- pytest
- ADDED Requirements
- Requirements
- Requirement: DQ01 registro_id único
- DocumentsError
- documents/config.py
- Proposal
- Tasks
- analytics/conftest.py
- Requirement: Documentos a cargar
- Requirement: Tablas en los fragmentos
- Design
- Requirement: Documentos a cargar
- Requirement: Tablas en los fragmentos
- Requirement: Conversión a Markdown
- Requirement: Embeddings de los fragmentos
- Requirement: Fragmentos por sección
- Requirement: Conversión a Markdown
- Requirement: Embeddings de los fragmentos
- Requirement: Fragmentos por sección
- Requirement: Estructura de los PDF
- Requirement: Fragmentos por ID de evidencia
- Requirement: Metadatos de cada fragmento
- Requirement: DQ01 registro_id único
- Requirement: Estructura de las incidencias
- Requirement: DQ03 recorte de espacios
- Spec Delta
- Requirement: DQ13 venta sin unidades
- Requirement: Estructura de los PDF
- Requirement: Fragmentos por ID de evidencia
- Requirement: Metadatos de cada fragmento
- Requirement: Filas en revisión
- Spec Delta
- Requirement: Publicación atómica e idempotente
- Requirement: Trazabilidad de la carga de documentos
- Requirement: Títulos en el Markdown
- Requirement: DQ05 mes inválido
- document-ingestion Specification
- Requirement: Tablas de PDF
- Requirement: Trazabilidad de la carga de documentos
- Requirement: Títulos en el Markdown

## God Nodes (most connected - your core abstractions)
1. `DocumentsConfig` - 87 edges
2. `evidence_id()` - 48 edges
3. `consultar_metrica()` - 44 edges
4. `calidad_datos()` - 43 edges
5. `buscar_documentos()` - 41 edges
6. `QueryError` - 38 edges
7. `RulesOutcome` - 38 edges
8. `ingest()` - 38 edges
9. `DocumentsSummary` - 36 edges
10. `MetricResult` - 33 edges

## Surprising Connections (you probably didn't know these)
- `Impact` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-document-retrieval/proposal.md → backend/src/analyst_backend/analytics/evidence.py
- `Goals / Non-Goals` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Alias en el filtro` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/specs/sales-metrics/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `7. Documentación` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/tasks.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Alias en el filtro` --references--> `evidence_id()`  [INFERRED]
  openspec/specs/sales-metrics/spec.md → backend/src/analyst_backend/analytics/evidence.py

## Import Cycles
- None detected.

## Communities (128 total, 22 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "Arquitectura de Brío Analyst"
Cohesion: 0.07
Nodes (24): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas (+16 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "markdown.py"
Cohesion: 0.10
Nodes (11): ConversionError, collapse_spaces(), _docx_table_rows(), docx_to_markdown(), _Line, markdown_table(), _page_lines(), pdf_to_markdown() (+3 more)

### Community 4 - "explore_data.py"
Cohesion: 0.16
Nodes (18): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), extract_documents(), _fmt(), load_raw() (+10 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "test_models_cli.py"
Cohesion: 0.46
Nodes (4): _fake_cached_model(), _make(), test_cache_with_other_fingerprint_fails_without_downloading(), test_check_without_model_points_to_make_models()

### Community 17 - "conftest.py"
Cohesion: 0.21
Nodes (9): _blocked_connect(), _blocked_connect_ex(), _blocked_resolution(), _blocked_sendmsg(), _blocked_sendto(), env_example_variables(), _guard(), _isolate_default_suite() (+1 more)

### Community 18 - "Requirements"
Cohesion: 0.05
Nodes (37): project-layout Specification, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Pruebas con LLM separadas (+29 more)

### Community 19 - "Exploración de datos"
Cohesion: 0.12
Nodes (16): 01 Contexto de negocio, 03 Investigación de consumidor, 04 Observaciones de canales, 05 Reporte comercial, Aprobación de reglas, Contradicciones entre fuentes, Cómo reproducir, Documentos y afirmaciones verificables (+8 more)

### Community 20 - "load_documents_config"
Cohesion: 0.24
Nodes (10): load_documents_config(), DocumentsConfigError, test_embedding_template_renders_with_and_without_section(), test_extensions_are_lowercased(), test_id_regexes_follow_configured_patterns(), test_invalid_config_is_rejected(), test_invalid_yaml_is_reported(), test_missing_file_is_reported() (+2 more)

### Community 22 - "test_app.py"
Cohesion: 0.06
Nodes (14): _coerce(), main(), parse_config(), load_settings(), Settings, _FakeApp, _render(), test_cli_launches_page_with_server_options() (+6 more)

### Community 23 - "Requirements"
Cohesion: 0.07
Nodes (28): data-quality Specification, Purpose, Requirement: Destino único por fila, Requirement: DQ04 catálogo de valores válidos, Requirement: DQ06 unidades faltantes, Requirement: DQ07 venta neta faltante, Requirement: DQ08 valores negativos, Requirement: DQ11 aviso de punto de venta único (+20 more)

### Community 24 - "Decisions"
Cohesion: 0.11
Nodes (17): config(), Alcance del bloqueo de red, Contenedores, Context, D2' Código fuente en `backend/src/` y `frontend/src/` (reemplaza D2), D4 Workspace de uv con un único `uv.lock`, Decisions, Design (+9 more)

### Community 25 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 31 - "Tasks"
Cohesion: 0.22
Nodes (8): 1. Decisiones D2' y D4 en la documentación, 2. Entorno Python (requisitos "Ubicación del código fuente", "Entorno Python reproducible" y "Aislamiento de la suite por defecto"), 3. Backend (requisito "Salud del backend"), 4. Frontend (requisito "Página mínima del frontend"), 5. Comandos comunes (requisitos "Suite de pruebas sin servicios externos", "Pruebas con LLM separadas" y "Evaluación reservada"), 6. Contenedores (requisito "Orquestación con contenedores"), 7. Cierre, Tasks

### Community 32 - "Almena Foods | Contexto de negocio"
Cohesion: 0.33
Nodes (5): Almena Foods | Contexto de negocio, Convenciones de análisis, Diccionario de la base de ventas, Información disponible, Situación

### Community 33 - "rules.py"
Cohesion: 0.14
Nodes (16): apply_catalog(), _as_number(), _check_integer(), check_month(), check_negative(), check_sales(), check_sales_without_units(), check_units() (+8 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.08
Nodes (25): paths(), Paths, valid_row(), write_csv(), frame_of(), _frame(), real_frame(), test_dq01_compares_after_trimming() (+17 more)

### Community 36 - "ingest"
Cohesion: 0.08
Nodes (38): ValidationFailedError, ingest(), IngestionSummary, _non_empty_text(), sales_schema(), validate_sales(), _make_ingest(), _rows() (+30 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.05
Nodes (54): RulesOutcome, test_missing_directory_fails_with_its_path_even_without_model(), _issue(), _issues(), real(), run(), test_actions_by_severity_in_real_file(), test_dq01_duplicate_with_differences_keeps_line_2_in_sales() (+46 more)

### Community 38 - "Requirements"
Cohesion: 0.06
Nodes (35): Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas, Requirement: Idempotencia (+27 more)

### Community 39 - "test_metrics.py"
Cohesion: 0.18
Nodes (30): MetricResult, _by_group(), _comparison(), run(), _single(), test_alias_gives_same_rows_and_evidence(), test_brand_by_region_in_t1(), test_comparison_against_period_without_data() (+22 more)

### Community 40 - "Decisions"
Cohesion: 0.12
Nodes (16): Almacenamiento y atomicidad, Arquitectura, Configuración fuera del código, Context, Decisions, Design, DQ12: fórmula y población, El catálogo vive ya en `semantic_layer.yaml` (+8 more)

### Community 41 - ".action"
Cohesion: 0.10
Nodes (18): Contrato de `dq_issues` y `sales_review`, Requirement: Acción e impacto de cada incidencia, Requirement: Estructura de las incidencias, Scenario: Acción según el destino final, Scenario: Columnas de dq_issues, Scenario: Impacto de un valor negativo, 1. Dependencias y configuración, 2. Lectura y validación de la entrada (requisito "Validación de la entrada") (+10 more)

### Community 42 - "ADDED Requirements"
Cohesion: 0.07
Nodes (27): ADDED Requirements, Requirement: Destino único por fila, Requirement: DQ03 recorte de espacios, Requirement: DQ05 mes inválido, Requirement: DQ06 unidades faltantes, Requirement: DQ07 venta neta faltante, Requirement: DQ11 aviso de punto de venta único, Requirement: DQ12 aviso de precio atípico (+19 more)

### Community 43 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 44 - "catalog.py"
Cohesion: 0.17
Nodes (17): Catalog, load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes() (+9 more)

### Community 45 - "semantic.py"
Cohesion: 0.15
Nodes (23): AggregateMetric, Dimension, _load_dimension(), _load_metric(), load_semantic_layer(), RatioMetric, SemanticLayerError, _text() (+15 more)

### Community 46 - "ADDED Requirements"
Cohesion: 0.05
Nodes (37): ADDED Requirements, Purpose, Requirement: Acceso de solo lectura, Requirement: Avisos de calidad en el resultado, Requirement: Comparación entre dos períodos, Requirement: Consulta de métricas en un período, Requirement: Datos faltantes, Requirement: Orden y ranking (+29 more)

### Community 47 - "Requirements"
Cohesion: 0.05
Nodes (37): Purpose, Requirement: Acceso de solo lectura, Requirement: Avisos de calidad en el resultado, Requirement: Comparación entre dos períodos, Requirement: Consulta de métricas en un período, Requirement: Datos faltantes, Requirement: Orden y ranking, Requirement: Validación de la consulta (+29 more)

### Community 48 - "ADDED Requirements"
Cohesion: 0.08
Nodes (24): ADDED Requirements, Purpose, Requirement: Alias y escritura de los valores, Requirement: Dimensiones consultables, Requirement: Expresiones de métricas seguras, Requirement: Expresiones de período, Requirement: Métricas definidas en configuración, Scenario: Alias de la marca (+16 more)

### Community 49 - "Requirements"
Cohesion: 0.08
Nodes (24): Purpose, Requirement: Alias y escritura de los valores, Requirement: Dimensiones consultables, Requirement: Expresiones de métricas seguras, Requirement: Expresiones de período, Requirement: Métricas definidas en configuración, Requirements, Scenario: Alias de la marca (+16 more)

### Community 50 - "evidence_id"
Cohesion: 0.06
Nodes (55): canonical_json(), evidence_id(), consultar_metrica(), calidad_datos(), Componentes, Decisiones, Fuera de alcance, Requirement: Trazabilidad de la búsqueda (+47 more)

### Community 51 - "ADDED Requirements"
Cohesion: 0.05
Nodes (37): ADDED Requirements, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 52 - "Requirements"
Cohesion: 0.05
Nodes (37): document-retrieval Specification, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 53 - "ingest_documents"
Cohesion: 0.19
Nodes (17): ingest_documents(), documents_settings(), _copy_raw(), _empty_pdf(), _rows(), test_double_load_is_identical(), test_errors_keep_an_existing_database(), test_every_chunk_has_a_384_value_embedding() (+9 more)

### Community 54 - "Requirement: Estructura de las incidencias"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada, Spec Delta

### Community 55 - "open_readonly"
Cohesion: 0.16
Nodes (12): _check_schema(), DatabaseError, open_readonly(), published_ingestion_id(), _sha(), test_external_access_and_configuration_are_rejected(), test_missing_database_asks_for_ingest(), test_old_database_without_issue_dimensions_asks_for_ingest() (+4 more)

### Community 56 - "settings.py"
Cohesion: 0.17
Nodes (11): main(), AnalyticsSettings, IngestionSettings, load_analytics_settings(), load_ingestion_settings(), load_models_settings(), ModelsSettings, _read_paths() (+3 more)

### Community 57 - "publish"
Cohesion: 0.20
Nodes (5): publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files(), write_tables()

### Community 58 - "documents/errors.py"
Cohesion: 0.22
Nodes (7): SourceError, list_documents(), test_directory_without_documents(), test_duplicated_doc_id_is_rejected(), test_ignored_files(), test_missing_directory_names_the_path(), test_real_directory_loads_the_four_documents()

### Community 59 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.12
Nodes (16): ADDED Requirements, MODIFIED Requirements, Requirement: Aislamiento de la suite por defecto, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Suite de pruebas sin servicios externos, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados (+8 more)

### Community 60 - "metrics.py"
Cohesion: 0.15
Nodes (20): _comparison_cell(), make_row(), _describe(), _issue_filter(), _metric_values(), Plan, _quality_notes(), _round() (+12 more)

### Community 61 - "pathlib"
Cohesion: 0.23
Nodes (5): config_path_real(), fake_config(), fake_config_path(), fake_db(), write_config()

### Community 62 - "test_settings.py"
Cohesion: 0.19
Nodes (9): test_absolute_paths_are_kept(), test_analytics_missing_variable_is_named(), test_analytics_settings_read_two_paths(), test_blank_variable_counts_as_missing(), test_documents_missing_variable_is_named(), test_documents_settings_read_four_paths(), test_missing_variable_is_named(), test_reads_process_environment_by_default() (+1 more)

### Community 63 - "retrieval.py"
Cohesion: 0.10
Nodes (19): _config(), DocumentHit, DocumentQuery, DocumentResult, SearchWarning, _Strict, buscar_documentos(), _check_filters() (+11 more)

### Community 64 - "test_chunking.py"
Cohesion: 0.14
Nodes (26): Chunk, _by_primary(), _chunk_all(), chunks(), _md(), test_configurable_patterns(), test_empty_section_is_discarded(), test_field_records_are_one_chunk_per_row() (+18 more)

### Community 65 - "Decisions"
Cohesion: 0.14
Nodes (12): Almacenamiento, Arquitectura, Configuración y comandos, Context, D7a: convertir PDF y Word a Markdown con código propio, y fragmentar solo Markdown, D7b: fragmentador de Markdown, Decisions, Design (+4 more)

### Community 66 - "test_quality.py"
Cohesion: 0.17
Nodes (17): QualityQuery, QualityResult, layer(), _run(), _ids(), run(), _run(), test_brand_in_south() (+9 more)

### Community 67 - "DocumentsConfig"
Cohesion: 0.19
Nodes (32): DocumentsConfig, DocumentsSummary, fake_embedder(), _codes(), _ids_and_scores(), _lexical(), _primaries(), _QueryFailingEmbedder (+24 more)

### Community 68 - "pipeline.py"
Cohesion: 0.30
Nodes (9): read_sales_csv(), test_columns_in_another_order_are_accepted(), test_extra_column_is_named(), test_header_only_is_rejected(), test_latin1_file_is_rejected(), test_missing_column_is_named(), test_missing_file_names_the_path(), test_real_file_reads_all_rows_with_physical_lines() (+1 more)

### Community 69 - "Tasks"
Cohesion: 0.15
Nodes (9): LuceneBM25, Recuperación, 10. Correcciones de la verificación, 2. Documentos a cargar, 4. Fragmentación, 6. Base de documentos, 8. Documentación, 9. Cierre (+1 more)

### Community 70 - "ingest.py"
Cohesion: 0.18
Nodes (7): documents_ingestion_id(), _file_sha256(), _ddl(), LoadedDocument, _quote(), RunRecord, write_tables()

### Community 71 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 72 - "pipeline.py"
Cohesion: 0.16
Nodes (8): IngestionError, InputError, ReconciliationError, _check_header(), check_reconciliation(), compute_ingestion_id(), parse_sales_csv(), read_csv_bytes()

### Community 73 - "Proposal"
Cohesion: 0.29
Nodes (6): Capabilities, Fuera de alcance, Impact, Modified Capabilities, Proposal, Why

### Community 74 - "documents/config.py"
Cohesion: 0.25
Nodes (6): ModelConfig, cached_model_file(), file_sha256(), _download(), main(), _verify()

### Community 75 - "chunking.py"
Cohesion: 0.16
Nodes (13): _blocks(), _cells(), chunk_markdown(), open_draft(), starting_id(), _Draft, _is_code(), _is_table() (+5 more)

### Community 76 - "pdf_to_markdown"
Cohesion: 0.17
Nodes (16): to_markdown(), SourceFile, _pdf(), test_damaged_file_names_the_file(), test_every_supported_extension_has_a_converter(), test_line_repeated_on_a_single_page_is_kept(), test_markdown_file_is_returned_as_is(), test_pdf_cell_with_several_lines() (+8 more)

### Community 77 - "Requirement: DQ08 valores negativos"
Cohesion: 0.67
Nodes (3): Requirement: DQ08 valores negativos, Scenario: Cero no es negativo, Scenario: Negativos del archivo real

### Community 78 - "EmbedderError"
Cohesion: 0.16
Nodes (4): FailingEmbedder, FastEmbedEmbedder, EmbedderError, D7c: embeddings con fastembed MiniLM detrás de `Embedder`

### Community 79 - "apply_rules"
Cohesion: 0.23
Nodes (9): apply_rules(), _corrected_frame(), _issues_frame(), _reason(), _review_frame(), _sales_frame(), Issue, _run() (+1 more)

### Community 80 - "QueryError"
Cohesion: 0.17
Nodes (7): build_plan(), build_sql(), resolve_filters(), QueryError, _normalize(), SemanticLayer, test_query_error_is_structured()

### Community 81 - "re"
Cohesion: 0.15
Nodes (11): MetricQuery, test_semantic_layer_change_changes_evidence(), test_ties_share_rank(), test_evidence_id_changes_with_each_input(), test_evidence_id_format_and_determinism(), test_limit_must_be_positive(), test_metrics_cannot_be_empty(), test_one_of_period_or_compare_is_required() (+3 more)

### Community 82 - "resolve_period"
Cohesion: 0.13
Nodes (12): quote_identifier(), is_valid_month(), _months(), normalize_period(), resolve_period(), _condition(), test_invalid_forms_list_valid_forms(), test_is_valid_month() (+4 more)

### Community 83 - "_query"
Cohesion: 0.21
Nodes (8): open_documents_db(), _error_fields(), _query(), test_empty_query_is_rejected(), test_external_access_and_configuration_are_rejected(), test_too_long_query_is_rejected(), test_top_k_out_of_range(), test_write_attempt_is_rejected()

### Community 84 - "Embedder"
Cohesion: 0.20
Nodes (4): Embedder, FakeEmbedder, real_model_db(), 5. Embeddings y modelo

### Community 85 - "pytest"
Cohesion: 0.09
Nodes (20): check_embedder(), rrf_fuse(), test_document_with_only_headings_fails(), test_different_dimension_shows_both(), test_different_fingerprint_shows_both(), test_different_model_name(), test_embedding_text_uses_title_and_section(), test_fake_embedder_matches_its_config() (+12 more)

### Community 86 - "ADDED Requirements"
Cohesion: 0.18
Nodes (11): ADDED Requirements, Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirement: Tablas de PDF, Scenario: Caché con otra huella, Scenario: Celda de varias líneas, Scenario: Código de punto de venta (+3 more)

### Community 87 - "Requirements"
Cohesion: 0.18
Nodes (11): Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirement: Publicación atómica e idempotente, Requirements, Scenario: Caché con otra huella, Scenario: Código de punto de venta, Scenario: Doble carga (+3 more)

### Community 88 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 89 - "DocumentsError"
Cohesion: 0.24
Nodes (5): DocumentsError, main(), DocumentsSettings, load_documents_settings(), 1. Dependencias, configuración y suite

### Community 90 - "documents/config.py"
Cohesion: 0.16
Nodes (5): _check_regex(), EmbeddingTemplate, PdfConfig, _Strict, embedding_text()

### Community 91 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 92 - "Tasks"
Cohesion: 0.29
Nodes (6): 2. Dimensiones en dq_issues (requisito MODIFIED "Estructura de las incidencias"), 3. Capa semántica, 6. calidad_datos, 7. Documentación, 8. Cierre, Tasks

### Community 94 - "Requirement: Documentos a cargar"
Cohesion: 0.33
Nodes (6): Requirement: Documentos a cargar, Scenario: Archivo dañado, Scenario: Archivos que se ignoran, Scenario: Directorio real, Scenario: doc_id duplicado, Scenario: Sin documentos válidos

### Community 95 - "Requirement: Tablas en los fragmentos"
Cohesion: 0.33
Nodes (6): Requirement: Tablas en los fragmentos, Scenario: ID repetido en una tabla, Scenario: Registros de campo, Scenario: Tabla con IDs ya divididos, Scenario: Tabla sin IDs, Scenario: Índice de referencias

### Community 96 - "Design"
Cohesion: 0.33
Nodes (5): Context, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 97 - "Requirement: Documentos a cargar"
Cohesion: 0.33
Nodes (6): Requirement: Documentos a cargar, Scenario: Archivo dañado, Scenario: Archivos que se ignoran, Scenario: Directorio real, Scenario: doc_id duplicado, Scenario: Sin documentos válidos

### Community 98 - "Requirement: Tablas en los fragmentos"
Cohesion: 0.33
Nodes (6): Requirement: Tablas en los fragmentos, Scenario: ID repetido en una tabla, Scenario: Registros de campo, Scenario: Tabla con IDs ya divididos, Scenario: Tabla sin IDs, Scenario: Índice de referencias

### Community 99 - "Requirement: Conversión a Markdown"
Cohesion: 0.40
Nodes (5): Requirement: Conversión a Markdown, Scenario: Celda combinada, Scenario: Espacios repetidos, Scenario: Markdown guardado, Scenario: Niveles de título en Word

### Community 100 - "Requirement: Embeddings de los fragmentos"
Cohesion: 0.40
Nodes (5): Requirement: Embeddings de los fragmentos, Scenario: Dimensión distinta, Scenario: Embeddings guardados, Scenario: Huella distinta, Scenario: Modelo no descargado

### Community 101 - "Requirement: Fragmentos por sección"
Cohesion: 0.40
Nodes (5): Requirement: Fragmentos por sección, Scenario: Documento sin fragmentos, Scenario: Fragmentos de los documentos reales, Scenario: Preámbulo sin sección, Scenario: Sección vacía descartada

### Community 102 - "Requirement: Conversión a Markdown"
Cohesion: 0.40
Nodes (5): Requirement: Conversión a Markdown, Scenario: Celda combinada, Scenario: Espacios repetidos, Scenario: Markdown guardado, Scenario: Niveles de título en Word

### Community 103 - "Requirement: Embeddings de los fragmentos"
Cohesion: 0.40
Nodes (5): Requirement: Embeddings de los fragmentos, Scenario: Dimensión distinta, Scenario: Embeddings guardados, Scenario: Huella distinta, Scenario: Modelo no descargado

### Community 104 - "Requirement: Fragmentos por sección"
Cohesion: 0.40
Nodes (5): Requirement: Fragmentos por sección, Scenario: Documento sin fragmentos, Scenario: Fragmentos de los documentos reales, Scenario: Preámbulo sin sección, Scenario: Sección vacía descartada

### Community 105 - "Requirement: Estructura de los PDF"
Cohesion: 0.50
Nodes (4): Requirement: Estructura de los PDF, Scenario: Cabeceras y pies eliminados, Scenario: Línea repetida en una sola página, Scenario: PDF de una página

### Community 106 - "Requirement: Fragmentos por ID de evidencia"
Cohesion: 0.50
Nodes (4): Requirement: Fragmentos por ID de evidencia, Scenario: Afirmaciones del reporte comercial, Scenario: Párrafo posterior sin ID, Scenario: Registros por título

### Community 107 - "Requirement: Metadatos de cada fragmento"
Cohesion: 0.50
Nodes (4): Requirement: Metadatos de cada fragmento, Scenario: Fragmento de Markdown, Scenario: Fragmento de una afirmación del reporte, Scenario: ID principal solo en el título

### Community 108 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 109 - "Requirement: Estructura de las incidencias"
Cohesion: 0.50
Nodes (4): Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada

### Community 110 - "Requirement: DQ03 recorte de espacios"
Cohesion: 0.50
Nodes (4): Requirement: DQ03 recorte de espacios, Scenario: Canal con espacio del archivo real, Scenario: Espacios intermedios intactos, Scenario: Región con espacio del archivo real

### Community 112 - "Requirement: DQ13 venta sin unidades"
Cohesion: 0.50
Nodes (4): Requirement: DQ13 venta sin unidades, Scenario: Sin casos en el archivo real, Scenario: Venta cero con unidades, Scenario: Venta positiva con cero unidades

### Community 113 - "Requirement: Estructura de los PDF"
Cohesion: 0.50
Nodes (4): Requirement: Estructura de los PDF, Scenario: Cabeceras y pies eliminados, Scenario: Línea repetida en una sola página, Scenario: PDF de una página

### Community 114 - "Requirement: Fragmentos por ID de evidencia"
Cohesion: 0.50
Nodes (4): Requirement: Fragmentos por ID de evidencia, Scenario: Afirmaciones del reporte comercial, Scenario: Párrafo posterior sin ID, Scenario: Registros por título

### Community 115 - "Requirement: Metadatos de cada fragmento"
Cohesion: 0.50
Nodes (4): Requirement: Metadatos de cada fragmento, Scenario: Fragmento de Markdown, Scenario: Fragmento de una afirmación del reporte, Scenario: ID principal solo en el título

### Community 116 - "Requirement: Filas en revisión"
Cohesion: 0.67
Nodes (3): Requirement: Filas en revisión, Scenario: Filas retenidas del archivo real, Scenario: Varias reglas de revisión

### Community 118 - "Requirement: Publicación atómica e idempotente"
Cohesion: 0.67
Nodes (3): Requirement: Publicación atómica e idempotente, Scenario: Doble carga, Scenario: Fallo a mitad de la carga

### Community 119 - "Requirement: Trazabilidad de la carga de documentos"
Cohesion: 0.67
Nodes (3): Requirement: Trazabilidad de la carga de documentos, Scenario: Archivo renombrado, Scenario: Carga registrada

### Community 120 - "Requirement: Títulos en el Markdown"
Cohesion: 0.67
Nodes (3): Requirement: Títulos en el Markdown, Scenario: Título de página fuera del texto, Scenario: Títulos que no abren sección

### Community 121 - "Requirement: DQ05 mes inválido"
Cohesion: 0.67
Nodes (3): Requirement: DQ05 mes inválido, Scenario: Mes 13 del archivo real, Scenario: Mes válido fuera del semestre

### Community 123 - "Requirement: Tablas de PDF"
Cohesion: 0.67
Nodes (3): Requirement: Tablas de PDF, Scenario: Celda de varias líneas, Scenario: Tabla de PDF sin bordes

### Community 124 - "Requirement: Trazabilidad de la carga de documentos"
Cohesion: 0.67
Nodes (3): Requirement: Trazabilidad de la carga de documentos, Scenario: Archivo renombrado, Scenario: Carga registrada

### Community 125 - "Requirement: Títulos en el Markdown"
Cohesion: 0.67
Nodes (3): Requirement: Títulos en el Markdown, Scenario: Título de página fuera del texto, Scenario: Títulos que no abren sección

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 856 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Embedder` connect `Embedder` to `DocumentsConfig`, `Requirement: Embeddings de los fragmentos`, `ingest.py`, `Requirement: Embeddings de los fragmentos`, `EmbedderError`, `evidence_id`, `ADDED Requirements`, `Requirements`, `pytest`, `ingest_documents`, `documents/config.py`, `Proposal`, `retrieval.py`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Are the 74 inferred relationships involving `DocumentsConfig` (e.g. with `chunk_markdown()` and `to_markdown()`) actually correct?**
  _`DocumentsConfig` has 74 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Arquitectura de Brío Analyst` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Why does `Issue` connect `apply_rules` to `rules.py`, `.action`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `evidence_id()` (e.g. with `Componentes` and `Decisiones`) actually correct?**
  _`evidence_id()` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._