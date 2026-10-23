# Tasks

## 1. Evidencias en la respuesta del agente

- [x] 1.1 (~1 h) Añadir `EvidenceView` y `AgentResponse.evidence` en `agent/models.py`; dar a `Evidence` los campos estructurados del origen (`doc_id`, `chunk_id`, `page`, herramienta; consulta y fragmentos en una búsqueda) en `agent/evidence.py`; construir las evidencias en `respond` (`agent/graph.py`) desde los artifacts de las consultas correctas, también en respuestas `error`
- [x] 1.2 (~45 min) Tests de los requisitos "Evidencias en la respuesta" (`EV-d5c128c22542` de tipo `metricas` con `Sur` primero y `-30.27`; `REP-01` → `05_Reporte_Comercial:004` con documento, página 1 y texto; `INV-01` citable en `:003` y `:018`; toda cita de la respuesta tiene su evidencia), la búsqueda (tipo `busqueda` con su consulta y `REP-01` entre sus fragmentos) y "Evidencias en respuestas con error" (cuota al sintetizar → `error`, sin hechos, con `EV-d5c128c22542`; cuota en la corrección → `error` con `EV-d5c128c22542`) en `backend/tests/agent/test_graph.py`; verificar que pasan junto con el resto de `backend/tests/agent/`

- [x] 1.3 (~45 min) Añadir `title` a `Evidence` y a `EvidenceView`, generado en `evidence_items` (métricas, calidad, fragmento con página o "sin página", búsqueda), con tests del requisito "Título de cada evidencia" (los cuatro escenarios con los títulos exactos) en `backend/tests/agent/test_evidence.py`; verificar que pasan junto con `backend/tests/agent/`

## 2. API de consulta

- [x] 2.1 (~1 h 30 min) Implementar `backend/src/analyst_backend/api/`: `AskRequest` (`StrictStr`, `extra="forbid"`), la tabla de estados HTTP, `POST /ask` síncrono con `threading.Lock` y la captura de cualquier excepción como `internal_error`. En `main.py`, `create_app(deps_factory=build_deps)` con las dependencias en el `lifespan`, el error guardado (configuración → `configuration_error`; cualquier otro → `internal_error`) y `internal_error` si faltan dependencias; `/health` como `async def`. Verificar que `backend/tests/test_health.py` sigue pasando
- [x] 2.2 (~45 min) Tests (con `with TestClient(...)`) de los requisitos:
  - "Pregunta por la API": pregunta de cifras → 200 con el hecho, la evidencia y la traza;
  - "Cuerpo de la petición": `{}`, `{"question": 123}` y `{"question": "hola", "history": [...]}` → 422 sin llamadas al LLM;
  - "Estado HTTP según el resultado": cuota → 429; `"   "` → 422 con `invalid_question`; fuera de alcance → 200; un código desconocido → 500;
  - "Fallos no controlados": excepción con `detalle-secreto` → 500 `internal_error` sin el texto; fallo de la API fuera del agente (manejador global) → 500 `internal_error` en JSON; fábrica que lanza un error que no es de configuración → `/health` 200 y pregunta 500 `internal_error`.

  En `backend/tests/api/test_ask.py`; verificar que pasan
- [x] 2.3 (~1 h) Tests de los requisitos:
  - "Dependencias del agente al arrancar": fábrica llamada una vez para dos preguntas, mismo cliente; `LLM_PROVIDER` vacía → `/health` 200 y pregunta 503 `configuration_error` con `LLM_PROVIDER`;
  - "Datos cargados después de arrancar": ventas ausente → 503 con `make ingest` y, tras crearla, 200 sin reiniciar; documentos ausente → 503 con `make ingest-docs`;
  - "Una pregunta a la vez": `run_graph` sustituido por una función con contador de ejecuciones activas y `threading.Event` (D9e) → máximo 1 simultánea y ambas 200; `/health` responde mientras una pregunta espera.

  Verificar que pasan

## 3. Interfaz del analista

