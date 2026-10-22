# query-agent Specification

## Purpose

Responde preguntas en lenguaje natural sobre las ventas y los documentos: el LLM planifica las consultas en una sola respuesta, el agente las ejecuta con herramientas deterministas y entrega una respuesta verificada que separa hechos, hipótesis, contradicciones e información insuficiente, con evidencia citada y traza.

## Requirements

### Requirement: Validación de la pregunta
Una pregunta vacía o más larga que el máximo de `agent.yaml` SHALL rechazarse con estado `error` y código `invalid_question`, sin llamar al LLM.

#### Scenario: Pregunta vacía
- **WHEN** la pregunta es `"   "`
- **THEN** la respuesta tiene estado `error`, código `invalid_question` y 0 llamadas al LLM

#### Scenario: Pregunta demasiado larga
- **WHEN** la pregunta tiene un carácter más que el máximo de `agent.yaml`
- **THEN** la respuesta tiene estado `error`, código `invalid_question` y 0 llamadas al LLM

### Requirement: Contexto de la planificación
El prompt de planificación SHALL incluir:
- el catálogo de `semantic_layer.yaml`: métricas, dimensiones, valores válidos y alias;
- los documentos disponibles;
- el rango de meses y trimestres con datos, leído de la base de ventas en cada ejecución;
- la regla de usar ese rango, o el que cite el documento, si la pregunta no indica período.

Ninguno de esos valores SHALL estar escrito en el código.

#### Scenario: Rango de datos real
- **WHEN** se construye el prompt sobre la base de ventas de `data/raw/`
- **THEN** indica datos de `2026-01` a `2026-06` y los trimestres `2026-T1` y `2026-T2`

#### Scenario: Catálogo desde configuración
- **WHEN** una capa semántica de prueba añade la marca `Prueba`
- **THEN** el prompt de planificación incluye `Prueba` sin cambios en el código

### Requirement: Prompts y descripciones desde configuración
Las descripciones de las herramientas que recibe el LLM SHALL salir de la configuración, sin valores de negocio escritos en el código: la de `consultar_metrica` nombra las métricas de la capa semántica. El nombre con el que se presenta el asistente y los ejemplos de expresiones atenuadas (las primeras de `hedges`), en los prompts y en los avisos de la verificación, SHALL leerse de `agent.yaml`.

#### Scenario: Descripción de herramienta desde configuración
- **WHEN** una capa semántica de prueba tiene una sola métrica
- **THEN** la descripción de `consultar_metrica` nombra esa métrica y ninguna otra

#### Scenario: Nombre del asistente desde configuración
- **WHEN** `agent.yaml` tiene `assistant_name: Asistente de Prueba`
- **THEN** los prompts de planificación y de síntesis empiezan por `Eres Asistente de Prueba,` y no contienen otro nombre

#### Scenario: Ejemplos de atenuación desde configuración
- **WHEN** `hedges` empieza por `tal vez`
- **THEN** las reglas del prompt de síntesis citan como ejemplos `"tal vez"` y las dos expresiones siguientes de la lista

### Requirement: Planificación en una sola respuesta
El LLM SHALL pedir en **una** respuesta todas las consultas necesarias a `consultar_metrica`, `calidad_datos` y `buscar_documentos`. El agente las ejecuta todas, incluso varias sobre la misma base. Después, el LLM solo SHALL poder pedir consultas en una corrección. Una respuesta sin consultas SHALL dar estado `fuera_de_alcance`, con el mensaje fijo de `agent.yaml`. Las consultas por encima del máximo de una herramienta SHALL descartarse con un aviso.

#### Scenario: Pregunta de cifras
- **WHEN** se pregunta por la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026 y el LLM pide `consultar_metrica` con `metrics=[venta_neta]`, `filters={marca: [Brío]}`, `group_by=[region]`, `compare={base: 2026-T1, target: 2026-T2}` y `sort={metric: venta_neta, field: var_pct, order: asc}`
- **THEN** el resultado tiene `evidence_id` `EV-d5c128c22542`, con `Sur` primero y `var_pct = -30.27`

