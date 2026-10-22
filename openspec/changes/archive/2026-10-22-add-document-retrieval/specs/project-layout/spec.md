# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Pruebas con el modelo de embeddings separadas
`make test-embeddings` SHALL ejecutar únicamente las pruebas marcadas como `embeddings`, sin red. Si el modelo configurado no está en `MODELS_CACHE_DIR`, SHALL terminar con código distinto de 0 y un mensaje que indique ejecutar `make models`, sin ejecutar las pruebas.

#### Scenario: Solo pruebas embeddings
- **WHEN** se recolecta, con el filtro de `make test-embeddings`, un directorio temporal que contiene una prueba marcada con `@pytest.mark.embeddings` y otra sin marca
- **THEN** solo se recoge la prueba marcada

#### Scenario: Modelo no descargado
- **WHEN** se ejecuta `make test-embeddings` con `MODELS_CACHE_DIR` apuntando a un directorio vacío
- **THEN** termina con código distinto de 0 y la salida contiene `make models`