- [x] 3.1 (~45 min) Añadir `httpx==0.28.1` a `frontend/pyproject.toml` y regenerar `uv.lock`; añadir `BACKEND_TIMEOUT_S` a `config.py` (vacía → 300; inválida → 300 con aviso); implementar `client.py` (`ask_backend` con `transport` opcional → respuesta del agente, tiempo agotado, API inaccesible para cualquier otro `httpx.TransportError`, o respuesta no reconocible con su estado HTTP); verificar con `uv sync --all-packages --locked`
- [x] 3.2 (~30 min) Tests del cliente con `httpx.MockTransport` (200 y 429 con cuerpo → respuesta del agente; texto plano 500 → no reconocible con `500`; `ConnectError` y `RemoteProtocolError` → inaccesible con la URL; `ReadTimeout` → tiempo agotado con los segundos; la petición lleva solo `{"question": ...}`) y de la lectura de `BACKEND_TIMEOUT_S` (`abc` e `inf` → 300 con aviso) en `frontend/tests/test_client.py`, sin abrir puertos; verificar que pasan
- [x] 3.3 (~1 h 30 min) Implementar `render.py` y `app.py` según D9c:
  - todo texto de la API con `st.text`; apartados; desplegables por id con todas sus evidencias (métricas, calidad, fragmento con página o "sin página", búsqueda);
  - avisos; traza con resumen y `st.json`; mensajes fijos por código;
  - historial con `st.chat_message`, aviso de independencia con `st.info`, pregunta pendiente con el campo desactivado y la respuesta guardada antes de pintar;
  - título y pie con `BACKEND_URL`.
- [x] 3.4 (~1 h 30 min) Tests con `AppTest` y `client.ask_backend` sustituido por un falso, de los requisitos:
  - "Pregunta y respuesta por apartados";
  - "Texto mostrado tal cual" (`Entre $1.000 y $2.000 **x** :red[y]`; `**negrita**` y `<b>etiqueta</b>`);
  - "Detalle de las evidencias" (`Sur` y `-30.27`; `REP-01` con texto, documento y página; `INV-01` con dos evidencias; búsqueda con su consulta y `REP-01`; calidad `DQ11` con sus 3 incidencias; fragmento sin página);
  - "Avisos y traza" (encabezado fijo seguido del aviso con `st.text`);
  - "Historial de la sesión";
  - "Pregunta en curso" (campo desactivado con una pregunta pendiente; respuesta guardada y campo activo);
  - "Mensajes de estado y de error" (cuota, datos sin cargar, configuración, fuera de alcance, insuficiente, otro error, sin bloquear otra pregunta);
  - "Respuesta no reconocible", "API inaccesible" (sin conexión y tiempo agotado en la página; la conexión cortada, en el cliente: `test_client.py`) y "Tiempo de espera configurable" (aviso en la página con `BACKEND_TIMEOUT_S=abc`).

  Verificar que pasan junto con `frontend/tests/test_app.py` (título y URL)

- [x] 3.5 (~45 min) Mostrar las evidencias por su título en `render.py` (un desplegable por evidencia con el título escapado; dentro, el id y sus ids citables; cita sin evidencia como texto con aviso) y adaptar `frontend/tests/test_page.py`: títulos en lugar de ids, "Id con varias evidencias" con dos desplegables, "Cita sin evidencia" y "Título con símbolos"; verificar que pasan todas las pruebas de `frontend/tests/`

## 4. Contenedores y `make up`

- [x] 4.1 (~45 min) `backend/Dockerfile`: `COPY backend/config /app/config`; `docker-compose.yml`: volúmenes de solo lectura con `DOCKER_DATA_DIR` y `DOCKER_MODELS_DIR`, rutas del backend en `environment`, `BACKEND_TIMEOUT_S` en el frontend y puertos en `127.0.0.1`; `.env.example`: `BACKEND_TIMEOUT_S`; verificar con `docker compose config`
- [x] 4.2 (~45 min) `Makefile`: `DOCKER_DATA_DIR ?= data/processed`, `DOCKER_MODELS_DIR ?= $(MODELS_CACHE_DIR)`, objetivo `up-check` (ventas → `make ingest`; documentos → `make ingest-docs`; modelo con `models_cli --check`, pasando `MODELS_CACHE_DIR` y `DOCUMENTS_CONFIG_PATH`, → `make models`) y `up`, que depende de él y pasa ambas variables con `$(abspath ...)`; verificar con `make up-check` sobre los datos reales y `make -n up`
- [x] 4.3 (~1 h) Tests sin levantar contenedores, en `tests/test_compose.py` y `tests/test_makefile.py`:
  - fixture de compose interpolado en una copia temporal con entorno limpio (D9e);
  - "Datos del host en el backend": volúmenes `bind` y `read_only`; rutas del contenedor aunque `.env` defina `DUCKDB_PATH=otra/ruta.duckdb`; `COPY backend/config /app/config` en el Dockerfile; los directorios de `make -n up` resueltos por compose;
  - "Tiempo de espera de la interfaz en contenedores" (`BACKEND_TIMEOUT_S=600`);
  - "Puertos solo en la máquina local" (`host_ip` `127.0.0.1`);
  - "Comprobación antes de arrancar": bases vacías → `make ingest`; sin documentos → `make ingest-docs`; caché vacía → `make models`.

  Verificar que pasan junto con las pruebas existentes de compose y Makefile
