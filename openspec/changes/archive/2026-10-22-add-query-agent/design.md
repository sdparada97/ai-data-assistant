# Design

## Context

Ver proposal.md (Why) y `benchmark.md` (resultados completos). Hechos que condicionan el diseño:

- **Herramientas (changes 3 y 4):** `consultar_metrica(MetricQuery, layer, db)`, `calidad_datos(QualityQuery, layer, db)` y `buscar_documentos(DocumentQuery, config, db, embedder)` son funciones puras. Ante una consulta inválida lanzan `QueryError(field, message, invalid_value, valid_options)`.
- **`MetricQuery` es estricto:** `extra="forbid"` y `period` XOR `compare`. Sus listas (`metrics`, `filters`, `group_by`) no admiten valores sueltos.
- **Datos reales:**
  - la base de ventas tiene meses de `2026-01` a `2026-06`;
  - `2025-T1` devuelve valor nulo con el aviso `El período 2025-T1 no tiene datos en la base`;
  - el `-23 %` del reporte está en el fragmento `05_Reporte_Comercial:003` (tabla regional, sin ID principal), no en el de `REP-01` (`:004`);
  - el índice de referencias (`03_Investigacion_Consumidor:018`) lleva `INV-01`…`INV-05` en sus `evidence_ids`.
- **Benchmark con Gemini 3 Flash**, con el rango de períodos en el prompt: las estrategias S1, S2, S3, S5 y S6 acertaron las dos preguntas. S6 usó 3 llamadas en cada una. La llamada extra fue una corrección porque Gemini pasó `filters.marca` como texto (`"Brio"`) en lugar de lista.
- **Capa gratuita de Gemini:** cuota diaria baja y errores 503 por saturación.
- **Versiones comprobadas con Python 3.14:** `langgraph 1.2.16`, `langchain-core 1.6.13`, `langchain-google-genai 4.4.2`.
  - `GenericFakeChatModel` no implementa `bind_tools` ni `with_structured_output`.
  - `with_structured_output` de Gemini admite `include_raw=True`.
  - `ToolNode` solo se ejecuta dentro de un grafo.
  - Errores tipados de Gemini: `GoogleRateLimitError`, `GoogleAuthenticationError`, `GooglePermissionDeniedError`, `GoogleInvalidRequestError`, `GoogleModelNotFoundError`, `GoogleContextOverflowError` y `GoogleAPIError` (resto, incluidos 5xx).

## Goals / Non-Goals

**Goals:**
- Pocas llamadas al LLM: 2 en el caso típico (plan y síntesis) y 4 como máximo (más una corrección y un reintento de síntesis).
- Usar las primitivas estándar: `@tool` con `content_and_artifact`, `bind_tools`, `ToolNode`, `with_structured_output`, `with_retry` y `StateGraph` con `error_handler`.
- Que toda cifra de la respuesta se pueda rastrear hasta la evidencia que su afirmación cita.
- Probar el grafo completo sin red: con un modelo de chat falso con guion y las herramientas reales sobre bases reales cargadas en un directorio temporal.

**Non-Goals:**
- Conversación con memoria, *streaming* y caché.
- Subgrafos de contraste y causal (change 6). Aquí el contraste lo resuelve el plan general: métricas más documentos.

## Decisions

### D8a: estrategia "plan y ejecución" con llamadas a herramientas en paralelo
Con `bind_tools`, el LLM devuelve en **una** respuesta todas las llamadas a herramientas, y ese mensaje es el plan. `ToolNode` las ejecuta. El LLM solo vuelve a pedir herramientas en una corrección acotada; después, la síntesis no tiene herramientas.
- *Descartada: plan con esquema propio y ejecución en código (S3).* Usa 2 llamadas, pero reinventa `ToolNode`. Además, el validador `period` XOR `compare` no cabe en JSON Schema: un plan así inválido haría fallar el *parser* en lugar de pasar a la corrección.
- *Descartadas: ReAct libre y ReAct verificado (S1 y S2).* Hacen 2–6 llamadas según la pregunta y deciden consultas después de leer documentos, la vía de la inyección indirecta.
- *Descartada: extracción guiada (S4 y S5).* Solo admite una consulta de métricas por pregunta.
- *Descartadas: self-consistency, autocrítica del LLM y Chain-of-Verification con LLM.* Multiplican las llamadas. La verificación la hace el código.

