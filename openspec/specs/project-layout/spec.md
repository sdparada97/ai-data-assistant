# project-layout Specification

## Purpose

Define dónde vive el código de Brío Analyst, cómo se reproduce su entorno, qué comandos comunes ofrece el repositorio y qué servicios mínimos levanta, para que cada change posterior parta de una base ejecutable y verificable.

## Requirements

### Requirement: Ubicación del código fuente
El código de la aplicación SHALL residir en `backend/src/` (API) y `frontend/src/` (interfaz). Las pruebas SHALL residir en `backend/tests/`, `frontend/tests/` o `tests/` (comprobaciones del repositorio), con un único `conftest.py` permitido en la raíz. No SHALL existir un directorio `src/` en la raíz del repositorio.

#### Scenario: Paquetes importables desde su ubicación
- **WHEN** se importan los paquetes `analyst_backend` y `analyst_frontend` en el entorno del workspace
- **THEN** cada import resuelve a un archivo bajo `backend/src/analyst_backend/` y `frontend/src/analyst_frontend/` respectivamente

#### Scenario: Sin código fuera de los directorios permitidos
- **WHEN** se buscan archivos `.py` en el repositorio, excluyendo `.venv/`, `.git/`, `graphify-out/`, `.claude/`, `node_modules/` y `__pycache__/`
- **THEN** todos están bajo `backend/`, `frontend/` o `tests/`, salvo `conftest.py` en la raíz
- **AND** no existe el directorio `src/` en la raíz

### Requirement: Entorno Python reproducible
El repositorio SHALL fijar la versión de Python en 3.14 y bloquear todas las dependencias en un único `uv.lock` versionado. Cada dependencia directa en `[project].dependencies` y `[dependency-groups]` de cualquier `pyproject.toml` del workspace SHALL tener una versión exacta (`==`). `[build-system].requires` queda excluido.

#### Scenario: Versión de Python fijada
- **WHEN** se lee `.python-version` en la raíz
- **THEN** su contenido es `3.14`

#### Scenario: Bloqueo sincronizado sin red
- **WHEN** se ejecuta `uv lock --check --offline`
- **THEN** termina con código 0 sin modificar `uv.lock`

#### Scenario: Dependencias directas con versión exacta
- **WHEN** se leen `[project].dependencies` y `[dependency-groups]` de los `pyproject.toml` de la raíz, `backend/` y `frontend/`
- **THEN** cada entrada usa el operador `==`

### Requirement: Suite de pruebas sin servicios externos
`make test` SHALL ejecutar las pruebas de `backend/tests/`, `frontend/tests/` y `tests/` excluyendo las marcadas como `llm` y como `embeddings`.

#### Scenario: Recolección de las tres ubicaciones
- **WHEN** se recolectan las pruebas con el mismo filtro que usa `make test`
- **THEN** se recoge al menos una prueba de `backend/tests/`, una de `frontend/tests/` y una de `tests/`

#### Scenario: Pruebas llm excluidas
- **WHEN** se recolecta, con el filtro de `make test`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.llm` y otra sin marca
- **THEN** solo se recoge la prueba sin marca

#### Scenario: Pruebas embeddings excluidas
- **WHEN** se recolecta, con el filtro de `make test`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.embeddings` y otra sin marca
- **THEN** solo se recoge la prueba sin marca

### Requirement: Aislamiento de la suite por defecto
Toda prueba no marcada como `llm` SHALL ejecutarse sin acceso a red y sin las variables definidas en `.env.example`, aunque existan en el entorno del desarrollador. Las pruebas marcadas como `embeddings` SHALL conservar únicamente `MODELS_CACHE_DIR`.

#### Scenario: Red bloqueada
- **WHEN** una prueba no marcada como `llm` intenta abrir una conexión de red
- **THEN** la conexión falla con un error que indica que la red está deshabilitada en la suite

#### Scenario: DNS y envío UDP bloqueados
- **WHEN** una prueba no marcada como `llm` resuelve un nombre de host o envía un datagrama UDP a una dirección de internet
- **THEN** la operación falla con el mismo error de red deshabilitada

#### Scenario: Sockets locales sin cambios
- **WHEN** una prueba no marcada como `llm` usa `connect_ex` sobre un socket local (AF_UNIX) inexistente
- **THEN** recibe un código de error distinto de 0, sin excepción

