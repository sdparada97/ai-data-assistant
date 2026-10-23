# Spec Delta

## ADDED Requirements

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