### D8b: herramientas `@tool` con `content_and_artifact` y entradas tolerantes
`agent/tools.py` envuelve las tres funciones puras con `@tool(args_schema=…, response_format="content_and_artifact")`.
- **Entradas tolerantes** (`MetricToolInput`, `QualityToolInput`, `DocumentToolInput`): tienen los campos de los modelos estrictos, pero un validador previo convierte un valor suelto en lista de un elemento en los campos de lista y en los valores de `filters`. Después se construye el modelo estricto, que sigue validando todo lo demás. *Descartado: esquemas estrictos.* En la medición costaron una corrección.
- **Content (lo que lee el LLM):** un resumen JSON con estos campos:
  - **Métricas:** `evidence_id`, `periods`, filas (grupo, `rank`, `value`/`base`/`target`/`var_abs`/`var_pct` redondeados a 2 decimales), total, `warnings`, número y reglas de las `quality_notes`, y `corrections_count`.
  - **Calidad:** `evidence_id`, `issue_count`, `by_rule_action` y como mucho `max_quality_issues` incidencias.
  - **Documentos:** `evidence_id`, códigos de aviso y, por fragmento, el id (principal o `chunk_id`), `doc_id`, página, `evidence_ids` y texto.
- **Artifact (no va al LLM):** el resultado completo como modelo pydantic (`MetricResult`, `QualityResult`, `DocumentResult`); la traza lo serializa con `model_dump(mode="json")`. Lo usan la verificación y la traza. *Descartado: devolver el resultado completo al LLM.* Más tokens y más cuota, sin beneficio.
- **Descripciones:** la de `consultar_metrica` se genera con las métricas de `SemanticLayer`; la de `buscar_documentos` remite a la lista de documentos del prompt. Ninguna lleva valores de negocio escritos en el código.
- **Errores:** las herramientas propagan `QueryError`. `ToolNode(handle_tool_errors=…)` los convierte en un `ToolMessage` con estado `error`, con `field`, `invalid_value` y `valid_options`. Cuando los argumentos no cumplen el `args_schema`, `ToolNode` lanza `ToolInvocationError`, no `ValidationError`, así que el manejador se anota con `QueryError | ValidationError | ToolInvocationError` y devuelve el campo y el motivo. Ese manejador vive en un módulo **sin** `from __future__ import annotations`: con anotaciones diferidas, `ToolNode` no puede deducir los tipos en Python 3.14 (comprobado).

### D8c: grafo LangGraph
`StateGraph` con estado `TypedDict` (mensajes y campos del agente):

`check_question` → `load_context` → `plan` → (`route`) → `execute` → [`repair` → `execute`]? → `collect` → (`route`) → `synthesize` → `verify` → [`synthesize`]? → `respond`.

- **Sin llamadas a herramientas:** estado `fuera_de_alcance` con el mensaje fijo `out_of_scope_message` de `agent.yaml`. El texto del LLM solo va a la traza, para que no se cuelen cifras sin verificar.
- **Base de documentos ausente:** también da `data_unavailable`, aunque la pregunta sea solo de ventas. Se acepta para no ofrecer herramientas a medias; seguir sin documentos queda para un change futuro.

