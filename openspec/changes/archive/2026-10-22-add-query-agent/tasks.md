# Tasks

## 1. Dependencias y configuración

- [x] 1.1 (~20 min) Añadir langgraph==1.2.16, langchain-core==1.6.13 y langchain-google-genai==4.4.2 a `backend/pyproject.toml`; regenerar `uv.lock`; verificar con `uv sync --all-packages --locked` y `make test`
- [x] 1.2 (~45 min) Crear `backend/config/agent.yaml` (`provider.gemini`, `limits`, `out_of_scope_message`, `causal_lexicon`, `hedges`) y `agent/config.py` (carga y validación con pydantic), con tests de configuración; verificar que pasan
- [x] 1.3 (~45 min) Añadir a `settings.py` `load_llm_settings()` (`LLM_PROVIDER`, `GEMINI_MODEL`, `GEMINI_API_KEY` como `SecretStr`) y `load_agent_settings()`; añadir `AGENT_CONFIG_PATH` y quitar las variables de Ollama de `.env.example`; añadir `AGENT_CONFIG_PATH` al `Makefile`; tests de settings; verificar que pasan

## 2. Proveedor de LLM

- [x] 2.1 (~1 h) Implementar en `agent/llm.py` la creación de `ChatGoogleGenerativeAI` (temperatura por prefijo, `max_output_tokens`, `timeout`, `max_retries=0`, `InMemoryRateLimiter`) y la selección de proveedor según `LLM_PROVIDER`
- [x] 2.2 (~30 min) Tests de los requisitos "Selección del proveedor" (`ollama`, ausente, clave vacía) y "Parámetros del modelo en configuración" (temperatura por prefijo; dos llamadas separadas al menos 1 s con 60 por minuto y ráfaga 1) en `backend/tests/agent/test_llm.py`; verificar que pasan
- [x] 2.3 (~1 h) Implementar `call_llm` (mapeo a `quota_exhausted`, `provider_unavailable`, `timeout` y `provider_error`; `ProviderError` lanzado `from None` y sin la clave; contador de llamadas, y de intentos dentro de la parte reintentada) y los reintentos ante 5xx con `with_retry` (`exponential_jitter_params` según `backoff_s`)
- [x] 2.4 (~30 min) Tests del requisito "Errores del proveedor" con un modelo falso que lanza las excepciones de `langchain-google-genai` y `httpx.ReadTimeout` (429 → 1 petición; 503 y después bien → 2; 503 siempre → 3 y `provider_unavailable`; tiempo agotado → `timeout`; autenticación → `provider_error` sin reintento); verificar que pasan
- [x] 2.5 (~15 min) Tests del requisito "Clave nunca expuesta" (error con `clave-de-prueba-123` en el texto → ni el mensaje ni `__cause__` la contienen); verificar que pasan
- [x] 2.6 (~45 min) Implementar `ScriptedChatModel` en `backend/tests/agent/fakes.py` (subclase de `GenericFakeChatModel` con `bind_tools`, `with_structured_output` con `include_raw` y registro de mensajes), con un test propio; verificar que pasa

## 3. Herramientas

- [x] 3.1 (~1 h 30 min) Implementar en `agent/tools.py` las entradas tolerantes (`MetricToolInput`, `QualityToolInput`, `DocumentToolInput`) y las tres `@tool` con `content_and_artifact` (resumen JSON según D8b y artifact completo), propagando `QueryError`; y en `agent/tool_errors.py` (sin `from __future__ import annotations`) el manejador de `ToolNode` para `QueryError`, `ValidationError` y `ToolInvocationError`
- [x] 3.2 (~45 min) Tests de las herramientas (campos del resumen y artifact completo de las tres; `QueryError` de `Zeta` propagado; conversión a lista en cada entrada tolerante; manejador con `ToolInvocationError` → campo y motivo) en `backend/tests/agent/test_tools.py`; verificar que pasan

## 4. Contexto de la planificación

- [x] 4.1 (~1 h) Implementar en `agent/context.py` el catálogo desde `SemanticLayer`, los documentos desde `documents` y el rango de meses y trimestres con datos desde `sales`; y en `agent/prompts.py` las plantillas en español de planificación, corrección y síntesis
- [x] 4.2 (~30 min) Tests del requisito "Contexto de la planificación" (rango `2026-01` a `2026-06` con `2026-T1` y `2026-T2` sobre la base real; marca `Prueba` en una capa semántica de prueba; regla de período presente) en `backend/tests/agent/test_context.py`; verificar que pasan

## 5. Grafo: esqueleto y validación

- [x] 5.1 (~1 h 30 min) Implementar `agent/models.py` (`Claim`, `Synthesis`, `Evidence`, `AgentResponse`, `Trace`, `AgentDeps`) y en `agent/graph.py` el grafo completo: estado, nodos `check_question`, `load_context` y `respond`, nodos `plan`, `execute`, `repair`, `collect`, `synthesize` y `verify` provisionales (dejan pasar sin llamar al LLM) y el `error_handler` del grafo (`ProviderError`, `DatabaseError` → `data_unavailable`, otras → `internal_error`); crear `backend/tests/agent/conftest.py` con las bases reales en un directorio temporal
- [x] 5.2 (~15 min) Tests del requisito "Validación de la pregunta" (pregunta vacía y pregunta un carácter más larga que el máximo → `invalid_question` y 0 llamadas); verificar que pasan