#### Scenario: Credenciales ausentes
- **WHEN** se ejecuta una prueba no marcada como `llm` ni como `embeddings` con `GEMINI_API_KEY` definida en el entorno del proceso
- **THEN** dentro de la prueba ninguna variable listada en `.env.example` está definida

#### Scenario: Caché de modelos en pruebas embeddings
- **WHEN** se ejecuta una prueba marcada como `embeddings` con `MODELS_CACHE_DIR` y `GEMINI_API_KEY` definidas en el entorno del proceso
- **THEN** dentro de la prueba `MODELS_CACHE_DIR` conserva su valor, `GEMINI_API_KEY` no está definida y la red está bloqueada

### Requirement: Pruebas con LLM separadas
`make test-llm` SHALL ejecutar únicamente las pruebas marcadas como `llm`, en las rutas de `LLM_TESTS` si se indica. Si no hay ninguna, SHALL terminar con código 0 e informarlo. SHALL cargar las variables del archivo `ENV_FILE` (por defecto `.env`) solo si existe, sin mostrar su contenido.

#### Scenario: Ninguna prueba llm registrada
- **WHEN** se ejecuta `make test-llm` con `LLM_TESTS` apuntando a un directorio sin pruebas marcadas como `llm`
- **THEN** termina con código 0
- **AND** la salida contiene "No hay pruebas llm"

#### Scenario: Solo pruebas llm
- **WHEN** se recolecta, con el filtro de `make test-llm`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.llm` y otra sin marca
- **THEN** solo se recoge la prueba marcada

#### Scenario: Archivo de entorno inexistente
- **WHEN** se ejecuta `make test-llm` con `ENV_FILE` apuntando a un archivo que no existe y `LLM_TESTS` a un directorio vacío
- **THEN** termina con código 0, sin error por el archivo ausente

### Requirement: Pruebas con el modelo de embeddings separadas
`make test-embeddings` SHALL ejecutar únicamente las pruebas marcadas como `embeddings`, sin red. Si el modelo configurado no está en `MODELS_CACHE_DIR`, SHALL terminar con código distinto de 0 y un mensaje que indique ejecutar `make models`, sin ejecutar las pruebas.

#### Scenario: Solo pruebas embeddings
- **WHEN** se recolecta, con el filtro de `make test-embeddings`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.embeddings` y otra sin marca
- **THEN** solo se recoge la prueba marcada

#### Scenario: Modelo no descargado
- **WHEN** se ejecuta `make test-embeddings` con `MODELS_CACHE_DIR` apuntando a un directorio vacío
- **THEN** termina con código distinto de 0 y la salida contiene `make models`

### Requirement: Evaluación reservada
Mientras el change `add-evaluation-suite` no esté implementado, `make eval` SHALL terminar con código distinto de 0 y un mensaje que indique que la evaluación aún no está disponible.

#### Scenario: Evaluación no implementada
- **WHEN** se ejecuta `make eval`
- **THEN** termina con código distinto de 0
- **AND** la salida contiene "add-evaluation-suite"

### Requirement: Salud del backend
El backend SHALL exponer `GET /health`, que responde 200 con un JSON `{"status": "ok"}` sin depender de datos, credenciales ni LLM.

#### Scenario: Backend sano
- **WHEN** se hace `GET /health` al backend
- **THEN** responde 200 con el cuerpo `{"status": "ok"}`

#### Scenario: Ruta inexistente
- **WHEN** se hace `GET /no-existe` al backend
- **THEN** responde 404

### Requirement: Página mínima del frontend
El frontend SHALL mostrar una página cuyo título se lee de `APP_TITLE` y que muestra la URL de la API leída de `BACKEND_URL`. Sin `APP_TITLE`, SHALL usar "Asistente de análisis"; sin `BACKEND_URL`, SHALL usar `http://localhost:8000`.

#### Scenario: Valores configurados
- **WHEN** se renderiza la página con `APP_TITLE=Brío Analyst` y `BACKEND_URL=http://backend:8000`
- **THEN** la página muestra el título "Brío Analyst" y el texto `http://backend:8000`
- **AND** no se produce ninguna excepción

#### Scenario: Valores por defecto
- **WHEN** se renderiza la página sin `APP_TITLE` ni `BACKEND_URL`
- **THEN** la página muestra el título "Asistente de análisis" y el texto `http://localhost:8000`

### Requirement: Orquestación con contenedores
`docker-compose.yml` SHALL definir los servicios `backend` y `frontend`, cada uno construido desde su Dockerfile. `frontend` SHALL recibir `BACKEND_URL=http://backend:8000` como valor fijo y depender de `backend`. Solo `backend` SHALL cargar `.env`, de forma opcional. La configuración SHALL ser válida aunque no exista `.env`.