- **`load_context`:** abre las bases (si falta alguna, `data_unavailable`) y construye el catálogo, la lista de documentos (con sus `doc_id`, que usa la verificación) y el rango de períodos. La configuración del LLM se valida antes, en `build_deps`, al construir las dependencias, así que nunca se abre una base sin LLM configurado.
- **`plan` y `repair`:** `llm.bind_tools(tools)`. `repair` recibe el `AIMessage` original y un `ToolMessage` por llamada: el error en las fallidas y "ejecutada correctamente; resultado omitido" en las correctas. Así no ve texto de documentos y Gemini 3 conserva sus *thought signatures*, como se comprobó en el benchmark.
- **`execute`:** antes de ejecutar recorta las llamadas por encima de `max_calls_per_tool`, contando las consultas **correctas** de las dos rondas: corregir una consulta fallida no consume otro hueco (corrección tras la verificación de la implementación). Por cada llamada recortada emite un `ToolMessage` de error "descartada: máximo N" sin artifact: Gemini exige una respuesta por cada llamada a función cuando se le reenvía el `AIMessage` en la corrección. Después invoca `ToolNode` con `config={"max_concurrency": 1}`. *Descartada: la ejecución en paralelo por defecto.* Dos conexiones simultáneas a la misma base fallan, porque `open_readonly` fija `lock_configuration` (reproducido: 5 de 5 fallos). El coste es nulo: son consultas de milisegundos sobre DuckDB.
- **`collect`:** construye las evidencias desde los artifacts (`agent/evidence.py`), sin duplicar fragmentos, y los avisos. Declara en información insuficiente las consultas fallidas sin resolver: como una corrección no indica a qué consulta sustituye, por herramienta quedan `max(fallos de la ronda 1, consultas de la ronda 2) − correctas de la ronda 2`, con el detalle de la última ronda en que esa herramienta falló.
- **Errores:** el `error_handler` de nodo de LangGraph 1.2 (`add_node(..., error_handler=…)` en todos los nodos salvo `respond`; `set_node_defaults` también se lo daría a `respond` y un fallo ahí entraría en bucle, comprobado) convierte cualquier excepción en estado `error` con su código (`ProviderError` → código del proveedor, `DatabaseError` → `data_unavailable`, otras → `internal_error`) y va a `respond`, conservando lo ejecutado.
- **Límite de pasos:** `recursion_limit` fijo; los contadores de corrección y reintento están en el estado.
- *Descartadas:* la API funcional (aristas menos visibles en las pruebas) y `try/except` en cada nodo (duplica lo que da `error_handler`).

### D8d: proveedor Gemini
`agent/llm.py` crea `ChatGoogleGenerativeAI` con:
- `model`, `api_key` (`SecretStr`) y temperatura por prefijo;
- `max_output_tokens` y `timeout`;
- `max_retries=0`;
- `rate_limiter=InMemoryRateLimiter(requests_per_second=rpm/60, max_bucket_size=burst)`.

**Reintentos ante 500/503/504:** `Runnable.with_retry(retry_if_exception_type=(…), stop_after_attempt=n+1)` sobre el modelo ya ligado a herramientas o a la salida estructurada. Ante 429 no se reintenta, porque `GoogleRateLimitError` queda fuera de los tipos reintentables. *Descartados:* `max_retries` del cliente (también reintenta los 429 de cuota) y `RetryPolicy` de nodo (repetiría la ejecución de herramientas).

**`call_llm(runnable, messages)`:** mapea las excepciones a `ProviderError(code)` lanzado `from None`, con la clave eliminada del texto.
- `GoogleRateLimitError` → `quota_exhausted`;
- `GoogleAPIError` 5xx, tras los reintentos → `provider_unavailable`;
- `httpx.TimeoutException` y el tiempo agotado de google-genai → `timeout`;
- el resto (autenticación, permisos, petición inválida, modelo, contexto) → `provider_error`.

Solo convierte las excepciones del proveedor y de la red (`GoogleGenerativeAIError`, `ModelAPIError` de langchain-core, `httpx.HTTPError`, `TimeoutError`); un fallo del propio código se propaga y el grafo lo da como `internal_error`. Cuenta las llamadas lógicas (`llm_calls`) y los intentos (`llm_attempts`); `run_graph` toma una instantánea de los contadores al empezar, y la traza registra solo los de esa pregunta. Los intentos se cuentan con un contador **dentro** de la parte reintentada, porque `with_retry` los oculta. La espera entre intentos es `exponential_jitter_params={"initial": backoff_s}` (0 en las pruebas).

**Síntesis:** `with_structured_output(Synthesis, method="json_schema", include_raw=True)`. Un `parsing_error` cuenta como el reintento de síntesis; si se repite, el código es `invalid_output`. Si la primera síntesis se interpretó pero no pasó la verificación y la segunda no se puede interpretar, se aplica el fallo cerrado sobre la primera (ajuste de la implementación). La traza acumula los problemas de verificación de los dos intentos.

