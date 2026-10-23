# llm-provider Specification

## Purpose

Crea, a partir de variables de entorno y de `agent.yaml`, el modelo de lenguaje que usa el agente (Gemini), con límites de peticiones y de tiempo y un manejo explícito de los errores del proveedor, sin exponer nunca la clave.

## Requirements

### Requirement: Selección del proveedor
El proveedor SHALL elegirse con `LLM_PROVIDER`, y el único admitido en esta versión es `gemini`. Un valor ausente o distinto SHALL producir un error que nombre `LLM_PROVIDER`, el valor recibido y los proveedores admitidos. `GEMINI_MODEL` y `GEMINI_API_KEY` SHALL ser obligatorias: si faltan o están vacías, el error SHALL nombrar la variable.

#### Scenario: Proveedor no admitido
- **WHEN** `LLM_PROVIDER = ollama`
- **THEN** se produce un error que menciona `LLM_PROVIDER`, `ollama` y `gemini`

#### Scenario: Proveedor ausente
- **WHEN** `LLM_PROVIDER` no está definida
- **THEN** se produce un error que menciona `LLM_PROVIDER` y `gemini`

#### Scenario: Clave ausente
- **WHEN** `LLM_PROVIDER = gemini`, `GEMINI_MODEL` tiene valor y `GEMINI_API_KEY` está vacía
- **THEN** se produce un error que menciona `GEMINI_API_KEY`

### Requirement: Clave nunca expuesta
El valor de `GEMINI_API_KEY` SHALL NOT aparecer en el mensaje ni en la causa encadenada de los errores que produce el proveedor, ni en registros, trazas o respuestas del agente.

#### Scenario: Error del proveedor con la clave en su texto
- **WHEN** la clave es `clave-de-prueba-123` y el modelo falla con un error cuyo texto incluye la clave
- **THEN** el error resultante no contiene `clave-de-prueba-123` ni en su mensaje ni en su causa

### Requirement: Parámetros del modelo en configuración
El límite de peticiones por minuto, la ráfaga, el tiempo máximo por llamada, el máximo de tokens de salida, los reintentos ante saturación y la temperatura SHALL leerse de `agent.yaml`. La temperatura SHALL poder fijarse por prefijo de nombre de modelo, con un valor por defecto.

#### Scenario: Temperatura por familia de modelo
- **WHEN** `agent.yaml` fija temperatura 1.0 para el prefijo `gemini-3` y 0 por defecto
- **THEN** el modelo `gemini-3-flash` se crea con temperatura 1.0 y `gemini-2.5-flash` con 0

#### Scenario: Límite de peticiones
- **WHEN** el límite es de 60 peticiones por minuto, con ráfaga 1, y se hacen dos llamadas seguidas
- **THEN** la segunda empieza al menos 1 segundo después de la primera

### Requirement: Errores del proveedor
Los errores del proveedor SHALL convertirse en un error con código:
- `quota_exhausted`: cuota agotada (429 `RESOURCE_EXHAUSTED`); no se reintenta.
- `provider_unavailable`: saturación o fallo temporal (500, 503, 504), tras los reintentos configurados.
- `timeout`: se superó el tiempo máximo.
- `provider_error`: cualquier otro fallo del proveedor (autenticación, permisos, petición inválida, modelo inexistente, contexto excedido).

#### Scenario: Cuota agotada
- **WHEN** el modelo falla con 429 `RESOURCE_EXHAUSTED`
- **THEN** el error tiene código `quota_exhausted` y se hizo una sola petición

#### Scenario: Saturación pasajera
- **WHEN** el modelo falla con 503 una vez y después responde bien, con 2 reintentos configurados
- **THEN** la llamada termina bien tras 2 peticiones

#### Scenario: Saturación persistente
- **WHEN** el modelo falla siempre con 503, con 2 reintentos configurados
- **THEN** el error tiene código `provider_unavailable` tras 3 peticiones

#### Scenario: Tiempo agotado
- **WHEN** el modelo lanza una excepción de tiempo agotado del cliente HTTP
- **THEN** el error tiene código `timeout`

#### Scenario: Clave rechazada
- **WHEN** el modelo falla por autenticación
- **THEN** el error tiene código `provider_error` y no se reintenta

### Requirement: Fallos que no son del proveedor
Solo las excepciones del proveedor y de la red SHALL convertirse en un error con código. Un fallo del propio código SHALL propagarse sin convertir ni reintentar.

#### Scenario: Fallo que no es del proveedor
- **WHEN** la llamada falla con un `KeyError`
- **THEN** se propaga el `KeyError`, sin código del proveedor ni reintentos

### Requirement: Razonamiento configurable por paso
El nivel de razonamiento del modelo SHALL configurarse en `agent.yaml` por prefijo del modelo (el prefijo más largo que coincide) y por paso: planificación y corrección por un lado, síntesis por otro. Los valores admitidos son `minimal`, `low`, `medium` y `high`. Un paso sin prefijo que coincida SHALL usar el razonamiento del modelo.

#### Scenario: Gemini 3 con razonamiento bajo
- **WHEN** el modelo es `gemini-3-flash` y `agent.yaml` asigna `low` al prefijo `gemini-3` en la planificación y en la síntesis
- **THEN** las llamadas de planificación y de síntesis usan razonamiento `low`, y el modelo compartido no cambia

#### Scenario: Solo la síntesis configurada
- **WHEN** solo la síntesis tiene valor para el prefijo `gemini-3`
- **THEN** la síntesis usa `low` y la planificación no fija ningún nivel

#### Scenario: Modelo sin prefijo configurado
- **WHEN** el modelo es `gemini-2.5-flash` y solo hay valores para `gemini-3`
- **THEN** ni la planificación ni la síntesis fijan ningún nivel de razonamiento

#### Scenario: Valor no admitido
- **WHEN** `agent.yaml` asigna `maximo` a un prefijo
- **THEN** la carga de la configuración falla y el error nombra el campo
