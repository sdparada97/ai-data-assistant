# Graph Report - ai-data-assistant  (2026-10-21)

## Corpus Check
- 69 files · ~60,723 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 874 nodes · 1538 edges · 56 communities (39 shown, 17 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `713b1d4e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- Arquitectura de Brío Analyst
- ADDED Requirements
- pytest
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
- test_end_to_end.py
- Decisions
- .action
- ADDED Requirements
- Proposal
- Tasks
- Requirement: DQ01 registro_id único
- Requirement: DQ03 recorte de espacios
- Requirement: DQ04 catálogo de valores válidos
- Requirement: DQ12 aviso de precio atípico
- Requirement: DQ13 venta sin unidades
- Spec Delta
- Requirement: Acción e impacto de cada incidencia
- Requirement: DQ05 mes inválido
- pathlib
- Requirement: DQ08 valores negativos
- Requirement: Filas en revisión

## God Nodes (most connected - your core abstractions)
1. `RulesOutcome` - 38 edges
2. `ingest()` - 36 edges
3. `apply_rules()` - 24 edges
4. `run()` - 24 edges
5. `read_sales_csv()` - 19 edges
6. `load_catalog()` - 16 edges
7. `ADDED Requirements` - 16 edges
8. `Requirements` - 16 edges
9. `InputError` - 15 edges
10. `load_ingestion_settings()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `main()` --uses--> `SettingsError`  [INFERRED]
  backend/src/analyst_backend/ingestion/__main__.py → backend/src/analyst_backend/settings.py
- `apply_rules()` --uses--> `Catalog`  [INFERRED]
  backend/src/analyst_backend/ingestion/pipeline.py → backend/src/analyst_backend/ingestion/catalog.py
- `apply_catalog()` --uses--> `Catalog`  [INFERRED]
  backend/src/analyst_backend/ingestion/rules.py → backend/src/analyst_backend/ingestion/catalog.py
- `apply_rules()` --uses--> `QualityConfig`  [INFERRED]
  backend/src/analyst_backend/ingestion/pipeline.py → backend/src/analyst_backend/ingestion/catalog.py
- `run()` --uses--> `QualityConfig`  [INFERRED]
  backend/tests/ingestion/test_pipeline.py → backend/src/analyst_backend/ingestion/catalog.py

## Import Cycles
- None detected.

## Communities (56 total, 17 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "Arquitectura de Brío Analyst"
Cohesion: 0.06
Nodes (28): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas (+20 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "pytest"
Cohesion: 0.10
Nodes (19): InputError, _check_header(), parse_sales_csv(), read_csv_bytes(), read_sales_csv(), test_columns_in_another_order_are_accepted(), test_extra_column_is_named(), test_header_only_is_rejected() (+11 more)

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
Cohesion: 0.07
Nodes (28): Catalog, load_catalog(), load_quality_config(), parse_catalog(), parse_quality_config(), _parse_yaml(), QualityConfig, read_config_bytes() (+20 more)

### Community 22 - "test_app.py"
Cohesion: 0.06
Nodes (14): _coerce(), main(), parse_config(), load_settings(), Settings, _FakeApp, _render(), test_cli_launches_page_with_server_options() (+6 more)

### Community 23 - "Requirements"
Cohesion: 0.05
Nodes (43): data-quality Specification, Purpose, Requirement: Destino único por fila, Requirement: DQ01 registro_id único, Requirement: DQ03 recorte de espacios, Requirement: DQ04 catálogo de valores válidos, Requirement: DQ05 mes inválido, Requirement: DQ06 unidades faltantes (+35 more)

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
Cohesion: 0.10
Nodes (24): apply_rules(), _corrected_frame(), _issues_frame(), _reason(), _review_frame(), _sales_frame(), apply_catalog(), _as_number() (+16 more)

### Community 34 - "ADDED Requirements"
Cohesion: 0.06
Nodes (35): ADDED Requirements, Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas (+27 more)

### Community 35 - "test_rules.py"
Cohesion: 0.12
Nodes (20): frame_of(), real_frame(), test_dq01_compares_after_trimming(), test_dq01_duplicate_with_differences(), test_dq01_real_file_identical_duplicate(), test_dq03_keeps_inner_spaces(), test_dq03_real_file_trims_region_and_channel(), test_dq04_catalog_comes_from_configuration() (+12 more)

### Community 36 - "test_storage.py"
Cohesion: 0.15
Nodes (21): compute_ingestion_id(), ingest(), IngestionSummary, IngestionSettings, con(), previous_db(), real_db(), _settings() (+13 more)

### Community 37 - "test_pipeline.py"
Cohesion: 0.13
Nodes (34): RulesOutcome, _issue(), _issues(), run(), test_actions_by_severity_in_real_file(), test_dq01_duplicate_with_differences_keeps_line_2_in_sales(), test_dq01_first_occurrence_invalid_keeps_id_out_of_sales(), test_dq01_real_duplicate_full_then() (+26 more)

### Community 38 - "Requirements"
Cohesion: 0.06
Nodes (35): Purpose, Requirement: Carga atómica, Requirement: Carga del CSV a DuckDB, Requirement: Comando de ingesta, Requirement: Cuadre de filas, Requirement: Descripción del esquema, Requirement: Esquema de la tabla de ventas, Requirement: Idempotencia (+27 more)

### Community 39 - "test_end_to_end.py"
Cohesion: 0.27
Nodes (12): _make_ingest(), _rows(), _settings(), test_columns_in_another_order_load_completely(), test_csv_without_bom_gives_same_sales(), test_failed_replace_restores_previous_wal(), test_make_ingest_publishes_the_database(), test_make_ingest_reports_errors() (+4 more)

### Community 40 - "Decisions"
Cohesion: 0.12
Nodes (16): Almacenamiento y atomicidad, Arquitectura, Configuración fuera del código, Context, Decisions, Design, DQ12: fórmula y población, El catálogo vive ya en `semantic_layer.yaml` (+8 more)

### Community 41 - ".action"
Cohesion: 0.18
Nodes (9): Contrato de `dq_issues` y `sales_review`, Requirement: Estructura de las incidencias, Scenario: Columnas de dq_issues, 4. Destino de las filas, avisos y reparto de incidencias, Requirement: Acción e impacto de cada incidencia, Requirement: Estructura de las incidencias, Scenario: Acción según el destino final, Scenario: Columnas de dq_issues (+1 more)

### Community 42 - "ADDED Requirements"
Cohesion: 0.17
Nodes (12): ADDED Requirements, Requirement: Destino único por fila, Requirement: DQ06 unidades faltantes, Requirement: DQ07 venta neta faltante, Requirement: DQ11 aviso de punto de venta único, Requirement: Incidencias del archivo real, Scenario: Fila con mes inválido y venta faltante, Scenario: Puntos de venta únicos del archivo real (+4 more)

### Community 43 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 44 - "Tasks"
Cohesion: 0.22
Nodes (8): 1. Dependencias y configuración, 2. Lectura y validación de la entrada (requisito "Validación de la entrada"), 3. Modelo de incidencias y reglas que actúan, 5. Validación final y almacenamiento, 6. Punto de entrada y pruebas de extremo a extremo, 7. Documentación, 8. Cierre, Tasks

### Community 45 - "Requirement: DQ01 registro_id único"
Cohesion: 0.50
Nodes (4): Requirement: DQ01 registro_id único, Scenario: Duplicado con diferencias, Scenario: Duplicado idéntico del archivo real, Scenario: Primera aparición no válida

### Community 46 - "Requirement: DQ03 recorte de espacios"
Cohesion: 0.50
Nodes (4): Requirement: DQ03 recorte de espacios, Scenario: Canal con espacio del archivo real, Scenario: Espacios intermedios intactos, Scenario: Región con espacio del archivo real

### Community 47 - "Requirement: DQ04 catálogo de valores válidos"
Cohesion: 0.50
Nodes (4): Requirement: DQ04 catálogo de valores válidos, Scenario: Catálogo leído de configuración, Scenario: Marca en mayúsculas del archivo real, Scenario: Valor fuera del catálogo

### Community 48 - "Requirement: DQ12 aviso de precio atípico"
Cohesion: 0.50
Nodes (4): Requirement: DQ12 aviso de precio atípico, Scenario: Error de escala, Scenario: Sin precios atípicos en el archivo real, Scenario: Umbral leído de configuración

### Community 49 - "Requirement: DQ13 venta sin unidades"
Cohesion: 0.50
Nodes (4): Requirement: DQ13 venta sin unidades, Scenario: Sin casos en el archivo real, Scenario: Venta cero con unidades, Scenario: Venta positiva con cero unidades

### Community 51 - "Requirement: Acción e impacto de cada incidencia"
Cohesion: 0.67
Nodes (3): Requirement: Acción e impacto de cada incidencia, Scenario: Acción según el destino final, Scenario: Impacto de un valor negativo

### Community 52 - "Requirement: DQ05 mes inválido"
Cohesion: 0.67
Nodes (3): Requirement: DQ05 mes inválido, Scenario: Mes 13 del archivo real, Scenario: Mes válido fuera del semestre

### Community 53 - "pathlib"
Cohesion: 0.06
Nodes (18): publish(), _quote(), _replace_keeping_old_wal_until_done(), _temporary_files(), write_tables(), load_ingestion_settings(), _resolve(), SettingsError (+10 more)

### Community 54 - "Requirement: DQ08 valores negativos"
Cohesion: 0.67
Nodes (3): Requirement: DQ08 valores negativos, Scenario: Cero no es negativo, Scenario: Negativos del archivo real

### Community 55 - "Requirement: Filas en revisión"
Cohesion: 0.67
Nodes (3): Requirement: Filas en revisión, Scenario: Filas retenidas del archivo real, Scenario: Varias reglas de revisión

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 426 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Issue` connect `pipeline.py` to `.action`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `RulesOutcome` (e.g. with `_issue()` and `_issues()`) actually correct?**
  _`RulesOutcome` has 34 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Arquitectura de Brío Analyst` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._
- **Why does `ADDED Requirements` connect `ADDED Requirements` to `.action`, `Requirement: DQ01 registro_id único`, `Requirement: DQ03 recorte de espacios`, `Requirement: DQ04 catálogo de valores válidos`, `Requirement: DQ12 aviso de precio atípico`, `Requirement: DQ13 venta sin unidades`, `Spec Delta`, `Requirement: Acción e impacto de cada incidencia`, `Requirement: DQ05 mes inválido`, `Requirement: DQ08 valores negativos`, `Requirement: Filas en revisión`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `apply_rules()` (e.g. with `Catalog` and `QualityConfig`) actually correct?**
  _`apply_rules()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._