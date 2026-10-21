# ai-data-assistant

Asistente de datos con IA. Proyecto en fase inicial: el código vive en `backend/src/` (API) y `frontend/src/` (interfaz), la documentación en `docs/`.

## Flujo de trabajo: Spec-Driven Development (OpenSpec)

- Todo cambio no trivial empieza como un change de OpenSpec, no como código.
  1. `/opsx:explore` para aclarar la idea.
  2. `/opsx:propose` para generar proposal, design, specs y tasks en `openspec/changes/<nombre>/`.
  3. `/opsx:apply` para implementar las tareas.
  4. `/opsx:archive` al terminar, para fusionar las specs en `openspec/specs/`.
- Las specs vigentes en `openspec/specs/` son la fuente de verdad del comportamiento. Si el código y la spec no coinciden, señálalo antes de cambiar cualquiera de los dos.
- Valida con `openspec validate --all` antes de dar un cambio por terminado.
- El CLI `openspec` requiere Node ≥ 20 (está en nvm: `~/.nvm/versions/node/v22.23.3/bin`).

## Arquitectura

- Decisiones y límites: [docs/architecture.md](docs/architecture.md). Léelo antes de proponer cambios estructurales.
- Para entender relaciones del código usa el grafo de graphify (ver sección siguiente) en lugar de recorrer archivos uno a uno.

## Convenciones

- Artefactos de OpenSpec y documentación en español; identificadores de código en inglés.
- No commitear secretos ni `.env`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

---
## Proyecto Brío Analyst
Contexto: openspec/config.yaml (context) y docs/architecture.md. Avance: @openspec/ROADMAP.md

### Reglas
- Todo cambio funcional pasa por un change de OpenSpec aprobado (/opsx:propose → /opsx:apply → /opsx:archive).
- Inspecciona los archivos reales antes de suponer columnas, valores o formatos.
- El LLM de la aplicación nunca calcula cifras: todo número sale de código determinista sobre DuckDB.
- Nada hardcodeado: marca, períodos, regiones y canales son parámetros. Los valores concretos solo viven en tests y en eval/golden_set.yaml.
- Cada escenario WHEN/THEN tiene al menos un test.
- Nunca archives un change sin mi aprobación explícita.
- Nunca leas, imprimas ni copies el contenido de .env.
- Al cerrar cada etapa o change, actualiza openspec/ROADMAP.md.

### Comandos
- OpenSpec: export PATH="$HOME/.nvm/versions/node/v22.23.3/bin:$PATH" && openspec <cmd>
- make test | make test-llm | make eval | make up
---
