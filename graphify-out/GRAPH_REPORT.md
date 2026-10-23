# Graph Report - ai-data-assistant  (2026-10-22)

## Corpus Check
- 191 files · ~180,478 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 3774 nodes · 8870 edges · 213 communities (189 shown, 24 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1482 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `96e948e7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- agent/evidence.py
- ADDED Requirements
- test_page.py
- AgentConfig
- Bases
- ADDED Requirements
- Requirements
- causal.py
- extraction.py
- explore.md
- ADDED Requirements
- contrast.py
- build_tools
- ADDED Requirements
- tools.py
- analytics/evidence.py
- conftest.py
- Requirements
- Exploración de datos
- re
- agent/config.py
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
- Requirements
- ADDED Requirements
- Requirements
- ADDED Requirements
- Requirements
- Requirement: Errores del proveedor
- ADDED Requirements
- Requirements
- ingest_documents
- Requirement: Estructura de las incidencias
- pytest
- ADDED Requirements
- re
- ADDED Requirements
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
- pdf_to_markdown
- ScriptedChatModel
- Requirement: DQ04 catálogo de valores válidos
- pathlib
- Requirements
- ADDED Requirements
- Requirements
- Proposal
- Requirement: DQ08 valores negativos
- calidad_datos
- analytics/models.py
- llm.py
- render.py
- llm.py
- test_settings.py
- Requirement: Pruebas con LLM separadas
- load_agent_settings
- ADDED Requirements
- Requirements
- Requirement: DQ01 registro_id único
- chunking.py
- Benchmark de estrategias del agente (2026-10-22)
- Proposal
- Decisions
- LLMClient
- Requirement: Documentos a cargar
- Requirement: Tablas en los fragmentos
- Proposal
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
- test_end_to_end.py
- embeddings.py
- test_compose.py
- test_verify.py
- Decisions
- graph.py
- test_markdown.py
- build_tools
- test_layout.py
- Tasks
- validate_request
- Tasks
- ADDED Requirements
- test_ask.py
- ask_backend
- Requirement: Evidencias en la respuesta
- schema.py
- Requirement: Detalle del contraste y de la evaluación causal
- DocumentsError
- EmbeddingTemplate
- .bind_tools
- ai-data-assistant
- buscar_documentos
- Decisions
- SettingsError
- ai-data-assistant
- Proposal
- agent/models.py
- collections_abc
- write_csv
- Decisiones
- Requirement: Razonamiento configurable por paso
- test_evidence.py
- analyst_frontend/config.py
- agent/conftest.py
- Requirement: Aislamiento de la suite por defecto
- Tasks
- SemanticLayer
- Requirement: Información insuficiente coherente con lo consultado
- explore_data.py
- Requirement: Verificación de citas y lenguaje
- test_models_cli.py
- Requirement: Patrones de IDs en configuración
- Requirement: Datos del host en el backend
- Requirement: Evidencias en la respuesta
- Requirement: Publicación atómica e idempotente
- cli.py
- asked
- Decisions
- Requirement: Comprobación antes de arrancar
- Requirement: Entorno Python reproducible
- Requirement: Pruebas con LLM separadas
- Requirement: Verificación de citas y lenguaje
- Requirement: Suite de pruebas sin servicios externos
- Requirement: Verificación de cifras
- project-layout Specification
- Requirement: Orquestación con contenedores
- Requirement: Pruebas con el modelo de embeddings separadas
- Requirement: Página mínima del frontend
- Requirement: Salud del backend
- Arquitectura de Brío Analyst
- Requirement: Máximo propio de las herramientas con extracción
- Requirement: Veredictos causales citados
- Requirement: Cifras citables de contraste y causalidad
- Requirement: Errores de la extracción
- Requirement: Reintento y fallo cerrado
- Requirement: Tipos de evidencia
- query-agent Specification
- Requirement: Validación de la pregunta
- Requirement: Errores del proveedor y de los datos
- Requirement: Título de cada evidencia
- Requirement: Síntesis estructurada
- Requirement: Evidencias en respuestas con error

## God Nodes (most connected - your core abstractions)
1. `AgentConfig` - 144 edges
2. `Bases` - 125 edges
3. `evidence_id()` - 100 edges
4. `DocumentsConfig` - 91 edges
5. `consultar_metrica()` - 89 edges
6. `SemanticLayer` - 83 edges
7. `make_deps()` - 75 edges
8. `run_graph()` - 66 edges
9. `QueryError` - 65 edges
10. `plan_message()` - 61 edges

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

## Communities (213 total, 24 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "agent/evidence.py"
Cohesion: 0.10
Nodes (25): causal_figures(), causal_title(), contrast_figures(), contrast_title(), evidence_items(), evidence_views(), figures(), _filters() (+17 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "test_page.py"
Cohesion: 0.19
Nodes (36): answer(), claim(), _comparison(), evidence_expanders(), joined(), labels(), page(), send() (+28 more)

### Community 4 - "AgentConfig"
Cohesion: 0.15
Nodes (55): AgentConfig, run_graph(), make_deps(), plan_message(), max_three(), metric(), _repair_messages(), _synthesis_prompt() (+47 more)

### Community 5 - "Bases"
Cohesion: 0.10
Nodes (49): DataRange, ClaimExtraction, Bases, check(), claim(), dates(), document(), most_affected() (+41 more)

### Community 6 - "ADDED Requirements"
Cohesion: 0.04
Nodes (45): ADDED Requirements, Purpose, Requirement: Criterio de diseño de la evidencia, Requirement: Criterio de explicaciones alternativas, Requirement: Criterio de localización, Requirement: Criterio de temporalidad, Requirement: Criterio del grupo de comparación, Requirement: Dimensiones de la evaluación (+37 more)

### Community 7 - "Requirements"
Cohesion: 0.04
Nodes (45): causal-assessment Specification, Purpose, Requirement: Criterio de diseño de la evidencia, Requirement: Criterio de explicaciones alternativas, Requirement: Criterio de localización, Requirement: Criterio de temporalidad, Requirement: Criterio del grupo de comparación, Requirement: Dimensiones de la evaluación (+37 more)

### Community 8 - "causal.py"
Cohesion: 0.11
Nodes (29): _alternatives(), assess_cause(), beyond(), _by_group(), CausalRequest, CausalThresholds, check_effect(), _comparison() (+21 more)

### Community 9 - "extraction.py"
Cohesion: 0.09
Nodes (36): ContrastConfig, ClaimValidation, contains(), _describe(), _Discard, Document, evidence_ref(), ExtractedClaim (+28 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "ADDED Requirements"
Cohesion: 0.10
Nodes (20): ADDED Requirements, Purpose, Requirement: Clave nunca expuesta, Requirement: Errores del proveedor, Requirement: Fallos que no son del proveedor, Requirement: Parámetros del modelo en configuración, Requirement: Selección del proveedor, Scenario: Clave ausente (+12 more)

### Community 12 - "contrast.py"
Cohesion: 0.22
Nodes (10): _compare(), compare_claims(), _key(), _query(), _sign(), _var_pct(), variation_verdict(), ClaimComparison (+2 more)

### Community 13 - "build_tools"
Cohesion: 0.10
Nodes (17): _blocks(), CauseSearch, extract_claims(), extract_observations(), _fragment(), llm_extractor(), load_document(), _messages() (+9 more)

### Community 14 - "ADDED Requirements"
Cohesion: 0.05
Nodes (41): ADDED Requirements, Purpose, Requirement: Afirmaciones cualitativas, Requirement: Contraste de un documento, Requirement: Enunciado generado en código, Requirement: Extracción con esquema cerrado, Requirement: ID de evidencia tomado del fragmento, Requirement: Períodos y métrica anclados en el texto (+33 more)

### Community 15 - "tools.py"
Cohesion: 0.15
Nodes (18): _as_list(), _as_list_values(), causal_summary(), CausalToolInput, _cells(), contrast_summary(), ContrastToolInput, document_summary() (+10 more)

### Community 16 - "analytics/evidence.py"
Cohesion: 0.21
Nodes (6): canonical_json(), causal_evidence_id(), contrast_evidence_id(), test_causal_id_changes_with_search_mode(), test_contrast_id_changes_with_threshold_document_or_claims(), test_same_contrast_same_id()

### Community 17 - "conftest.py"
Cohesion: 0.21
Nodes (9): _blocked_connect(), _blocked_connect_ex(), _blocked_resolution(), _blocked_sendmsg(), _blocked_sendto(), env_example_variables(), _guard(), _isolate_default_suite() (+1 more)

### Community 18 - "Requirements"
Cohesion: 0.20
Nodes (10): Requirement: Evaluación reservada, Requirement: Puertos solo en la máquina local, Requirement: Tiempo de espera de la interfaz en contenedores, Requirement: Ubicación del código fuente, Requirements, Scenario: Evaluación no implementada, Scenario: Paquetes importables desde su ubicación, Scenario: Puertos locales (+2 more)

### Community 19 - "Exploración de datos"
Cohesion: 0.12
Nodes (16): 01 Contexto de negocio, 03 Investigación de consumidor, 04 Observaciones de canales, 05 Reporte comercial, Aprobación de reglas, Contradicciones entre fuentes, Cómo reproducir, Documentos y afirmaciones verificables (+8 more)

### Community 20 - "re"
Cohesion: 0.26
Nodes (9): ask(), _cited(), _contrast_ids(), _report_ids(), _sales_ids(), test_largest_drop_with_gemini(), test_promotions_with_gemini(), test_report_conclusions_with_gemini() (+1 more)

### Community 21 - "agent/config.py"
Cohesion: 0.09
Nodes (21): AgentConfigError, CausalConfig, GeminiConfig, LimitsConfig, load_agent_config(), _non_blank_items(), ProviderConfig, _Strict (+13 more)

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
Cohesion: 0.11
Nodes (23): apply_rules(), _issues_frame(), _reason(), _review_frame(), _sales_frame(), apply_catalog(), _as_number(), _check_integer() (+15 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.12
Nodes (20): frame_of(), real_frame(), test_dq01_compares_after_trimming(), test_dq01_duplicate_with_differences(), test_dq01_real_file_identical_duplicate(), test_dq03_keeps_inner_spaces(), test_dq03_real_file_trims_region_and_channel(), test_dq04_catalog_comes_from_configuration() (+12 more)

### Community 36 - "test_storage.py"
Cohesion: 0.16
Nodes (20): IngestionSummary, con(), previous_db(), real_db(), _settings(), _sha(), test_broken_reconciliation_stops_the_load(), test_dq_issues_columns_and_details() (+12 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.12
Nodes (35): RulesOutcome, _issue(), _issues(), real(), run(), test_actions_by_severity_in_real_file(), test_dq01_duplicate_with_differences_keeps_line_2_in_sales(), test_dq01_first_occurrence_invalid_keeps_id_out_of_sales() (+27 more)

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
Cohesion: 0.16
Nodes (18): Catalog, load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes() (+10 more)

### Community 45 - "Requirements"
Cohesion: 0.05
Nodes (41): Purpose, report-contrast Specification, Requirement: Afirmaciones cualitativas, Requirement: Contraste de un documento, Requirement: Enunciado generado en código, Requirement: Extracción con esquema cerrado, Requirement: ID de evidencia tomado del fragmento, Requirement: Períodos y métrica anclados en el texto (+33 more)

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
Cohesion: 0.13
Nodes (20): ingest_documents(), DocumentsSettings, real_documents(), documents_settings(), _copy_raw(), _empty_pdf(), _rows(), test_double_load_is_identical() (+12 more)

### Community 54 - "Requirement: Estructura de las incidencias"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada, Spec Delta

### Community 55 - "pytest"
Cohesion: 0.13
Nodes (11): rrf_fuse(), test_chunk_without_word_match_counts_only_similarity(), test_query_requires_the_config_in_context(), test_rrf_fusion_of_two_rankings(), test_dns_resolution_fails_with_explicit_error(), test_embeddings_tests_keep_only_models_cache_dir(), test_env_example_variables_are_hidden(), test_local_unix_sockets_keep_native_behaviour() (+3 more)

### Community 56 - "ADDED Requirements"
Cohesion: 0.04
Nodes (45): ADDED Requirements, Purpose, Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Contexto de la planificación, Requirement: Errores del proveedor y de los datos, Requirement: Evidencia válida y avisos, Requirement: Reintento y fallo cerrado (+37 more)

### Community 57 - "re"
Cohesion: 0.14
Nodes (15): Consulted, _contains_phrase(), drop_failing(), figures_in(), _plain(), _pool(), Problem, _readings() (+7 more)

### Community 58 - "ADDED Requirements"
Cohesion: 0.06
Nodes (34): ADDED Requirements, Requirement: Cifras citables de contraste y causalidad, Requirement: Consultas conservadas ante un fallo en una herramienta, Requirement: Errores de la extracción, Requirement: Información insuficiente coherente con lo consultado, Requirement: Máximo propio de las herramientas con extracción, Requirement: Preguntas guía con el modelo real, Requirement: Tipos de evidencia (+26 more)

### Community 59 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.12
Nodes (16): ADDED Requirements, MODIFIED Requirements, Requirement: Aislamiento de la suite por defecto, Requirement: Pruebas con el modelo de embeddings separadas, Requirement: Suite de pruebas sin servicios externos, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados (+8 more)

### Community 60 - "consultar_metrica"
Cohesion: 0.04
Nodes (57): consultar_metrica(), metric(), _run(), MODIFIED Requirements, Requirement: Consultas fallidas sin resolver, Requirement: Evidencias en la respuesta, Requirement: Planificación en una sola respuesta, Scenario: Consultas por encima del máximo (+49 more)

### Community 61 - "pathlib"
Cohesion: 0.23
Nodes (6): config(), config_path_real(), fake_config(), fake_config_path(), fake_db(), write_config()

### Community 62 - "ADDED Requirements"
Cohesion: 0.06
Nodes (30): ADDED Requirements, Purpose, Requirement: API inaccesible, Requirement: Historial de la sesión, Requirement: Mensajes de estado y de error, Requirement: Pregunta en curso, Requirement: Pregunta y respuesta por apartados, Requirement: Respuesta no reconocible (+22 more)

### Community 63 - "Requirements"
Cohesion: 0.06
Nodes (34): analyst-ui Specification, Purpose, Requirement: API inaccesible, Requirement: Detalle del contraste y de la evaluación causal, Requirement: Historial de la sesión, Requirement: Mensajes de estado y de error, Requirement: Pregunta en curso, Requirement: Pregunta y respuesta por apartados (+26 more)

### Community 64 - "test_chunking.py"
Cohesion: 0.14
Nodes (27): Chunk, _by_primary(), _chunk_all(), chunks(), _md(), test_configurable_patterns(), test_document_with_only_headings_fails(), test_empty_section_is_discarded() (+19 more)

### Community 65 - "build_graph"
Cohesion: 0.08
Nodes (34): index(), build_graph(), check_question(), collect(), execute(), limit_of(), load_context(), plan() (+26 more)

### Community 66 - "test_quality.py"
Cohesion: 0.20
Nodes (13): QualityResult, _ids(), run(), _run(), test_brand_in_south(), test_corrections_listed_on_request(), test_missing_ingestion_counts_raise_instead_of_zeros(), test_period_filter_includes_invalid_months() (+5 more)

### Community 67 - "DocumentsConfig"
Cohesion: 0.13
Nodes (42): DocumentsConfig, DocumentsSummary, DocumentResult, fake_embedder(), _codes(), _error_fields(), _ids_and_scores(), _lexical() (+34 more)

### Community 68 - "read_sales_csv"
Cohesion: 0.11
Nodes (18): IngestionError, InputError, ReconciliationError, main(), _check_header(), check_reconciliation(), _corrected_frame(), parse_sales_csv() (+10 more)

### Community 69 - "pdf_to_markdown"
Cohesion: 0.10
Nodes (9): collapse_spaces(), _docx_table_rows(), _Line, markdown_table(), _page_lines(), pdf_to_markdown(), _table_cells(), _table_rows() (+1 more)

### Community 70 - "ScriptedChatModel"
Cohesion: 0.08
Nodes (29): Claim, promotions_extraction(), report_extraction(), variation(), json_message(), scripted(), ScriptedChatModel, tool_call() (+21 more)

### Community 71 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 72 - "pathlib"
Cohesion: 0.08
Nodes (24): load_documents_config(), DocumentsConfigError, SourceError, documents_ingestion_id(), _file_sha256(), list_documents(), _ddl(), LoadedDocument (+16 more)

### Community 73 - "Requirements"
Cohesion: 0.10
Nodes (20): Requirement: Argumentos tolerantes, Requirement: Comando de consulta, Requirement: Consultas conservadas ante un fallo en una herramienta, Requirement: Evidencia válida y avisos, Requirement: Preguntas guía con el modelo real, Requirement: Sin evidencia, sin síntesis, Requirement: Traza por pregunta, Requirement: Títulos de contraste y causalidad (+12 more)

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

### Community 78 - "calidad_datos"
Cohesion: 0.09
Nodes (27): calidad_datos(), Requirement: Herramientas del agente, Scenario: Contraste del reporte, Scenario: Herramientas ofrecidas al plan, Capabilities, Fuera de alcance, Impact, Modified Capabilities (+19 more)

### Community 79 - "analytics/models.py"
Cohesion: 0.07
Nodes (37): published_ingestion_id(), build_plan(), build_sql(), _comparison_cell(), make_row(), _describe(), _issue_filter(), _metric_values() (+29 more)

### Community 80 - "llm.py"
Cohesion: 0.22
Nodes (3): _error_code(), _is_retryable(), make_rate_limiter()

### Community 81 - "render.py"
Cohesion: 0.18
Nodes (17): AskOutcome, _contrast_table(), _criteria_table(), _discarded_table(), escape_label(), _filters_text(), _metric_table(), _periods_text() (+9 more)

### Community 82 - "llm.py"
Cohesion: 0.26
Nodes (8): build_chat_model(), build_llm_client(), LLMSettings, _chat_models(), test_no_synthesis_reasoning_for_other_models(), test_reasoning_per_step_from_configuration(), test_synthesis_reasoning_without_plan_reasoning(), test_temperature_by_model_family()

### Community 83 - "test_settings.py"
Cohesion: 0.18
Nodes (11): load_ingestion_settings(), test_absolute_paths_are_kept(), test_agent_missing_variable_is_named(), test_agent_settings_read_six_paths(), test_analytics_settings_read_two_paths(), test_blank_variable_counts_as_missing(), test_documents_missing_variable_is_named(), test_documents_settings_read_four_paths() (+3 more)

### Community 84 - "Requirement: Pruebas con LLM separadas"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Pruebas con LLM separadas, Scenario: Archivo de entorno inexistente, Scenario: Ninguna prueba llm registrada, Scenario: Solo pruebas llm, Spec Delta

### Community 85 - "load_agent_settings"
Cohesion: 0.22
Nodes (10): AgentSettings, AnalyticsSettings, load_agent_settings(), load_analytics_settings(), load_models_settings(), ModelsSettings, _read_paths(), _resolve() (+2 more)

### Community 86 - "ADDED Requirements"
Cohesion: 0.25
Nodes (8): ADDED Requirements, Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Tablas de PDF, Scenario: Caché con otra huella, Scenario: Celda de varias líneas, Scenario: Error desde make, Scenario: Tabla de PDF sin bordes

### Community 87 - "Requirements"
Cohesion: 0.25
Nodes (8): Requirement: Comando de ingesta de documentos, Requirement: Descarga del modelo, Requirement: Patrones de IDs en configuración, Requirements, Scenario: Caché con otra huella, Scenario: Código de punto de venta, Scenario: Error desde make, Scenario: Patrón configurable

### Community 88 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 89 - "chunking.py"
Cohesion: 0.20
Nodes (13): _blocks(), _cells(), chunk_markdown(), open_draft(), starting_id(), _Draft, _is_code(), _is_table() (+5 more)

### Community 90 - "Benchmark de estrategias del agente (2026-10-22)"
Cohesion: 0.33
Nodes (5): Benchmark de estrategias del agente (2026-10-22), Estrategias, Preguntas, Resultados: Gemini (capa gratuita, Gemini 3 Flash), Resultados: modelos locales (Ollama, 190 ejecuciones)

### Community 91 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 92 - "Decisions"
Cohesion: 0.17
Nodes (11): Context, D10d: veredictos y criterios (`agent.yaml`: `contrast` y `causal`), D10f: prompts, D10g: interfaz, D10h: pruebas, D10i: documentación, Decisions, Design (+3 more)

### Community 93 - "LLMClient"
Cohesion: 0.23
Nodes (3): LLMClient, D9g: ajustes tras la prueba manual (2026-10-22), 4. Contenedores y `make up`

### Community 94 - "Requirement: Documentos a cargar"
Cohesion: 0.33
Nodes (6): Requirement: Documentos a cargar, Scenario: Archivo dañado, Scenario: Archivos que se ignoran, Scenario: Directorio real, Scenario: doc_id duplicado, Scenario: Sin documentos válidos

### Community 95 - "Requirement: Tablas en los fragmentos"
Cohesion: 0.33
Nodes (6): Requirement: Tablas en los fragmentos, Scenario: ID repetido en una tabla, Scenario: Registros de campo, Scenario: Tabla con IDs ya divididos, Scenario: Tabla sin IDs, Scenario: Índice de referencias

### Community 96 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

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
Cohesion: 0.18
Nodes (11): _client(), config(), _failing(), test_key_never_exposed_in_provider_errors(), test_persistent_unavailability(), test_programming_errors_are_not_provider_errors(), test_quota_exhausted_is_not_retried(), test_rejected_key_is_not_retried() (+3 more)

### Community 127 - "evidence_id"
Cohesion: 0.04
Nodes (65): evidence_id(), test_evidence_id_changes_with_each_input(), Requirement: Avisos y traza, Requirement: Detalle de las evidencias, Scenario: Aviso de período sin datos, Scenario: Cita sin evidencia, Scenario: Evidencia de calidad, Scenario: Evidencia de métricas (+57 more)

### Community 128 - "test_end_to_end.py"
Cohesion: 0.17
Nodes (17): compute_ingestion_id(), ingest(), IngestionSettings, bases(), test_ties_share_rank(), _make_ingest(), _rows(), _settings() (+9 more)

### Community 129 - "embeddings.py"
Cohesion: 0.08
Nodes (20): ModelConfig, cached_model_file(), check_embedder(), Embedder, FailingEmbedder, FakeEmbedder, FastEmbedEmbedder, file_sha256() (+12 more)

### Community 130 - "test_compose.py"
Cohesion: 0.07
Nodes (33): test_empty_key(), test_missing_directory_fails_with_its_path_even_without_model(), _compose_config(), interpolated(), _interpolated(), _mounts(), resolved(), test_backend_mounts_host_data_read_only() (+25 more)

### Community 131 - "test_verify.py"
Cohesion: 0.10
Nodes (37): Synthesis, check(), fact(), _hits(), hypothesis(), _insufficient(), run_evidence(), test_absence_through_an_internal_query() (+29 more)

### Community 132 - "Decisions"
Cohesion: 0.11
Nodes (17): Arquitectura, Avisos de calidad, Conexión de solo lectura, Context, Decisions, Design, Evidencia y trazabilidad, Generación de SQL (+9 more)

### Community 134 - "graph.py"
Cohesion: 0.10
Nodes (15): metric_has_values(), AgentState, _discarded_warning(), _error_detail(), _failure_notes(), claim_extraction_prompt(), evidence_block(), hedge_examples() (+7 more)

### Community 135 - "test_markdown.py"
Cohesion: 0.15
Nodes (18): ConversionError, docx_to_markdown(), to_markdown(), SourceFile, _pdf(), test_damaged_file_names_the_file(), test_every_supported_extension_has_a_converter(), test_line_repeated_on_a_single_page_is_kept() (+10 more)

### Community 136 - "build_tools"
Cohesion: 0.12
Nodes (21): format_tool_error(), _validation_details(), ToolContext, _call(), _run_tool_node(), test_causal_assessment_of_promotions(), test_contrast_of_the_report(), test_discarded_claims_are_not_a_plan_error() (+13 more)

### Community 138 - "Tasks"
Cohesion: 0.25
Nodes (7): 2. Contraste (lógica pura), 3. Evaluación causal (lógica pura), 6. Interfaz, 7. Pruebas con Gemini y documentación, 8. Cierre, Tasks, Workflow follow-up

### Community 140 - "Tasks"
Cohesion: 0.20
Nodes (9): 1. Dependencias y configuración, 2. Dimensiones en dq_issues (requisito MODIFIED "Estructura de las incidencias"), 3. Capa semántica, 4. Modelos, conexión y evidencia, 5. consultar_metrica, 6. calidad_datos, 7. Documentación, 8. Cierre (+1 more)

### Community 141 - "ADDED Requirements"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Requirement: Comprobación antes de arrancar, Requirement: Datos del host en el backend, Requirement: Puertos solo en la máquina local, Requirement: Tiempo de espera de la interfaz en contenedores, Scenario: Base de documentos ausente, Scenario: Base de ventas ausente, Scenario: Configuración en la imagen (+7 more)

### Community 142 - "test_ask.py"
Cohesion: 0.13
Nodes (16): test_request_rate_limit(), ask(), client_for(), test_blank_question_is_422_with_agent_body(), test_dependencies_are_built_once(), test_documents_database_missing(), test_exception_outside_the_nodes(), test_failure_in_the_api_outside_the_agent() (+8 more)

### Community 143 - "ask_backend"
Cohesion: 0.15
Nodes (9): ask_backend(), _is_agent_response(), test_agent_response_with_any_status(), handler(), test_backend_timeout_setting(), test_connection_failures_are_unreachable(), test_plain_text_500_is_unrecognized(), test_read_timeout() (+1 more)

### Community 144 - "Requirement: Evidencias en la respuesta"
Cohesion: 0.12
Nodes (15): ADDED Requirements, Requirement: Evidencias en la respuesta, Requirement: Evidencias en respuestas con error, Requirement: Título de cada evidencia, Scenario: Cuota agotada al corregir, Scenario: Cuota agotada al sintetizar, Scenario: Evidencia citada por un ID principal, Scenario: Evidencia de una búsqueda (+7 more)

### Community 145 - "schema.py"
Cohesion: 0.23
Nodes (5): ValidationFailedError, _non_empty_text(), sales_schema(), validate_sales(), test_pandera_names_the_failing_column()

### Community 146 - "Requirement: Detalle del contraste y de la evaluación causal"
Cohesion: 0.29
Nodes (6): ADDED Requirements, Requirement: Detalle del contraste y de la evaluación causal, Scenario: Afirmación descartada, Scenario: Criterios causales, Scenario: Tabla del contraste, Spec Delta

### Community 147 - "DocumentsError"
Cohesion: 0.32
Nodes (3): DocumentsError, main(), load_documents_settings()

### Community 148 - "EmbeddingTemplate"
Cohesion: 0.17
Nodes (6): _check_regex(), EmbeddingTemplate, PdfConfig, _Strict, embedding_text(), test_embedding_text_uses_title_and_section()

### Community 149 - ".bind_tools"
Cohesion: 0.21
Nodes (8): Grafo LangGraph, Context, D8d: proveedor Gemini, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs, 2. Proveedor de LLM

### Community 150 - "ai-data-assistant"
Cohesion: 0.25
Nodes (8): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas

### Community 152 - "buscar_documentos"
Cohesion: 0.07
Nodes (27): _config(), DocumentHit, DocumentQuery, SearchWarning, _Strict, buscar_documentos(), _check_filters(), _cosine() (+19 more)

### Community 153 - "Decisions"
Cohesion: 0.20
Nodes (9): Context, D9c: interfaz Streamlit en tres módulos, D9d: contenedores con datos del host, D9f: documentación, Decisions, Design, Goals / Non-Goals, Migration Plan (+1 more)

### Community 154 - "SettingsError"
Cohesion: 0.31
Nodes (6): load_llm_settings(), SettingsError, test_missing_key(), test_missing_provider(), test_unsupported_provider(), test_llm_settings_keep_the_key_secret()

### Community 155 - "ai-data-assistant"
Cohesion: 0.25
Nodes (8): ai-data-assistant, Comandos, Consultar la base desde Python, Estructura, Instalación, Preguntar al agente, Requisitos, Usar la aplicación

### Community 156 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 157 - "agent/models.py"
Cohesion: 0.06
Nodes (32): _claim(), main(), render(), AgentDeps, AgentResponse, ToolRun, Trace, answer_question() (+24 more)

### Community 158 - "collections_abc"
Cohesion: 0.06
Nodes (27): _check_schema(), open_readonly(), publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files(), write_tables(), _sha() (+19 more)

### Community 159 - "write_csv"
Cohesion: 0.20
Nodes (5): paths(), Paths, valid_row(), write_csv(), _frame()

### Community 160 - "Decisiones"
Cohesion: 0.33
Nodes (3): Arquitectura, Decisiones, Límites

### Community 162 - "Requirement: Razonamiento configurable por paso"
Cohesion: 0.25
Nodes (7): ADDED Requirements, Requirement: Razonamiento configurable por paso, Scenario: Gemini 3 con razonamiento bajo, Scenario: Modelo sin prefijo configurado, Scenario: Solo la síntesis configurada, Scenario: Valor no admitido, Spec Delta

### Community 163 - "test_evidence.py"
Cohesion: 0.39
Nodes (6): _artifact(), test_fragment_title(), test_fragment_without_page_title(), test_metric_query_title(), test_search_and_quality_titles(), _titles()

### Community 164 - "analyst_frontend/config.py"
Cohesion: 0.33
Nodes (3): load_settings(), Settings, _timeout()

### Community 165 - "agent/conftest.py"
Cohesion: 0.18
Nodes (6): agent_config(), fake_embedder(), _no_extraction(), tool_context(), test_promotions_with_the_test_search(), run()

### Community 166 - "Requirement: Aislamiento de la suite por defecto"
Cohesion: 0.33
Nodes (6): Requirement: Aislamiento de la suite por defecto, Scenario: Caché de modelos en pruebas embeddings, Scenario: Credenciales ausentes, Scenario: DNS y envío UDP bloqueados, Scenario: Red bloqueada, Scenario: Sockets locales sin cambios

### Community 167 - "Tasks"
Cohesion: 0.33
Nodes (5): 3. Interfaz del analista, 5. Documentación, 6. Cierre, Tasks, Workflow follow-up

### Community 168 - "SemanticLayer"
Cohesion: 0.05
Nodes (78): build_planning_context(), catalog_text(), data_range(), _document_rows(), PlanningContext, cause_kind_rules(), planning_system_prompt(), is_valid_month() (+70 more)

### Community 169 - "Requirement: Información insuficiente coherente con lo consultado"
Cohesion: 0.33
Nodes (6): Requirement: Información insuficiente coherente con lo consultado, Scenario: Inventarios por región, Scenario: Precios de la competencia, Scenario: Ventas de la competencia consultadas, Scenario: Ventas por región consultadas, Scenario: Ventas por región sin consultar

### Community 170 - "explore_data.py"
Cohesion: 0.16
Nodes (18): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), extract_documents(), _fmt(), load_raw() (+10 more)

### Community 171 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 172 - "test_models_cli.py"
Cohesion: 0.46
Nodes (4): _fake_cached_model(), _make(), test_cache_with_other_fingerprint_fails_without_downloading(), test_check_without_model_points_to_make_models()

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

### Community 177 - "cli.py"
Cohesion: 0.39
Nodes (3): _coerce(), main(), parse_config()

### Community 179 - "Decisions"
Cohesion: 0.22
Nodes (6): D8a: estrategia "plan y ejecución" con llamadas a herramientas en paralelo, D8e: contexto de la planificación, D8f: verificación por afirmación, D8h: configuración, D8j: diferencias con lo medido y cambios en la arquitectura, Decisions

### Community 180 - "Requirement: Comprobación antes de arrancar"
Cohesion: 0.50
Nodes (4): Requirement: Comprobación antes de arrancar, Scenario: Base de documentos ausente, Scenario: Base de ventas ausente, Scenario: Modelo ausente

### Community 181 - "Requirement: Entorno Python reproducible"
Cohesion: 0.50
Nodes (4): Requirement: Entorno Python reproducible, Scenario: Bloqueo sincronizado sin red, Scenario: Dependencias directas con versión exacta, Scenario: Versión de Python fijada

### Community 182 - "Requirement: Pruebas con LLM separadas"
Cohesion: 0.50
Nodes (4): Requirement: Pruebas con LLM separadas, Scenario: Archivo de entorno inexistente, Scenario: Ninguna prueba llm registrada, Scenario: Solo pruebas llm

### Community 183 - "Requirement: Verificación de citas y lenguaje"
Cohesion: 0.40
Nodes (5): Requirement: Verificación de citas y lenguaje, Scenario: Cita inexistente, Scenario: Hipótesis sin atenuar, Scenario: ID citado dentro de un fragmento, Scenario: Lenguaje causal en un hecho

### Community 184 - "Requirement: Suite de pruebas sin servicios externos"
Cohesion: 0.50
Nodes (4): Requirement: Suite de pruebas sin servicios externos, Scenario: Pruebas embeddings excluidas, Scenario: Pruebas llm excluidas, Scenario: Recolección de las tres ubicaciones

### Community 185 - "Requirement: Verificación de cifras"
Cohesion: 0.25
Nodes (8): Requirement: Verificación de cifras, Scenario: Caída expresada sin signo, Scenario: Cifra citada con un fragmento que no la contiene, Scenario: Cifra de cuatro dígitos sin respaldo, Scenario: Cifra del reporte citada con su fragmento, Scenario: Cifra del reporte presentada como dato de ventas, Scenario: Cifra junto al nombre de un documento, Scenario: Nombre de documento en la afirmación

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

### Community 191 - "Arquitectura de Brío Analyst"
Cohesion: 0.33
Nodes (6): Arquitectura de Brío Analyst, Componentes, Convenciones, Propósito, Pruebas, Requisitos transversales

### Community 192 - "Requirement: Máximo propio de las herramientas con extracción"
Cohesion: 0.40
Nodes (5): Requirement: Máximo propio de las herramientas con extracción, Scenario: Documento inexistente corregido, Scenario: Dos contrastes pedidos, Scenario: Evaluación sin efecto corregida, Scenario: Extracción fallida y corrección

### Community 193 - "Requirement: Veredictos causales citados"
Cohesion: 0.50
Nodes (4): Requirement: Veredictos causales citados, Scenario: Causa descrita con su veredicto, Scenario: Léxico causal sin veredicto, Scenario: Veredicto alterado

### Community 194 - "Requirement: Cifras citables de contraste y causalidad"
Cohesion: 0.67
Nodes (3): Requirement: Cifras citables de contraste y causalidad, Scenario: Cifra de una afirmación descartada, Scenario: Cifra del contraste citada

### Community 195 - "Requirement: Errores de la extracción"
Cohesion: 0.67
Nodes (3): Requirement: Errores de la extracción, Scenario: Afirmación descartada no es un error del plan, Scenario: Error sin texto del documento

### Community 196 - "Requirement: Reintento y fallo cerrado"
Cohesion: 0.67
Nodes (3): Requirement: Reintento y fallo cerrado, Scenario: Corrección tras el reintento, Scenario: Fallo cerrado

### Community 197 - "Requirement: Tipos de evidencia"
Cohesion: 0.67
Nodes (3): Requirement: Tipos de evidencia, Scenario: Evidencia de una evaluación causal, Scenario: Evidencias de un contraste

### Community 198 - "query-agent Specification"
Cohesion: 0.27
Nodes (5): Purpose, query-agent Specification, Requirement: Contexto de la planificación, Scenario: Catálogo desde configuración, Scenario: Rango de datos real

### Community 199 - "Requirement: Validación de la pregunta"
Cohesion: 0.67
Nodes (3): Requirement: Validación de la pregunta, Scenario: Pregunta demasiado larga, Scenario: Pregunta vacía

### Community 200 - "Requirement: Errores del proveedor y de los datos"
Cohesion: 0.33
Nodes (6): Requirement: Errores del proveedor y de los datos, Scenario: Base de ventas ausente, Scenario: Clave fuera de la traza, Scenario: Cuota agotada al planificar, Scenario: Cuota agotada al sintetizar, Scenario: Fallo interno

### Community 203 - "Requirement: Título de cada evidencia"
Cohesion: 0.40
Nodes (5): Requirement: Título de cada evidencia, Scenario: Título de un fragmento, Scenario: Título de un fragmento sin página, Scenario: Título de una búsqueda y de una consulta de calidad, Scenario: Título de una consulta de métricas

### Community 207 - "Requirement: Síntesis estructurada"
Cohesion: 0.50
Nodes (4): Requirement: Síntesis estructurada, Scenario: Delimitador dentro de un fragmento, Scenario: Documentos delimitados, Scenario: Síntesis no interpretable

### Community 211 - "Requirement: Evidencias en respuestas con error"
Cohesion: 0.67
Nodes (3): Requirement: Evidencias en respuestas con error, Scenario: Cuota agotada al corregir, Scenario: Cuota agotada al sintetizar

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1581 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `consultar_metrica()` connect `consultar_metrica` to `test_end_to_end.py`, `test_verify.py`, `Decisions`, `ADDED Requirements`, `Requirements`, `causal.py`, `contrast.py`, `build_tools`, `ADDED Requirements`, `tools.py`, `Tasks`, `ai-data-assistant`, `collections_abc`, `Decisiones`, `test_metrics.py`, `SemanticLayer`, `Proposal`, `Requirements`, `ADDED Requirements`, `Requirements`, `Arquitectura de Brío Analyst`, `build_graph`, `ADDED Requirements`, `Requirements`, `Proposal`, `calidad_datos`, `analytics/models.py`, `Decisions`, `Proposal`, `evidence_id`?**
  _High betweenness centrality (0.166) - this node is a cross-community bridge._
- **Are the 138 inferred relationships involving `AgentConfig` (e.g. with `build_chat_model()` and `build_llm_client()`) actually correct?**
  _`AgentConfig` has 138 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `agent/evidence.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09966777408637874 - nodes in this community are weakly interconnected._
- **Why does `evidence_id()` connect `evidence_id` to `agent/evidence.py`, `Decisions`, `graph.py`, `causal.py`, `Tasks`, `tools.py`, `analytics/evidence.py`, `buscar_documentos`, `Decisions`, `collections_abc`, `Decisiones`, `Requirement: Verificación de citas y lenguaje`, `ADDED Requirements`, `Requirements`, `Decisions`, `Requirement: Verificación de citas y lenguaje`, `ADDED Requirements`, `ADDED Requirements`, `consultar_metrica`, `Arquitectura de Brío Analyst`, `build_graph`, `Requirement: Cifras citables de contraste y causalidad`, `pathlib`, `Requirements`, `calidad_datos`, `analytics/models.py`, `Proposal`, `Decisions`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 115 inferred relationships involving `Bases` (e.g. with `test_catalog_comes_from_configuration()` and `test_planning_prompt_lists_catalog_documents_and_period_rule()`) actually correct?**
  _`Bases` has 115 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._