- [x] 4.4 (~45 min) Prueba manual de punta a punta:
  1. `make up`;
  2. la pregunta de la región con mayor caída desde `http://localhost:8501` (como mucho 4 llamadas a Gemini);
  3. comprobar los apartados, el detalle de `EV-…` y de un fragmento, la traza y que la búsqueda no avisa de modo léxico (el modelo funciona con el montaje `:ro`);
  4. `docker compose down`.

  Anotar el resultado en esta tarea
  - Resultado (2026-10-22): `make up` construye y arranca; `/health` y la interfaz responden; la búsqueda funciona en modo híbrido con el modelo montado en solo lectura; los errores llegan con su estado HTTP y las evidencias conservadas. Con 120 s y sin límite de razonamiento, la síntesis agotaba el tiempo; tras D9g, las preguntas del responsable desde la interfaz respondieron 200 y él valida la aplicación. Riesgo residual de timeouts con preguntas amplias (D9g)

- [x] 4.5 (~20 min) Ajustes de la prueba manual (D9g): `max_calls_per_tool` 5 y `timeout_s` 240 en `agent.yaml`; las pruebas de máximos fijan 3 en su configuración; `test_config.py` comprueba los valores nuevos; verificar con `make test`
- [x] 4.6 (~45 min) Razonamiento limitado en la síntesis (D9g): `synthesis_reasoning_by_prefix` en `GeminiConfig` y `agent.yaml`, `LLMClient.structured` con `reasoning_effort` solo en la síntesis; tests del requisito "Razonamiento limitado en la síntesis" (síntesis `low` y plan sin fijar con `gemini-3-flash`; nada con `gemini-2.5-flash`; valor no admitido) en `test_llm.py` y `test_config.py`; medir con Gemini en Docker la pregunta "¿Son consistentes las principales conclusiones del reporte comercial con los datos de ventas?" (como mucho 4 llamadas) y anotar el tiempo
  - Resultado (2026-10-22, Docker, gemini-3.8-flash): 1.º intento `ok` en 21 s; 2.º intento `timeout` a los 240 s en la planificación, que entonces no tenía el razonamiento limitado (ver 4.7)
- [x] 4.7 (~30 min) Razonamiento configurable también en la planificación y la corrección (D9g): `plan_reasoning_by_prefix` en `GeminiConfig` y `agent.yaml`, `LLMClient.with_tools` con `reasoning_effort`; tests del requisito "Razonamiento configurable por paso" (ambos pasos `low` con `gemini-3-flash`; solo la síntesis; nada con `gemini-2.5-flash`; valor no admitido) en `test_llm.py` y `test_config.py`; `make test-llm` 2 de 2 en 43 s; en Docker, pregunta causal en 18 s y pregunta amplia 22 s / `timeout` en la síntesis a los 240 s

## 5. Documentación

- [x] 5.1 (~45 min) Documentación:
  - README: `make up` (requisitos previos `make ingest`, `make models`, `make ingest-docs` y Gemini en `.env`; volver a ejecutar `make up` tras cambiar `.env`; `DOCKER_DATA_DIR` y `DOCKER_MODELS_DIR` como variables de `make` (absolutas o con `./` si se usa `docker compose` directamente), `BACKEND_TIMEOUT_S`; puertos locales; nombres fijos de las bases; permisos de lectura para el uid 1000) y `POST /ask` con un ejemplo de `curl`;
  - `docs/architecture.md`: D9 y la sección de componentes;
  - ROADMAP: el change 8 se adelanta al 6 y su estado.

  Verificar que los comandos documentados existen en el `Makefile`

## 6. Cierre

- [x] 6.1 (~15 min) Ejecutar `make test`; verificar que todo pasa
- [x] 6.2 (~10 min) Ejecutar `graphify update .` y `openspec validate --all --strict`; verificar que ambos terminan sin errores

## Workflow follow-up

- `/verify-change add-api-and-ui` y punto de control 5B.
- `/opsx:archive add-api-and-ui` solo con la aprobación explícita del responsable; después, ROADMAP y mensaje de commit (punto de control 5C).
