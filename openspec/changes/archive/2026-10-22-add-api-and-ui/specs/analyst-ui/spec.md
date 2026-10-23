# Spec Delta

## Purpose

Página en la que el analista escribe preguntas en lenguaje natural y lee la respuesta del agente separada en hechos, hipótesis, contradicciones e información insuficiente, con el detalle de cada evidencia citada, los avisos y la traza.

## ADDED Requirements

### Requirement: Pregunta y respuesta por apartados
La página SHALL tener un campo para escribir la pregunta. Al enviarla, SHALL llamar a `POST /ask` de la API en `BACKEND_URL` y mostrar la respuesta en los apartados "Hechos", "Hipótesis", "Contradicciones" e "Información insuficiente", omitiendo los vacíos. Cada afirmación SHALL mostrar sus evidencias citadas por su título, y el id en el detalle.

#### Scenario: Respuesta con hechos y contradicciones
- **WHEN** se envía una pregunta y la API devuelve un hecho que cita `EV-d5c128c22542` y una contradicción que cita `REP-01` y `EV-d5c128c22542`
- **THEN** la página muestra los apartados "Hechos" y "Contradicciones" con esas afirmaciones y los títulos de sus evidencias, y no muestra "Hipótesis"

### Requirement: Texto mostrado tal cual
Las afirmaciones, los mensajes, los avisos, la traza, los títulos de las evidencias y el texto de los fragmentos SHALL mostrarse tal cual: sin interpretar Markdown, HTML, fórmulas, colores ni emojis abreviados, ni como instrucciones.

#### Scenario: Afirmación con símbolos
- **WHEN** una afirmación dice `Entre $1.000 y $2.000 **x** :red[y]`
- **THEN** la página muestra exactamente ese texto

#### Scenario: Fragmento con formato
- **WHEN** el texto de un fragmento contiene `**negrita**` y `<b>etiqueta</b>`
- **THEN** la página muestra esos caracteres tal cual

#### Scenario: Título con símbolos
- **WHEN** el título de una evidencia es `Informe **Q2** $1.000 :red[x]`
- **THEN** el desplegable muestra ese título tal cual

### Requirement: Detalle de las evidencias
Cada evidencia citable por un id citado SHALL poder desplegarse desde su título; el detalle empieza por su id y sus ids citables. Para una consulta de métricas, la tabla de resultados (grupo y valores); para una consulta de calidad, sus incidencias; para un fragmento, su texto con el documento y la página, o "sin página" si no la tiene; para una búsqueda, la consulta y los ids de sus fragmentos. Las cifras SHALL mostrarse como vienen en la respuesta, sin calcularlas ni redondearlas.

#### Scenario: Evidencia de métricas
- **WHEN** se despliega la evidencia citada como `EV-d5c128c22542`, la consulta de la región con mayor caída
- **THEN** el desplegable se titula `Venta neta por region · marca Brio · 2026-T1 frente a 2026-T2`, muestra el id `EV-d5c128c22542` y una tabla cuya primera fila es `Sur` con la variación porcentual (`var_pct`) `-30.27`

#### Scenario: Evidencia de un documento
- **WHEN** se despliega `REP-01`
- **THEN** se ve el texto del fragmento `05_Reporte_Comercial:004`, el documento `05_Reporte_Comercial` y la página 1

#### Scenario: Id con varias evidencias
- **WHEN** una afirmación cita `INV-01` y la respuesta tiene dos evidencias citables por `INV-01` (`03_Investigacion_Consumidor:003` y `03_Investigacion_Consumidor:018`)
- **THEN** la afirmación muestra dos desplegables, uno por evidencia, cada uno con su título

#### Scenario: Cita sin evidencia
- **WHEN** una afirmación cita un id que no corresponde a ninguna evidencia de la respuesta
- **THEN** la página muestra ese id con el aviso de que la evidencia no viene en la respuesta

#### Scenario: Evidencia de una búsqueda
- **WHEN** se despliega el `evidence_id` de una búsqueda que recuperó `05_Reporte_Comercial:004`
- **THEN** se ven la consulta y `REP-01` entre los ids de sus fragmentos

#### Scenario: Evidencia de calidad
- **WHEN** se despliega el `evidence_id` de una consulta de calidad de la regla `DQ11`
- **THEN** se ve una tabla con sus 3 incidencias y la regla `DQ11`

#### Scenario: Fragmento sin página
- **WHEN** se despliega un fragmento de `01_Contexto_Negocio`, que no tiene página
- **THEN** se ve su texto y el documento con la indicación "sin página"

### Requirement: Avisos y traza
La página SHALL mostrar los avisos de la respuesta destacados y, desplegable, la traza: modelo, llamadas al LLM, duración, cada consulta (herramienta, estado y `evidence_id`) y los problemas de verificación.

#### Scenario: Aviso de período sin datos
- **WHEN** la respuesta trae el aviso `El período 2025-T1 no tiene datos en la base`
- **THEN** la página muestra el encabezado fijo de avisos seguido de ese texto tal cual

#### Scenario: Traza desplegable
- **WHEN** se despliega la traza de una respuesta con 2 llamadas al LLM y una consulta a `consultar_metrica`
- **THEN** se ven el modelo, `2` llamadas, la duración y la consulta con su estado y su `evidence_id`

