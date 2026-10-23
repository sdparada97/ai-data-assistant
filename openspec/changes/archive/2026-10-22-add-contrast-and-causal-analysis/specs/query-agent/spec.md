# Spec Delta

## MODIFIED Requirements

### Requirement: Planificación en una sola respuesta
El LLM SHALL pedir en **una** respuesta todas las consultas necesarias a las herramientas del agente (ver «Herramientas del agente»). El agente las ejecuta todas, incluso varias sobre la misma base. Después, el LLM solo SHALL poder pedir consultas en una corrección. Una respuesta sin consultas SHALL dar estado `fuera_de_alcance`, con el mensaje fijo de `agent.yaml`. Las consultas por encima del máximo de una herramienta SHALL descartarse con un aviso.

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

### Requirement: Evidencias en la respuesta
La respuesta SHALL incluir cada evidencia de las consultas correctas de la ejecución con su id, su tipo (ver «Tipos de evidencia»), los ids por los que se puede citar, su origen y su contenido. El origen es la herramienta o el documento, el fragmento y la página. El contenido es el resultado completo de la consulta, el texto del fragmento o, en una búsqueda, la consulta y los ids de sus fragmentos. Toda cita de una afirmación SHALL corresponder a alguna evidencia.

#### Scenario: Evidencia de una consulta de métricas
- **WHEN** se responde la pregunta de la región con mayor caída con la consulta del escenario "Pregunta de cifras" y un hecho que cita `EV-d5c128c22542`
- **THEN** la respuesta incluye la evidencia `EV-d5c128c22542` de tipo `metricas`, cuyo resultado tiene `Sur` primero con `var_pct = -30.27`

#### Scenario: Evidencia citada por un ID principal
- **WHEN** se recupera el fragmento `05_Reporte_Comercial:004` y una afirmación cita `REP-01`
- **THEN** la respuesta incluye una evidencia de tipo `documento`, citable por `REP-01` y por `05_Reporte_Comercial:004`, con el documento `05_Reporte_Comercial`, la página 1 y el texto del fragmento

#### Scenario: Evidencia de una búsqueda
- **WHEN** una búsqueda de documentos recupera el fragmento `05_Reporte_Comercial:004`
- **THEN** la respuesta incluye la evidencia de la búsqueda, de tipo `busqueda`, con su consulta y `REP-01` entre los ids de sus fragmentos, sin repetir sus textos

#### Scenario: Un ID en varios fragmentos
- **WHEN** se recuperan `03_Investigacion_Consumidor:003` (cuyo ID principal es `INV-01`) y el índice `03_Investigacion_Consumidor:018`, que también contiene `INV-01`
- **THEN** la respuesta incluye las dos evidencias y ambas son citables por `INV-01`

### Requirement: Verificación de citas y lenguaje
La verificación SHALL comprobar que:
- toda evidencia citada pertenece a esta ejecución (un `evidence_id`, un identificador de fragmento o un ID de evidencia que contiene un fragmento recuperado);
- todo hecho, hipótesis y contradicción cita al menos una;
- hechos, contradicciones e información insuficiente no usan el léxico causal de `agent.yaml` (salvo lo previsto en «Veredictos causales citados»);
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

### Requirement: Respuesta con el modelo real
Con Gemini configurado, el agente SHALL responder correctamente las preguntas de cifras y de contraste del benchmark. Estas pruebas están marcadas como `llm`.

#### Scenario: Región con mayor caída con Gemini
- **WHEN** con Gemini configurado se pregunta por la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026
- **THEN** la respuesta tiene estado `ok` y un hecho que menciona `Sur` y `30.27` o `30,27`, citando un `evidence_id` de esta ejecución

#### Scenario: Consistencia del reporte con Gemini
- **WHEN** con Gemini configurado se pregunta si es consistente la afirmación del reporte de que Centro es la región con mayor caída
- **THEN** la respuesta tiene una contradicción que menciona `Sur` y cita la evidencia de un contraste o un `evidence_id` de ventas, y una evidencia del reporte

