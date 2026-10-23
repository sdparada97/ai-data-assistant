# query-api Specification

## Purpose

Expone el agente de consulta por HTTP para que la interfaz, u otro cliente, envíe preguntas en lenguaje natural y reciba la respuesta verificada con sus evidencias y su traza, con un estado HTTP coherente con el resultado.

## Requirements

### Requirement: Pregunta por la API
El backend SHALL exponer `POST /ask`, que recibe un JSON `{"question": "<texto>"}` y devuelve la respuesta del agente en JSON: estado, código y mensaje de error si los hay, hechos, hipótesis, contradicciones, información insuficiente, avisos, evidencias y traza.

#### Scenario: Pregunta de cifras
- **WHEN** se envía a `POST /ask` la pregunta por la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026, con un LLM de prueba que pide la consulta del escenario "Pregunta de cifras" y redacta un hecho sobre `Sur` citando `EV-d5c128c22542`
- **THEN** responde 200 con estado `ok`, ese hecho, la evidencia `EV-d5c128c22542` y una traza con la consulta a `consultar_metrica`

### Requirement: Cuerpo de la petición
El cuerpo SHALL tener solo el campo `question`, de tipo texto. Un cuerpo sin `question`, con `question` que no sea texto o con otros campos (por ejemplo, un historial) SHALL rechazarse con 422 y el detalle de validación de la API, sin llamar al agente. Este es el único caso en que el cuerpo de la respuesta no es la respuesta del agente.

#### Scenario: Cuerpo sin pregunta
- **WHEN** se envía a `POST /ask` el cuerpo `{}`
- **THEN** responde 422 y no se llama al LLM

#### Scenario: Pregunta que no es texto
- **WHEN** se envía `{"question": 123}`
- **THEN** responde 422 y no se llama al LLM

#### Scenario: Historial enviado
- **WHEN** se envía `{"question": "hola", "history": ["pregunta anterior"]}`
- **THEN** responde 422 y no se llama al LLM

### Requirement: Estado HTTP según el resultado
Con un cuerpo válido, el estado HTTP SHALL depender del estado y del código de la respuesta, que siempre va en el cuerpo:
- `ok`, `insuficiente` y `fuera_de_alcance`: 200;
- `invalid_question`: 422;
- `quota_exhausted`: 429;
- `configuration_error`, `data_unavailable` y `provider_unavailable`: 503;
- `timeout`: 504;
- `provider_error` e `invalid_output`: 502;
- `internal_error` y cualquier código no listado: 500.

#### Scenario: Cuota agotada
- **WHEN** el LLM de prueba falla con cuota agotada al planificar
- **THEN** responde 429 con estado `error` y código `quota_exhausted` en el cuerpo

#### Scenario: Pregunta vacía
- **WHEN** se envía la pregunta `"   "`
- **THEN** responde 422 con estado `error` y código `invalid_question` en el cuerpo

#### Scenario: Fuera de alcance
- **WHEN** el LLM de prueba no pide ninguna consulta
- **THEN** responde 200 con estado `fuera_de_alcance`

### Requirement: Fallos no controlados
Cualquier excepción que escape del agente o de la API al responder una pregunta, o al construir las dependencias al arrancar sin ser de configuración, SHALL convertirse en una respuesta del agente con estado `error`, código `internal_error` y estado HTTP 500, con un mensaje sin el texto de la excepción.

#### Scenario: Excepción fuera de los nodos
- **WHEN** responder la pregunta lanza una excepción con el texto `detalle-secreto`
- **THEN** responde 500 con estado `error` y código `internal_error`, y el cuerpo no contiene `detalle-secreto`

#### Scenario: Fallo de la API fuera del agente
- **WHEN** preparar la respuesta HTTP de una pregunta lanza una excepción con el texto `detalle-secreto`
- **THEN** responde 500 con estado `error` y código `internal_error`, y el cuerpo no contiene `detalle-secreto`

#### Scenario: Error inesperado al arrancar
- **WHEN** construir las dependencias lanza una excepción que no es de configuración
- **THEN** el backend arranca, `GET /health` responde 200 y cada pregunta responde 500 con código `internal_error`

### Requirement: Dependencias del agente al arrancar
El backend SHALL construir las dependencias del agente una sola vez al arrancar y reutilizarlas en todas las preguntas, para que el límite de peticiones al LLM se comparta. Si la configuración es inválida, el backend SHALL arrancar igualmente: `GET /health` responde 200 y cada pregunta responde 503 con código `configuration_error` y un mensaje que nombra lo que falta, sin llamar al LLM.

#### Scenario: Dependencias compartidas
- **WHEN** se envían dos preguntas seguidas
- **THEN** las dependencias se construyeron una sola vez y ambas preguntas usan el mismo cliente del LLM

#### Scenario: Configuración inválida al arrancar
- **WHEN** el backend arranca con `LLM_PROVIDER` vacía y se envía una pregunta
- **THEN** `GET /health` responde 200 y la pregunta responde 503 con código `configuration_error` y un mensaje que menciona `LLM_PROVIDER`

### Requirement: Datos cargados después de arrancar
Las bases de ventas y de documentos SHALL comprobarse en cada pregunta, no al arrancar: si se crean después de arrancar el backend, la siguiente pregunta las usa sin reiniciarlo.

#### Scenario: Base de ventas creada después
- **WHEN** se envía una pregunta con la base de ventas ausente, después se crea la base y se envía otra
- **THEN** la primera responde 503 con código `data_unavailable` y un mensaje que menciona `make ingest`, y la segunda responde 200

#### Scenario: Base de documentos ausente
- **WHEN** se envía una pregunta con la base de documentos ausente
- **THEN** responde 503 con código `data_unavailable` y un mensaje que menciona `make ingest-docs`

### Requirement: Una pregunta a la vez
El backend SHALL responder las preguntas de una en una: una pregunta que llega mientras otra se responde espera a que termine, y ambas reciben su respuesta. `GET /health` SHALL responder aunque haya preguntas esperando.

#### Scenario: Dos preguntas simultáneas
- **WHEN** se envían dos preguntas a la vez y el agente tarda en responder la primera
- **THEN** las dos respuestas nunca se calculan a la vez y ambas responden 200

#### Scenario: Salud con preguntas esperando
- **WHEN** una pregunta se está respondiendo y otra espera su turno
- **THEN** `GET /health` responde 200 sin esperar a que terminen
