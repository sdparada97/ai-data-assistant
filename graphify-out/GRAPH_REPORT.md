# Graph Report - ai-data-assistant  (2026-10-22)

## Corpus Check
- 92 files · ~76,460 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 1298 nodes · 2536 edges · 74 communities (57 shown, 17 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 291 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c4b96f55`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- Arquitectura de Brío Analyst
- ADDED Requirements
- models.py
- explore_data.py
- explore.md
- test_makefile.py
- conftest.py
- Requirements
- Exploración de datos
- catalog.py
- test_health.py
- test_app.py
- Requirements
- Decisions
- Proposal
- analyst-backend
- analyst-frontend
- Tasks
- Almena Foods | Contexto de negocio
- pipeline.py
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
- Tasks
- semantic.py
- ADDED Requirements
- Requirements
- ADDED Requirements
- Requirements
- consultar_metrica
- calidad_datos
- evidence_id
- Arquitectura de Brío Analyst
- Requirement: Estructura de las incidencias
- Design
- settings.py
- collections_abc
- Requirement: DQ01 registro_id único
- Requirement: DQ03 recorte de espacios
- metrics.py
- resolve_period
- QueryError
- Requirement: DQ04 catálogo de valores válidos
- Requirement: DQ12 aviso de precio atípico
- Requirement: DQ13 venta sin unidades
- test_quality.py
- pipeline.py
- read_sales_csv
- apply_rules
- errors.py
- data-quality Specification
- Requirement: DQ08 valores negativos
- Requirement: Filas en revisión

## God Nodes (most connected - your core abstractions)
1. `consultar_metrica()` - 43 edges
2. `calidad_datos()` - 42 edges
3. `RulesOutcome` - 38 edges
4. `ingest()` - 38 edges
5. `evidence_id()` - 33 edges
6. `QueryError` - 33 edges
7. `MetricResult` - 33 edges
8. `run()` - 32 edges
9. `apply_rules()` - 24 edges
10. `run()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Arquitectura` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py
- `Goals / Non-Goals` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Alias en el filtro` --references--> `evidence_id()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/specs/sales-metrics/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Scenario: Alias en el filtro` --references--> `evidence_id()`  [INFERRED]
  openspec/specs/sales-metrics/spec.md → backend/src/analyst_backend/analytics/evidence.py
- `Avisos de calidad` --references--> `calidad_datos()`  [INFERRED]
  openspec/changes/archive/2026-10-22-add-sales-analytics/design.md → backend/src/analyst_backend/analytics/quality.py

## Import Cycles
- None detected.

## Communities (74 total, 17 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "Arquitectura de Brío Analyst"
Cohesion: 0.09
Nodes (18): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas (+10 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "models.py"
Cohesion: 0.21
Nodes (8): Comparison, IngestionCounts, MetricCell, QualityNote, QualityQuery, RuleActionCount, SortSpec, _Strict

### Community 4 - "explore_data.py"
Cohesion: 0.16
Nodes (18): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), extract_documents(), _fmt(), load_raw() (+10 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "test_makefile.py"
Cohesion: 0.10
Nodes (17): _compose_config(), resolved(), test_config_is_valid_without_env_file(), test_defines_backend_and_frontend(), test_frontend_points_to_backend_and_depends_on_it(), test_only_backend_loads_env_file(), _declared_dependencies(), test_direct_dependencies_use_exact_versions() (+9 more)

### Community 17 - "conftest.py"
Cohesion: 0.21
Nodes (9): _blocked_connect(), _blocked_connect_ex(), _blocked_resolution(), _blocked_sendmsg(), _blocked_sendto(), env_example_variables(), _guard(), _isolate_default_suite() (+1 more)

### Community 18 - "Requirements"
Cohesion: 0.06
Nodes (32): project-layout Specification, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 19 - "Exploración de datos"
Cohesion: 0.12
Nodes (15): 01 Contexto de negocio, 03 Investigación de consumidor, 04 Observaciones de canales, 05 Reporte comercial, Aprobación de reglas, Contradicciones entre fuentes, Cómo reproducir, Documentos y afirmaciones verificables (+7 more)

### Community 20 - "catalog.py"
Cohesion: 0.19
Nodes (16): load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes(), ConfigError (+8 more)

### Community 22 - "test_app.py"
Cohesion: 0.09
Nodes (9): _FakeApp, _render(), test_cli_launches_page_with_server_options(), test_cli_rejects_malformed_options(), test_cli_without_options_uses_default_config(), test_page_shows_configured_title_and_url(), test_page_uses_defaults_without_variables(), _python_files() (+1 more)

### Community 23 - "Requirements"
Cohesion: 0.13
Nodes (15): Requirement: Destino único por fila, Requirement: DQ05 mes inválido, Requirement: DQ06 unidades faltantes, Requirement: DQ07 venta neta faltante, Requirement: DQ11 aviso de punto de venta único, Requirement: Incidencias del archivo real, Requirements, Scenario: Fila con mes inválido y venta faltante (+7 more)

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

### Community 33 - "pipeline.py"
Cohesion: 0.14
Nodes (16): apply_catalog(), _as_number(), _check_integer(), check_month(), check_negative(), check_sales(), check_sales_without_units(), check_units() (+8 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.12
Nodes (21): _by_id(), frame_of(), real_frame(), test_dq01_compares_after_trimming(), test_dq01_duplicate_with_differences(), test_dq01_real_file_identical_duplicate(), test_dq03_keeps_inner_spaces(), test_dq03_real_file_trims_region_and_channel() (+13 more)

### Community 36 - "test_storage.py"
Cohesion: 0.09
Nodes (35): compute_ingestion_id(), ingest(), IngestionSummary, _make_ingest(), _rows(), _settings(), test_columns_in_another_order_load_completely(), test_csv_without_bom_gives_same_sales() (+27 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.12
Nodes (35): RulesOutcome, _issue(), _issues(), real(), run(), test_actions_by_severity_in_real_file(), test_dq01_duplicate_with_differences_keeps_line_2_in_sales(), test_dq01_first_occurrence_invalid_keeps_id_out_of_sales() (+27 more)

### Community 38 - "Requirements"
Cohesion: 0.06
Nodes (35): Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas, Requirement: Idempotencia (+27 more)

### Community 39 - "test_metrics.py"
Cohesion: 0.09
Nodes (43): MetricResult, _by_group(), _comparison(), run(), _single(), test_alias_gives_same_rows_and_evidence(), test_brand_by_region_in_t1(), test_comparison_against_period_without_data() (+35 more)

### Community 40 - "Decisions"
Cohesion: 0.12
Nodes (16): Almacenamiento y atomicidad, Arquitectura, Configuración fuera del código, Context, Decisions, Design, DQ12: fórmula y población, El catálogo vive ya en `semantic_layer.yaml` (+8 more)

### Community 41 - ".action"
Cohesion: 0.12
Nodes (14): Contrato de `dq_issues` y `sales_review`, Requirement: Acción e impacto de cada incidencia, Requirement: Estructura de las incidencias, Scenario: Acción según el destino final, Scenario: Columnas de dq_issues, Scenario: Impacto de un valor negativo, 4. Destino de las filas, avisos y reparto de incidencias, Requirement: Acción e impacto de cada incidencia (+6 more)

### Community 42 - "ADDED Requirements"
Cohesion: 0.05
Nodes (43): ADDED Requirements, Purpose, Requirement: Destino único por fila, Requirement: DQ01 registro_id único, Requirement: DQ03 recorte de espacios, Requirement: DQ04 catálogo de valores válidos, Requirement: DQ05 mes inválido, Requirement: DQ06 unidades faltantes (+35 more)

### Community 43 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 44 - "Tasks"
Cohesion: 0.22
Nodes (8): 1. Dependencias y configuración, 2. Lectura y validación de la entrada (requisito "Validación de la entrada"), 3. Modelo de incidencias y reglas que actúan, 5. Validación final y almacenamiento, 6. Punto de entrada y pruebas de extremo a extremo, 7. Documentación, 8. Cierre, Tasks

### Community 45 - "semantic.py"
Cohesion: 0.13
Nodes (22): Dimension, _load_dimension(), _load_metric(), load_semantic_layer(), RatioMetric, SemanticLayerError, _text(), validate_expression() (+14 more)

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

### Community 50 - "consultar_metrica"
Cohesion: 0.11
Nodes (19): consultar_metrica(), MetricQuery, _run(), test_semantic_layer_change_changes_evidence(), test_ties_share_rank(), Arquitectura, Avisos de calidad, Conexión de solo lectura (+11 more)

### Community 51 - "calidad_datos"
Cohesion: 0.12
Nodes (21): calidad_datos(), Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes (+13 more)

### Community 52 - "evidence_id"
Cohesion: 0.12
Nodes (21): canonical_json(), evidence_id(), test_evidence_id_changes_with_each_input(), Requirement: Trazabilidad de los resultados, Scenario: Cambio en la capa semántica, Scenario: Consultas distintas, Scenario: Consultas equivalentes, Scenario: Evidencia de calidad_datos (+13 more)

### Community 53 - "Arquitectura de Brío Analyst"
Cohesion: 0.20
Nodes (10): Arquitectura, Arquitectura de Brío Analyst, Componentes, Convenciones, Decisiones, Grafo LangGraph, Límites, Propósito (+2 more)

### Community 54 - "Requirement: Estructura de las incidencias"
Cohesion: 0.29
Nodes (6): MODIFIED Requirements, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, Scenario: Dimensiones de una fila excluida, Scenario: Dimensión normalizada, Spec Delta

### Community 55 - "Design"
Cohesion: 0.33
Nodes (5): Context, Design, Goals / Non-Goals, Migration Plan, Risks / Trade-offs

### Community 56 - "settings.py"
Cohesion: 0.10
Nodes (19): AnalyticsSettings, IngestionSettings, load_analytics_settings(), load_ingestion_settings(), _read_paths(), _resolve(), SettingsError, layer() (+11 more)

### Community 57 - "collections_abc"
Cohesion: 0.05
Nodes (25): _check_schema(), DatabaseError, open_readonly(), published_ingestion_id(), publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files() (+17 more)

### Community 58 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 59 - "Requirement: DQ03 recorte de espacios"
Cohesion: 0.50
Nodes (4): Requirement: DQ03 recorte de espacios, Scenario: Canal con espacio del archivo real, Scenario: Espacios intermedios intactos, Scenario: Región con espacio del archivo real

### Community 60 - "metrics.py"
Cohesion: 0.14
Nodes (16): build_sql(), _comparison_cell(), make_row(), _describe(), _issue_filter(), Plan, _quality_notes(), quote_identifier() (+8 more)

### Community 61 - "resolve_period"
Cohesion: 0.19
Nodes (10): is_valid_month(), _months(), normalize_period(), resolve_period(), test_invalid_forms_list_valid_forms(), test_is_valid_month(), test_lowercase_and_spaces_are_normalised(), test_quarter() (+2 more)

### Community 62 - "QueryError"
Cohesion: 0.23
Nodes (7): build_plan(), _metric_values(), resolve_filters(), QueryError, _normalize(), SemanticLayer, test_query_error_is_structured()

### Community 63 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 64 - "Requirement: DQ12 aviso de precio atípico"
Cohesion: 0.50
Nodes (4): Requirement: DQ12 aviso de precio atípico, Scenario: Error de escala, Scenario: Sin precios atípicos en el archivo real, Scenario: Umbral leído de configuración

### Community 65 - "Requirement: DQ13 venta sin unidades"
Cohesion: 0.50
Nodes (4): Requirement: DQ13 venta sin unidades, Scenario: Sin casos en el archivo real, Scenario: Venta cero con unidades, Scenario: Venta positiva con cero unidades

### Community 66 - "test_quality.py"
Cohesion: 0.24
Nodes (11): QualityResult, _ids(), run(), test_brand_in_south(), test_corrections_listed_on_request(), test_missing_ingestion_counts_raise_instead_of_zeros(), test_period_filter_includes_invalid_months(), test_quality_evidence_is_deterministic() (+3 more)

### Community 67 - "pipeline.py"
Cohesion: 0.15
Nodes (8): IngestionError, InputError, ReconciliationError, main(), _check_header(), check_reconciliation(), parse_sales_csv(), read_csv_bytes()

### Community 68 - "read_sales_csv"
Cohesion: 0.30
Nodes (9): read_sales_csv(), test_columns_in_another_order_are_accepted(), test_extra_column_is_named(), test_header_only_is_rejected(), test_latin1_file_is_rejected(), test_missing_column_is_named(), test_missing_file_names_the_path(), test_real_file_reads_all_rows_with_physical_lines() (+1 more)

### Community 69 - "apply_rules"
Cohesion: 0.26
Nodes (8): apply_rules(), _corrected_frame(), _issues_frame(), _reason(), _review_frame(), _sales_frame(), Issue, _run()

### Community 70 - "errors.py"
Cohesion: 0.16
Nodes (5): Catalog, ValidationFailedError, _non_empty_text(), sales_schema(), validate_sales()

### Community 72 - "Requirement: DQ08 valores negativos"
Cohesion: 0.67
Nodes (3): Requirement: DQ08 valores negativos, Scenario: Cero no es negativo, Scenario: Negativos del archivo real

### Community 73 - "Requirement: Filas en revisión"
Cohesion: 0.67
Nodes (3): Requirement: Filas en revisión, Scenario: Filas retenidas del archivo real, Scenario: Varias reglas de revisión

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 581 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Issue` connect `apply_rules` to `pipeline.py`, `test_rules.py`, `.action`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `consultar_metrica()` (e.g. with `ComparisonCell` and `MetricCell`) actually correct?**
  _`consultar_metrica()` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Arquitectura de Brío Analyst` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Why does `consultar_metrica()` connect `consultar_metrica` to `Arquitectura de Brío Analyst`, `models.py`, `test_metrics.py`, `Proposal`, `ADDED Requirements`, `Requirements`, `calidad_datos`, `evidence_id`, `Arquitectura de Brío Analyst`, `collections_abc`, `metrics.py`, `QueryError`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `calidad_datos()` (e.g. with `QualityQuery` and `SemanticLayer`) actually correct?**
  _`calidad_datos()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._