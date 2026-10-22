# Hoja de ruta: Brío Analyst

Avance del proyecto. Se actualiza al cerrar cada etapa o change. Tras un `/clear`, retoma desde **Siguiente paso**.
Temporal: al archivar el change 9, elimina este archivo y su referencia en `CLAUDE.md` (el `@` y la regla de actualización).

Estados: `pendiente` → `propuesto` → `aprobado` → `implementado` → `verificado` → `archivado`.

## Siguiente paso

Change 3 `add-sales-analytics`: proponer (capa semántica de métricas y alias en `backend/config/semantic_layer.yaml`, métricas sobre `sales`, herramientas `consultar_metrica` y `calidad_datos`).

## Pendientes para retomar

- **Datos en revisión: decidido (opción B).** Tablas DuckDB `sales` (única fuente de cifras), `sales_review` (filas retenidas por DQ04 fuera de catálogo, DQ05, DQ08 y DQ13), `dq_issues` e `ingestion_runs`. Sin archivo de decisiones por ahora (posible change futuro). Implementado en `add-sales-ingestion` (D5).
- **Varios CSV de ventas (posible change futuro):** hoy la ingesta carga un solo archivo (decisión del 2026-10-21). Si llegan varios, añadir patrón de archivos, `source_file` y DQ01 entre archivos; nunca cargas incrementales.
- **Consultas del agente:** nada de SQL fijo en código. Capa semántica primero (`consultar_metrica`) y SQL libre validado como respaldo (`sql_libre`, change 7). Confirmado por el responsable (2026-10-21).

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
| 3 | `add-sales-analytics` | `semantic-layer`, `sales-metrics` | 2 | Indirecto | pendiente |
| 4 | `add-document-retrieval` | `document-ingestion`, `document-retrieval` | 1, Etapa 4 | Sí | pendiente |
| 5 | `add-query-agent` | `llm-provider`, `query-agent` | 3, 4 | Indirecto | pendiente |
| 6 | `add-contrast-and-causal-analysis` | `report-contrast`, `causal-assessment` | 5 | Indirecto | pendiente |
| 7 | `add-safe-sql-tool` | `safe-sql` | 3, 5 | Indirecto | pendiente |
| 8 | `add-api-and-ui` | `query-api`, `analyst-ui` | 5 | No | pendiente |
| 9 | `add-evaluation-suite` | `evaluation` | 5, 6, 7 | Sí | pendiente |