### Requirement: Historial de la sesión
La página SHALL mostrar, en orden, las preguntas y respuestas de la sesión del navegador, e indicar con un texto fijo que cada pregunta se responde de forma independiente, sin recordar las anteriores. Cada petición a la API SHALL llevar solo la pregunta nueva.

#### Scenario: Dos preguntas en la sesión
- **WHEN** se envían dos preguntas seguidas
- **THEN** la página muestra ambas con sus respuestas, en el orden en que se hicieron, y la segunda petición a la API contiene solo la segunda pregunta

#### Scenario: Aviso de independencia
- **WHEN** se abre la página
- **THEN** se ve el texto fijo que indica que el asistente no recuerda las preguntas anteriores

### Requirement: Pregunta en curso
Mientras se espera una respuesta, el campo de pregunta SHALL estar desactivado. La respuesta SHALL guardarse en el historial en cuanto llega, para que no se pierda aunque la página se vuelva a pintar.

#### Scenario: Campo desactivado
- **WHEN** hay una pregunta en curso
- **THEN** el campo de pregunta está desactivado y la pregunta aparece en el historial como pendiente

#### Scenario: Respuesta guardada
- **WHEN** llega la respuesta de una pregunta en curso
- **THEN** queda en el historial junto a su pregunta y el campo vuelve a estar activo

### Requirement: Mensajes de estado y de error
La página SHALL mostrar un mensaje claro según el resultado:
- `fuera_de_alcance` e `insuficiente`: el mensaje de la respuesta;
- `quota_exhausted`: que se agotó la cuota del LLM y conviene esperar;
- `data_unavailable` y `configuration_error`: el mensaje de la API, que nombra el comando o la variable;
- otros errores: el código y el mensaje.

Un error SHALL quedar en el historial sin impedir nuevas preguntas.

#### Scenario: Cuota agotada
- **WHEN** la API responde 429 con código `quota_exhausted`
- **THEN** la página muestra un error que menciona la cuota y permite enviar otra pregunta

#### Scenario: Datos sin cargar
- **WHEN** la API responde 503 con código `data_unavailable` y un mensaje que menciona `make ingest`
- **THEN** la página muestra ese mensaje

#### Scenario: Configuración inválida
- **WHEN** la API responde 503 con código `configuration_error` y un mensaje que menciona `GEMINI_API_KEY`
- **THEN** la página muestra ese mensaje

#### Scenario: Fuera de alcance
- **WHEN** la API responde 200 con estado `fuera_de_alcance` y su mensaje
- **THEN** la página muestra ese mensaje, sin apartados

#### Scenario: Respuesta insuficiente
- **WHEN** la API responde 200 con estado `insuficiente`, su mensaje y una nota en información insuficiente
- **THEN** la página muestra el aviso de evidencia insuficiente, el mensaje y el apartado "Información insuficiente" con la nota

#### Scenario: Otro error
- **WHEN** la API responde 502 con código `invalid_output` y un mensaje
- **THEN** la página muestra el código `invalid_output` y el mensaje

### Requirement: Respuesta no reconocible
Si la API responde con un cuerpo que no es una respuesta del agente (por ejemplo, texto plano o un JSON sin estado), la página SHALL mostrar un error con el estado HTTP, sin lanzar ninguna excepción y permitiendo nuevas preguntas.

#### Scenario: Error 500 en texto plano
- **WHEN** la API responde 500 con el cuerpo `Internal Server Error`
- **THEN** la página muestra un error que incluye `500` y permite enviar otra pregunta

### Requirement: API inaccesible
Si el cliente HTTP no puede conectar con la API, la conexión se corta, o la API no contesta en `BACKEND_TIMEOUT_S` segundos (300 por defecto), la página SHALL mostrar un error con `BACKEND_URL` y, si se agotó el tiempo, los segundos esperados y que la pregunta puede seguir en curso en la API. No SHALL lanzar ninguna excepción y SHALL permitir nuevas preguntas.

#### Scenario: Sin conexión
- **WHEN** el cliente HTTP falla con un error de conexión
- **THEN** la página muestra un error que incluye `BACKEND_URL` y no lanza ninguna excepción

#### Scenario: Conexión cortada
- **WHEN** la conexión se corta a mitad de la respuesta (error de protocolo del cliente HTTP)
- **THEN** la página muestra un error que incluye `BACKEND_URL` y no lanza ninguna excepción

#### Scenario: API que no contesta a tiempo
- **WHEN** el cliente HTTP agota los `BACKEND_TIMEOUT_S` segundos
- **THEN** la página muestra un error con `BACKEND_URL`, los segundos y que la pregunta puede seguir en curso

### Requirement: Tiempo de espera configurable
`BACKEND_TIMEOUT_S` SHALL leerse del entorno. Un valor vacío usa 300; un valor que no sea un número positivo y finito SHALL sustituirse por 300 y avisarse en la página.

#### Scenario: Valor inválido
- **WHEN** la página se abre con `BACKEND_TIMEOUT_S=abc`
- **THEN** usa 300 segundos y muestra un aviso que nombra `BACKEND_TIMEOUT_S`