## 6. Grafo: plan, ejecución y corrección

- [x] 6.1 (~1 h 30 min) Implementar los nodos `plan` (`bind_tools`; sin llamadas → `fuera_de_alcance` con el mensaje fijo y el texto del LLM solo en la traza), `execute` (recorte por `max_calls_per_tool` con aviso y `ToolMessage` de descarte; `ToolNode` con `handle_tool_errors` y `max_concurrency=1`) y `collect` (evidencias desde los artifacts, sin duplicados; validez; avisos de las herramientas), con la ruta a `respond` si no hay evidencia válida
- [x] 6.2 (~45 min) Tests del requisito "Planificación en una sola respuesta" (consulta exacta → `EV-d5c128c22542` con `Sur` primero y `-30.27`; fuera de alcance → mensaje fijo sin el texto del LLM, sin herramientas y 1 llamada; dos `consultar_metrica` en la misma respuesta → ambas con `evidence_id`; 5 búsquedas → 3 y el aviso exacto) en `backend/tests/agent/test_graph.py`. Los guiones incluyen la respuesta de síntesis para que sigan valiendo con el nodo real; verificar que pasan
- [x] 6.3 (~30 min) Tests del requisito "Argumentos tolerantes" (`filters={marca: "Brío"}` → sin corrección y `EV-d5c128c22542`; además, prueba directa de las tres entradas tolerantes); verificar que pasan
- [x] 6.4 (~1 h) Implementar el nodo `repair` (una corrección con el `AIMessage` original y un `ToolMessage` por cada llamada pedida: error, descartada o "resultado omitido"; máximos aplicados al total; fallos persistentes a información insuficiente con campo y valor)
- [x] 6.5 (~1 h) Tests del requisito "Corrección única" (`Zeta` → la corrección incluye `filters.marca`, `Zeta` y las cinco marcas; `period` y `compare` a la vez → error de validación con el motivo; 4 búsquedas y `Zeta` → una respuesta por cada consulta pedida, con la sobrante descartada; búsqueda correcta + `Zeta` → la corrección no contiene texto de fragmentos; `Zeta` dos veces → sin segunda corrección e insuficiente con `filters.marca` y `Zeta`); verificar que pasan
- [x] 6.6 (~20 min) Tests del requisito "Evidencia válida y avisos" (`2025-T1` → estado `insuficiente`, aviso `El período 2025-T1 no tiene datos en la base` y sin llamada de síntesis); verificar que pasan
- [x] 6.7 (~15 min) Tests del requisito "Sin evidencia, sin síntesis" (todo falla también tras la corrección → `insuficiente` y 2 llamadas); verificar que pasan

## 7. Grafo: síntesis, verificación y respuesta

- [x] 7.1 (~1 h) Implementar el nodo `synthesize` (evidencia delimitada con los delimitadores neutralizados, reglas al final, `with_structured_output(include_raw=True)`; un error de interpretación cuenta como reintento y el segundo da `invalid_output`)
- [x] 7.2 (~30 min) Tests del requisito "Síntesis estructurada" (`OC-EXT-06` entre delimitadores y reglas después; fragmento con el delimitador de cierre neutralizado; dos respuestas no interpretables → `invalid_output`); verificar que pasan
- [x] 7.3 (~1 h 30 min) Implementar en `agent/verify.py` la verificación de cifras por afirmación (números de los modelos pydantic y del texto de los fragmentos; eliminación de períodos —incluidos `Tn` y `Sn` sueltos—, años del rango e IDs; formatos es/en ambiguos; sin signo; redondeo de 0–2 decimales; sin cifras en lo que el LLM escribe en información insuficiente)
- [x] 7.4 (~45 min) Tests del requisito "Verificación de cifras" (−23 % citando solo `EV-d5c128c22542` → rechazo; citando `REP-01` y `05_Reporte_Comercial:003` → aceptado; solo `REP-01` → rechazo; `1500 unidades` → rechazo; "Sur cayó 30,27 %" → aceptado; riesgo documentado: cifra correcta atribuida a otra región se acepta) en `backend/tests/agent/test_verify.py`; verificar que pasan
- [x] 7.5 (~45 min) Implementar la verificación de citas (ids de la ejecución, `chunk_id` y `evidence_ids` de fragmentos; al menos una en hechos, hipótesis y contradicciones) y de lenguaje (léxico causal en hechos, contradicciones e insuficiente; expresión atenuada obligatoria en hipótesis)
- [x] 7.6 (~30 min) Tests del requisito "Verificación de citas y lenguaje" (`REP-99`; `INV-01` vía el índice de referencias; lenguaje causal; hipótesis sin atenuar); verificar que pasan
- [x] 7.7 (~1 h) Implementar el reintento de síntesis con la lista de problemas, el fallo cerrado (estado `insuficiente` si no queda ningún hecho ni contradicción) y el nodo `respond` completo (apartados, avisos y traza con artifacts, llamadas, intentos, modelo y duración)
- [x] 7.8 (~30 min) Tests del requisito "Reintento y fallo cerrado" (`REP-99` y después `REP-01` → 1 reintento; cifra sin respaldo dos veces → hecho retirado y `Se retiró 1 afirmación no verificada`); verificar que pasan
- [x] 7.9 (~20 min) Tests del requisito "Respuesta y traza" (2 llamadas, consulta con `EV-d5c128c22542` y su resultado completo, verificación sin problemas); verificar que pasan
- [x] 7.10 (~30 min) Tests del requisito "Errores del proveedor y de los datos" (cuota en el plan → `error` sin hechos; cuota en la síntesis → traza con las consultas; base de ventas ausente → `data_unavailable`, `make ingest` y 0 llamadas; clave fuera de la respuesta y de la traza); verificar que pasan

