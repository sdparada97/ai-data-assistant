# Design

## Context

Ver `proposal.md` (Why). Estado actual:

- **Backend:** `backend/src/analyst_backend/main.py` crea la app FastAPI con solo `GET /health`. El agente se usa con `answer_question(question, deps=None)` (`agent/service.py`), que construye `AgentDeps` con `build_deps()` y devuelve `AgentResponse`. Los errores de configuración, datos y proveedor vuelven como respuesta con código; un fallo fuera de los nodos del grafo, en cambio, se propaga como excepción.
- **Frontend:** `frontend/src/analyst_frontend/app.py` solo muestra el título (`APP_TITLE`) y la URL de la API (`BACKEND_URL`), y su única dependencia es `streamlit`. No puede importar el backend: van en contenedores distintos.
- **Contenedores:**
  - la imagen del backend instala el paquete sin `backend/config/`, y `.dockerignore` excluye `data/` y `.cache/`;
  - compose publica los puertos en todas las interfaces y pasa `.env` solo al backend.
- **Comprobado:**
  - fastembed (`local_files_only=True`) y DuckDB en solo lectura funcionan con copias del modelo y de las bases sin permiso de escritura (`chmod -R a-w`);
  - los enlaces de la caché de Hugging Face son relativos (`snapshots/` → `blobs/`);
  - `models_cli --check` falla con código 1 y nombra `make models`;
  - Docker 29.8 y compose 5.6 están instalados;
  - en esta máquina (WSL en modo espejo), conectar a un puerto cerrado de `127.0.0.1` tarda ~130 s, así que las pruebas no deben abrir conexiones reales.

## Goals / Non-Goals

**Goals:**
- `make up` deja la aplicación usable en `http://localhost:8501` con los datos preparados en el host.
- La interfaz no repite lógica del agente: muestra lo que devuelve la API, con las evidencias ya resueltas.
- Pruebas sin red, sin Docker en ejecución y sin LLM real.

**Non-Goals:**
- Rendimiento con varios usuarios, *streaming*, autenticación.
- Cambiar el comportamiento del agente, más allá de añadir las evidencias a la respuesta.

## Decisions

### D9a: `POST /ask` síncrono con dependencias de proceso y un candado
- **Arranque:** `create_app(deps_factory=build_deps)` construye las dependencias en el `lifespan` de FastAPI, una vez por proceso, y las guarda en `app.state`.
  - Si fallan por configuración (`CONFIGURATION_ERRORS` de `agent/service.py`), guarda el error, la app arranca y cada pregunta devuelve `configuration_error`, con la misma respuesta que `answer_question`.
  - Si fallan con otra excepción, también se guarda el error: el backend arranca, `/health` responde y cada pregunta devuelve `internal_error`, sin el texto de la excepción. Así la regla "Salud del backend" (sin depender de datos, credenciales ni LLM) se cumple siempre.
  - Si `app.state` no tiene dependencias ni error (por ejemplo, el `lifespan` no se ejecutó), `/ask` responde `internal_error`.
- **Endpoint `/ask`:** síncrono (`def`); FastAPI lo ejecuta en su pool de hilos.
  - Un `threading.Lock` hace que se responda una pregunta a la vez; las demás esperan. Así el `InMemoryRateLimiter`, los contadores del `LLMClient` y el embedder (que carga el modelo una vez, en la primera búsqueda) no se usan a la vez.
  - Captura cualquier excepción y devuelve `internal_error` (500), sin el texto de la excepción. Cubre un fallo en `respond`, `GraphRecursionError` o `build_graph`.
  - Para cualquier fallo de la API fuera del agente (por ejemplo, al preparar la respuesta HTTP), un manejador global (`add_exception_handler(Exception, unhandled_error)`) devuelve la misma respuesta `internal_error` en JSON, en lugar del 500 en texto plano de FastAPI.
- **`/health`:** pasa a `async def`, para que no ocupe un hilo del pool y siga respondiendo aunque haya preguntas esperando el candado.
- **Bases:** se abren en cada pregunta, como ya hace el grafo (`load_context`). Por eso un `make ingest` posterior se usa sin reiniciar.
- **Estados HTTP:** la tabla vive en el módulo de la API. El cuerpo siempre es `AgentResponse`, salvo el 422 de validación de la petición.
- **Petición:** `AskRequest(question: StrictStr)` con `extra="forbid"`. Un historial u otros campos se rechazan, lo que refuerza que el agente no tiene memoria. La pregunta vacía o demasiado larga la valida el agente (`invalid_question`), para no duplicar el límite.
- *Descartadas:*
  - dependencias por petición: el límite de peticiones no se compartiría y el modelo de embeddings se cargaría en cada pregunta;
  - una cola con un trabajador o `asyncio`: más piezas para un solo analista;
  - responder 409 si hay otra pregunta en curso: obligaría a la interfaz a reintentar;
  - un plazo total por pregunta en el backend: una llamada síncrona al LLM no se puede cancelar a medias sin hilos adicionales (ver Risks).

