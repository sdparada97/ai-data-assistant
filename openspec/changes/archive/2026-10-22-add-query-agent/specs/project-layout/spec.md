# Spec Delta

## MODIFIED Requirements

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
