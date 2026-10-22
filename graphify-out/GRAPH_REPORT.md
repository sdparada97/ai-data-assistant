# Graph Report - ai-data-assistant  (2026-10-22)

## Corpus Check
- 156 files · ~129,408 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 2622 nodes · 5898 edges · 153 communities (130 shown, 23 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 962 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `95f33929`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- pathlib
- ADDED Requirements
- consultar_metrica
- test_graph.py
- explore.md
- ADDED Requirements
- conftest.py
- Requirements
- Exploración de datos
- documents/config.py
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
- test_storage.py
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
- Requirement: Errores del proveedor
- ADDED Requirements
- Requirements
- ingest_documents
- Requirement: Estructura de las incidencias
- open_readonly
- ADDED Requirements
- calidad_datos
- ingest.py
- Requirement: Aislamiento de la suite por defecto
- metrics.py
- pathlib
- settings.py
- retrieval.py
- test_chunking.py
- graph.py
- test_quality.py
- DocumentsConfig
- pipeline.py
- Decisions
- ingestion/errors.py
- Requirement: DQ04 catálogo de valores válidos
- json
- Requirements
- Embedder
- tool_errors.py
- Proposal
- Requirement: DQ08 valores negativos
- Requirement: Verificación de cifras
- QueryError
- ingest
- Tasks
- Requirement: Verificación de cifras
- figures
- Requirement: Pruebas con LLM separadas
- pytest
- ADDED Requirements
- Requirements
- Requirement: DQ01 registro_id único
- load_agent_config
- Benchmark de estrategias del agente (2026-10-22)
- Proposal
- publish
- context.py
- Requirement: Documentos a cargar
- Requirement: Tablas en los fragmentos
- Requirement: Corrección única
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
- test_llm.py
- evidence_id
- Requirement: Errores del proveedor y de los datos
- Requirement: Corrección única
- test_makefile.py
- test_verify.py
- Decisions
- AgentDeps
- write_csv
- markdown.py
- tools.py
- verify.py
- Requirement: Errores del proveedor y de los datos
- Requirement: Verificación de citas y lenguaje
- Requirement: Verificación de citas y lenguaje
- Requirement: Síntesis estructurada
- Requirement: Síntesis estructurada
- Requirement: Contexto de la planificación
- Requirement: Reintento y fallo cerrado
- schema.py
- Requirement: Validación de la pregunta
- query-agent Specification
- Arquitectura de Brío Analyst
- Requirement: Contexto de la planificación
- Requirement: Reintento y fallo cerrado
- Requirement: Validación de la pregunta

## God Nodes (most connected - your core abstractions)
1. `DocumentsConfig` - 92 edges
2. `consultar_metrica()` - 69 edges
3. `evidence_id()` - 68 edges
4. `AgentConfig` - 55 edges
5. `Bases` - 53 edges
6. `calidad_datos()` - 48 edges
7. `buscar_documentos()` - 47 edges
8. `QueryError` - 46 edges
9. `build_graph()` - 45 edges
10. `make_deps()` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Impact` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-document-retrieval/proposal.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Filtro como texto` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-query-agent/specs/query-agent/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Arquitectura` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py
- `Goals / Non-Goals` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Alias en el filtro` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/specs/sales-metrics/spec.md → backend/src/analyst_backend/analytics/evidence.py

## Import Cycles
- None detected.

## Communities (153 total, 23 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "pathlib"
Cohesion: 0.10
Nodes (8): LimitsConfig, ProviderConfig, _Strict, metric_description(), bases(), fake_embedder(), paths(), Paths

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "consultar_metrica"
Cohesion: 0.09
Nodes (28): consultar_metrica(), Requirement: Consultas fallidas sin resolver, Requirement: Planificación en una sola respuesta, Requirement: Prompts y descripciones desde configuración, Scenario: Consultas por encima del máximo, Scenario: Corrección con el máximo ocupado, Scenario: Corrección descartada, Scenario: Corrección parcial (+20 more)

### Community 4 - "test_graph.py"
Cohesion: 0.07
Nodes (73): AgentConfig, run_graph(), Bases, make_deps(), tool_context(), json_message(), plan_message(), scripted() (+65 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "ADDED Requirements"
Cohesion: 0.10
Nodes (20): ADDED Requirements, Purpose, Requirement: Clave nunca expuesta, Requirement: Errores del proveedor, Requirement: Fallos que no son del proveedor, Requirement: Parámetros del modelo en configuración, Requirement: Selección del proveedor, Scenario: Clave ausente (+12 more)

### Community 17 - "conftest.py"
Cohesion: 0.21
Nodes (9): _blocked_connect(), _blocked_connect_ex(), _blocked_resolution(), _blocked_sendmsg(), _blocked_sendto(), env_example_variables(), _guard(), _isolate_default_suite() (+1 more)

### Community 18 - "Requirements"
Cohesion: 0.05
Nodes (38): project-layout Specification, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Pruebas con LLM separadas (+30 more)

### Community 19 - "Exploración de datos"
Cohesion: 0.12
Nodes (16): 01 Contexto de negocio, 03 Investigación de consumidor, 04 Observaciones de canales, 05 Reporte comercial, Aprobación de reglas, Contradicciones entre fuentes, Cómo reproducir, Documentos y afirmaciones verificables (+8 more)

### Community 20 - "documents/config.py"
Cohesion: 0.10
Nodes (16): _check_regex(), EmbeddingTemplate, load_documents_config(), PdfConfig, _Strict, embedding_text(), DocumentsConfigError, test_embedding_template_renders_with_and_without_section() (+8 more)

### Community 22 - "test_app.py"
Cohesion: 0.06
Nodes (14): _coerce(), main(), parse_config(), load_settings(), Settings, _FakeApp, _render(), test_cli_launches_page_with_server_options() (+6 more)

### Community 23 - "Requirements"
Cohesion: 0.07
Nodes (28): data-quality Specification, Purpose, Requirement: Destino único por fila, Requirement: DQ04 catálogo de valores válidos, Requirement: DQ06 unidades faltantes, Requirement: DQ07 venta neta faltante, Requirement: DQ08 valores negativos, Requirement: DQ11 aviso de punto de venta único (+20 more)

### Community 24 - "Decisions"
Cohesion: 0.12
Nodes (16): Alcance del bloqueo de red, Contenedores, Context, D2' Código fuente en `backend/src/` y `frontend/src/` (reemplaza D2), D4 Workspace de uv con un único `uv.lock`, Decisions, Design, Goals / Non-Goals (+8 more)

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
Cohesion: 0.13
Nodes (19): apply_rules(), apply_catalog(), _as_number(), _check_integer(), check_month(), check_negative(), check_sales(), check_sales_without_units() (+11 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.14
Nodes (19): frame_of(), real_frame(), test_dq01_compares_after_trimming(), test_dq01_duplicate_with_differences(), test_dq01_real_file_identical_duplicate(), test_dq03_keeps_inner_spaces(), test_dq03_real_file_trims_region_and_channel(), test_dq04_catalog_comes_from_configuration() (+11 more)

### Community 36 - "test_storage.py"
Cohesion: 0.16
Nodes (22): ingest(), IngestionSummary, IngestionSettings, con(), previous_db(), real_db(), _settings(), _sha() (+14 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.12
Nodes (35): RulesOutcome, _issue(), _issues(), real(), run(), test_actions_by_severity_in_real_file(), test_dq01_duplicate_with_differences_keeps_line_2_in_sales(), test_dq01_first_occurrence_invalid_keeps_id_out_of_sales() (+27 more)

### Community 38 - "Requirements"
Cohesion: 0.06
Nodes (35): Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas, Requirement: Idempotencia (+27 more)

### Community 39 - "test_metrics.py"
Cohesion: 0.08
Nodes (45): MetricQuery, MetricResult, layer(), real_db(), RealDatabase, _by_group(), _comparison(), run() (+37 more)

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
Cohesion: 0.20
Nodes (16): load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes(), ConfigError (+8 more)

### Community 45 - "semantic.py"
Cohesion: 0.16
Nodes (20): _load_dimension(), _load_metric(), load_semantic_layer(), SemanticLayerError, _text(), validate_expression(), _layer(), _metric() (+12 more)

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

### Community 50 - "Requirement: Errores del proveedor"
Cohesion: 0.10
Nodes (20): llm-provider Specification, Purpose, Requirement: Clave nunca expuesta, Requirement: Errores del proveedor, Requirement: Fallos que no son del proveedor, Requirement: Parámetros del modelo en configuración, Requirement: Selección del proveedor, Requirements (+12 more)

### Community 51 - "ADDED Requirements"
Cohesion: 0.05
Nodes (37): ADDED Requirements, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 52 - "Requirements"
Cohesion: 0.05
Nodes (37): document-retrieval Specification, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 53 - "ingest_documents"
Cohesion: 0.16
Nodes (20): ingest_documents(), DocumentsSettings, documents_settings(), fake_embedder(), _copy_raw(), _empty_pdf(), _rows(), test_double_load_is_identical() (+12 more)

### Community 54 - "Requirement: Estructura de las incidencias"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada, Spec Delta

### Community 55 - "open_readonly"
Cohesion: 0.17
Nodes (11): _check_schema(), DatabaseError, open_readonly(), published_ingestion_id(), _sha(), test_external_access_and_configuration_are_rejected(), test_missing_database_asks_for_ingest(), test_old_database_without_issue_dimensions_asks_for_ingest() (+3 more)

### Community 56 - "ADDED Requirements"
Cohesion: 0.14
Nodes (13): ADDED Requirements, Purpose, Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Evidencia válida y avisos, Requirement: Sin evidencia, sin síntesis, Requirement: Traza por pregunta, Scenario: Clave vacía (+5 more)

### Community 57 - "calidad_datos"
Cohesion: 0.10
Nodes (26): calidad_datos(), Componentes, Decisiones, Fuera de alcance, Why, Capabilities, Fuera de alcance, Impact (+18 more)

### Community 58 - "ingest.py"
Cohesion: 0.11
Nodes (14): SourceError, documents_ingestion_id(), _file_sha256(), list_documents(), _ddl(), LoadedDocument, _quote(), RunRecord (+6 more)

### Community 59 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.12
Nodes (16): ADDED Requirements, MODIFIED Requirements, Requirement: Aislamiento de la suite por defecto, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Suite de pruebas sin servicios externos, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados (+8 more)

### Community 60 - "metrics.py"
Cohesion: 0.11
Nodes (25): MetricToolInput, build_sql(), _comparison_cell(), make_row(), _describe(), _issue_filter(), _metric_values(), Plan (+17 more)

### Community 61 - "pathlib"
Cohesion: 0.28
Nodes (6): config(), config_path_real(), fake_config(), fake_config_path(), fake_db(), write_config()

### Community 62 - "settings.py"
Cohesion: 0.07
Nodes (31): main(), AgentSettings, AnalyticsSettings, load_agent_settings(), load_analytics_settings(), load_documents_settings(), load_ingestion_settings(), load_llm_settings() (+23 more)

### Community 63 - "retrieval.py"
Cohesion: 0.10
Nodes (18): _config(), DocumentHit, DocumentQuery, DocumentResult, SearchWarning, _Strict, buscar_documentos(), _check_filters() (+10 more)

### Community 64 - "test_chunking.py"
Cohesion: 0.08
Nodes (41): _blocks(), _cells(), Chunk, chunk_markdown(), open_draft(), starting_id(), _Draft, _is_code() (+33 more)

### Community 65 - "graph.py"
Cohesion: 0.07
Nodes (41): evidence_items(), index(), metric_has_values(), AgentState, build_graph(), check_question(), collect(), execute() (+33 more)

### Community 66 - "test_quality.py"
Cohesion: 0.19
Nodes (15): QualityQuery, QualityResult, _ids(), run(), _run(), test_brand_in_south(), test_corrections_listed_on_request(), test_missing_ingestion_counts_raise_instead_of_zeros() (+7 more)

### Community 67 - "DocumentsConfig"
Cohesion: 0.12
Nodes (41): DocumentsConfig, DocumentsSummary, _codes(), _error_fields(), _ids_and_scores(), _lexical(), _primaries(), _query() (+33 more)

### Community 68 - "pipeline.py"
Cohesion: 0.12
Nodes (19): InputError, _check_header(), compute_ingestion_id(), _corrected_frame(), _issues_frame(), parse_sales_csv(), read_csv_bytes(), read_sales_csv() (+11 more)

### Community 69 - "Decisions"
Cohesion: 0.17
Nodes (9): LuceneBM25, Arquitectura, Configuración y comandos, D7a: convertir PDF y Word a Markdown con código propio, y fragmentar solo Markdown, D7b: fragmentador de Markdown, Decisions, Pruebas, Recuperación (+1 more)

### Community 70 - "ingestion/errors.py"
Cohesion: 0.21
Nodes (4): IngestionError, ReconciliationError, main(), check_reconciliation()

### Community 71 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 72 - "json"
Cohesion: 0.18
Nodes (12): build_tools(), ToolContext, _call(), _run_tool_node(), test_document_summary_has_citable_fragments(), test_format_tool_error_for_query_error(), test_handler_reports_invalid_arguments_and_query_errors(), test_metric_summary_and_full_artifact() (+4 more)

### Community 73 - "Requirements"
Cohesion: 0.18
Nodes (11): Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Evidencia válida y avisos, Requirement: Sin evidencia, sin síntesis, Requirement: Traza por pregunta, Requirements, Scenario: Clave vacía, Scenario: Dos preguntas con las mismas dependencias (+3 more)

### Community 74 - "Embedder"
Cohesion: 0.06
Nodes (28): ModelConfig, cached_model_file(), check_embedder(), Embedder, FailingEmbedder, FakeEmbedder, FastEmbedEmbedder, file_sha256() (+20 more)

### Community 76 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes

### Community 77 - "Requirement: DQ08 valores negativos"
Cohesion: 0.67
Nodes (3): Requirement: DQ08 valores negativos, Scenario: Cero no es negativo, Scenario: Negativos del archivo real

### Community 78 - "Requirement: Verificación de cifras"
Cohesion: 0.25
Nodes (8): Requirement: Verificación de cifras, Scenario: Caída expresada sin signo, Scenario: Cifra citada con un fragmento que no la contiene, Scenario: Cifra de cuatro dígitos sin respaldo, Scenario: Cifra del reporte citada con su fragmento, Scenario: Cifra del reporte presentada como dato de ventas, Scenario: Cifra junto al nombre de un documento, Scenario: Nombre de documento en la afirmación

### Community 79 - "QueryError"
Cohesion: 0.10
Nodes (18): build_plan(), resolve_filters(), QueryError, _months(), normalize_period(), resolve_period(), _condition(), _normalize() (+10 more)

### Community 80 - "ingest"
Cohesion: 0.27
Nodes (12): _make_ingest(), _rows(), _settings(), test_columns_in_another_order_load_completely(), test_csv_without_bom_gives_same_sales(), test_failed_replace_restores_previous_wal(), test_make_ingest_publishes_the_database(), test_make_ingest_reports_errors() (+4 more)

### Community 81 - "Tasks"
Cohesion: 0.25
Nodes (7): 2. Dimensiones en dq_issues (requisito MODIFIED "Estructura de las incidencias"), 3. Capa semántica, 5. consultar_metrica, 6. calidad_datos, 7. Documentación, 8. Cierre, Tasks

### Community 82 - "Requirement: Verificación de cifras"
Cohesion: 0.25
Nodes (8): Requirement: Verificación de cifras, Scenario: Caída expresada sin signo, Scenario: Cifra citada con un fragmento que no la contiene, Scenario: Cifra de cuatro dígitos sin respaldo, Scenario: Cifra del reporte citada con su fragmento, Scenario: Cifra del reporte presentada como dato de ventas, Scenario: Cifra junto al nombre de un documento, Scenario: Nombre de documento en la afirmación

### Community 84 - "Requirement: Pruebas con LLM separadas"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Pruebas con LLM separadas, Scenario: Archivo de entorno inexistente, Scenario: Ninguna prueba llm registrada, Scenario: Solo pruebas llm, Spec Delta

### Community 85 - "pytest"
Cohesion: 0.13
Nodes (11): rrf_fuse(), test_chunk_without_word_match_counts_only_similarity(), test_query_requires_the_config_in_context(), test_rrf_fusion_of_two_rankings(), test_dns_resolution_fails_with_explicit_error(), test_embeddings_tests_keep_only_models_cache_dir(), test_env_example_variables_are_hidden(), test_local_unix_sockets_keep_native_behaviour() (+3 more)

### Community 86 - "ADDED Requirements"
Cohesion: 0.18
Nodes (11): ADDED Requirements, Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirement: Tablas de PDF, Scenario: Caché con otra huella, Scenario: Celda de varias líneas, Scenario: Código de punto de venta (+3 more)

### Community 87 - "Requirements"
Cohesion: 0.18
Nodes (11): Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirement: Publicación atómica e idempotente, Requirements, Scenario: Caché con otra huella, Scenario: Código de punto de venta, Scenario: Doble carga (+3 more)

### Community 88 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 89 - "load_agent_config"
Cohesion: 0.19
Nodes (9): AgentConfigError, load_agent_config(), agent_config(), test_invalid_config_is_rejected(), test_missing_file(), test_real_config_loads(), test_temperature_by_longest_prefix(), _write() (+1 more)

### Community 90 - "Benchmark de estrategias del agente (2026-10-22)"
Cohesion: 0.33
Nodes (5): Benchmark de estrategias del agente (2026-10-22), Estrategias, Preguntas, Resultados: Gemini (capa gratuita, Gemini 3 Flash), Resultados: modelos locales (Ollama, 190 ejecuciones)

### Community 91 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 92 - "publish"
Cohesion: 0.12
Nodes (11): publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files(), write_tables(), Almacenamiento, Context, Design (+3 more)

### Community 93 - "context.py"
Cohesion: 0.13
Nodes (17): build_planning_context(), catalog_text(), data_range(), DataRange, _document_rows(), PlanningContext, evidence_block(), hedge_examples() (+9 more)

### Community 94 - "Requirement: Documentos a cargar"
Cohesion: 0.33
Nodes (6): Requirement: Documentos a cargar, Scenario: Archivo dañado, Scenario: Archivos que se ignoran, Scenario: Directorio real, Scenario: doc_id duplicado, Scenario: Sin documentos válidos

### Community 95 - "Requirement: Tablas en los fragmentos"
Cohesion: 0.33
Nodes (6): Requirement: Tablas en los fragmentos, Scenario: ID repetido en una tabla, Scenario: Registros de campo, Scenario: Tabla con IDs ya divididos, Scenario: Tabla sin IDs, Scenario: Índice de referencias

### Community 96 - "Requirement: Corrección única"
Cohesion: 0.33
Nodes (6): Requirement: Corrección única, Scenario: Argumentos inválidos, Scenario: Consulta descartada y consulta fallida, Scenario: Corrección que vuelve a fallar, Scenario: Corrección sin texto de documentos, Scenario: Marca inexistente

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

### Community 126 - "test_llm.py"
Cohesion: 0.07
Nodes (21): GeminiConfig, build_chat_model(), build_llm_client(), _error_code(), _is_retryable(), LLMClient, make_rate_limiter(), ProviderError (+13 more)

### Community 127 - "evidence_id"
Cohesion: 0.09
Nodes (30): canonical_json(), evidence_id(), Requirement: Trazabilidad de la búsqueda, Scenario: Cambio de modo, Scenario: Espacios y tildes, Scenario: Misma búsqueda, Requirement: Respuesta con el modelo real, Requirement: Respuesta y traza (+22 more)

### Community 128 - "Requirement: Errores del proveedor y de los datos"
Cohesion: 0.33
Nodes (6): Requirement: Errores del proveedor y de los datos, Scenario: Base de ventas ausente, Scenario: Clave fuera de la traza, Scenario: Cuota agotada al planificar, Scenario: Cuota agotada al sintetizar, Scenario: Fallo interno

### Community 129 - "Requirement: Corrección única"
Cohesion: 0.33
Nodes (6): Requirement: Corrección única, Scenario: Argumentos inválidos, Scenario: Consulta descartada y consulta fallida, Scenario: Corrección que vuelve a fallar, Scenario: Corrección sin texto de documentos, Scenario: Marca inexistente

### Community 130 - "test_makefile.py"
Cohesion: 0.07
Nodes (25): test_empty_key(), test_missing_directory_fails_with_its_path_even_without_model(), _fake_cached_model(), _make(), test_cache_with_other_fingerprint_fails_without_downloading(), test_check_without_model_points_to_make_models(), _compose_config(), resolved() (+17 more)

### Community 131 - "test_verify.py"
Cohesion: 0.16
Nodes (22): check(), run(), fact(), _hits(), hypothesis(), run_evidence(), test_causal_language_in_a_fact(), test_claim_without_citation() (+14 more)

### Community 132 - "Decisions"
Cohesion: 0.11
Nodes (17): Arquitectura, Avisos de calidad, Conexión de solo lectura, Context, Decisions, Design, Evidencia y trazabilidad, Generación de SQL (+9 more)

### Community 133 - "AgentDeps"
Cohesion: 0.09
Nodes (20): _claim(), main(), render(), AgentDeps, answer_question(), build_deps(), test_invalid_configuration_is_a_response(), test_llm_configuration_is_checked_before_the_paths() (+12 more)

### Community 134 - "write_csv"
Cohesion: 0.22
Nodes (4): valid_row(), write_csv(), _run(), _frame()

### Community 135 - "markdown.py"
Cohesion: 0.05
Nodes (44): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), extract_documents(), _fmt(), load_raw() (+36 more)

### Community 136 - "tools.py"
Cohesion: 0.15
Nodes (16): _as_list(), _as_list_values(), documents_tool(), metric_tool(), quality_tool(), _cells(), document_summary(), DocumentToolInput (+8 more)

### Community 137 - "verify.py"
Cohesion: 0.20
Nodes (12): Evidence, _contains_phrase(), figures_in(), _plain(), _pool(), Problem, _readings(), _strip_non_figures() (+4 more)

### Community 138 - "Requirement: Errores del proveedor y de los datos"
Cohesion: 0.33
Nodes (6): Requirement: Errores del proveedor y de los datos, Scenario: Base de ventas ausente, Scenario: Clave fuera de la traza, Scenario: Cuota agotada al planificar, Scenario: Cuota agotada al sintetizar, Scenario: Fallo interno

### Community 139 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 140 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 141 - "Requirement: Síntesis estructurada"
Cohesion: 0.50
Nodes (4): Requirement: Síntesis estructurada, Scenario: Delimitador dentro de un fragmento, Scenario: Documentos delimitados, Scenario: Síntesis no interpretable

### Community 142 - "Requirement: Síntesis estructurada"
Cohesion: 0.50
Nodes (4): Requirement: Síntesis estructurada, Scenario: Delimitador dentro de un fragmento, Scenario: Documentos delimitados, Scenario: Síntesis no interpretable

### Community 143 - "Requirement: Contexto de la planificación"
Cohesion: 0.67
Nodes (3): Requirement: Contexto de la planificación, Scenario: Catálogo desde configuración, Scenario: Rango de datos real

### Community 144 - "Requirement: Reintento y fallo cerrado"
Cohesion: 0.67
Nodes (3): Requirement: Reintento y fallo cerrado, Scenario: Corrección tras el reintento, Scenario: Fallo cerrado

### Community 145 - "schema.py"
Cohesion: 0.18
Nodes (6): Catalog, ValidationFailedError, _non_empty_text(), sales_schema(), validate_sales(), test_pandera_names_the_failing_column()

### Community 146 - "Requirement: Validación de la pregunta"
Cohesion: 0.67
Nodes (3): Requirement: Validación de la pregunta, Scenario: Pregunta demasiado larga, Scenario: Pregunta vacía

### Community 148 - "Arquitectura de Brío Analyst"
Cohesion: 0.08
Nodes (20): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas (+12 more)

### Community 149 - "Requirement: Contexto de la planificación"
Cohesion: 0.67
Nodes (3): Requirement: Contexto de la planificación, Scenario: Catálogo desde configuración, Scenario: Rango de datos real

### Community 150 - "Requirement: Reintento y fallo cerrado"
Cohesion: 0.67
Nodes (3): Requirement: Reintento y fallo cerrado, Scenario: Corrección tras el reintento, Scenario: Fallo cerrado

### Community 151 - "Requirement: Validación de la pregunta"
Cohesion: 0.67
Nodes (3): Requirement: Validación de la pregunta, Scenario: Pregunta demasiado larga, Scenario: Pregunta vacía

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1103 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Embedder` connect `Embedder` to `pathlib`, `DocumentsConfig`, `Requirement: Embeddings de los fragmentos`, `AgentDeps`, `Requirement: Embeddings de los fragmentos`, `json`, `ADDED Requirements`, `Requirements`, `ingest_documents`, `calidad_datos`, `ingest.py`, `Proposal`, `retrieval.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 77 inferred relationships involving `DocumentsConfig` (e.g. with `AgentDeps` and `ToolContext`) actually correct?**
  _`DocumentsConfig` has 77 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pathlib` be split into smaller, more focused modules?**
  _Cohesion score 0.09830866807610994 - nodes in this community are weakly interconnected._
- **Why does `buscar_documentos()` connect `retrieval.py` to `pathlib`, `graph.py`, `DocumentsConfig`, `consultar_metrica`, `Decisions`, `json`, `tools.py`, `Embedder`, `QueryError`, `ADDED Requirements`, `Requirements`, `pytest`, `open_readonly`, `calidad_datos`, `Proposal`, `evidence_id`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `consultar_metrica()` (e.g. with `ComparisonCell` and `MetricCell`) actually correct?**
  _`consultar_metrica()` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._