### Requirement: Consultas fallidas sin resolver
El máximo por herramienta SHALL contar las consultas correctas de las dos rondas, así que corregir una consulta fallida no consume otro hueco (salvo lo previsto en «Máximo propio de las herramientas con extracción»). Toda consulta fallida que la corrección no resuelve (porque vuelve a fallar, se descarta o no se corrige) SHALL declararse en información insuficiente.

#### Scenario: Corrección parcial
- **WHEN** fallan una consulta de la marca `Zeta` y otra de la métrica `margen`, y la corrección pide una sola consulta, que funciona
- **THEN** la información insuficiente indica que no se pudo completar una consulta a `consultar_metrica` y menciona `margen`

#### Scenario: Corrección con el máximo ocupado
- **WHEN** el LLM pide 3 consultas a `consultar_metrica` (el máximo), una falla y la corrección pide una consulta correcta
- **THEN** la corrección se ejecuta y no hay avisos de consultas descartadas

#### Scenario: Corrección descartada
- **WHEN** en ese caso la corrección pide dos consultas
- **THEN** la segunda se descarta con el aviso `Se descartó 1 consulta a consultar_metrica (máximo 3)` y la información insuficiente declara la consulta sin completar

## ADDED Requirements

### Requirement: Herramientas del agente
El plan SHALL disponer de cinco herramientas: `consultar_metrica`, `calidad_datos`, `buscar_documentos`, `contrastar_afirmaciones` (consistencia de un documento con los datos) y `evaluar_causalidad` (afirmación causal). Las reglas del plan SHALL indicar cuándo usar cada una de las dos nuevas, los tipos de causa (`competencia`, `disponibilidad`, `metrica_propia`, con ejemplos de `agent.yaml`) y que el segmento donde la pregunta localiza el efecto va como segmento afirmado, no como filtro.

#### Scenario: Herramientas ofrecidas al plan
- **WHEN** se planifica una pregunta
- **THEN** el LLM recibe las cinco herramientas y las reglas mencionan `contrastar_afirmaciones`, `evaluar_causalidad` y los tres tipos de causa

#### Scenario: Contraste del reporte
- **WHEN** el LLM de prueba pide `contrastar_afirmaciones` con `05_Reporte_Comercial` y la extracción de prueba devuelve la tabla regional y `REP-01`
- **THEN** la ejecución usa 3 llamadas al LLM (plan, extracción y síntesis) y la respuesta incluye la evidencia del contraste

### Requirement: Máximo propio de las herramientas con extracción
`contrastar_afirmaciones` y `evaluar_causalidad` SHALL tener su propio máximo por pregunta en `agent.yaml` (1 por defecto), que cuenta las ejecuciones que llegaron a llamar al LLM de extracción, correctas o fallidas. Una ejecución rechazada antes de la extracción (por ejemplo, por un `doc_id` inexistente o por no haber efecto que evaluar) no cuenta, para que la corrección pueda arreglarla.

#### Scenario: Dos contrastes pedidos
- **WHEN** el plan pide dos contrastes con máximo 1
- **THEN** se ejecuta el primero, el segundo se descarta con el aviso `Se descartó 1 consulta a contrastar_afirmaciones (máximo 1)` y se hace una sola extracción

#### Scenario: Documento inexistente corregido
- **WHEN** el plan pide contrastar `06_Inexistente` y la corrección pide `05_Reporte_Comercial`
- **THEN** el segundo contraste se ejecuta y hay una sola extracción

#### Scenario: Evaluación sin efecto corregida
- **WHEN** el plan pide evaluar una causa comparando `2026-T1` con `2026-T1` y la corrección pide `2026-T1` frente a `2026-T2`
- **THEN** la segunda evaluación se ejecuta y hay una sola extracción

#### Scenario: Extracción fallida y corrección
- **WHEN** la extracción devuelve una salida no interpretable y la corrección vuelve a pedir el contraste
- **THEN** el segundo intento se descarta por el máximo, la información insuficiente declara el contraste sin completar y solo hubo una extracción