#### Scenario: Pregunta fuera de alcance
- **WHEN** se pregunta `¿Qué tiempo hará mañana en Bogotá?` y el LLM no pide ninguna consulta
- **THEN** la respuesta tiene estado `fuera_de_alcance` y el mensaje fijo de `agent.yaml`, sin el texto del LLM; no se ejecuta ninguna herramienta y la traza registra 1 llamada al LLM

#### Scenario: Varias consultas a la misma base
- **WHEN** en la misma respuesta el LLM pide dos consultas a `consultar_metrica`, una de `venta_neta` y otra de `unidades`
- **THEN** ambas se ejecutan bien y cada una tiene su `evidence_id`

#### Scenario: Consultas por encima del máximo
- **WHEN** el LLM pide 5 búsquedas de documentos y el máximo es 3
- **THEN** se ejecutan las 3 primeras y los avisos incluyen `Se descartaron 2 consultas a buscar_documentos (máximo 3)`

### Requirement: Argumentos tolerantes
Donde una herramienta espera una lista, un valor suelto SHALL aceptarse como lista de un elemento, antes de validar la consulta.

#### Scenario: Filtro como texto
- **WHEN** el LLM pide la consulta de la región con mayor caída con `filters={marca: "Brío"}` en lugar de `["Brío"]`
- **THEN** se ejecuta sin corrección y su `evidence_id` es `EV-d5c128c22542`

### Requirement: Corrección única
Si alguna consulta falla, por un `QueryError` o por argumentos inválidos, el agente SHALL pedir al LLM **una** corrección. La petición incluye:
- solo las consultas fallidas y sus errores (campo, valor rechazado y opciones válidas);
- ningún texto de documentos ni resultado de consultas correctas.

Las consultas correctas no se repiten. Si la corrección vuelve a fallar, cada fallo se declara en información insuficiente.

#### Scenario: Marca inexistente
- **WHEN** el LLM pide ventas de la marca `Zeta`
- **THEN** la petición de corrección incluye `filters.marca`, `Zeta` y `Brio, Luma, Nativa, Rizo, Senda`

#### Scenario: Argumentos inválidos
- **WHEN** el LLM pide `consultar_metrica` con `period` y `compare` a la vez
- **THEN** la petición de corrección incluye el error de validación con el motivo

#### Scenario: Consulta descartada y consulta fallida
- **WHEN** el LLM pide 4 búsquedas de documentos (máximo 3) y una consulta de la marca `Zeta`
- **THEN** la petición de corrección incluye una respuesta para cada consulta pedida, y la búsqueda sobrante figura como descartada por el máximo

#### Scenario: Corrección sin texto de documentos
- **WHEN** en la misma respuesta el LLM pide una búsqueda de documentos que funciona y una consulta de la marca `Zeta`
- **THEN** la petición de corrección no contiene texto de ningún fragmento

#### Scenario: Corrección que vuelve a fallar
- **WHEN** la corrección vuelve a pedir la marca `Zeta`
- **THEN** no hay una segunda corrección y la información insuficiente menciona `filters.marca` y `Zeta`

### Requirement: Consultas fallidas sin resolver
El máximo por herramienta SHALL contar las consultas correctas de las dos rondas, así que corregir una consulta fallida no consume otro hueco. Toda consulta fallida que la corrección no resuelve (porque vuelve a fallar, se descarta o no se corrige) SHALL declararse en información insuficiente.

#### Scenario: Corrección parcial
- **WHEN** fallan una consulta de la marca `Zeta` y otra de la métrica `margen`, y la corrección pide una sola consulta, que funciona
- **THEN** la información insuficiente indica que no se pudo completar una consulta a `consultar_metrica` y menciona `margen`

#### Scenario: Corrección con el máximo ocupado
- **WHEN** el LLM pide 3 consultas a `consultar_metrica` (el máximo), una falla y la corrección pide una consulta correcta
- **THEN** la corrección se ejecuta y no hay avisos de consultas descartadas

