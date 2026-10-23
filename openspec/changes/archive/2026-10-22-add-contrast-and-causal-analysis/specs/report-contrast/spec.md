# Spec Delta

## Purpose

Contrasta las afirmaciones de un documento cargado con los datos de ventas: las extrae con un esquema cerrado, las valida en código, las compara con consultas deterministas y da por cada una el valor reportado, el valor real, la diferencia y un veredicto reproducible.

## ADDED Requirements

### Requirement: Contraste de un documento
La herramienta `contrastar_afirmaciones` SHALL recibir el `doc_id` de un documento cargado y contrastar todas sus afirmaciones, leyendo todos sus fragmentos de la base de documentos, sin búsqueda. Un `doc_id` que no esté cargado SHALL rechazarse con un error que nombre el valor y los documentos cargados.

#### Scenario: Documento inexistente
- **WHEN** se pide contrastar `06_Inexistente`
- **THEN** la herramienta devuelve un error que menciona `06_Inexistente` y `05_Reporte_Comercial`

#### Scenario: Todos los fragmentos del documento
- **WHEN** se contrasta `05_Reporte_Comercial`
- **THEN** la extracción recibe sus 12 fragmentos, de `05_Reporte_Comercial:001` a `05_Reporte_Comercial:012`

### Requirement: Extracción con esquema cerrado
Las afirmaciones SHALL extraerse con una llamada al LLM con salida estructurada. Cada una tiene tipo (`variacion`, `ranking`, `direccion` o `cualitativa`), fragmento y, según el tipo, métrica, dimensión y valor, filtros, períodos, valor reportado y dirección. Los fragmentos SHALL ir delimitados como evidencia, con los delimitadores neutralizados y las reglas repetidas después, y el número de afirmaciones SHALL limitarse con `agent.yaml`.

#### Scenario: Fragmentos delimitados
- **WHEN** se contrasta `04_Observaciones_Canales`
- **THEN** el texto de `OC-EXT-06` aparece entre delimitadores de evidencia en el prompt de extracción y las reglas aparecen después de todos ellos

#### Scenario: Máximo de afirmaciones
- **WHEN** la extracción devuelve más afirmaciones que el máximo configurado
- **THEN** se contrastan las primeras hasta el máximo y el resultado avisa de cuántas se omitieron

### Requirement: Enunciado generado en código
El LLM SHALL no escribir enunciados: el de cada afirmación lo genera el código con sus campos validados, de modo que ningún texto libre de la extracción llegue a la síntesis.

#### Scenario: Enunciado de una variación
- **WHEN** se valida la afirmación de Centro de `05_Reporte_Comercial:003`
- **THEN** su enunciado es `Centro: venta neta -23 % (2026-T1 frente a 2026-T2)`, construido con los campos validados

### Requirement: Validación literal de las afirmaciones
Cada afirmación SHALL validarse en código y descartarse, con su motivo, si su fragmento no pertenece al documento o si en la línea del fragmento que contiene el valor de la dimensión no aparece la cifra reportada con el mismo signo (`-`, `−` o `+`; sin signo, positiva). El motivo es "signo distinto" si en esa línea está la cifra con otro signo, y "no está en la línea del valor" si no está. En un párrafo sin saltos de línea vale la frase, sin cortar en abreviaturas ni decimales.

#### Scenario: Afirmación válida
- **WHEN** se extrae que Centro varió `-23 %` en `venta_neta` de la marca Brío entre `2026-T1` y `2026-T2`, con el fragmento `05_Reporte_Comercial:003`
- **THEN** la afirmación es válida

#### Scenario: Valor que no está en el fragmento
- **WHEN** la misma afirmación cita el fragmento `05_Reporte_Comercial:004`
- **THEN** se descarta porque `Centro` y `-23` no están en una misma línea de ese fragmento

#### Scenario: Signo invertido
- **WHEN** se extrae que Oriente varió `-4 %` con el fragmento `05_Reporte_Comercial:003`, cuya línea de Oriente dice `+4 %`
- **THEN** se descarta con el motivo "signo distinto"

