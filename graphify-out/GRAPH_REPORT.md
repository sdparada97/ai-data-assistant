# Graph Report - ai-data-assistant  (2026-10-22)

## Corpus Check
- 175 files · ~149,672 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 3070 nodes · 6921 edges · 193 communities (167 shown, 26 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1115 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `435362a7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- agent/evidence.py
- ADDED Requirements
- test_page.py
- AgentConfig
- explore.md
- ADDED Requirements
- conftest.py
- Requirements
- Exploración de datos
- agent/conftest.py
- load_agent_config
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
- search
- Requirement: Aislamiento de la suite por defecto
- consultar_metrica
- pathlib
- ADDED Requirements
- Requirements
- test_chunking.py
- build_graph
- test_quality.py
- DocumentsConfig
- read_sales_csv
- markdown.py
- ScriptedChatModel
- Requirement: DQ04 catálogo de valores válidos
- load_documents_config
- Requirements
- ADDED Requirements
- Requirements
- Proposal
- Requirement: DQ08 valores negativos
- Requirement: Verificación de cifras
- QueryError
- agent/config.py
- render.py
- Requirement: Verificación de cifras
- settings.py
- Requirement: Pruebas con LLM separadas
- chunking.py
- ADDED Requirements
- Requirements
- Requirement: DQ01 registro_id único
- graph.py
- Benchmark de estrategias del agente (2026-10-22)
- Proposal
- publish
- LLMClient
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
- embeddings.py
- test_compose.py
- test_verify.py
- Decisions
- ask.py
- ingest.py
- test_markdown.py
- tools.py
- verify.py
- Requirement: Errores del proveedor y de los datos
- Requirement: Verificación de citas y lenguaje
- QueryError
- ADDED Requirements
- test_ask.py
- ask_backend
- Requirement: Evidencias en la respuesta
- schema.py
- pipeline.py
- Tasks
- ai-data-assistant
- .bind_tools
- context.py
- analytics/models.py
- buscar_documentos
- Decisions
- ai-data-assistant
- Hoja de ruta: Brío Analyst
- Proposal
- AgentResponse
- Requirement: Detalle de las evidencias
- Decisions
- Arquitectura de Brío Analyst
- Requirement: Razonamiento configurable por paso
- analyst_frontend/config.py
- Requirement: Detalle de las evidencias
- test_layout.py
- Requirement: Aislamiento de la suite por defecto
- query-agent Specification
- analytics/conftest.py
- Requirement: Corrección única
- explore_data.py
- Requirement: Verificación de citas y lenguaje
- Requirement: Patrones de IDs en configuración
- Requirement: Datos del host en el backend
- Requirement: Evidencias en la respuesta
- Requirement: Publicación atómica e idempotente
- Requirement: Título de cada evidencia
- asked
- .id_regex
- Requirement: Comprobación antes de arrancar
- Requirement: Entorno Python reproducible
- Requirement: Pruebas con LLM separadas
- Requirement: Suite de pruebas sin servicios externos
- Requirement: Síntesis estructurada
- project-layout Specification
- Requirement: Orquestación con contenedores
- Requirement: Pruebas con el modelo de embeddings separadas
- Requirement: Página mínima del frontend
- Requirement: Salud del backend
- Requirement: Contexto de la planificación
- Requirement: Evidencias en respuestas con error

## God Nodes (most connected - your core abstractions)
1. `DocumentsConfig` - 92 edges
2. `evidence_id()` - 78 edges
3. `AgentConfig` - 75 edges
4. `consultar_metrica()` - 73 edges
5. `Bases` - 70 edges
6. `make_deps()` - 61 edges
7. `run_graph()` - 52 edges
8. `calidad_datos()` - 48 edges
9. `build_graph()` - 47 edges
10. `buscar_documentos()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `Scenario: Evidencia de calidad` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-api-and-ui/specs/analyst-ui/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Evidencia de una búsqueda` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-api-and-ui/specs/analyst-ui/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Impact` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-document-retrieval/proposal.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Filtro como texto` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-query-agent/specs/query-agent/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Arquitectura` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py

## Import Cycles
- None detected.

## Communities (193 total, 26 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "agent/evidence.py"
Cohesion: 0.15
Nodes (12): evidence_items(), evidence_views(), figures(), _filters(), fragment_title(), _join(), metric_title(), quality_title() (+4 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "test_page.py"
Cohesion: 0.21
Nodes (32): answer(), claim(), evidence_expanders(), joined(), labels(), page(), send(), test_answer_is_saved_and_input_enabled() (+24 more)

### Community 4 - "AgentConfig"
Cohesion: 0.20
Nodes (44): AgentConfig, run_graph(), Bases, make_deps(), plan_message(), max_three(), metric(), _repair_messages() (+36 more)

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
Cohesion: 0.20
Nodes (10): Requirement: Evaluación reservada, Requirement: Puertos solo en la máquina local, Requirement: Tiempo de espera de la interfaz en contenedores, Requirement: Ubicación del código fuente, Requirements, Scenario: Evaluación no implementada, Scenario: Paquetes importables desde su ubicación, Scenario: Puertos locales (+2 more)

### Community 19 - "Exploración de datos"
Cohesion: 0.12
Nodes (16): 01 Contexto de negocio, 03 Investigación de consumidor, 04 Observaciones de canales, 05 Reporte comercial, Aprobación de reglas, Contradicciones entre fuentes, Cómo reproducir, Documentos y afirmaciones verificables (+8 more)

### Community 20 - "agent/conftest.py"
Cohesion: 0.10
Nodes (16): LimitsConfig, ProviderConfig, _Strict, agent_config(), bases(), fake_embedder(), tool_context(), test_catalog_comes_from_configuration() (+8 more)

### Community 21 - "load_agent_config"
Cohesion: 0.23
Nodes (11): AgentConfigError, load_agent_config(), test_invalid_config_is_rejected(), test_invalid_reasoning_is_rejected(), test_missing_file(), test_plan_reasoning_by_longest_prefix(), test_real_config_loads(), test_synthesis_reasoning_by_longest_prefix() (+3 more)

### Community 22 - "test_app.py"
Cohesion: 0.17
Nodes (7): _FakeApp, _render(), test_cli_launches_page_with_server_options(), test_cli_rejects_malformed_options(), test_cli_without_options_uses_default_config(), test_page_shows_configured_title_and_url(), test_page_uses_defaults_without_variables()

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
Nodes (18): apply_rules(), apply_catalog(), _as_number(), _check_integer(), check_month(), check_negative(), check_sales(), check_sales_without_units() (+10 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.13
Nodes (21): _by_id(), frame_of(), real_frame(), test_dq01_compares_after_trimming(), test_dq01_duplicate_with_differences(), test_dq01_real_file_identical_duplicate(), test_dq03_keeps_inner_spaces(), test_dq03_real_file_trims_region_and_channel() (+13 more)

### Community 36 - "test_storage.py"
Cohesion: 0.14
Nodes (23): ingest(), IngestionSummary, IngestionSettings, test_ties_share_rank(), con(), previous_db(), real_db(), _settings() (+15 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.10
Nodes (38): RulesOutcome, paths(), Paths, valid_row(), _issue(), _issues(), real(), run() (+30 more)

### Community 38 - "Requirements"
Cohesion: 0.06
Nodes (35): Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas, Requirement: Idempotencia (+27 more)

### Community 39 - "test_metrics.py"
Cohesion: 0.17
Nodes (31): MetricResult, _by_group(), _comparison(), run(), _single(), test_alias_gives_same_rows_and_evidence(), test_brand_by_region_in_t1(), test_comparison_against_period_without_data() (+23 more)

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
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 44 - "catalog.py"
Cohesion: 0.20
Nodes (16): load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes(), ConfigError (+8 more)

### Community 45 - "semantic.py"
Cohesion: 0.14
Nodes (22): AggregateMetric, _load_dimension(), _load_metric(), load_semantic_layer(), RatioMetric, SemanticLayerError, _text(), validate_expression() (+14 more)

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
Cohesion: 0.08
Nodes (25): llm-provider Specification, Purpose, Requirement: Clave nunca expuesta, Requirement: Errores del proveedor, Requirement: Fallos que no son del proveedor, Requirement: Parámetros del modelo en configuración, Requirement: Razonamiento configurable por paso, Requirement: Selección del proveedor (+17 more)

### Community 51 - "ADDED Requirements"
Cohesion: 0.05
Nodes (37): ADDED Requirements, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 52 - "Requirements"
Cohesion: 0.05
Nodes (37): document-retrieval Specification, Purpose, Requirement: Acceso de solo lectura a la base de documentos, Requirement: Búsqueda híbrida, Requirement: Contenido documental como evidencia, Requirement: Degradación a BM25, Requirement: Filtros, Requirement: Normalización del texto para BM25 (+29 more)

### Community 53 - "ingest_documents"
Cohesion: 0.15
Nodes (19): ingest_documents(), DocumentsSettings, documents_settings(), _copy_raw(), _empty_pdf(), _rows(), test_double_load_is_identical(), test_errors_keep_an_existing_database() (+11 more)

### Community 54 - "Requirement: Estructura de las incidencias"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada, Spec Delta

### Community 55 - "open_readonly"
Cohesion: 0.09
Nodes (19): _check_schema(), DatabaseError, open_readonly(), published_ingestion_id(), _sha(), test_external_access_and_configuration_are_rejected(), test_missing_database_asks_for_ingest(), test_old_database_without_issue_dimensions_asks_for_ingest() (+11 more)

### Community 56 - "ADDED Requirements"
Cohesion: 0.07
Nodes (26): ADDED Requirements, Purpose, Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Contexto de la planificación, Requirement: Evidencia válida y avisos, Requirement: Reintento y fallo cerrado, Requirement: Sin evidencia, sin síntesis (+18 more)

### Community 57 - "calidad_datos"
Cohesion: 0.10
Nodes (22): calidad_datos(), _condition(), Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal (+14 more)

### Community 58 - "search"
Cohesion: 0.33
Nodes (8): _citable(), _report_synthesis(), search(), _synthesis_prompt(), test_correction_after_the_retry(), test_documents_are_delimited_and_rules_come_last(), test_evidence_cited_by_primary_id_and_search(), test_one_id_in_two_fragments()

### Community 59 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.12
Nodes (16): ADDED Requirements, MODIFIED Requirements, Requirement: Aislamiento de la suite por defecto, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Suite de pruebas sin servicios externos, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados (+8 more)

### Community 60 - "consultar_metrica"
Cohesion: 0.09
Nodes (27): consultar_metrica(), Requirement: Consultas fallidas sin resolver, Requirement: Planificación en una sola respuesta, Requirement: Prompts y descripciones desde configuración, Scenario: Consultas por encima del máximo, Scenario: Corrección con el máximo ocupado, Scenario: Corrección descartada, Scenario: Corrección parcial (+19 more)

### Community 61 - "pathlib"
Cohesion: 0.28
Nodes (6): config(), config_path_real(), fake_config(), fake_config_path(), fake_db(), write_config()

### Community 62 - "ADDED Requirements"
Cohesion: 0.06
Nodes (33): ADDED Requirements, Purpose, Requirement: API inaccesible, Requirement: Avisos y traza, Requirement: Historial de la sesión, Requirement: Mensajes de estado y de error, Requirement: Pregunta en curso, Requirement: Pregunta y respuesta por apartados (+25 more)

### Community 63 - "Requirements"
Cohesion: 0.06
Nodes (30): analyst-ui Specification, Purpose, Requirement: API inaccesible, Requirement: Historial de la sesión, Requirement: Mensajes de estado y de error, Requirement: Pregunta en curso, Requirement: Pregunta y respuesta por apartados, Requirement: Respuesta no reconocible (+22 more)

### Community 64 - "test_chunking.py"
Cohesion: 0.15
Nodes (25): Chunk, _by_primary(), _chunk_all(), chunks(), _md(), test_empty_section_is_discarded(), test_field_records_are_one_chunk_per_row(), test_following_paragraph_stays_with_the_id() (+17 more)

### Community 65 - "build_graph"
Cohesion: 0.09
Nodes (33): index(), metric_has_values(), build_graph(), check_question(), collect(), execute(), load_context(), plan() (+25 more)

### Community 66 - "test_quality.py"
Cohesion: 0.24
Nodes (11): QualityResult, _ids(), run(), test_brand_in_south(), test_corrections_listed_on_request(), test_missing_ingestion_counts_raise_instead_of_zeros(), test_period_filter_includes_invalid_months(), test_quality_evidence_is_deterministic() (+3 more)

### Community 67 - "DocumentsConfig"
Cohesion: 0.12
Nodes (44): DocumentsConfig, DocumentsSummary, DocumentResult, fake_embedder(), test_fake_embedder_matches_its_config(), _codes(), _error_fields(), _ids_and_scores() (+36 more)

### Community 68 - "read_sales_csv"
Cohesion: 0.15
Nodes (13): InputError, read_sales_csv(), write_csv(), test_columns_in_another_order_are_accepted(), test_extra_column_is_named(), test_header_only_is_rejected(), test_latin1_file_is_rejected(), test_missing_column_is_named() (+5 more)

### Community 69 - "markdown.py"
Cohesion: 0.12
Nodes (9): PdfConfig, collapse_spaces(), _docx_table_rows(), _Line, markdown_table(), _page_lines(), pdf_to_markdown(), _table_cells() (+1 more)

### Community 70 - "ScriptedChatModel"
Cohesion: 0.13
Nodes (9): json_message(), scripted(), ScriptedChatModel, tool_call(), _Answer, test_returns_tool_calls_and_records_messages(), test_scripted_exception_is_raised(), test_structured_output_with_include_raw() (+1 more)

### Community 71 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 72 - "load_documents_config"
Cohesion: 0.10
Nodes (16): _check_regex(), EmbeddingTemplate, load_documents_config(), _Strict, embedding_text(), DocumentsConfigError, test_configurable_patterns(), test_embedding_template_renders_with_and_without_section() (+8 more)

### Community 73 - "Requirements"
Cohesion: 0.14
Nodes (14): Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Evidencia válida y avisos, Requirement: Reintento y fallo cerrado, Requirement: Sin evidencia, sin síntesis, Requirement: Traza por pregunta, Requirements, Scenario: Clave vacía (+6 more)

### Community 74 - "ADDED Requirements"
Cohesion: 0.07
Nodes (26): ADDED Requirements, Purpose, Requirement: Cuerpo de la petición, Requirement: Datos cargados después de arrancar, Requirement: Dependencias del agente al arrancar, Requirement: Estado HTTP según el resultado, Requirement: Fallos no controlados, Requirement: Pregunta por la API (+18 more)

### Community 75 - "Requirements"
Cohesion: 0.07
Nodes (26): Purpose, query-api Specification, Requirement: Cuerpo de la petición, Requirement: Datos cargados después de arrancar, Requirement: Dependencias del agente al arrancar, Requirement: Estado HTTP según el resultado, Requirement: Fallos no controlados, Requirement: Pregunta por la API (+18 more)

### Community 76 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 77 - "Requirement: DQ08 valores negativos"
Cohesion: 0.67
Nodes (3): Requirement: DQ08 valores negativos, Scenario: Cero no es negativo, Scenario: Negativos del archivo real

### Community 78 - "Requirement: Verificación de cifras"
Cohesion: 0.25
Nodes (8): Requirement: Verificación de cifras, Scenario: Caída expresada sin signo, Scenario: Cifra citada con un fragmento que no la contiene, Scenario: Cifra de cuatro dígitos sin respaldo, Scenario: Cifra del reporte citada con su fragmento, Scenario: Cifra del reporte presentada como dato de ventas, Scenario: Cifra junto al nombre de un documento, Scenario: Nombre de documento en la afirmación

### Community 79 - "QueryError"
Cohesion: 0.19
Nodes (15): build_sql(), _comparison_cell(), make_row(), _describe(), _issue_filter(), _metric_values(), Plan, _quality_notes() (+7 more)

### Community 81 - "render.py"
Cohesion: 0.24
Nodes (11): escape_label(), _metric_table(), _quality_table(), render_claim_evidence(), _render_claims(), _render_error(), render_evidence(), render_outcome() (+3 more)

### Community 82 - "Requirement: Verificación de cifras"
Cohesion: 0.25
Nodes (8): Requirement: Verificación de cifras, Scenario: Caída expresada sin signo, Scenario: Cifra citada con un fragmento que no la contiene, Scenario: Cifra de cuatro dígitos sin respaldo, Scenario: Cifra del reporte citada con su fragmento, Scenario: Cifra del reporte presentada como dato de ventas, Scenario: Cifra junto al nombre de un documento, Scenario: Nombre de documento en la afirmación

### Community 83 - "settings.py"
Cohesion: 0.08
Nodes (33): main(), AgentSettings, AnalyticsSettings, load_agent_settings(), load_analytics_settings(), load_documents_settings(), load_ingestion_settings(), load_llm_settings() (+25 more)

### Community 84 - "Requirement: Pruebas con LLM separadas"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Pruebas con LLM separadas, Scenario: Archivo de entorno inexistente, Scenario: Ninguna prueba llm registrada, Scenario: Solo pruebas llm, Spec Delta

### Community 85 - "chunking.py"
Cohesion: 0.20
Nodes (13): _blocks(), _cells(), chunk_markdown(), open_draft(), starting_id(), _Draft, _is_code(), _is_table() (+5 more)

### Community 86 - "ADDED Requirements"
Cohesion: 0.25
Nodes (8): ADDED Requirements, Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Tablas de PDF, Scenario: Caché con otra huella, Scenario: Celda de varias líneas, Scenario: Error desde make, Scenario: Tabla de PDF sin bordes

### Community 87 - "Requirements"
Cohesion: 0.25
Nodes (8): Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirements, Scenario: Caché con otra huella, Scenario: Código de punto de venta, Scenario: Error desde make, Scenario: Patrón configurable

### Community 88 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 89 - "graph.py"
Cohesion: 0.11
Nodes (14): PlanningContext, AgentState, synthesize(), _discarded_warning(), _error_detail(), _failure_notes(), evidence_block(), neutralize() (+6 more)

### Community 90 - "Benchmark de estrategias del agente (2026-10-22)"
Cohesion: 0.33
Nodes (5): Benchmark de estrategias del agente (2026-10-22), Estrategias, Preguntas, Resultados: Gemini (capa gratuita, Gemini 3 Flash), Resultados: modelos locales (Ollama, 190 ejecuciones)

### Community 91 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 92 - "publish"
Cohesion: 0.12
Nodes (12): publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files(), write_tables(), Almacenamiento, Context, Design (+4 more)

### Community 93 - "LLMClient"
Cohesion: 0.12
Nodes (10): _error_code(), _is_retryable(), LLMClient, D9g: ajustes tras la prueba manual (2026-10-22), 3. Interfaz del analista, 4. Contenedores y `make up`, 5. Documentación, 6. Cierre (+2 more)

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
Cohesion: 0.10
Nodes (20): build_chat_model(), build_llm_client(), make_rate_limiter(), ProviderError, LLMSettings, _chat_models(), _client(), _failing() (+12 more)

### Community 127 - "evidence_id"
Cohesion: 0.09
Nodes (33): evidence_id(), test_evidence_id_changes_with_each_input(), Requirement: Trazabilidad de la búsqueda, Scenario: Cambio de modo, Scenario: Espacios y tildes, Scenario: Misma búsqueda, Requirement: Respuesta con el modelo real, Requirement: Respuesta y traza (+25 more)

### Community 128 - "Requirement: Errores del proveedor y de los datos"
Cohesion: 0.33
Nodes (6): Requirement: Errores del proveedor y de los datos, Scenario: Base de ventas ausente, Scenario: Clave fuera de la traza, Scenario: Cuota agotada al planificar, Scenario: Cuota agotada al sintetizar, Scenario: Fallo interno

### Community 129 - "embeddings.py"
Cohesion: 0.05
Nodes (36): ModelConfig, cached_model_file(), check_embedder(), Embedder, FailingEmbedder, FakeEmbedder, FastEmbedEmbedder, file_sha256() (+28 more)

### Community 130 - "test_compose.py"
Cohesion: 0.05
Nodes (49): test_empty_key(), test_missing_directory_fails_with_its_path_even_without_model(), _fake_cached_model(), _make(), test_cache_with_other_fingerprint_fails_without_downloading(), test_check_without_model_points_to_make_models(), _make_ingest(), _rows() (+41 more)

### Community 131 - "test_verify.py"
Cohesion: 0.17
Nodes (22): Synthesis, check(), fact(), hypothesis(), run_evidence(), test_causal_language_in_a_fact(), test_claim_without_citation(), test_document_name_in_a_fact() (+14 more)

### Community 132 - "Decisions"
Cohesion: 0.12
Nodes (16): Arquitectura, Avisos de calidad, Conexión de solo lectura, Context, Decisions, Design, Evidencia y trazabilidad, Generación de SQL (+8 more)

### Community 133 - "ask.py"
Cohesion: 0.09
Nodes (12): AgentDeps, build_deps(), AgentRuntime, ask(), AskRequest, start_runtime(), unhandled_error(), create_app() (+4 more)

### Community 134 - "ingest.py"
Cohesion: 0.09
Nodes (15): canonical_json(), SourceError, documents_ingestion_id(), _file_sha256(), list_documents(), _ddl(), LoadedDocument, _quote() (+7 more)

### Community 135 - "test_markdown.py"
Cohesion: 0.13
Nodes (20): extract_documents(), ConversionError, docx_to_markdown(), to_markdown(), SourceFile, _pdf(), test_damaged_file_names_the_file(), test_every_supported_extension_has_a_converter() (+12 more)

### Community 136 - "tools.py"
Cohesion: 0.07
Nodes (38): format_tool_error(), _validation_details(), _as_list(), _as_list_values(), build_tools(), documents_tool(), metric_tool(), quality_tool() (+30 more)

### Community 137 - "verify.py"
Cohesion: 0.15
Nodes (15): Evidence, hedge_examples(), _contains_phrase(), drop_failing(), figures_in(), _plain(), _pool(), Problem (+7 more)

### Community 138 - "Requirement: Errores del proveedor y de los datos"
Cohesion: 0.33
Nodes (6): Requirement: Errores del proveedor y de los datos, Scenario: Base de ventas ausente, Scenario: Clave fuera de la traza, Scenario: Cuota agotada al planificar, Scenario: Cuota agotada al sintetizar, Scenario: Fallo interno

### Community 139 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 140 - "QueryError"
Cohesion: 0.22
Nodes (7): build_plan(), resolve_filters(), QueryError, _normalize(), Dimension, SemanticLayer, test_query_error_is_structured()

### Community 141 - "ADDED Requirements"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Requirement: Comprobación antes de arrancar, Requirement: Datos del host en el backend, Requirement: Puertos solo en la máquina local, Requirement: Tiempo de espera de la interfaz en contenedores, Scenario: Base de documentos ausente, Scenario: Base de ventas ausente, Scenario: Configuración en la imagen (+7 more)

### Community 142 - "test_ask.py"
Cohesion: 0.12
Nodes (17): test_request_rate_limit(), ask(), client_for(), test_blank_question_is_422_with_agent_body(), test_dependencies_are_built_once(), test_documents_database_missing(), test_exception_outside_the_nodes(), test_failure_in_the_api_outside_the_agent() (+9 more)

### Community 143 - "ask_backend"
Cohesion: 0.14
Nodes (10): ask_backend(), AskOutcome, _is_agent_response(), test_agent_response_with_any_status(), handler(), test_backend_timeout_setting(), test_connection_failures_are_unreachable(), test_plain_text_500_is_unrecognized() (+2 more)

### Community 144 - "Requirement: Evidencias en la respuesta"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Requirement: Evidencias en la respuesta, Requirement: Evidencias en respuestas con error, Requirement: Título de cada evidencia, Scenario: Cuota agotada al corregir, Scenario: Cuota agotada al sintetizar, Scenario: Evidencia citada por un ID principal, Scenario: Evidencia de una búsqueda (+7 more)

### Community 145 - "schema.py"
Cohesion: 0.18
Nodes (6): Catalog, ValidationFailedError, _non_empty_text(), sales_schema(), validate_sales(), test_pandera_names_the_failing_column()

### Community 146 - "pipeline.py"
Cohesion: 0.10
Nodes (13): IngestionError, ReconciliationError, main(), _check_header(), check_reconciliation(), compute_ingestion_id(), _corrected_frame(), _issues_frame() (+5 more)

### Community 147 - "Tasks"
Cohesion: 0.25
Nodes (7): 2. Dimensiones en dq_issues (requisito MODIFIED "Estructura de las incidencias"), 3. Capa semántica, 5. consultar_metrica, 6. calidad_datos, 7. Documentación, 8. Cierre, Tasks

### Community 148 - "ai-data-assistant"
Cohesion: 0.25
Nodes (8): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas

### Community 149 - ".bind_tools"
Cohesion: 0.21
Nodes (8): Grafo LangGraph, Pruebas, Context, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs, 2. Proveedor de LLM

### Community 150 - "context.py"
Cohesion: 0.13
Nodes (15): build_planning_context(), catalog_text(), data_range(), DataRange, _document_rows(), is_valid_month(), _months(), normalize_period() (+7 more)

### Community 151 - "analytics/models.py"
Cohesion: 0.13
Nodes (18): Comparison, IngestionCounts, MetricCell, MetricQuery, QualityNote, QualityQuery, RuleActionCount, SortSpec (+10 more)

### Community 152 - "buscar_documentos"
Cohesion: 0.09
Nodes (20): _config(), DocumentHit, DocumentQuery, SearchWarning, _Strict, buscar_documentos(), _check_filters(), _cosine() (+12 more)

### Community 153 - "Decisions"
Cohesion: 0.20
Nodes (9): D9c: interfaz Streamlit en tres módulos, D9d: contenedores con datos del host, D9e: pruebas, D9f: documentación, Decisions, Design, Goals / Non-Goals, Migration Plan (+1 more)

### Community 154 - "ai-data-assistant"
Cohesion: 0.25
Nodes (8): ai-data-assistant, Comandos, Consultar la base desde Python, Estructura, Instalación, Preguntar al agente, Requisitos, Usar la aplicación

### Community 155 - "Hoja de ruta: Brío Analyst"
Cohesion: 0.22
Nodes (5): Changes, Etapas, Hoja de ruta: Brío Analyst, Pendientes para retomar, Siguiente paso

### Community 156 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 157 - "AgentResponse"
Cohesion: 0.12
Nodes (14): _claim(), main(), render(), Claim, ToolRun, answer_question(), test_invalid_configuration_is_a_response(), test_llm_configuration_is_checked_before_the_paths() (+6 more)

### Community 158 - "Requirement: Detalle de las evidencias"
Cohesion: 0.25
Nodes (8): Requirement: Detalle de las evidencias, Scenario: Cita sin evidencia, Scenario: Evidencia de calidad, Scenario: Evidencia de métricas, Scenario: Evidencia de un documento, Scenario: Evidencia de una búsqueda, Scenario: Fragmento sin página, Scenario: Id con varias evidencias

### Community 159 - "Decisions"
Cohesion: 0.33
Nodes (6): D8a: estrategia "plan y ejecución" con llamadas a herramientas en paralelo, D8d: proveedor Gemini, D8e: contexto de la planificación, D8i: pruebas, D8j: diferencias con lo medido y cambios en la arquitectura, Decisions

### Community 160 - "Arquitectura de Brío Analyst"
Cohesion: 0.25
Nodes (8): Arquitectura, Arquitectura de Brío Analyst, Componentes, Convenciones, Decisiones, Límites, Propósito, Requisitos transversales

### Community 162 - "Requirement: Razonamiento configurable por paso"
Cohesion: 0.25
Nodes (7): ADDED Requirements, Requirement: Razonamiento configurable por paso, Scenario: Gemini 3 con razonamiento bajo, Scenario: Modelo sin prefijo configurado, Scenario: Solo la síntesis configurada, Scenario: Valor no admitido, Spec Delta

### Community 163 - "analyst_frontend/config.py"
Cohesion: 0.25
Nodes (3): load_settings(), Settings, _timeout()

### Community 164 - "Requirement: Detalle de las evidencias"
Cohesion: 0.25
Nodes (8): Requirement: Detalle de las evidencias, Scenario: Cita sin evidencia, Scenario: Evidencia de calidad, Scenario: Evidencia de métricas, Scenario: Evidencia de un documento, Scenario: Evidencia de una búsqueda, Scenario: Fragmento sin página, Scenario: Id con varias evidencias

### Community 166 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.33
Nodes (6): Requirement: Aislamiento de la suite por defecto, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados, Scenario: Red bloqueada, Scenario: Sockets locales sin cambios

### Community 167 - "query-agent Specification"
Cohesion: 0.27
Nodes (5): Purpose, query-agent Specification, Requirement: Validación de la pregunta, Scenario: Pregunta demasiado larga, Scenario: Pregunta vacía

### Community 168 - "analytics/conftest.py"
Cohesion: 0.31
Nodes (5): layer(), real_db(), RealDatabase, _run(), _run()

### Community 169 - "Requirement: Corrección única"
Cohesion: 0.33
Nodes (6): Requirement: Corrección única, Scenario: Argumentos inválidos, Scenario: Consulta descartada y consulta fallida, Scenario: Corrección que vuelve a fallar, Scenario: Corrección sin texto de documentos, Scenario: Marca inexistente

### Community 170 - "explore_data.py"
Cohesion: 0.12
Nodes (20): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), _fmt(), load_raw(), main() (+12 more)

### Community 171 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 173 - "Requirement: Patrones de IDs en configuración"
Cohesion: 0.67
Nodes (3): Requirement: Patrones de IDs en configuración, Scenario: Código de punto de venta, Scenario: Patrón configurable

### Community 174 - "Requirement: Datos del host en el backend"
Cohesion: 0.40
Nodes (5): Requirement: Datos del host en el backend, Scenario: Configuración en la imagen, Scenario: Directorios que pasa make up, Scenario: Rutas fijas del backend, Scenario: Volúmenes de solo lectura

### Community 175 - "Requirement: Evidencias en la respuesta"
Cohesion: 0.40
Nodes (5): Requirement: Evidencias en la respuesta, Scenario: Evidencia citada por un ID principal, Scenario: Evidencia de una búsqueda, Scenario: Evidencia de una consulta de métricas, Scenario: Un ID en varios fragmentos

### Community 176 - "Requirement: Publicación atómica e idempotente"
Cohesion: 0.67
Nodes (3): Requirement: Publicación atómica e idempotente, Scenario: Doble carga, Scenario: Fallo a mitad de la carga

### Community 177 - "Requirement: Título de cada evidencia"
Cohesion: 0.40
Nodes (5): Requirement: Título de cada evidencia, Scenario: Título de un fragmento, Scenario: Título de un fragmento sin página, Scenario: Título de una búsqueda y de una consulta de calidad, Scenario: Título de una consulta de métricas

### Community 180 - "Requirement: Comprobación antes de arrancar"
Cohesion: 0.50
Nodes (4): Requirement: Comprobación antes de arrancar, Scenario: Base de documentos ausente, Scenario: Base de ventas ausente, Scenario: Modelo ausente

### Community 181 - "Requirement: Entorno Python reproducible"
Cohesion: 0.50
Nodes (4): Requirement: Entorno Python reproducible, Scenario: Bloqueo sincronizado sin red, Scenario: Dependencias directas con versión exacta, Scenario: Versión de Python fijada

### Community 182 - "Requirement: Pruebas con LLM separadas"
Cohesion: 0.50
Nodes (4): Requirement: Pruebas con LLM separadas, Scenario: Archivo de entorno inexistente, Scenario: Ninguna prueba llm registrada, Scenario: Solo pruebas llm

### Community 184 - "Requirement: Suite de pruebas sin servicios externos"
Cohesion: 0.50
Nodes (4): Requirement: Suite de pruebas sin servicios externos, Scenario: Pruebas embeddings excluidas, Scenario: Pruebas llm excluidas, Scenario: Recolección de las tres ubicaciones

### Community 185 - "Requirement: Síntesis estructurada"
Cohesion: 0.50
Nodes (4): Requirement: Síntesis estructurada, Scenario: Delimitador dentro de un fragmento, Scenario: Documentos delimitados, Scenario: Síntesis no interpretable

### Community 187 - "Requirement: Orquestación con contenedores"
Cohesion: 0.67
Nodes (3): Requirement: Orquestación con contenedores, Scenario: Configuración válida sin .env, Scenario: Servicios y conexión

### Community 188 - "Requirement: Pruebas con el modelo de embeddings separadas"
Cohesion: 0.67
Nodes (3): Requirement: Pruebas con el modelo de embeddings separadas, Scenario: Modelo no descargado, Scenario: Solo pruebas embeddings

### Community 189 - "Requirement: Página mínima del frontend"
Cohesion: 0.67
Nodes (3): Requirement: Página mínima del frontend, Scenario: Valores configurados, Scenario: Valores por defecto

### Community 190 - "Requirement: Salud del backend"
Cohesion: 0.67
Nodes (3): Requirement: Salud del backend, Scenario: Backend sano, Scenario: Ruta inexistente

### Community 191 - "Requirement: Contexto de la planificación"
Cohesion: 0.67
Nodes (3): Requirement: Contexto de la planificación, Scenario: Catálogo desde configuración, Scenario: Rango de datos real

### Community 192 - "Requirement: Evidencias en respuestas con error"
Cohesion: 0.67
Nodes (3): Requirement: Evidencias en respuestas con error, Scenario: Cuota agotada al corregir, Scenario: Cuota agotada al sintetizar

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1304 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `consultar_metrica()` connect `consultar_metrica` to `test_verify.py`, `Decisions`, `tools.py`, `QueryError`, `Tasks`, `analytics/models.py`, `ai-data-assistant`, `Hoja de ruta: Brío Analyst`, `Arquitectura de Brío Analyst`, `test_storage.py`, `test_metrics.py`, `analytics/conftest.py`, `Requirement: Corrección única`, `Proposal`, `ADDED Requirements`, `Requirements`, `open_readonly`, `calidad_datos`, `ADDED Requirements`, `build_graph`, `ADDED Requirements`, `Requirements`, `Proposal`, `QueryError`, `settings.py`, `Requirement: Corrección única`, `evidence_id`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 77 inferred relationships involving `DocumentsConfig` (e.g. with `AgentDeps` and `ToolContext`) actually correct?**
  _`DocumentsConfig` has 77 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent/evidence.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._
- **Why does `Issue` connect `rules.py` to `.action`, `pipeline.py`, `test_rules.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `evidence_id()` (e.g. with `Componentes` and `Decisiones`) actually correct?**
  _`evidence_id()` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._