#### Scenario: Corrección descartada
- **WHEN** en ese caso la corrección pide dos consultas
- **THEN** la segunda se descarta con el aviso `Se descartó 1 consulta a consultar_metrica (máximo 3)` y la información insuficiente declara la consulta sin completar

### Requirement: Evidencia válida y avisos
Un resultado de métricas SHALL ser evidencia válida solo si tiene al menos un valor no nulo; uno de documentos, si tiene al menos un fragmento; uno de calidad, siempre. Los avisos de las herramientas (período sin datos, búsqueda solo por palabras, sin coincidencias) SHALL aparecer en los avisos de la respuesta, generados por código.

#### Scenario: Período sin datos
- **WHEN** el LLM pide ventas de Brío en `2025-T1` y nada más
- **THEN** la respuesta tiene estado `insuficiente`, los avisos incluyen `El período 2025-T1 no tiene datos en la base` y no se llama al LLM para sintetizar

### Requirement: Sin evidencia, sin síntesis
Si tras la ejecución no hay ninguna evidencia válida, el agente SHALL responder con información insuficiente sin llamar al LLM para sintetizar.

#### Scenario: Todas las consultas fallan
- **WHEN** todas las consultas fallan, también tras la corrección
- **THEN** la respuesta tiene estado `insuficiente` y la traza registra 2 llamadas al LLM

### Requirement: Síntesis estructurada
El LLM SHALL redactar, con salida estructurada, cuatro apartados: hechos, hipótesis, contradicciones e información insuficiente. Cada hecho, hipótesis o contradicción cita al menos una evidencia. El LLM recibe resúmenes de los resultados, no los resultados completos. El texto de los documentos SHALL ir delimitado como evidencia, con los delimitadores neutralizados dentro del texto, y las reglas se repiten tras la evidencia.

#### Scenario: Documentos delimitados
- **WHEN** la evidencia incluye el fragmento de `OC-EXT-06`
- **THEN** en el prompt de síntesis ese texto aparece entre delimitadores de evidencia y las reglas aparecen después de todos ellos

#### Scenario: Delimitador dentro de un fragmento
- **WHEN** un fragmento de prueba contiene el texto del delimitador de cierre
- **THEN** en el prompt de síntesis ese texto aparece neutralizado y el número de delimitadores de cierre es igual al de fragmentos

#### Scenario: Síntesis no interpretable
- **WHEN** las dos respuestas de síntesis no se ajustan al esquema
- **THEN** la respuesta tiene estado `error` y código `invalid_output`

### Requirement: Verificación de cifras
Toda cifra de una afirmación SHALL aparecer en los valores o en el texto literal de alguna evidencia que esa afirmación cita, con o sin signo, con redondeo a 0–2 decimales y en formato `1.234,5` o `1,234.5`. Se ignoran los períodos (`AAAA-Tn`, `AAAA-Sn`, `AAAA-MM`, `Tn`, `Sn`), los años del rango con datos y los identificadores de evidencia, fragmentos y documentos (los `doc_id` de la tabla `documents`). Lo que el LLM escribe en información insuficiente no lleva cifras.

#### Scenario: Cifra del reporte presentada como dato de ventas
- **WHEN** un hecho dice `Centro tuvo la mayor caída, con -23 %` y cita solo `EV-d5c128c22542`
- **THEN** la verificación lo rechaza porque `23` no está en esa evidencia

#### Scenario: Cifra del reporte citada con su fragmento
- **WHEN** un hecho dice `El reporte afirma que Centro cayó -23 %` y cita `REP-01` y `05_Reporte_Comercial:003`
- **THEN** la verificación lo acepta

#### Scenario: Cifra citada con un fragmento que no la contiene
- **WHEN** un hecho dice `El reporte afirma que Centro cayó -23 %` y cita solo `REP-01`
- **THEN** la verificación lo rechaza, porque el fragmento de `REP-01` no contiene `-23`

#### Scenario: Cifra de cuatro dígitos sin respaldo
- **WHEN** un hecho dice `Brío vendió 1500 unidades más en Norte` y cita `EV-d5c128c22542`
- **THEN** la verificación lo rechaza porque `1500` no está en esa evidencia

