# Proposal

## Why

En las pruebas con la aplicación (change 8), las preguntas de contraste ("¿son consistentes las conclusiones del reporte con los datos?") y las causales ("¿las promociones causaron la caída?") salieron incompletas y distintas en cada ejecución. El LLM decidía qué consultar, no podía dar diferencias sin calcularlas y omitía el argumento de los datos. A veces agotaba el tiempo por la cantidad de evidencia y llegó a declarar ausentes datos que existen.

## What Changes

- **Contraste de afirmaciones (`report-contrast`):** herramienta `contrastar_afirmaciones(doc_id)` para cualquier documento cargado.
  1. El LLM extrae sus afirmaciones con un esquema cerrado (variación, ranking, dirección o cualitativa).
  2. El código las valida: valor literal en el fragmento, catálogo y períodos con datos.
  3. El código las compara con `consultar_metrica` y da diferencia y veredicto ("coincide", "aproximado", "no coincide"; ranking "verdadera" o "falsa"; cualitativa "no verificable con los datos"), con umbrales en `agent.yaml`.
- **Evaluación causal (`causal-assessment`):** herramienta `evaluar_causalidad`.
  - Cinco criterios fijos, calculados en código (localización, grupo de comparación, temporalidad, explicaciones alternativas) o extraídos y validados de los documentos (dónde y cuándo se observó la causa; diseño de la evidencia).
  - Veredicto "contradicha", "no sustentada" o "compatible (hipótesis)" según el tipo de causa (competencia, disponibilidad o métrica propia). Nunca "causa demostrada".
- **Agente (`query-agent`):**
  - las dos herramientas entran en el plan;
  - sus resultados son evidencias citables con título;
  - la verificación rechaza que "información insuficiente" declare ausentes datos que la ejecución consultó (por ejemplo, "faltan ventas por región").
- **Interfaz (`analyst-ui`):** tabla de afirmaciones con valor reportado, valor real, diferencia y veredicto; tabla de criterios con su resultado.

Una pregunta de contraste o causal pasa a hacer 3 llamadas al LLM (plan, extracción, síntesis). Las cifras siguen saliendo de código.

## Capabilities

### New Capabilities

- `report-contrast`: extracción validada de afirmaciones de un documento, comparación con los datos y veredicto por afirmación.
- `causal-assessment`: evaluación de una afirmación causal con criterios fijos y veredicto que nunca afirma causalidad.

### Modified Capabilities

- `query-agent`: herramientas, máximos propios, tipos y cifras de evidencia, veredictos citados, errores y coherencia de "información insuficiente".
- `analyst-ui`: detalle de las evidencias de contraste y causalidad.

## Impact

- **Código:** `analytics/contrast.py` y `analytics/causal.py` (comparación y criterios, Python puro); en `agent/`, `extraction.py`, `tools.py`, `evidence.py`, `verify.py`, `prompts.py` y `graph.py`; `render.py` en el frontend.
- **Configuración:** `agent.yaml` (umbrales del veredicto y de los criterios, máximo de afirmaciones por documento, marcadores de ausencia y sinónimos de métricas).
- **Pruebas:** LLM de guion sobre las bases reales; pruebas `llm` con las preguntas guía.
- **Documentación:** `docs/architecture.md` (D10), `openspec/config.yaml`, README y ROADMAP.

## Fuera de alcance

- Métricas nuevas (cuota de formatos, inventarios, precios de competidores): esas afirmaciones salen como "no verificable con los datos".
- Inferencia causal estadística (regresiones, grupos de control).
- Contrastar varios documentos en una pregunta: con el máximo de 1, el segundo se descarta.
- `sql_libre` (change 7) y golden set (change 9), aunque las preguntas guía servirán de base.
