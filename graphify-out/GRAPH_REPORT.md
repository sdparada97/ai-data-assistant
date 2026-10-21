# Graph Report - ai-data-assistant  (2026-10-21)

## Corpus Check
- 45 files · ~42,348 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 359 nodes · 471 edges · 33 communities (16 shown, 17 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2c8cd7d2`
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
- test_layout.py
- test_health.py
- test_app.py
- cli.py
- Decisions
- Proposal
- analyst-backend
- analyst-frontend
- Tasks
- Almena Foods | Contexto de negocio

## God Nodes (most connected - your core abstractions)
1. `main()` - 11 edges
2. `Decisions` - 11 edges
3. `rules_report()` - 10 edges
4. `_isolate_default_suite()` - 10 edges
5. `ADDED Requirements` - 10 edges
6. `Requirements` - 10 edges
7. `Exploración de datos` - 9 edges
8. `_numeric()` - 8 edges
9. `build_rules()` - 8 edges
10. `sensitivity()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `extract_documents()` --calls--> `re`  [EXTRACTED]
  backend/scripts/explore_data.py →   _Bridges community 4 → community 11_
- `test_lockfile_is_in_sync_offline()` --calls--> `pytest`  [EXTRACTED]
  tests/test_environment.py →   _Bridges community 11 → community 3_

## Import Cycles
- None detected.

## Communities (33 total, 17 thin omitted)

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
Cohesion: 0.16
Nodes (6): test_dns_resolution_fails_with_explicit_error(), test_env_example_variables_are_hidden(), test_local_unix_sockets_keep_native_behaviour(), test_network_connect_ex_fails_with_explicit_error(), test_network_connect_fails_with_explicit_error(), test_udp_send_fails_with_explicit_error()

### Community 4 - "explore_data.py"
Cohesion: 0.16
Nodes (18): assign_period(), build_rules(), unit_price_outlier(), _canonical_spelling(), clean(), extract_documents(), _fmt(), load_raw() (+10 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "test_makefile.py"
Cohesion: 0.09
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

### Community 22 - "test_app.py"
Cohesion: 0.17
Nodes (7): _FakeApp, _render(), test_cli_launches_page_with_server_options(), test_cli_rejects_malformed_options(), test_cli_without_options_uses_default_config(), test_page_shows_configured_title_and_url(), test_page_uses_defaults_without_variables()

### Community 23 - "cli.py"
Cohesion: 0.15
Nodes (5): _coerce(), main(), parse_config(), load_settings(), Settings

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

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 205 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Arquitectura de Brío Analyst` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `test_makefile.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0931174089068826 - nodes in this community are weakly interconnected._
- **Should `Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `Exploración de datos` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Should `cli.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._