**Modelo falso para pruebas:** `ScriptedChatModel`, subclase de `GenericFakeChatModel` que implementa `bind_tools` (devuelve el mismo modelo) y `with_structured_output` (interpreta la llamada a herramienta o el JSON del mensaje con guion; admite `include_raw`), y registra los mensajes recibidos. *Descartada: una interfaz propia de LLM.* Ocultaría las primitivas de LangChain que el agente usa en producción.

### D8e: contexto de la planificación
- **Catálogo:** desde `SemanticLayer`.
- **Documentos:** `doc_id` y título desde la tabla `documents`.
- **Rango:** `min` y `max` de los meses válidos de `sales` y los trimestres que cubren (por ejemplo, "Datos disponibles: de 2026-01 a 2026-06 (trimestres 2026-T1, 2026-T2)"), con la regla "si la pregunta no indica el período, usa estos o los que cite el documento", tal como se midió.
- **Prompts:** en español, en `agent/prompts.py`, sin valores escritos a mano: el nombre del asistente (`assistant_name`) y los ejemplos de expresiones atenuadas (las tres primeras de `hedges`) salen de `agent.yaml`.

*Descartadas:* omitir el rango (con él fallaron S3 y S5 sin rango) y escribirlo en configuración (quedaría desfasado de la base).

### D8f: verificación por afirmación
- **Números de la evidencia:**
  - de los resultados de métricas y calidad, se recorren los **modelos pydantic** (sus campos `Decimal` e `int`), no el JSON del artifact, donde los `Decimal` son texto. Se excluyen `periods`, `sql_params`, `query`, `source_line` e identificadores;
  - de los fragmentos, se toma el texto literal.
- **Números de la afirmación:** se extraen tras eliminar las expresiones de período (`AAAA-Sn`, `AAAA-Tn`, `AAAA-MM` y `Tn` o `Sn` sueltos), los `evidence_id`, los `chunk_id` (`<doc_id>:NNN`), los `doc_id` de la tabla `documents` (sin ellos, `05_Reporte_Comercial` aportaba un 5) y los IDs de `DocumentsConfig.id_regex`. Lo mismo se aplica al texto de los fragmentos. Un número de cuatro dígitos solo se ignora si es un año del rango con datos; "1500 unidades" se verifica.
- **Información insuficiente:** la regla "sin cifras" se aplica a lo que escribe el LLM, no al texto que genera el código (por ejemplo, "Se retiró 1 afirmación no verificada"). Se normalizan `−` y `+`. "1.234" y "1,234" valen si cualquiera de sus dos lecturas coincide. La comparación ignora el signo y admite redondeo a 0–2 decimales.
- **Citas válidas:** `evidence_id` de los resultados, `chunk_id`, IDs principales y todos los `evidence_ids` de los fragmentos recuperados.
- **Léxico:** el causal (en hechos, contradicciones e información insuficiente) y las expresiones atenuadas (obligatorias en hipótesis), ambos en `agent.yaml`, con límites de palabra y sin distinguir mayúsculas ni tildes.
- *Descartado: el conjunto global de cifras del benchmark.* Aceptaba el `-23 %` del reporte como dato de ventas.
- *Descartado: un LLM como juez.* Más llamadas y más cuota.

### D8g: respuesta, traza y entrada
- **Identificadores en inglés** (convención del repo): `answer_question`, nodos `plan/execute/repair/synthesize/verify/respond`; `Synthesis(facts, hypotheses, contradictions, insufficient)` y `Claim(statement, evidence)`, con descripciones de campo en español, que es lo que lee el LLM.
- **`AgentResponse`:** `status`, `error_code`, `message`, los cuatro apartados, `warnings` y `trace`. La traza incluye consultas con artifact, correcciones, problemas, `llm_calls`, `llm_attempts`, `model` y `duration_ms`.
- **`answer_question(question, deps=None)`:** `AgentDeps` (capa semántica, rutas, configuración de documentos, embedder y modelo de chat) se construye desde `settings` salvo en las pruebas. Una configuración inválida devuelve estado `error` con código `configuration_error`, no una excepción; la CLI termina entonces con código 1.
- **CLI:** `python -m analyst_backend.agent`, con la pregunta en la variable `Q`.
- **`make ask Q=...`:** pasa las rutas de ventas, documentos y modelos y carga `ENV_FILE` (por defecto `.env`) solo si existe.

