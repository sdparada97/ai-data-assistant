# Hoja de ruta: Brío Analyst

Avance del proyecto. Se actualiza al cerrar cada etapa o change. Tras un `/clear`, retoma desde **Siguiente paso**.
Temporal: al archivar el change 9, elimina este archivo y su referencia en `CLAUDE.md` (el `@` y la regla de actualización).

Estados: `pendiente` → `propuesto` → `aprobado` → `implementado` → `verificado` → `archivado`.

## Siguiente paso

Change 1 `restructure-monorepo-layout`: verificado (cumple); esperando aprobación para `/opsx:archive` (punto de control 5B).

## Etapas

| Etapa | Descripción | Estado |
|-------|-------------|--------|
| 0 | Diagnóstico y configuración | hecha |
| 1 | Contexto de OpenSpec | hecha |
| 2 | Hoja de ruta | hecha |
| 4 | Exploración de datos → `docs/EXPLORACION_DATOS.md` | bloqueada: faltan datos en `data/raw/`. Va antes de los changes 2 y 4 |

## Changes

| # | Change | Capabilities | Depende de | ¿Usa `data/raw/`? | Estado |
|---|--------|--------------|------------|-------------------|--------|
| 1 | `restructure-monorepo-layout` | `project-layout` | — | No | verificado |
| 2 | `add-sales-ingestion` | `sales-ingestion`, `data-quality` | 1, Etapa 4 | Sí | pendiente |
| 3 | `add-sales-analytics` | `semantic-layer`, `sales-metrics` | 2 | Indirecto | pendiente |
| 4 | `add-document-retrieval` | `document-ingestion`, `document-retrieval` | 1, Etapa 4 | Sí | pendiente |
| 5 | `add-query-agent` | `llm-provider`, `query-agent` | 3, 4 | Indirecto | pendiente |
| 6 | `add-contrast-and-causal-analysis` | `report-contrast`, `causal-assessment` | 5 | Indirecto | pendiente |
| 7 | `add-safe-sql-tool` | `safe-sql` | 3, 5 | Indirecto | pendiente |
| 8 | `add-api-and-ui` | `query-api`, `analyst-ui` | 5 | No | pendiente |
| 9 | `add-evaluation-suite` | `evaluation` | 5, 6, 7 | Sí | pendiente |
