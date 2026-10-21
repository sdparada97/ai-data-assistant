# Graph Report - ai-data-assistant  (2026-10-20)

## Corpus Check
- 41 files · ~36,447 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 10, .example 1, .lock 1)

## Summary
- 270 nodes · 330 edges · 33 communities (14 shown, 19 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d1a039ef`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- openspec-explore/SKILL.md
- Arquitectura de Brío Analyst
- ADDED Requirements
- pytest
- ai-data-assistant
- explore.md
- test_compose.py
- conftest.py
- Decisions
- test_makefile.py
- test_layout.py
- test_health.py
- test_app.py
- cli.py
- Proposal
- Tasks
- analyst-backend
- analyst-frontend
- config.py
- test_environment.py

## God Nodes (most connected - your core abstractions)
1. `Decisions` - 11 edges
2. `_isolate_default_suite()` - 10 edges
3. `ADDED Requirements` - 10 edges
4. `Tasks` - 8 edges
5. `resolved()` - 7 edges
6. `_marker_filter()` - 7 edges
7. `Arquitectura de Brío Analyst` - 7 edges
8. `_guard()` - 6 edges
9. `_compose_config()` - 6 edges
10. `_make()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `_compose_config()` --calls--> `subprocess`  [EXTRACTED]
  tests/test_compose.py →   _Bridges community 11 → community 19_
- `test_lockfile_is_in_sync_offline()` --calls--> `pytest`  [EXTRACTED]
  tests/test_environment.py →   _Bridges community 11 → community 3_

## Import Cycles
- None detected.

## Communities (33 total, 19 thin omitted)

### Community 0 - "openspec-explore/SKILL.md"
Cohesion: 0.17
Nodes (11): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do (+3 more)

### Community 1 - "Arquitectura de Brío Analyst"
Cohesion: 0.10
Nodes (18): ai-data-assistant, Arquitectura, Comandos, Convenciones, Flujo de trabajo: Spec-Driven Development (OpenSpec), graphify, Proyecto Brío Analyst, Reglas (+10 more)

### Community 2 - "ADDED Requirements"
Cohesion: 0.06
Nodes (32): ADDED Requirements, Purpose, Requirement: Aislamiento de la suite por defecto, Requirement: Entorno Python reproducible, Requirement: Evaluación reservada, Requirement: Orquestación con contenedores, Requirement: Pruebas con LLM separadas, Requirement: Página mínima del frontend (+24 more)

### Community 3 - "pytest"
Cohesion: 0.17
Nodes (6): test_dns_resolution_fails_with_explicit_error(), test_env_example_variables_are_hidden(), test_local_unix_sockets_keep_native_behaviour(), test_network_connect_ex_fails_with_explicit_error(), test_network_connect_fails_with_explicit_error(), test_udp_send_fails_with_explicit_error()

### Community 4 - "ai-data-assistant"
Cohesion: 0.18
Nodes (9): Changes, Etapas, Hoja de ruta: Brío Analyst, Siguiente paso, ai-data-assistant, Comandos, Estructura, Instalación (+1 more)

### Community 10 - "explore.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, Planning a Change, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 11 - "test_compose.py"
Cohesion: 0.18
Nodes (7): _compose_config(), resolved(), test_config_is_valid_without_env_file(), test_defines_backend_and_frontend(), test_frontend_points_to_backend_and_depends_on_it(), test_only_backend_loads_env_file(), test_lockfile_is_in_sync_offline()

### Community 17 - "conftest.py"
Cohesion: 0.21
Nodes (9): _blocked_connect(), _blocked_connect_ex(), _blocked_resolution(), _blocked_sendmsg(), _blocked_sendto(), env_example_variables(), _guard(), _isolate_default_suite() (+1 more)

### Community 18 - "Decisions"
Cohesion: 0.12
Nodes (16): Alcance del bloqueo de red, Contenedores, Context, D2' Código fuente en `backend/src/` y `frontend/src/` (reemplaza D2), D4 Workspace de uv con un único `uv.lock`, Decisions, Design, Goals / Non-Goals (+8 more)

### Community 19 - "test_makefile.py"
Cohesion: 0.26
Nodes (8): _collect_sample(), _make(), _marker_filter(), test_default_filter_collects_from_all_three_locations(), test_default_filter_excludes_llm_tests(), test_llm_filter_collects_only_marked_tests(), test_make_eval_fails_explicitly(), test_make_test_llm_succeeds_without_llm_tests()

### Community 22 - "test_app.py"
Cohesion: 0.17
Nodes (7): _FakeApp, _render(), test_cli_launches_page_with_server_options(), test_cli_rejects_malformed_options(), test_cli_without_options_uses_default_config(), test_page_shows_configured_title_and_url(), test_page_uses_defaults_without_variables()

### Community 23 - "cli.py"
Cohesion: 0.31
Nodes (3): _coerce(), main(), parse_config()

### Community 24 - "Proposal"
Cohesion: 0.22
Nodes (8): Capabilities, Fuera de alcance, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 25 - "Tasks"
Cohesion: 0.22
Nodes (8): 1. Decisiones D2' y D4 en la documentación, 2. Entorno Python (requisitos "Ubicación del código fuente", "Entorno Python reproducible" y "Aislamiento de la suite por defecto"), 3. Backend (requisito "Salud del backend"), 4. Frontend (requisito "Página mínima del frontend"), 5. Comandos comunes (requisitos "Suite de pruebas sin servicios externos", "Pruebas con LLM separadas" y "Evaluación reservada"), 6. Contenedores (requisito "Orquestación con contenedores"), 7. Cierre, Tasks

## Knowledge Gaps
- **2 isolated node(s):** `analyst-backend`, `analyst-frontend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 159 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 5 inferred relationships involving `_isolate_default_suite()` (e.g. with `_blocked_connect()` and `_blocked_connect_ex()`) actually correct?**
  _`_isolate_default_suite()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `analyst-backend`, `analyst-frontend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Arquitectura de Brío Analyst` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `ADDED Requirements` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `Decisions` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._