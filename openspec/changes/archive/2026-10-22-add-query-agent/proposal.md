# Proposal

## Why

Las herramientas deterministas ya existen (`consultar_metrica`, `calidad_datos` y `buscar_documentos`), pero el analista aún no puede preguntar en lenguaje natural. Falta un agente que entienda la pregunta, decida qué consultar y responda separando hechos, hipótesis, contradicciones e información insuficiente, con evidencia citada y sin que el LLM calcule ni invente cifras.

## What Changes

- **Proveedor de LLM (`llm-provider`)**:
  - solo Gemini, configurado con `LLM_PROVIDER`, `GEMINI_MODEL` y `GEMINI_API_KEY`;
  - límite de peticiones y tiempo máximo;
  - sin reintentos ante cuota agotada (429) y con reintentos acotados ante 5xx;
  - errores con código, sin exponer la clave;
  - parámetros en `backend/config/agent.yaml`.
- **Agente de consulta (`query-agent`)**, un grafo LangGraph con la estrategia "plan y ejecución":
  1. **plan**: con `bind_tools`, el LLM pide en **una** respuesta todas las consultas. El prompt incluye el catálogo de la capa semántica y el **rango de meses y trimestres con datos, leído de DuckDB**;
  2. **ejecución** con `ToolNode`. Las herramientas son `@tool` con `content_and_artifact`: el LLM lee un resumen y el resultado completo queda para la verificación y la traza. Los argumentos admiten valores sueltos donde se espera una lista;
  3. **una corrección** ante errores, que solo ve las consultas fallidas y nunca texto de documentos;
  4. **síntesis estructurada** con hechos, hipótesis, contradicciones e información insuficiente, cada afirmación con su evidencia;
  5. **verificación en código**: cifras presentes en la evidencia que cada afirmación cita, citas existentes y lenguaje causal y atenuado; 1 reintento y fallo cerrado;
  6. **respuesta** con avisos y traza.
- `answer_question()` y `make ask Q="..."`.
- `make test-llm` carga `.env` si existe y acepta rutas de pruebas.

**Base de la decisión** (`benchmark.md`). Modelos locales de 7–8B: 190 ejecuciones y 2 de 57 preguntas de cifras correctas. Con Gemini y el rango de períodos, las 5 estrategias probadas acertaron las 2 preguntas. "Plan y ejecución" usó 2–3 llamadas fijas frente a 2–6 de ReAct. La investigación respalda planificar antes de leer documentos y verificar por código.

## Capabilities

### New Capabilities

- `llm-provider`: modelo de chat de Gemini desde configuración, límites y errores del proveedor.
- `query-agent`: planificación, ejecución de herramientas, corrección, síntesis, verificación y respuesta trazable.

### Modified Capabilities

- `project-layout`: `make test-llm` carga `ENV_FILE` si existe y acepta `LLM_TESTS`.

## Impact

- **Código nuevo:** `backend/src/analyst_backend/agent/` y pruebas en `backend/tests/agent/`. Las herramientas de los changes 3 y 4 se reutilizan sin cambios.
- **Dependencias:** `langgraph`, `langchain-core` y `langchain-google-genai`, con versión fija.
- **Configuración:** `agent.yaml` y `AGENT_CONFIG_PATH`; se quitan las variables de Ollama de `.env.example`.
- **Documentación:** `docs/architecture.md` (D8: solo Gemini; Ollama deja de ser la alternativa) y el contexto de `openspec/config.yaml`.

## Fuera de alcance

- Subgrafos de contraste y causal (change 6); `sql_libre` (change 7); API y UI (change 8); evaluación (change 9).
- Ollama, Claude u otros proveedores; caché; memoria entre preguntas.
- Ejemplos plantilla en el prompt y marcadores de cifras.