#### Scenario: Valor de otra fila
- **WHEN** se extrae que Sur varió `-23 %` con el fragmento `05_Reporte_Comercial:003`
- **THEN** se descarta con el motivo "no está en la línea del valor"

### Requirement: ID de evidencia tomado del fragmento
El ID de evidencia de cada afirmación SHALL tomarse en código del fragmento (su ID principal, su primer ID contenido o su `chunk_id`), nunca del LLM.

#### Scenario: ID de evidencia del fragmento
- **WHEN** se valida una afirmación del fragmento `05_Reporte_Comercial:004`
- **THEN** su ID de evidencia es `REP-01`, tomado del fragmento

### Requirement: Validación de rankings y direcciones
Un ranking SHALL descartarse si el valor de su dimensión (o su alias) no aparece, sin tildes ni mayúsculas, en el texto o en la sección de su fragmento. Una dirección SHALL descartarse si su palabra de sentido (por ejemplo, "contracción" o "crecimiento") no aparece en el texto del fragmento.

#### Scenario: Región en la sección del fragmento
- **WHEN** se extrae de `OC-CEN-02` que Centro sería la región más afectada
- **THEN** la afirmación es válida porque `Centro` aparece en la sección `OC-CEN-02 | Centro`

#### Scenario: Región que no aparece
- **WHEN** se extrae de `OC-CEN-02` que Norte sería la región más afectada
- **THEN** se descarta porque `Norte` no aparece en el texto ni en la sección del fragmento

### Requirement: Validación de alcance y catálogo
Cada afirmación SHALL descartarse, con su motivo, si la dimensión, el valor o los filtros no están en el catálogo (con alias), o si algún valor de filtro (o su alias) no aparece en el título, la sección o el texto del documento. Una afirmación cuya métrica no está en el catálogo SHALL quedar como "no verificable con los datos", sin consulta.

#### Scenario: Región fuera del catálogo
- **WHEN** una afirmación nombra la región `Atlántico`
- **THEN** se descarta con un motivo que nombra `region`, `Atlántico` y las regiones válidas

#### Scenario: Filtro que el documento no menciona
- **WHEN** una afirmación del reporte filtra por la marca `Luma`, que el documento no menciona
- **THEN** se descarta porque `Luma` no aparece en el documento

#### Scenario: Métrica fuera del catálogo
- **WHEN** una afirmación de prueba dice que la cuota de formatos pequeños en Norte subió `5 %`
- **THEN** queda como "no verificable con los datos", sin consulta

### Requirement: Períodos y métrica anclados en el texto
Los períodos de una afirmación SHALL ser válidos, tener datos y estar anclados: su expresión (trimestre, semestre, mes o año) aparece en el fragmento, su sección o el primer fragmento del documento. Los dos períodos SHALL ser distintos. Si no están anclados, se usan los dos últimos trimestres con datos, marcados como "períodos por defecto" y con un aviso. La métrica (su nombre con espacios o un sinónimo de `agent.yaml`) SHALL aparecer en el documento; si no, la afirmación se descarta.

#### Scenario: Período sin datos
- **WHEN** una afirmación compara `2025-T1` con `2025-T2` citando un fragmento que los nombra
- **THEN** se descarta porque esos períodos no tienen datos

#### Scenario: Períodos anclados en el fragmento
- **WHEN** se valida la afirmación de Centro de `05_Reporte_Comercial:003`, cuya línea dice `T2 vs. T1`
- **THEN** compara `2026-T1` con `2026-T2` sin la marca de períodos por defecto

#### Scenario: Períodos por defecto
- **WHEN** la afirmación de `OC-CEN-02` sobre la región más afectada no tiene períodos anclados
- **THEN** se compara entre `2026-T1` y `2026-T2`, el resultado la marca como "períodos por defecto" y los avisos lo indican

#### Scenario: Períodos iguales
- **WHEN** una afirmación de `05_Reporte_Comercial:003` compara `2026-T2` con `2026-T2`
- **THEN** se descarta porque el período base y el de comparación son el mismo