### D9b: evidencias resueltas en `AgentResponse`
- `AgentResponse.evidence: list[EvidenceView]`, con:
  - `id`, `kind`, `citable_ids` (ordenados) y `source` (`tool`; o `doc_id`, `chunk_id` y `page`, que puede ser nula);
  - `text` en los fragmentos y `result` en métricas y calidad (`model_dump(mode="json")`, donde los `Decimal` llegan como texto, por ejemplo `"-30.27"`);
  - en una búsqueda, `query` y `fragment_ids`, sin repetir los textos;
  - `title`: un título legible para la interfaz, generado en `evidence_items` sin el LLM. Pedido por el responsable tras probar la interfaz (2026-10-22):
    - métricas: métricas, agrupación, filtros y períodos de `MetricResult.query` (`Venta neta por region · marca Brio · 2026-T1 frente a 2026-T2`);
    - calidad: reglas, filtros y períodos de `QualityResult.query`;
    - fragmento: título del documento, sección y página (`DocumentHit.title`, `section`, `page`);
    - búsqueda: el texto buscado.

    Los nombres de métricas y dimensiones van con espacios en vez de guiones bajos, y los filtros con su valor del catálogo (`Brio`, el filtro real), para no escribir traducciones en el código. *Descartado: que el LLM titule las evidencias.* Gastaría llamadas y podría inventar.
- **Construcción:** `respond` las construye directamente desde los artifacts de las consultas correctas (`state["artifacts"]`, con `evidence_items` e `index` de `agent/evidence.py`), no desde `state["evidence"]`. Así también salen cuando el fallo ocurre antes de `collect`, por ejemplo en `repair`. `Evidence` gana los campos estructurados del origen, que hoy solo están como texto en `extra`.
- Un id citable puede corresponder a varias evidencias: `INV-01` está en su fragmento y en el índice de la investigación. `citable_ids` lo refleja y la interfaz muestra todas.
- *Descartado: que la interfaz reconstruya las evidencias desde la traza.* Duplicaría en el frontend la regla de alias.
- *Descartado: referenciar el resultado por `evidence_id` en vez de copiarlo.* El resultado pesa pocos KB y la interfaz queda más simple.

### D9c: interfaz Streamlit en tres módulos
- **`client.py`:**
  - `ask_backend(url, question, timeout, transport=None) -> AskOutcome`, con `httpx`;
  - cuatro casos:
    - respuesta del agente: cualquier estado HTTP con un JSON que tenga `status` y `trace`;
    - tiempo agotado: `httpx.TimeoutException`;
    - API inaccesible: cualquier otro `httpx.TransportError`, como `ConnectError`, o `RemoteProtocolError` y `ReadError` si el backend se reinicia a mitad de una pregunta;
    - respuesta no reconocible: con el estado HTTP;
  - las páginas llaman a `client.ask_backend` a través del módulo (`from analyst_frontend import client`), para que las pruebas puedan sustituirlo.
