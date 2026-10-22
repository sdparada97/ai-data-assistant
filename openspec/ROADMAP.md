# Hoja de ruta: Brío Analyst

Avance del proyecto. Se actualiza al cerrar cada etapa o change. Tras un `/clear`, retoma desde **Siguiente paso**.
Temporal: al archivar el change 9, elimina este archivo y su referencia en `CLAUDE.md` (el `@` y la regla de actualización).

Estados: `pendiente` → `propuesto` → `aprobado` → `implementado` → `verificado` → `archivado`.

## Siguiente paso

Change 5 `add-query-agent`: pendiente. Empezar con `/opsx:propose` (agente LangGraph con `consultar_metrica`, `calidad_datos` y `buscar_documentos` como tools; ver "Tools de LangChain" abajo).

## Pendientes para retomar

- **Datos en revisión: decidido (opción B).** Tablas DuckDB `sales` (única fuente de cifras), `sales_review` (filas retenidas por DQ04 fuera de catálogo, DQ05, DQ08 y DQ13), `dq_issues` e `ingestion_runs`. Sin archivo de decisiones por ahora (posible change futuro). Implementado en `add-sales-ingestion` (D5).
- **Varios CSV de ventas (posible change futuro):** hoy la ingesta carga un solo archivo (decisión del 2026-10-21). Si llegan varios, añadir patrón de archivos, `source_file` y DQ01 entre archivos; nunca cargas incrementales.
- **Consultas del agente:** nada de SQL fijo en código. Capa semántica primero (`consultar_metrica`) y SQL libre validado como respaldo (`sql_libre`, change 7). Confirmado por el responsable (2026-10-21).

- **Tools de LangChain para el change 5 (`add-query-agent`), decidido el 2026-10-22:** la lógica sigue en Python puro (`analytics/`) y el change 5 solo la envuelve.
  - `@tool(args_schema=MetricQuery|QualityQuery, response_format="content_and_artifact")`: el LLM recibe un resumen con cifras redondeadas y el *artifact* lleva el resultado completo (`evidence_id`, valores exactos, SQL) para el nodo "verificar".
  - `ToolNode(handle_tool_errors=...)` debe devolver al LLM el `QueryError` (campo, valor, opciones válidas) además de los argumentos inválidos de pydantic, para que corrija y reintente. Por defecto `ToolNode` vuelve a lanzar los errores de ejecución.
  - Cubrir con un test la combinación de `content_and_artifact` y el manejo de errores (la documentación no la muestra junta).
  - En el artifact, `model_dump(mode="json")` convierte los `Decimal` en texto: el nodo "verificar" debe compararlos así.
  - `buscar_documentos` (change 4) se envuelve igual: el texto de los fragmentos llega al LLM como evidencia citable por su ID (`content_kind = "evidencia_documental"`), nunca como instrucciones; el agente debe defenderse de textos como `OC-EXT-06`. Avisos con código (`semantic_unavailable`, `model_mismatch`, `no_matches`, `no_lexical_matches`, `filters_empty`).
- **Evaluación de la recuperación (change 9):** las preguntas de los escenarios de `document-retrieval` son las mismas que sirvieron para elegir el modelo (MiniLM + BM25 con RRF). El change 9 debe medir hit@k y MRR con preguntas distintas y valorar ahí un reranker (`bge-reranker-v2-m3-int8`, 0,57 GB) si el orden del top 3 falla.
- **Catálogo de valores válidos: resuelto** en `add-sales-ingestion`: `backend/config/semantic_layer.yaml` (sección `dimensions`); el change 3 añade métricas y alias al mismo archivo.

## Etapas

| Etapa | Descripción | Estado |
|-------|-------------|--------|
| 0 | Diagnóstico y configuración | hecha |
| 1 | Contexto de OpenSpec | hecha |
| 2 | Hoja de ruta | hecha |
| 4 | Exploración de datos → `docs/EXPLORACION_DATOS.md` | hecha; reglas aprobadas (2026-10-21) |

## Changes

| # | Change | Capabilities | Depende de | ¿Usa `data/raw/`? | Estado |
|---|--------|--------------|------------|-------------------|--------|
| 1 | `restructure-monorepo-layout` | `project-layout` | — | No | archivado (2026-10-20) |
| 2 | `add-sales-ingestion` | `sales-ingestion`, `data-quality` | 1, Etapa 4 | Sí | archivado (2026-10-21) |
| 3 | `add-sales-analytics` | `semantic-layer`, `sales-metrics` (modifica `data-quality`) | 2 | Indirecto | archivado (2026-10-22) |
| 4 | `add-document-retrieval` | `document-ingestion`, `document-retrieval` (modifica `project-layout`) | 1, Etapa 4 | Sí | archivado (2026-10-22) |
| 5 | `add-query-agent` | `llm-provider`, `query-agent` | 3, 4 | Indirecto | pendiente |
| 6 | `add-contrast-and-causal-analysis` | `report-contrast`, `causal-assessment` | 5 | Indirecto | pendiente |
| 7 | `add-safe-sql-tool` | `safe-sql` | 3, 5 | Indirecto | pendiente |
| 8 | `add-api-and-ui` | `query-api`, `analyst-ui` | 5 | No | pendiente |
| 9 | `add-evaluation-suite` | `evaluation` | 5, 6, 7 | Sí | pendiente |