### Requirement: Errores de la extracción
Una salida de la extracción no interpretable SHALL convertirse en un error de herramienta que pasa a la corrección sin texto de documentos ni la salida del LLM. Los descartes de la validación de afirmaciones u observaciones SHALL ir en el resultado, nunca como argumentos inválidos del plan.

#### Scenario: Error sin texto del documento
- **WHEN** la extracción del contraste de `04_Observaciones_Canales` no es interpretable
- **THEN** el mensaje de la corrección menciona `contrastar_afirmaciones` y no contiene texto de ningún fragmento ni la salida del LLM

#### Scenario: Afirmación descartada no es un error del plan
- **WHEN** todas las afirmaciones extraídas de un contraste salvo una se descartan en la validación
- **THEN** la consulta tiene estado correcto, los descartes van en su resultado y no hay corrección

### Requirement: Consultas conservadas ante un fallo en una herramienta
Si el proveedor del LLM falla dentro de una herramienta, el agente SHALL responder con el código del proveedor conservando en la traza y en las evidencias las consultas que ya terminaron bien en esa ronda. Las llamadas posteriores a la que falla no se ejecutan y quedan en la traza como descartadas.

#### Scenario: Cuota agotada en la extracción
- **WHEN** el plan pide primero la consulta de la región con mayor caída, después un contraste y después otra consulta, y la extracción del contraste falla con cuota agotada
- **THEN** la respuesta tiene estado `error` y código `quota_exhausted`, la traza y las evidencias incluyen `EV-d5c128c22542` y la tercera consulta figura como descartada

### Requirement: Tipos de evidencia
Las evidencias de la respuesta SHALL ser de tipo `metricas`, `calidad`, `documento`, `busqueda`, `contraste` o `causalidad`. Un contraste y una evaluación causal traen su resultado completo, tal como lo definen `report-contrast` y `causal-assessment`. Sus consultas internas SHALL incluirse como evidencias `metricas` con su resultado, y los fragmentos de sus afirmaciones u observaciones validadas, como evidencias `documento`.

#### Scenario: Evidencias de un contraste
- **WHEN** se contrasta `05_Reporte_Comercial`
- **THEN** la respuesta incluye la evidencia `contraste`, la evidencia `metricas` de su consulta de `venta_neta` por región con su resultado y la evidencia `documento` de `REP-01`

#### Scenario: Evidencia de una evaluación causal
- **WHEN** se evalúa "promociones de la competencia"
- **THEN** la respuesta incluye una evidencia `causalidad` titulada `Evaluación causal: «promociones de la competencia»` con el veredicto "no sustentada"

### Requirement: Títulos de contraste y causalidad
Las evidencias de contraste y de causalidad SHALL titularse, en código, `Contraste de <título del documento>` y `Evaluación causal: «<causa>»`.

#### Scenario: Título de un contraste
- **WHEN** se contrasta `05_Reporte_Comercial`
- **THEN** la evidencia del contraste se titula `Contraste de Reporte ejecutivo | Desempeño de Brío`

### Requirement: Cifras citables de contraste y causalidad
Para «Verificación de cifras», los valores de una evidencia de contraste SHALL ser solo, por afirmación comparada, el reportado, el real y la diferencia (en un ranking, la variación real del afirmado y la del primero); los de una causal, solo los de sus criterios. No son valores suyos sus consultas internas (citables por su `evidence_id`), los umbrales, las afirmaciones descartadas ni ningún texto del LLM.

#### Scenario: Cifra del contraste citada
- **WHEN** un hecho dice `En Sur, el reporte indica -7 % y los datos -30.27 %: 23.27 puntos de diferencia` y cita la evidencia del contraste
- **THEN** la verificación lo acepta

#### Scenario: Cifra de una afirmación descartada
- **WHEN** un hecho cita la evidencia del contraste con una cifra que solo aparece en una afirmación descartada
- **THEN** la verificación lo rechaza