## 8. Entrada y pruebas con Gemini

- [x] 8.1 (~45 min) Implementar `answer_question()`, `agent/__main__.py` (pregunta en `Q`; respuesta por apartados con evidencias y avisos; código 1 si falta configuración) y `make ask` (rutas de ventas, documentos y modelos; `ENV_FILE` solo si existe)
- [x] 8.2 (~20 min) Tests del requisito "Comando de consulta" (`ENV_FILE=/dev/null`, `LLM_PROVIDER=gemini`, `GEMINI_MODEL` con valor y clave vacía → código distinto de 0 y `GEMINI_API_KEY`); verificar que pasan
- [x] 8.3 (~30 min) Hacer que `make test-llm` acepte `LLM_TESTS` y cargue `ENV_FILE` solo si existe
- [x] 8.4 (~30 min) Tests del requisito modificado "Pruebas con LLM separadas" (directorio sin pruebas `llm` → código 0 y "No hay pruebas llm", con `ENV_FILE=/dev/null`; `ENV_FILE` inexistente → código 0; recolección solo de pruebas `llm`) adaptando `tests/test_makefile.py`; verificar con `make test`
- [x] 8.5 (~30 min) Tests `@pytest.mark.llm` del requisito "Respuesta con el modelo real" (región con mayor caída → `ok` con `Sur` y `30.27`/`30,27`; consistencia del reporte → contradicción con `Sur`, `evidence_id` de ventas y evidencia del reporte); verificar con `make test-llm` (como mucho 8 llamadas)

## 9. Documentación

- [x] 9.1 (~45 min) Registrar D8 en `docs/architecture.md` y actualizar el LLM (solo Gemini), el grafo, `langchain-ollama`, `GenericFakeChatModel` y el `LLMProvider`; actualizar el contexto de `openspec/config.yaml`; documentar en `README.md` `make ask` y la configuración de Gemini; actualizar en el ROADMAP la nota de las tools (`ToolNode` y `content_and_artifact`) y el resumen del benchmark

## 10. Cierre

- [x] 10.1 (~15 min) Ejecutar `make test` y `make test-llm`; verificar que todo pasa
- [x] 10.2 (~10 min) Actualizar `openspec/ROADMAP.md` (change 5 implementado)
- [x] 10.3 (~10 min) Ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores

## 11. Correcciones de la verificación (`/verify-change`, 2026-10-22)

- [x] 11.1 (~45 min) B1: la verificación de cifras ignora los `doc_id` de la tabla `documents` (contexto con `document_ids`); tests del nombre de documento en hechos e hipótesis y de una cifra junto al nombre
- [x] 11.2 (~45 min) I1: el máximo por herramienta cuenta solo las consultas correctas y se declaran todas las consultas fallidas sin resolver; tests de corrección parcial, con el máximo ocupado y descartada
- [x] 11.3 (~20 min) I2: la descripción de `consultar_metrica` sale de la capa semántica y la de `buscar_documentos` no lista documentos; test con una capa de una sola métrica
- [x] 11.4 (~20 min) I3: `answer_question` devuelve `configuration_error` en lugar de lanzar; la CLI termina con código 1; test
- [x] 11.5 (~45 min) Menores: D8c al día; traza por pregunta; problemas sin repetir; `assistant_name` en `agent.yaml` y textos fijos en `prompts.py`; solo las excepciones del proveedor se convierten; aviso en singular; tests más estrictos (texto de fragmentos, prompt completo, límite de peticiones y tiempo máximo); identificadores en inglés en los tests
- [x] 11.6 (~15 min) Actualizar specs y design; ejecutar `make test`, `make test-llm`, `graphify update .` y `openspec validate --all`
- [x] 11.7 (~30 min) Menores de la segunda verificación: prueba de grafo completo con un nombre de documento en la afirmación (`document_ids` en el nodo `verify`); nombre del asistente y ejemplos de atenuación desde `agent.yaml`, con sus escenarios y tests
