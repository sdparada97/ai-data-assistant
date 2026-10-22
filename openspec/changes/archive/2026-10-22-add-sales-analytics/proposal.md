# Proposal

## Why

La base de ventas ya existe (change 2), pero nada la consulta. El agente (change 5) necesita herramientas que respondan preguntas como "¿qué región cayó más entre T1 y T2?" con cifras exactas y trazables, sin que el LLM calcule ni escriba SQL. La capa semántica es la vía principal acordada: el LLM elige métricas, filtros y períodos, y el código genera la consulta.

## What Changes

- **Capa semántica** en `backend/config/semantic_layer.yaml`: métricas (venta neta, unidades, precio efectivo, registros) con su expresión, unidad y descripción; alias de valores (por ejemplo "Brío" → `Brio`); y `punto_venta_id` y `mes` como dimensiones consultables. Las expresiones se validan al cargar.
- **Períodos como expresiones de calendario** (`2026`, `2026-S1`, `2026-T1`, `2026-03`) resueltas a meses por reglas genéricas. Un período sin datos se informa como tal, nunca como 0.
- **`consultar_metrica`** (función Python pura, entradas y salidas pydantic):
  - métricas de un período o comparación entre dos, con variación absoluta y porcentual según la fórmula del contexto de negocio;
  - filtros, agrupación, orden y ranking;
  - SQL generado desde el YAML con parámetros enlazados, sobre una conexión DuckDB de solo lectura;
  - cada resultado lleva `evidence_id` determinista, `ingestion_id`, el SQL ejecutado y los avisos de calidad que afectan al corte consultado.
- **`calidad_datos`**: resumen y detalle de incidencias y filas en revisión, filtrables por dimensión, período y regla.
- **Ingesta (modificación)**: `dq_issues` guarda las dimensiones de la fila afectada (`mes`, `marca`, `region`, `canal`, `presentacion`, `punto_venta_id`), necesarias para asociar cada incidencia a un corte.

## Capabilities

### New Capabilities

- `semantic-layer`: definición y validación de métricas, dimensiones, alias y expresiones de período.
- `sales-metrics`: consultas deterministas de métricas y de calidad de datos (`consultar_metrica`, `calidad_datos`), su trazabilidad y sus avisos.

### Modified Capabilities

- `data-quality`: el requisito "Estructura de las incidencias" añade las columnas de dimensión de la fila afectada.

## Impact

- **Código nuevo:** paquete `backend/src/analyst_backend/analytics/` y sus pruebas.
- **Código modificado:** ingesta (`rules.py`, `pipeline.py`, `storage.py`) para las nuevas columnas de `dq_issues`; `settings.py` para la configuración de consulta.
- **Configuración:** `semantic_layer.yaml` crece con `metrics` y `aliases`; el catálogo de DQ04 no cambia.
- **Dependencias:** pydantic pasa a dependencia directa del backend con versión fija (ya estaba instalada como transitiva).
- **Base de datos:** hay que volver a ejecutar `make ingest` para tener las columnas nuevas.
- **Documentación:** `docs/architecture.md` registra la capa semántica y las herramientas (D6).

## Fuera de alcance

- Wrappers de LangChain y el grafo del agente (change 5).
- SQL libre del agente y sus controles (change 7).
- Métricas derivadas más allá de las cuatro definidas (cuota, crecimiento compuesto, etc.).
- Interpretación causal o redacción de respuestas: estas herramientas solo devuelven datos.
- Caché de resultados y límites de tiempo por consulta.