### D8h: configuración
`backend/config/agent.yaml`:
- `assistant_name`: el nombre con el que se presenta el asistente en los prompts;
- `provider.gemini`: `requests_per_minute`, `burst`, `timeout_s`, `max_output_tokens`, `unavailable_retries`, `backoff_s`, `temperature_by_prefix` y `default_temperature`;
- `limits`: `max_question_chars`, `max_calls_per_tool`, `max_quality_issues` y `docs_top_k`;
- `out_of_scope_message`;
- `causal_lexicon` y `hedges` (las tres primeras expresiones atenuadas sirven de ejemplo en el prompt y en los avisos).

`settings.py` añade `load_llm_settings()` y `load_agent_settings()`. `.env.example` añade `AGENT_CONFIG_PATH` y quita las variables de Ollama.

### D8i: pruebas
- **Unitarias:** configuración, settings, proveedor (modelo falso que lanza las excepciones de Gemini y `httpx.ReadTimeout`), herramientas y entradas tolerantes, contexto y verificación.
- **Grafo desde la primera tarea:** se construye completo en 5.1, con `synthesize` y `verify` provisionales que dejan pasar sin llamar al LLM, y luego se sustituyen en el grupo 7. Los guiones de las pruebas de los grupos 5 y 6 incluyen ya la respuesta de síntesis, que se consume cuando el nodo real existe.
- **Grafo:** `ScriptedChatModel` más fixtures compartidas en `backend/tests/agent/conftest.py`: la base de ventas real cargada con la ingesta y la de documentos con `FakeEmbedder`. Los `evidence_id` fijos dependen de la huella de `semantic_layer.yaml`, y se anota en las pruebas.
- **`llm`:** 2 preguntas con Gemini (como mucho 8 llamadas).
- **`project-layout`:** la prueba "Ninguna prueba llm registrada" pasa `LLM_TESTS` a un directorio vacío y `ENV_FILE=/dev/null`, para no cargar el `.env` ni usar la red desde `make test`.

### D8j: diferencias con lo medido y cambios en la arquitectura
- **No medido:**
  - las entradas tolerantes, que deberían bajar S6 de 3 a 2 llamadas;
  - la verificación por afirmación en lugar del conjunto global;
  - la intención explícita sustituida por "sin llamadas = fuera de alcance";
  - los topes de calidad;
  - el escape de delimitadores.

  Se comprobarán en las pruebas `llm` y en el change 9.
- **Tareas de documentación:**
  - `docs/architecture.md`: D8; solo Gemini (Ollama, posible change futuro); el grafo; las líneas de `langchain-ollama` y `GenericFakeChatModel`; el `LLMProvider` sin caché ni reintento ante cuota;
  - `openspec/config.yaml`: el contexto deja de mencionar Ollama;
  - ROADMAP: la nota de las tools queda confirmada con `ToolNode` y `content_and_artifact`.

## Risks / Trade-offs

- [Cuota gratuita de Gemini baja e impredecible] → 2–4 llamadas por pregunta, error `quota_exhausted` claro y sin reintentos, y pruebas `llm` limitadas a 2 preguntas.
- [Falsos negativos de la verificación: una cifra correcta atribuida a otra región, o "creció" con la cifra de una caída, porque se ignora el signo] → Riesgo aceptado y documentado con una prueba. El change 9 medirá la atribución.
- [Falsos positivos: cifras escritas en palabras o conteos] → Reintento con la lista de problemas y fallo cerrado; nunca se entrega una afirmación no verificada.
- [Inyección en documentos] → Plan antes de leer documentos, corrección sin texto de documentos, síntesis sin herramientas, delimitadores neutralizados y verificación de citas. No hay garantía total sobre la redacción.
- [El tope de salida de Gemini 3 incluye tokens de razonamiento y una síntesis puede truncarse] → El *parsing error* cuenta como reintento; si se repite, `invalid_output`. `max_output_tokens` se ajusta en `agent.yaml`.
- [Muestra pequeña con Gemini] → La elección se apoya también en el coste y en la investigación. Evaluación formal en el change 9.

## Migration Plan

Código nuevo, sin migración. Requiere `GEMINI_API_KEY` y `GEMINI_MODEL` en `.env` para `make ask` y `make test-llm`; `make test` no las necesita. Rollback: revertir el commit.