### Requirement: Veredicto de una variación
Las variaciones válidas SHALL compararse con `consultar_metrica` (una consulta por métrica, dimensión, filtros y períodos; variación porcentual con 2 decimales). Diferencia = reportado − real, en pp. Veredicto: "coincide" si el real redondeado a los decimales del reportado (el empate se aleja de cero: −2.5 → −3) es igual; "aproximado" si la diferencia absoluta no supera el umbral de `agent.yaml` (1 pp) con el mismo signo (negativo, cero o positivo); si no, "no coincide".

#### Scenario: Tabla regional del reporte
- **WHEN** se contrastan las cinco filas de `05_Reporte_Comercial:003`
- **THEN** los veredictos son:
  - Centro: reportado −23, real −9.03, diferencia −13.97, "no coincide";
  - Sur: −7 y −30.27, diferencia 23.27, "no coincide";
  - Norte: −4 y −3.48, diferencia −0.52, "aproximado";
  - Oriente: +4 y +4.65, diferencia −0.65, "aproximado";
  - Occidente: −6 y −5.27, diferencia −0.73, "aproximado";
- **AND** las cinco usan una sola consulta de `venta_neta` por región

#### Scenario: Coincidencia por redondeo
- **WHEN** un fragmento de prueba afirma que Sur cayó `-30 %`
- **THEN** el veredicto es "coincide", porque −30.27 redondeado a enteros es −30

#### Scenario: Signo distinto
- **WHEN** un fragmento de prueba afirma que el precio efectivo de Brío en Sur bajó `-0,5 %` entre `2026-T1` y `2026-T2`
- **THEN** el veredicto es "no coincide": la diferencia con el real (+0.02) no llega a 1 pp, pero el signo es distinto

#### Scenario: Umbral configurable
- **WHEN** el umbral de "aproximado" es 0.5 pp
- **THEN** Norte (diferencia −0.52) es "no coincide"

### Requirement: Veredicto de un ranking y de una dirección
Un ranking válido SHALL compararse con la consulta agrupada por su dimensión y ordenada por la variación en su dirección (mayor caída o mayor crecimiento): "verdadera" si el valor afirmado está entre los primeros empatados y "falsa" en otro caso, con el primero real. Una dirección ("se contrae", "crece") SHALL compararse con el signo de la variación total: "verdadera" o "falsa", con el valor real.

#### Scenario: Región con mayor caída según el reporte
- **WHEN** se contrasta `REP-01` (Centro es la región con mayor caída porcentual)
- **THEN** el veredicto es "falsa" y el primero real es Sur con −30.27

#### Scenario: Región más afectada según una supervisora
- **WHEN** se contrasta la afirmación de `OC-CEN-02` de que Centro podría ser la región más afectada
- **THEN** el veredicto es "falsa" y el primero real es Sur

#### Scenario: Contracción de Brío
- **WHEN** se contrasta la afirmación de `05_Reporte_Comercial:002` de que Brío se contrae en el segundo trimestre frente al primero
- **THEN** el veredicto es "verdadera" con una variación real de −10.50

### Requirement: Afirmaciones cualitativas
Las afirmaciones cualitativas SHALL quedar como "no verificable con los datos", sin consulta.

#### Scenario: Faltantes sin inventarios
- **WHEN** se contrasta `REP-03` (alertas de faltantes en Sur)
- **THEN** su veredicto es "no verificable con los datos"

### Requirement: Resultado trazable
El resultado SHALL incluir por afirmación su enunciado generado, fragmento, ID de evidencia, filtros, períodos, valor reportado, real, diferencia, veredicto y el `evidence_id` de su consulta, y aparte las descartadas con su motivo. Su `evidence_id` SHALL derivarse del documento (con la huella de su ingesta), de los umbrales, de las afirmaciones validadas y de los `evidence_id` de sus consultas. Con la misma extracción, el resultado SHALL ser idéntico.

#### Scenario: Misma extracción, mismo resultado
- **WHEN** se contrasta dos veces `05_Reporte_Comercial` con la misma extracción
- **THEN** ambos resultados tienen el mismo `evidence_id` y los mismos veredictos

#### Scenario: Umbral distinto, otra huella
- **WHEN** se contrasta con la misma extracción y otro umbral de "aproximado"
- **THEN** el `evidence_id` es distinto
