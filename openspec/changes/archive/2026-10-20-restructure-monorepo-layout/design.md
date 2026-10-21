# Design

## Context

Ver proposal.md (Why). Estado actual: `src/` raíz vacío (solo `.gitkeep`), sin `pyproject.toml`, sin Docker ni Makefile. En local hay pyenv con Python 3.14.7 global, uv 0.13.4 en `~/.local/bin`, Docker 29.8 con Compose 5.6 y GNU Make 4.3. graphify indexa el repositorio completo respetando `.gitignore` y no depende de `src/`. Las menciones a la ubicación del código están en `docs/architecture.md` (D2, la nota "D1–D3 siguen vigentes" y "Python 3.11+"), `openspec/config.yaml` (context) y `CLAUDE.md` (línea 3). En el shell local `VIRTUAL_ENV` apunta a la instalación de pyenv, lo que hace que uv emita un aviso.

## Goals / Non-Goals

**Goals:**
- Que `make test` y `docker compose config` funcionen desde un checkout limpio tras `uv sync --all-packages`.
- Que backend y frontend evolucionen con dependencias propias y un único bloqueo.

**Non-Goals:**
- Imágenes optimizadas para producción, CI remoto o publicación de imágenes.
- Healthchecks de Docker y `make up` en la suite automática (se comprueba a mano en la tarea 6.3).

## Decisions

### D2' Código fuente en `backend/src/` y `frontend/src/` (reemplaza D2)
Cada aplicación es un proyecto Python con layout `src/` y sus pruebas en `<app>/tests/`. Las comprobaciones del repositorio viven en `tests/` raíz y un único `conftest.py` raíz aplica el aislamiento a las tres ubicaciones. Los scripts auxiliares de cada aplicación (p. ej. `backend/scripts/`, que se usará en la exploración de datos) quedan dentro de su directorio. Motivo: backend y frontend se despliegan en contenedores distintos con dependencias distintas (Streamlit no debe entrar en la imagen de la API). El layout `src/` evita que el directorio de trabajo enmascare el paquete instalado; en local los miembros se instalan en modo editable, y en Docker con `--no-editable`, de modo que la imagen contiene exactamente el paquete construido.
- *Descartada: mantener `src/` raíz.* Mezclaría ambas aplicaciones en un paquete con dependencias unidas, imágenes más pesadas y límites difusos entre API e interfaz.
- *Descartada: `backend/` y `frontend/` sin `src/`.* El paquete sería importable desde la raíz de cada app sin instalarse, ocultando errores de empaquetado que solo aparecerían en la imagen.

### D4 Workspace de uv con un único `uv.lock`
`pyproject.toml` raíz virtual con `[tool.uv.workspace] members = ["backend", "frontend"]`, `[tool.uv] required-version = "==0.13.4"` y un grupo `dev` con pytest y httpx2 (cliente que usa `TestClient`; Starlette marcó `httpx` como obsoleto). Paquetes `analyst_backend` y `analyst_frontend`; nombres sin la marca, porque la marca es un parámetro de negocio. Los comandos usan `--all-packages` y `--frozen` para que `make test` no resuelva ni descargue. El `Makefile` hace `unexport VIRTUAL_ENV` para evitar el aviso de uv.
- *Descartada: pip + `requirements.txt` por aplicación.* Requiere fijar versiones transitivas a mano y no garantiza resoluciones coherentes entre ambas aplicaciones.
- *Descartada: dos proyectos uv independientes.* Dos locks que pueden divergir en dependencias compartidas (pydantic, httpx).

### Python 3.14 (parte de D4)
Fijado en `.python-version` e imagen base `python:3.14-slim`. Las dependencias nativas previstas en el ROADMAP (onnxruntime, duckdb, pandas, numpy, pyarrow, tokenizers, PyMuPDF abi3) publican wheels cp314; 3.14 cumple "3.11+". Se registra como D4 en `docs/architecture.md` y "3.11+" pasa a "3.14".
- *Descartada: 3.12 o 3.13.* Sin ventaja de compatibilidad para este stack y menor horizonte de soporte.
- *Descartada: 3.14t (sin GIL).* Varias extensiones no la soportan.

### Separación y aislamiento de pruebas
Marca `llm` registrada con `--strict-markers`. `make test` usa `-m "not llm"`; `make test-llm` usa `-m llm`, trata el código 5 de pytest como éxito e imprime "No hay pruebas llm". Un fixture autouse en `conftest.py` raíz, solo para pruebas sin marca `llm`, elimina del entorno las variables listadas en `.env.example` y sustituye `socket.socket.connect` por una función que lanza un error explícito. Las pruebas que lanzan subprocesos (uv, docker, make) no se ven afectadas por el bloqueo de sockets; sus comandos no requieren red (`--offline`, `--frozen`, `docker compose config`).
- *Descartada: directorios separados por tipo.* Las marcas permiten que una prueba de integración viva junto al módulo que prueba.
- *Descartada: dependencia externa (pytest-socket).* Una dependencia más para unas pocas líneas.