### Requirement: Veredictos causales citados
Una afirmación que cita una evidencia causal y nombra un veredicto ("contradicha", "no sustentada" o "compatible") SHALL nombrar el de esa evidencia; si no, la verificación la rechaza. Si incluye literal el veredicto "no sustentada" o "contradicha" de la evidencia que cita, SHALL poder usar el léxico causal para describir la causa evaluada.

#### Scenario: Veredicto alterado
- **WHEN** una contradicción dice que la hipótesis de las promociones es compatible y cita una evidencia causal "no sustentada"
- **THEN** la verificación la rechaza

#### Scenario: Causa descrita con su veredicto
- **WHEN** un hecho dice `Que las promociones causaron la caída es una afirmación no sustentada` y cita la evidencia causal "no sustentada"
- **THEN** la verificación lo acepta

#### Scenario: Léxico causal sin veredicto
- **WHEN** un hecho dice `Las promociones causaron la caída` y cita la evidencia causal
- **THEN** la verificación lo rechaza por lenguaje causal

### Requirement: Validez y avisos de contraste y causalidad
Un contraste SHALL ser evidencia válida si tiene al menos una afirmación comparada; una evaluación causal, siempre. Los avisos de afirmaciones omitidas por el máximo y los de sus consultas internas SHALL aparecer en los avisos de la respuesta.

#### Scenario: Contraste sin afirmaciones válidas
- **WHEN** todas las afirmaciones extraídas se descartan y no hay otra evidencia válida
- **THEN** la respuesta tiene estado `insuficiente` y no se llama al LLM para sintetizar

### Requirement: Información insuficiente coherente con lo consultado
La verificación SHALL rechazar una nota de información insuficiente que, en una misma frase, use un marcador de ausencia de `agent.yaml` y nombre una métrica (o un sinónimo de `agent.yaml`) por una dimensión del catálogo, cuando la ejecución tiene una evidencia `metricas` de esa métrica agrupada por esa dimensión. Solo se mantiene si la métrica forma parte de una frase de excepción de `agent.yaml` (por ejemplo, "precios de la competencia").

#### Scenario: Ventas por región consultadas
- **WHEN** la información insuficiente dice `Faltan registros consolidados de ventas por región` y la ejecución consultó `venta_neta` por región
- **THEN** la verificación la rechaza y el problema nombra `venta_neta` y `region`

#### Scenario: Ventas de la competencia consultadas
- **WHEN** la información insuficiente dice `Faltan ventas de la competencia por región` y la ejecución consultó `venta_neta` por marca y región
- **THEN** la verificación la rechaza

#### Scenario: Ventas por región sin consultar
- **WHEN** la nota de ventas por región aparece en una ejecución sin consulta de `venta_neta` por región
- **THEN** la verificación la acepta

#### Scenario: Precios de la competencia
- **WHEN** la información insuficiente dice `Faltan datos de precios de la competencia por región` y la ejecución consultó `precio_efectivo` por región
- **THEN** la verificación la acepta

#### Scenario: Inventarios por región
- **WHEN** la información insuficiente dice `Faltan datos de inventarios por región`
- **THEN** la verificación la acepta

### Requirement: Preguntas guía con el modelo real
Con Gemini configurado, las preguntas guía del equipo de ventas sobre el reporte y la causalidad SHALL responderse con las herramientas de contraste y de causalidad. Estas pruebas están marcadas como `llm`.

#### Scenario: Conclusiones del reporte con Gemini
- **WHEN** con Gemini se pregunta `¿Son consistentes las principales conclusiones del reporte comercial con los datos de ventas?`
- **THEN** la respuesta tiene estado `ok`, cita la evidencia de un contraste de `05_Reporte_Comercial` y tiene una contradicción que menciona Sur

#### Scenario: Promociones con Gemini
- **WHEN** con Gemini se pregunta `¿Podemos afirmar que las promociones de la competencia causaron la caída de ventas?`
- **THEN** la respuesta cita una evidencia `causalidad` con el veredicto "no sustentada" y ningún hecho ni contradicción contiene léxico causal sin ese veredicto
