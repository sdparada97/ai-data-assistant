# Proposal

## Why

El objetivo es una aplicación en la que un analista pregunta en lenguaje natural y recibe respuestas fundamentadas. El agente ya responde (change 5), pero solo desde la terminal: la API solo tiene `/health`, la página de Streamlit solo muestra el título y `make up` no accede a los datos. Por eso este change se adelanta al 6 (decisión del responsable, 2026-10-22).

## What Changes

- **API de consulta (`query-api`):**
  - `POST /ask` con `{"question": "..."}` devuelve la respuesta del agente: estado, los cuatro apartados, avisos, evidencias y traza;
  - cada código de error del agente tiene su estado HTTP (por ejemplo, `quota_exhausted` → 429 y `data_unavailable` → 503), siempre con el cuerpo de la respuesta;
  - las dependencias se crean una vez al arrancar (el límite de peticiones a Gemini se comparte); una configuración inválida no impide el arranque y se informa en cada pregunta;
  - una pregunta a la vez.
- **Interfaz del analista (`analyst-ui`):**
  - respuesta por apartados con sus evidencias citadas y el detalle de cada una (cifras de la consulta o texto del fragmento con documento y página);
  - avisos y traza;
  - historial visual de la sesión; la página indica que cada pregunta se responde sola;
  - mensajes claros para cuota agotada, datos sin cargar, configuración inválida o API inaccesible.
- **Evidencias en la respuesta (`query-agent`):** la respuesta incluye las evidencias de la ejecución, citables por cualquiera de sus ids.
- **`make up` de punta a punta (`project-layout`):**
  - compose monta `data/processed` y `.cache/models` del host en solo lectura y fija las rutas; `backend/config/` va en la imagen;
  - `make up` comprueba antes las bases y el modelo y nombra el comando que falta.

## Capabilities

### New Capabilities

- `query-api`: endpoint de preguntas, estados HTTP, ciclo de vida de las dependencias y una pregunta a la vez.
- `analyst-ui`: página de preguntas y respuestas, detalle de evidencias, traza, historial de la sesión y mensajes de error.

### Modified Capabilities

- `query-agent`: evidencias con título en la respuesta, también con error (requisitos nuevos).
- `llm-provider`: razonamiento configurable por paso (requisito nuevo, tras la prueba manual).
- `project-layout`: requisitos nuevos "Datos del host en el backend", "Tiempo de espera de la interfaz en contenedores", "Comprobación antes de arrancar" y "Puertos solo en la máquina local". "Orquestación con contenedores" y "Página mínima del frontend" no cambian: la página de preguntas conserva el título y la URL de la API.

## Impact

- **Código:** `main.py` y `api/`; en `agent/`, `models`, `evidence`, `graph`, `service`, `config` y `llm`; `agent.yaml`; `frontend/src/analyst_frontend/`.
- **Pruebas:** `backend/tests/api/` y `agent/`, `frontend/tests/`, `tests/test_compose.py` y `tests/test_makefile.py`, sin red ni LLM real.
- **Dependencias:** `httpx` en el frontend.
- **Contenedores:** `docker-compose.yml`, `backend/Dockerfile`, `make up` y `.env.example` (`BACKEND_TIMEOUT_S`).
- **Documentación:** README, `docs/architecture.md` y ROADMAP.

## Fuera de alcance

- Memoria entre preguntas.
- Ingesta dentro de Docker: los datos se preparan en el host.
- Autenticación, varios usuarios, colas, *streaming* y despliegue fuera de la máquina local.
- Changes 6, 7 y 9.