### Alcance del bloqueo de red
Se bloquean `connect`, `connect_ex`, `sendto` y `sendmsg` en sockets AF_INET/AF_INET6, y la resolución DNS (`getaddrinfo`, `gethostbyname`, `gethostbyname_ex`). Incluye el loopback: la suite por defecto no habla con ningún servicio, ni siquiera local por TCP. Los sockets locales (AF_UNIX) conservan su comportamiento nativo, incluido el código de retorno de `connect_ex`.
- *Descartada: bloquear solo `connect`.* Dejaba abiertas la resolución DNS y el envío UDP.

### Lanzador del frontend con `st.App`
`analyst-frontend` usa la API pública `st.App(APP_PATH).run(config=...)` (Streamlit ≥ 1.65) y traduce opciones `--seccion.opcion=valor` al diccionario `config`; rechaza cualquier otra forma con un mensaje y código de salida 1. El Dockerfile pasa `--server.port`, `--server.address` y `--server.headless` así.
- *Descartada: `streamlit.web.cli.main` reescribiendo `sys.argv`.* Es una API interna que puede cambiar sin aviso.
- *Descartada: variables `STREAMLIT_SERVER_*`.* Las procesa el comando `streamlit run`; `st.App.run()` las ignora (comprobado: arrancó en otro puerto).

### `make eval` falla explícitamente
Hasta el change 9, `make eval` imprime "Evaluación no disponible: pendiente del change add-evaluation-suite" y sale con código 1, sin condiciones. El change 9 modificará este requisito.
- *Descartada: objetivo vacío que termina con 0.* Daría por buena una evaluación que no se ejecutó.

### Título del frontend configurable
El título sale de `APP_TITLE` (por defecto "Asistente de análisis") y la URL de `BACKEND_URL` (por defecto `http://localhost:8000`), leídos en una función de configuración. "Brío Analyst" solo aparece en pruebas. Se añade `APP_TITLE=` a `.env.example`.
- *Descartada: título literal "Brío Analyst".* Contradice "nada hardcodeado: marca".

### Contenedores
Dockerfile por aplicación con contexto de build en la raíz (necesita `uv.lock`), uv copiado desde `ghcr.io/astral-sh/uv:0.13.4` y `uv sync --locked --no-dev --no-editable --package <app>`. En compose, solo `backend` declara `env_file: [{path: .env, required: false}]` (el frontend no recibe credenciales). `frontend` fija `BACKEND_URL: http://backend:8000` en `environment`, que tiene prioridad sobre cualquier `.env`. Los puertos publicados usan valores por defecto sobrescribibles (`${BACKEND_PORT:-8000}`, `${FRONTEND_PORT:-8501}`).
- *Descartada: Dockerfile único multi-target.* Acopla ambas imágenes y complica el cache de capas.
- *Descartada: `env_file` obligatorio o en ambos servicios.* El primero rompe `docker compose config` sin `.env`; el segundo expone credenciales al frontend.
- *Descartada: `BACKEND_URL` sobrescribible en compose.* Un `.env` local pensado para `streamlit run` rompería la conexión entre contenedores.

### Prueba de `docker compose config`
La prueba copia `docker-compose.yml` a un directorio temporal sin `.env` e invoca `docker compose -f <copia> config --format json`; si Docker no está instalado, se omite con `pytest.skip` y motivo visible. Así no depende del `.env` del desarrollador ni lo toca.
- *Descartada: exigir Docker en `make test`.* Rompería la suite en entornos sin Docker.

## Risks / Trade-offs

- [Algún paquete futuro sin wheels cp314] → Se comprueba en cada change que agrega dependencias nativas; si falla, se reevalúa la versión en ese change.
- [Prueba de compose omitida sin Docker] → El motivo del skip aparece en la salida y el verificador lo reporta.
- [uv no disponible en otra máquina] → `README.md` indica los requisitos y su instalación; las imágenes Docker no dependen del uv local.
- [Un change futuro añade `.py` fuera de las ubicaciones permitidas (p. ej. `eval/`)] → Ese change debe modificar el requisito "Ubicación del código fuente"; la prueba de estructura lo detecta.
- [`python:3.14-slim` sin digest fijo] → Aceptado en esta fase; el parche de Python puede variar entre builds.

## Migration Plan

1. Actualizar D2 → D2', añadir D4 y las referencias en `config.yaml` y `CLAUDE.md`.
2. Eliminar `src/` raíz (sin código que migrar).
3. Crear el esqueleto. Rollback: revertir el commit; no hay datos ni estado persistente.