#### Scenario: Nombre de documento en la afirmación
- **WHEN** un hecho dice `Según 05_Reporte_Comercial, Centro cayó -23 %` y cita `05_Reporte_Comercial:003`
- **THEN** la verificación lo acepta: el `05` del nombre del documento no es una cifra

#### Scenario: Cifra junto al nombre de un documento
- **WHEN** un hecho dice `Según 05_Reporte_Comercial, Centro cayó 5 %` y cita `05_Reporte_Comercial:003`
- **THEN** la verificación lo rechaza porque `5` no está en esa evidencia

#### Scenario: Caída expresada sin signo
- **WHEN** un hecho dice `Sur cayó 30,27 % entre 2026-T1 y 2026-T2` y cita `EV-d5c128c22542`
- **THEN** la verificación lo acepta

### Requirement: Verificación de citas y lenguaje
La verificación SHALL comprobar que:
- toda evidencia citada pertenece a esta ejecución (un `evidence_id`, un identificador de fragmento o un ID de evidencia que contiene un fragmento recuperado);
- todo hecho, hipótesis y contradicción cita al menos una;
- hechos, contradicciones e información insuficiente no usan el léxico causal de `agent.yaml`;
- cada hipótesis contiene una de las expresiones atenuadas de `agent.yaml`.

#### Scenario: Cita inexistente
- **WHEN** una afirmación cita `REP-99`
- **THEN** la verificación la rechaza por evidencia inexistente

#### Scenario: ID citado dentro de un fragmento
- **WHEN** se recuperó el fragmento del índice de referencias de la investigación y una hipótesis cita `INV-01`
- **THEN** la verificación acepta la cita

#### Scenario: Lenguaje causal en un hecho
- **WHEN** un hecho dice `Las promociones de la competencia causaron la caída`
- **THEN** la verificación lo rechaza por lenguaje causal

#### Scenario: Hipótesis sin atenuar
- **WHEN** una hipótesis dice `La caída se explica por los faltantes en Sur`
- **THEN** la verificación la rechaza por no estar atenuada

### Requirement: Reintento y fallo cerrado
Si la verificación encuentra problemas, el agente SHALL pedir **una** nueva síntesis con la lista de problemas. Si persisten, SHALL retirar las afirmaciones que fallan y declararlo en información insuficiente. Si no queda ningún hecho ni contradicción, el estado SHALL ser `insuficiente`.

#### Scenario: Corrección tras el reintento
- **WHEN** la primera síntesis cita `REP-99` y la segunda cita `REP-01`
- **THEN** la respuesta usa la segunda síntesis y la traza registra 1 reintento de síntesis

#### Scenario: Fallo cerrado
- **WHEN** la segunda síntesis mantiene un hecho con una cifra sin respaldo
- **THEN** ese hecho no aparece en la respuesta y la información insuficiente indica `Se retiró 1 afirmación no verificada`

### Requirement: Respuesta y traza
La respuesta SHALL incluir el estado (`ok`, `insuficiente`, `fuera_de_alcance` o `error`), el código de error si lo hay, los cuatro apartados, los avisos y una traza con:
- cada consulta (herramienta, argumentos, estado, `evidence_id` y resultado completo);
- las correcciones y los problemas de verificación;
- las llamadas al LLM y los intentos al proveedor;
- el modelo y la duración.

#### Scenario: Traza de una pregunta de cifras
- **WHEN** se responde la pregunta de la región con mayor caída con la consulta del escenario "Pregunta de cifras" y una síntesis válida
- **THEN** la traza registra 2 llamadas al LLM, 1 consulta a `consultar_metrica` con `evidence_id` `EV-d5c128c22542` y su resultado completo, y la verificación sin problemas

### Requirement: Traza por pregunta
Las llamadas y los intentos de la traza SHALL ser los de esa pregunta, aunque las dependencias se reutilicen, y los problemas de verificación SHALL aparecer una sola vez.