#### Scenario: Configuración válida sin .env
- **WHEN** se ejecuta `docker compose config` sobre una copia de `docker-compose.yml` en un directorio temporal sin `.env`
- **THEN** termina con código 0

#### Scenario: Servicios y conexión
- **WHEN** se lee la configuración resuelta de `docker compose config`
- **THEN** contiene los servicios `backend` y `frontend`
- **AND** `frontend` tiene `BACKEND_URL=http://backend:8000` y depende de `backend`
- **AND** solo `backend` declara `env_file`

### Requirement: Datos del host en el backend
El servicio `backend` de `docker-compose.yml` SHALL montar en solo lectura el directorio de bases procesadas (por defecto `./data/processed`) y la caché de modelos (por defecto `./.cache/models`) del host. SHALL fijar en `environment` las rutas de las bases, de la caché y de la configuración dentro del contenedor, que prevalecen sobre las de `.env`. La configuración de `backend/config/` SHALL ir dentro de la imagen.

#### Scenario: Volúmenes de solo lectura
- **WHEN** se resuelve `docker compose config` con los valores por defecto
- **THEN** `backend` monta `data/processed` y `.cache/models` como directorios del host en modo solo lectura

#### Scenario: Rutas fijas del backend
- **WHEN** se resuelve `docker compose config` con un `.env` que define `DUCKDB_PATH=otra/ruta.duckdb`
- **THEN** `backend` tiene `DUCKDB_PATH`, `DOCUMENTS_DB_PATH`, `MODELS_CACHE_DIR`, `AGENT_CONFIG_PATH`, `SEMANTIC_LAYER_PATH` y `DOCUMENTS_CONFIG_PATH` apuntando a rutas del contenedor, y no `otra/ruta.duckdb`

#### Scenario: Configuración en la imagen
- **WHEN** se lee `backend/Dockerfile`
- **THEN** la etapa final copia `backend/config` en la ruta que usan `AGENT_CONFIG_PATH`, `SEMANTIC_LAYER_PATH` y `DOCUMENTS_CONFIG_PATH`

#### Scenario: Directorios que pasa make up
- **WHEN** se resuelve `docker compose config` con los directorios que `make up` pasa a compose
- **THEN** termina con código 0 y `backend` monta esos directorios del host en solo lectura

### Requirement: Tiempo de espera de la interfaz en contenedores
El servicio `frontend` SHALL recibir `BACKEND_TIMEOUT_S` del entorno de compose, vacío si no se define, como `APP_TITLE`.

#### Scenario: Tiempo de espera definido
- **WHEN** se resuelve `docker compose config` con `BACKEND_TIMEOUT_S=600` en el entorno
- **THEN** `frontend` tiene `BACKEND_TIMEOUT_S=600`

### Requirement: Comprobación antes de arrancar
`make up` SHALL comprobar, antes de construir y levantar los contenedores, que existen la base de ventas, la base de documentos y el modelo de embeddings con su huella. Si falta alguno, SHALL terminar con código distinto de 0 y un mensaje que nombra el comando que lo genera (`make ingest`, `make ingest-docs` o `make models`), sin levantar contenedores.

#### Scenario: Base de ventas ausente
- **WHEN** se ejecuta la comprobación de `make up` con un directorio de bases vacío
- **THEN** termina con código distinto de 0 y la salida menciona `make ingest`

#### Scenario: Base de documentos ausente
- **WHEN** se ejecuta la comprobación de `make up` con la base de ventas presente y sin la de documentos
- **THEN** termina con código distinto de 0 y la salida menciona `make ingest-docs`

#### Scenario: Modelo ausente
- **WHEN** se ejecuta la comprobación de `make up` con las bases presentes y una caché de modelos vacía
- **THEN** termina con código distinto de 0 y la salida menciona `make models`

### Requirement: Puertos solo en la máquina local
`docker-compose.yml` SHALL publicar los puertos de `backend` y `frontend` solo en `127.0.0.1`, para que otros equipos de la red no puedan usar la API ni consumir la cuota del LLM.

#### Scenario: Puertos locales
- **WHEN** se resuelve `docker compose config` con los valores por defecto
- **THEN** los puertos publicados de `backend` y `frontend` tienen `host_ip` `127.0.0.1`
