# Tasks

## 1. Decisiones D2' y D4 en la documentación

- [x] 1.1 (~45 min) En `docs/architecture.md`: reemplazar D2 por D2' (con nota "reemplaza D2"), añadir D4 (Python 3.14 y workspace uv), cambiar "D1–D3 siguen vigentes" por "D1, D2', D3 y D4" y "Python 3.11+" por "Python 3.14". Actualizar la línea del `context` en `openspec/config.yaml` y la línea 3 de `CLAUDE.md`. Verificar con `grep -rnE '(^|[^a-z/_])src/' CLAUDE.md docs/architecture.md openspec/config.yaml` sin resultados
- [x] 1.2 (~10 min) Eliminar `src/.gitkeep` y el directorio `src/` raíz; verificar que `src/` ya no existe

## 2. Entorno Python (requisitos "Ubicación del código fuente", "Entorno Python reproducible" y "Aislamiento de la suite por defecto")

- [x] 2.1 (~1 h) Crear `.python-version` (3.14), `pyproject.toml` raíz (workspace virtual, `required-version`, grupo `dev` con pytest y httpx2 `==`, pytest con marca `llm`, `--strict-markers` y `testpaths`), `backend/pyproject.toml` y `frontend/pyproject.toml` con dependencias `==` (FastAPI y Uvicorn; Streamlit) y los paquetes `analyst_backend` y `analyst_frontend` con `__init__.py`; generar `uv.lock` y verificar con `uv sync --all-packages --locked`
- [x] 2.2 (~45 min) Crear `conftest.py` raíz con el fixture de aislamiento (sin red, sin variables de `.env.example`) para pruebas sin marca `llm`, y los tests del requisito "Aislamiento de la suite por defecto" en `tests/test_isolation.py`: conexión de red falla con error explícito; `GEMINI_API_KEY` definida fuera no es visible dentro; verificar que pasan
- [x] 2.3 (~45 min) Tests del requisito "Ubicación del código fuente" en `tests/test_layout.py`: imports resuelven bajo `backend/src/` y `frontend/src/`; todos los `.py` (con las exclusiones de la spec) están en ubicaciones permitidas; no existe `src/` raíz; verificar que pasan
- [x] 2.4 (~30 min) Tests del requisito "Entorno Python reproducible" en `tests/test_environment.py`: `.python-version` es `3.14`; `uv lock --check --offline` termina en 0; toda entrada de `[project].dependencies` y `[dependency-groups]` usa `==`; verificar que pasan
- [x] 2.5 (~30 min) Ampliar el aislamiento tras la verificación: bloquear DNS (`getaddrinfo`, `gethostbyname`, `gethostbyname_ex`) y `sendto`/`sendmsg` en sockets de red, y conservar `connect_ex` nativo en sockets locales; tests de `connect` y `connect_ex` directos (con timeout, sin pasar por DNS) y de los escenarios "DNS y envío UDP bloqueados" y "Sockets locales sin cambios" en `tests/test_isolation.py`; verificar que pasan

## 3. Backend (requisito "Salud del backend")

- [x] 3.1 (~30 min) Implementar la app FastAPI mínima en `analyst_backend` con `GET /health` → `{"status": "ok"}`; verificar importando la app
- [x] 3.2 (~30 min) Tests del requisito "Salud del backend" en `backend/tests/test_health.py` con `TestClient`: `/health` responde 200 y el cuerpo esperado; `/no-existe` responde 404; verificar que pasan

## 4. Frontend (requisito "Página mínima del frontend")

- [x] 4.1 (~45 min) Implementar la página Streamlit en `analyst_frontend` con una función de configuración que lee `APP_TITLE` (por defecto "Asistente de análisis") y `BACKEND_URL` (por defecto `http://localhost:8000`); añadir `APP_TITLE=` a `.env.example`; verificar con `uv run streamlit run` a mano
- [x] 4.2 (~45 min) Tests del requisito "Página mínima del frontend" en `frontend/tests/test_app.py` con `streamlit.testing.v1.AppTest`: con `APP_TITLE=Brío Analyst` y `BACKEND_URL=http://backend:8000` muestra ambos sin excepción; sin variables muestra los valores por defecto; verificar que pasan
- [x] 4.3 (~45 min) Sustituir el lanzador interno de Streamlit por la API pública `st.App(...).run(config=...)` en `analyst_frontend/cli.py`, con tests de opciones válidas, sin opciones y mal formadas en `frontend/tests/test_app.py`; verificar que pasan y que la imagen Docker del frontend arranca en el puerto 8501

## 5. Comandos comunes (requisitos "Suite de pruebas sin servicios externos", "Pruebas con LLM separadas" y "Evaluación reservada")

- [x] 5.1 (~30 min) Crear `Makefile` con `unexport VIRTUAL_ENV`, `test` (`uv run --all-packages --frozen pytest -m "not llm"`), `test-llm` (`-m llm`, código 5 → éxito con "No hay pruebas llm"), `eval` (mensaje con "add-evaluation-suite" y salida 1) y `up` (`docker compose up --build`); verificar `make test` y `make eval` a mano
- [x] 5.2 (~45 min) Tests del requisito "Suite de pruebas sin servicios externos" en `tests/test_makefile.py`: la recolección con el filtro de `make test` incluye pruebas de las tres ubicaciones; en un directorio temporal con una prueba `llm` y otra sin marca solo recoge la segunda; verificar que pasan
- [x] 5.3 (~30 min) Tests del requisito "Pruebas con LLM separadas": `make test-llm` sin pruebas `llm` termina en 0 y su salida contiene "No hay pruebas llm"; en un directorio temporal el filtro `-m llm` solo recoge la prueba marcada; verificar que pasan
- [x] 5.4 (~15 min) Tests del requisito "Evaluación reservada": `make eval` termina con código distinto de 0 y su salida contiene "add-evaluation-suite"; verificar que pasan
- [x] 5.5 (~30 min) Reescribir `README.md` con requisitos (Python 3.14, uv 0.13.4, Docker, Make), instalación (`uv sync --all-packages`) y los objetivos `make`; verificar que cada comando documentado existe en el `Makefile`

## 6. Contenedores (requisito "Orquestación con contenedores")

- [x] 6.1 (~1 h 30 min) Crear `backend/Dockerfile` y `frontend/Dockerfile` (base `python:3.14-slim`, uv `0.13.4`, `uv sync --locked --no-dev --no-editable --package`), `.dockerignore` y `docker-compose.yml` (servicios `backend` y `frontend`, `env_file` opcional solo en `backend`, `BACKEND_URL=http://backend:8000` fijo en `frontend`, `depends_on`, puertos con valores por defecto); verificar con `docker compose config`
- [x] 6.2 (~45 min) Tests del requisito "Orquestación con contenedores" en `tests/test_compose.py`: `docker compose config` sobre una copia en un directorio temporal sin `.env` termina en 0 (skip con motivo si no hay Docker); la configuración resuelta contiene ambos servicios, `BACKEND_URL` fijo, `depends_on` y `env_file` solo en `backend`; verificar que pasan
- [x] 6.3 (~30 min) Comprobación de integración: `make up`, `curl` a `/health` del backend responde `{"status": "ok"}` y la página del frontend carga; `docker compose down` al terminar

## 7. Cierre

- [x] 7.1 (~10 min) Ejecutar `make test` y verificar que todo pasa
- [x] 7.2 (~10 min) Ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores
