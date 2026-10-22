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
`make test-llm` SHALL ejecutar únicamente las pruebas marcadas como `llm`. Si no hay ninguna, SHALL terminar con código 0 e informarlo.

#### Scenario: Ninguna prueba llm registrada
- **WHEN** se ejecuta `make test-llm` y no existe ninguna prueba marcada como `llm`
- **THEN** termina con código 0
- **AND** la salida contiene "No hay pruebas llm"

#### Scenario: Solo pruebas llm
- **WHEN** se recolecta, con el filtro de `make test-llm`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.llm` y otra sin marca
- **THEN** solo se recoge la prueba marcada

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
