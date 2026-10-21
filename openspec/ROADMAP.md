# Hoja de ruta: Brío Analyst

Avance del proyecto. Se actualiza al cerrar cada etapa o change. Tras un `/clear`, retoma desde **Siguiente paso**.
Temporal: al archivar el change 9, elimina este archivo y su referencia en `CLAUDE.md` (el `@` y la regla de actualización).

Estados: `pendiente` → `propuesto` → `aprobado` → `implementado` → `verificado` → `archivado`.

## Siguiente paso

Change 2 `add-sales-ingestion`: proponer con las reglas aprobadas en `docs/EXPLORACION_DATOS.md` (sección "Aprobación de reglas") y resolver los pendientes de abajo.

## Pendientes para retomar

- **Datos en revisión (cuarentena):** valorar dejar ciertos registros "en revisión" en lugar de eliminarlos o corregirlos (surgió al fusionar DQ02 en DQ01). Recordarlo al proponer `add-sales-ingestion` y al revisar las reglas DQ restantes.

- **Catálogo de valores válidos antes del change 3:** DQ04 lo necesita en la ingesta (change 2), pero la capa semántica estaba prevista para el change 3. Resolverlo al proponer `add-sales-ingestion`.

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
| 2 | `add-sales-ingestion` | `sales-ingestion`, `data-quality` | 1, Etapa 4 | Sí | pendiente |
| 3 | `add-sales-analytics` | `semantic-layer`, `sales-metrics` | 2 | Indirecto | pendiente |
| 4 | `add-document-retrieval` | `document-ingestion`, `document-retrieval` | 1, Etapa 4 | Sí | pendiente |
| 5 | `add-query-agent` | `llm-provider`, `query-agent` | 3, 4 | Indirecto | pendiente |
| 6 | `add-contrast-and-causal-analysis` | `report-contrast`, `causal-assessment` | 5 | Indirecto | pendiente |
| 7 | `add-safe-sql-tool` | `safe-sql` | 3, 5 | Indirecto | pendiente |
| 8 | `add-api-and-ui` | `query-api`, `analyst-ui` | 5 | No | pendiente |
| 9 | `add-evaluation-suite` | `evaluation` | 5, 6, 7 | Sí | pendiente |
