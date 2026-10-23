# Hoja de ruta: Brío Analyst

Avance del proyecto. Se actualiza al cerrar cada etapa o change. Tras un `/clear`, retoma desde **Siguiente paso**.
Temporal: al archivar el change 9, elimina este archivo y su referencia en `CLAUDE.md` (el `@` y la regla de actualización).

Estados: `pendiente` → `propuesto` → `aprobado` → `implementado` → `verificado` → `archivado`.

## Siguiente paso

Change 6 `add-contrast-and-causal-analysis` (`report-contrast`, `causal-assessment`): pendiente de proponer con `/opsx:propose`. Debe resolver la variación de las respuestas a preguntas amplias, los timeouts que quedan y el argumento de datos en la evaluación causal. Antes de las specs, el responsable decide: integración como herramientas del plan, extracción de afirmaciones con el LLM y validación en código, umbrales del veredicto, criterios causales y comprobar que "información insuficiente" no declare ausentes datos que el catálogo sí tiene.

El change 8 `add-api-and-ui` quedó archivado el 2026-10-22: specs nuevas `query-api` y `analyst-ui`; `query-agent`, `llm-provider` y `project-layout` ampliadas. La aplicación se usa con `make up` (interfaz en `http://localhost:8501`).

## Pendientes para retomar

- **Datos en revisión: decidido (opción B).** Tablas DuckDB `sales` (única fuente de cifras), `sales_review` (filas retenidas por DQ04 fuera de catálogo, DQ05, DQ08 y DQ13), `dq_issues` e `ingestion_runs`. Sin archivo de decisiones por ahora (posible change futuro). Implementado en `add-sales-ingestion` (D5).
- **Varios CSV de ventas (posible change futuro):** hoy la ingesta carga un solo archivo (decisión del 2026-10-21). Si llegan varios, añadir patrón de archivos, `source_file` y DQ01 entre archivos; nunca cargas incrementales.
- **Consultas del agente:** nada de SQL fijo en código. Capa semántica primero (`consultar_metrica`) y SQL libre validado como respaldo (`sql_libre`, change 7). Confirmado por el responsable (2026-10-21).

- **Tools de LangChain: confirmado e implementado en el change 5 (`add-query-agent`).** La lógica sigue en Python puro (`analytics/`, `documents/`); `agent/tools.py` solo la envuelve.
  - `@tool(..., response_format="content_and_artifact")`: el LLM recibe un resumen JSON con cifras redondeadas; el *artifact* es el modelo pydantic completo, que usan la verificación (recorre sus `Decimal`, no el JSON) y la traza (`model_dump(mode="json")`).
  - `ToolNode(handle_tool_errors=format_tool_error)` devuelve al LLM el `QueryError` (campo, valor, opciones válidas) y los argumentos inválidos (`ToolInvocationError`); probado junto con `content_and_artifact`. `max_concurrency=1`, porque DuckDB con `lock_configuration` no admite dos conexiones a la vez.
  - El texto de los documentos llega a la síntesis delimitado como evidencia, con los delimitadores neutralizados; la corrección nunca lo ve.
- **Benchmark del change 5 (resumen):** 6 estrategias (S1–S6: ReAct libre y verificado, plan y ejecución, extracción guiada con y sin ejemplos, y plan y ejecución con primitivas nativas) con modelos locales de 7–8B (2 de 57 preguntas de cifras correctas) y Gemini (cuota gratuita). Ganó "plan y ejecución" con primitivas nativas: 2 llamadas por pregunta y ninguna lectura de documentos antes de decidir las consultas. Con Gemini, las 2 preguntas `llm` pasan (región con mayor caída; contradicción del reporte). Detalle en `openspec/changes/archive/2026-10-22-add-query-agent/benchmark.md`.
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
| 5 | `add-query-agent` | `llm-provider`, `query-agent` (modifica `project-layout`) | 3, 4 | Indirecto | archivado (2026-10-22) |
| 6 | `add-contrast-and-causal-analysis` | `report-contrast`, `causal-assessment` | 5 | Indirecto | pendiente |
| 7 | `add-safe-sql-tool` | `safe-sql` | 3, 5 | Indirecto | pendiente |
| 8 | `add-api-and-ui` | `query-api`, `analyst-ui` (modifica `query-agent`, `llm-provider` y `project-layout`) | 5 | No | archivado (2026-10-22) |
| 9 | `add-evaluation-suite` | `evaluation` | 5, 6, 7 | Sí | pendiente |