#### Scenario: Dos preguntas con las mismas dependencias
- **WHEN** se responden dos preguntas seguidas con las mismas dependencias, cada una con 2 llamadas al LLM
- **THEN** la traza de cada respuesta registra 2 llamadas, no la suma

### Requirement: Errores del proveedor y de los datos
Ante un fallo, el agente SHALL devolver una respuesta con estado `error`, sin afirmaciones y conservando en la traza lo ejecutado, en lugar de lanzar una excepción. Códigos:
- el del proveedor de LLM;
- `configuration_error` si la configuración es inválida;
- `data_unavailable` si falta una base, con un mensaje que indica `make ingest` o `make ingest-docs` y sin llamar al LLM;
- `internal_error` ante cualquier otro fallo, con un mensaje sin el texto de la excepción.

#### Scenario: Fallo interno
- **WHEN** la planificación falla con una excepción que no es del proveedor ni de los datos
- **THEN** la respuesta tiene estado `error`, código `internal_error` y un mensaje sin el texto de la excepción

#### Scenario: Cuota agotada al planificar
- **WHEN** el LLM falla con `quota_exhausted` en la planificación
- **THEN** la respuesta tiene estado `error`, código `quota_exhausted` y ningún hecho

#### Scenario: Cuota agotada al sintetizar
- **WHEN** las consultas se ejecutan y el LLM falla con `quota_exhausted` en la síntesis
- **THEN** la respuesta tiene estado `error` y la traza conserva las consultas ejecutadas

#### Scenario: Base de ventas ausente
- **WHEN** la base de ventas configurada no existe
- **THEN** la respuesta tiene estado `error`, código `data_unavailable`, un mensaje que menciona `make ingest` y 0 llamadas al LLM

#### Scenario: Clave fuera de la traza
- **WHEN** la clave es `clave-de-prueba-123` y el LLM falla con un error cuyo texto incluye la clave
- **THEN** ni la respuesta ni la traza contienen `clave-de-prueba-123`

### Requirement: Configuración inválida
Si `answer_question` construye sus dependencias y la configuración es inválida (variables del LLM, rutas o archivos de configuración), SHALL devolver una respuesta con estado `error` y código `configuration_error`, con un mensaje que nombra lo que falta, sin llamar al LLM. La configuración del LLM SHALL validarse antes de abrir las bases.

#### Scenario: Configuración inválida
- **WHEN** se llama a `answer_question` sin dependencias y `LLM_PROVIDER` está vacía
- **THEN** la respuesta tiene estado `error`, código `configuration_error`, un mensaje que menciona `LLM_PROVIDER` y 0 llamadas al LLM

### Requirement: Comando de consulta
`make ask Q="<pregunta>"` SHALL responder la pregunta e imprimir la respuesta por apartados con sus evidencias y avisos. SHALL terminar con código distinto de 0 si falta configuración del proveedor.

#### Scenario: Clave vacía
- **WHEN** se ejecuta `make ask Q="hola"` con `ENV_FILE=/dev/null`, `LLM_PROVIDER=gemini`, `GEMINI_MODEL` con valor y `GEMINI_API_KEY` vacía
- **THEN** termina con código distinto de 0 y la salida menciona `GEMINI_API_KEY`

### Requirement: Respuesta con el modelo real
Con Gemini configurado, el agente SHALL responder correctamente las preguntas de cifras y de contraste del benchmark. Estas pruebas están marcadas como `llm`.

#### Scenario: Región con mayor caída con Gemini
- **WHEN** con Gemini configurado se pregunta por la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026
- **THEN** la respuesta tiene estado `ok` y un hecho que menciona `Sur` y `30.27` o `30,27`, citando un `evidence_id` de esta ejecución

#### Scenario: Consistencia del reporte con Gemini
- **WHEN** con Gemini configurado se pregunta si es consistente la afirmación del reporte de que Centro es la región con mayor caída
- **THEN** la respuesta tiene una contradicción que menciona `Sur` y cita un `evidence_id` de ventas y una evidencia del reporte