- **`render.py`:** funciones que reciben diccionarios y pintan con Streamlit. **Todo texto que viene del LLM, de los documentos o de la API se pinta con `st.text`**, que no interpreta Markdown, HTML, fórmulas, colores ni emojis abreviados. `st.warning`, `st.error` y `st.info` solo llevan textos fijos de la interfaz.
  - **Apartados:** un encabezado fijo por apartado y, por afirmación, `st.text` con el enunciado y, debajo, un desplegable por evidencia citada, con su `title` como etiqueta. Dentro, la primera línea es el id y los ids citables. Una cita sin evidencia se muestra como texto con el id y el aviso. La pregunta del analista en el historial también va con `st.text`.
  - **Excepción documentada:** las etiquetas de `st.expander` (los títulos) se interpretan como Markdown. Pueden traer texto de los documentos, así que se escapan: `\` antes de cada signo de puntuación ASCII, lo que cubre `$`, `*`, `:`, `[`, `<` y el resto.
  - **Evidencias:** por id citado, un `st.expander` por cada evidencia cuyo `citable_ids` lo contiene, titulado con su `title`.
    - Métricas: `st.dataframe` con una fila por grupo y los valores tal como vienen, sin redondear (base, objetivo, variación absoluta y `var_pct`; o `value`).
    - Calidad: sus incidencias en tabla.
    - Fragmentos: `st.text` con el texto, más documento y página, o "sin página".
    - Búsqueda: la consulta y los ids de sus fragmentos.
    - Las evidencias que ninguna afirmación cita (por ejemplo, en una respuesta `error`) no tienen desplegable propio: se ven en la traza (`st.json`). Es intencionado, para que los apartados solo muestren lo citado.
  - **Avisos:** `st.warning("Avisos sobre los datos")` seguido de `st.text` por aviso.
  - **Traza:** `st.expander` con un resumen (modelo, llamadas, intentos, duración, consultas con estado y `evidence_id`, problemas) y `st.json` con la traza completa.
  - **Mensajes por código:** textos fijos en `render.py`. En `data_unavailable` y `configuration_error` se añade el mensaje de la API con `st.text`. En `configuration_error` se recuerda que, tras corregir `.env`, hay que volver a ejecutar `make up`.
- **`app.py`:**
  - título (`APP_TITLE`), el aviso fijo de independencia con `st.info` (no `st.caption`, que ya usa la URL en la prueba de "Página mínima") y el pie `st.caption` con `BACKEND_URL`;
  - historial en `st.session_state`, pintado con `st.chat_message`.
- **Pregunta en curso:**
  1. Al enviar, la pregunta se añade al historial como pendiente y se vuelve a ejecutar el script (`st.rerun`).
  2. Con una pendiente, `st.chat_input(disabled=True)` y la llamada a la API dentro de `st.spinner`.
  3. El resultado se guarda en `st.session_state` dentro del bloque `st.spinner`, justo después de la llamada y antes de cualquier otro elemento. Al salir del bloque Streamlit emite un elemento, y una petición de volver a ejecutar podría interrumpir ahí. Después se vuelve a ejecutar el script.

  Si Streamlit interrumpe el script después, la respuesta ya está guardada.
- **`config.py`:** lee `BACKEND_TIMEOUT_S`. Si está vacía, 300; si no es un número positivo y finito (`inf` no vale), 300 y un aviso fijo en la página que nombra la variable.
- **Dependencia:** `httpx==0.28.1`, la misma versión que el backend, como dependencia directa del frontend.
- *Descartadas:*
  - escapar el Markdown y usar `st.markdown`: Streamlit interpreta además `$…$`, `:color[…]` y emojis abreviados, y un escape incompleto deja pasar formato;
  - importar los modelos pydantic del backend: acopla las imágenes;
  - otra interfaz (Gradio, React): la arquitectura fija Streamlit.

### D9d: contenedores con datos del host
- **`docker-compose.yml`, servicio `backend`:**
  - `volumes`: `${DOCKER_DATA_DIR:-./data/processed}:/data/processed:ro` y `${DOCKER_MODELS_DIR:-./.cache/models}:/models:ro`. Se monta la caché completa por los enlaces relativos de Hugging Face;
  - `environment`: `DUCKDB_PATH=/data/processed/analytics.duckdb`, `DOCUMENTS_DB_PATH=/data/processed/documents.duckdb`, `MODELS_CACHE_DIR=/models` y `AGENT_CONFIG_PATH`, `SEMANTIC_LAYER_PATH` y `DOCUMENTS_CONFIG_PATH` en `/app/config/`. `environment` prevalece sobre `env_file` (comprobado con `docker compose config`);
  - puerto `127.0.0.1:${BACKEND_PORT:-8000}:8000`.
- **Servicio `frontend`:** puerto `127.0.0.1:${FRONTEND_PORT:-8501}:8501` y `BACKEND_TIMEOUT_S: ${BACKEND_TIMEOUT_S:-}`, como `APP_TITLE`. `.env.example` documenta `BACKEND_TIMEOUT_S`. Compose lo interpola desde el `.env` del directorio, aunque el contenedor del frontend no cargue `.env`.
- **`backend/Dockerfile`:** `COPY backend/config /app/config` en la etapa final.
- **Nombres fijos dentro del contenedor:** las bases deben llamarse `analytics.duckdb` y `documents.duckdb` dentro de `DOCKER_DATA_DIR`, que son los nombres por defecto de `make ingest` y `make ingest-docs`.
- **Makefile:**
  - `DOCKER_DATA_DIR ?= data/processed` y `DOCKER_MODELS_DIR ?= $(MODELS_CACHE_DIR)`;
  - el objetivo `up-check`:
    - comprueba `$(DOCKER_DATA_DIR)/analytics.duckdb` (si falta, `make ingest`) y `$(DOCKER_DATA_DIR)/documents.duckdb` (si falta, `make ingest-docs`);
    - comprueba el modelo con `MODELS_CACHE_DIR=$(DOCKER_MODELS_DIR) DOCUMENTS_CONFIG_PATH=$(DOCUMENTS_CONFIG_PATH) python -m analyst_backend.documents.models_cli --check`, que nombra `make models` (sin `DOCUMENTS_CONFIG_PATH` falla por la variable que falta). Es el mismo `backend/config/documents.yaml` que se copia en la imagen;
  - `up` depende de `up-check` y ejecuta `docker compose up --build` con `DOCKER_DATA_DIR=$(abspath $(DOCKER_DATA_DIR))` y `DOCKER_MODELS_DIR=$(abspath $(DOCKER_MODELS_DIR))`. Hacen falta rutas absolutas: compose toma `data/processed`, sin `./`, como un volumen con nombre (comprobado: "refers to undefined volume").

  Sin esta comprobación, Docker crearía directorios vacíos de `root` en el host.
- **`DOCKER_DATA_DIR` y `DOCKER_MODELS_DIR` son variables de `make`.** Con `make up` prevalecen sobre `.env`. Quien use `docker compose up` directamente debe darlas como rutas absolutas o que empiecen por `./`; lo dice el README.
- *Descartadas:*
  - ingesta en Docker: decisión del responsable;
  - copiar las bases en la imagen: habría que reconstruirla en cada ingesta;
  - publicar en todas las interfaces: cualquiera en la red podría gastar la cuota de Gemini.

### D9e: pruebas
- **API:**
  - `with TestClient(create_app(deps_factory=...)) as client`: el `lifespan` solo se ejecuta dentro de `with`. `backend/tests/test_health.py` sigue sin `with` y no construye dependencias;
  - fixtures de `backend/tests/agent/conftest.py`: bases reales en un directorio temporal y `ScriptedChatModel`;
  - **"Una pregunta a la vez":**
    1. se sustituye la ejecución del grafo (`run_graph` en `api/ask.py`) por una función con un contador de ejecuciones activas que espera un `threading.Event`; así no hace falta un guion de LLM por hilo;
    2. dos hilos envían una pregunta cada uno;
    3. con la primera en curso, se esperan 0,3 s (sin candado, la segunda entraría en ese intervalo), se comprueba que `/health` responde en menos de 2 s y se libera el evento;
    4. se comprueba que el máximo de ejecuciones simultáneas fue 1 y que ambas respondieron 200. Sin el candado, la prueba falla (comprobado).
- **Interfaz:**
  - `streamlit.testing.v1.AppTest` con `client.ask_backend` sustituido por un falso que devuelve respuestas fijas;
  - "Campo desactivado": `AppTest` devuelve el árbol después de `st.rerun`. Por eso el falso llama a `st.stop()` y la prueba comprueba `chat_input[0].disabled` y la pregunta pendiente (comprobado con Streamlit 1.66);
  - "Texto mostrado tal cual": `.value` devuelve el texto sin interpretar tanto en `st.text` como en `st.markdown`. Por eso la prueba comprueba que el texto está en `at.text` y no en `at.markdown`;
  - el cliente se prueba con `httpx.MockTransport`: cuerpos válidos, texto plano, `ConnectError`, `RemoteProtocolError` y `ReadTimeout`. No se abren puertos reales. En la página basta un caso por resultado del cliente (inaccesible y tiempo agotado), porque la conexión cortada y la falta de conexión dan el mismo resultado.
- **Compose:**
  - un fixture **interpolado**: copia temporal de `docker-compose.yml` y entorno limpio, sin heredar `DOCKER_*`, `BACKEND_PORT`, `FRONTEND_PORT` ni `BACKEND_TIMEOUT_S`. Comprueba volúmenes (`type: bind`, `read_only: true`), `environment`, `host_ip` y `BACKEND_TIMEOUT_S`. Para "Rutas fijas", con un `.env` en el directorio temporal;
  - el fixture actual con `--no-interpolate` se queda solo para `env_file`;
  - "Directorios que pasa make up": se leen con `make -n up` y se resuelve compose con ellos.
- **Dockerfile y Makefile:** se lee `backend/Dockerfile` (la línea `COPY backend/config /app/config`, sin construir la imagen) y se ejecuta `make up-check` con `DOCKER_DATA_DIR` y `DOCKER_MODELS_DIR` en directorios temporales. Ninguna prueba levanta contenedores.
- **Comprobación manual:** `make up` con los datos reales y una pregunta desde el navegador, anotada en las tareas. No forma parte de `make test`.
- *Descartadas:*
  - pruebas con contenedores levantados: requieren Docker en marcha y minutos de construcción en cada `make test`;
  - puertos reales para "API inaccesible": ~130 s por conexión en WSL;
  - Playwright o Selenium para la interfaz: otra dependencia y un navegador, cuando `AppTest` cubre los elementos.

### D9f: documentación
- `docs/architecture.md`: D9 (API, interfaz y contenedores con datos del host) y la sección de componentes.
- README: `make up` y sus requisitos previos, `POST /ask` con `curl` y las variables nuevas.
- ROADMAP: el change 8 se hace antes que el 6.
- *Descartado: documentar la API solo con el OpenAPI de FastAPI (`/docs`).* No explica los requisitos previos de datos ni de Gemini.

### D9g: ajustes tras la prueba manual (2026-10-22)
Con preguntas amplias ("¿son consistentes las principales conclusiones del reporte con los datos?"), la prueba con Gemini mostró:
- consultas descartadas por el máximo de 3 por herramienta;
- planificaciones y síntesis que pasaban de los 120 s de `timeout_s`, por el razonamiento sin límite de Gemini 3.

Ajustes aprobados por el responsable, que deciden mantenerlos tras sus pruebas manuales:
- **`agent.yaml`:** `max_calls_per_tool` de 3 a 5 y `timeout_s` de 120 a 240. Las pruebas de los escenarios de máximos fijan el máximo a 3 en su configuración, como dicen esos escenarios.
- **`plan_reasoning_by_prefix` y `synthesis_reasoning_by_prefix` en `agent.yaml`** (`gemini-3: low` en ambos). `LLMClient.with_tools` (planificación y corrección) y `LLMClient.structured` (síntesis) usan una copia del modelo con su `reasoning_effort`; el modelo compartido no cambia.

**Medición:**
- `make test-llm`: 2 de 2 en 43 s (antes 64 s), así que la calidad de las preguntas de referencia se mantiene.
- En Docker:
  - pregunta causal, 18 s;
  - pregunta amplia del reporte, 21–22 s en dos intentos y un `timeout` de 240 s en otros dos (uno en la planificación, antes de limitarla; otro en la síntesis).
- Las preguntas del responsable desde la interfaz respondieron 200.

*Descartadas:*
- bajar la temperatura de Gemini 3: Google recomienda 1.0;
- solo subir `timeout_s`: no ataca la causa y alarga la espera;
- reintentar ante tiempo agotado: duplica el gasto de cuota.

**Riesgo residual:** con mucha evidencia, Gemini a veces sigue pasando de 240 s, y las respuestas a preguntas amplias varían entre ejecuciones. La solución de fondo para el contraste del reporte y la causalidad es el change 6.

## Risks / Trade-offs

- **[Riesgo] Una pregunta tarda ~30 s y bloquea las siguientes** → Para un analista es aceptable. La interfaz desactiva el campo mientras espera.
- **[Riesgo] El peor caso del backend supera el tiempo de espera de la interfaz.** Con `timeout_s` 120, 2 reintentos y hasta 4 llamadas, más el limitador, se pasa de 300 s. Si la interfaz deja de esperar, la pregunta sigue en el backend gastando cuota, y una nueva pregunta espera detrás → El mensaje de tiempo agotado dice que la pregunta puede seguir en curso. `BACKEND_TIMEOUT_S` es configurable. El caso típico son 2 llamadas (~30 s).
- **[Riesgo] La cuota gratuita de Gemini se agota en una demo** → La interfaz explica `quota_exhausted` y permite volver a preguntar. El límite de peticiones se comparte entre preguntas.
- **[Riesgo] El montaje real `:ro` (EROFS) se comporta distinto de `chmod a-w` (EACCES)** → La prueba manual de `make up` lo comprueba. Si fastembed falla, la búsqueda degrada a modo léxico con aviso.
- **[Riesgo] Archivos del host sin permiso de lectura para el uid 1000 del contenedor** → `data_unavailable` recomendaría `make ingest` sin ser la causa. Hoy los archivos son 644 y el uid del host es 1000. Queda documentado en el README.
- **[Riesgo] El historial visual hace creer que el agente recuerda** → Aviso fijo bajo el título; la API rechaza un historial en la petición.
- **[Compromiso] El resultado de las consultas va dos veces en la respuesta** (traza y evidencias) → Simplicidad de la interfaz frente a unos KB más.
- **[Compromiso] Docker usa los nombres de base por defecto** → Documentado en el README.

## Migration Plan

Sin migración de datos. Pasos:
1. `make ingest`, `make models` y `make ingest-docs`.
2. Configurar Gemini en `.env`.
3. `make up`.

Rollback: revertir el commit. `make ask` sigue funcionando sin Docker.
