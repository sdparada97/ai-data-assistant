# Spec Delta

## ADDED Requirements

### Requirement: Evidencias en la respuesta
La respuesta SHALL incluir cada evidencia de las consultas correctas de la ejecución con su id, su tipo (`metricas`, `calidad`, `documento` o `busqueda`), los ids por los que se puede citar, su origen y su contenido. El origen es la herramienta o el documento, el fragmento y la página. El contenido es el resultado completo de la consulta, el texto del fragmento o, en una búsqueda, la consulta y los ids de sus fragmentos. Toda cita de una afirmación SHALL corresponder a alguna evidencia.

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

### Requirement: Título de cada evidencia
Cada evidencia de la respuesta SHALL tener un título legible, generado en código a partir de la consulta o del documento, sin el LLM ni valores escritos en el código:
- métricas: las métricas, la agrupación, los filtros y los períodos;
- calidad: las reglas, los filtros y los períodos pedidos;
- fragmento: el título del documento, la sección y la página, o "sin página";
- búsqueda: el texto buscado.

#### Scenario: Título de una consulta de métricas
- **WHEN** la evidencia es la consulta de la región con mayor caída
- **THEN** su título es `Venta neta por region · marca Brio · 2026-T1 frente a 2026-T2`

#### Scenario: Título de un fragmento
- **WHEN** la evidencia es el fragmento `05_Reporte_Comercial:004`
- **THEN** su título es `Reporte ejecutivo | Desempeño de Brío · 3. Interpretación preliminar · p. 1`

#### Scenario: Título de un fragmento sin página
- **WHEN** la evidencia es un fragmento de `04_Observaciones_Canales`, que no tiene página
- **THEN** su título termina en `sin página`

#### Scenario: Título de una búsqueda y de una consulta de calidad
- **WHEN** las evidencias son la búsqueda `Sensibilidad al precio en Sur` y una consulta de calidad de la regla `DQ11`
- **THEN** sus títulos son `Búsqueda en documentos: «Sensibilidad al precio en Sur»` y `Calidad de datos · reglas DQ11`

### Requirement: Evidencias en respuestas con error
Una respuesta con estado `error` SHALL incluir las evidencias de las consultas que llegaron a ejecutarse correctamente, aunque el fallo ocurra antes de reunirlas, sin ninguna afirmación.

#### Scenario: Cuota agotada al sintetizar
- **WHEN** la consulta de la región con mayor caída se ejecuta y el LLM falla con cuota agotada en la síntesis
- **THEN** la respuesta tiene estado `error`, ningún hecho e incluye la evidencia `EV-d5c128c22542`

#### Scenario: Cuota agotada al corregir
- **WHEN** en la primera ronda la consulta de la región con mayor caída funciona y otra de la marca `Zeta` falla, y el LLM falla con cuota agotada en la corrección
- **THEN** la respuesta tiene estado `error` e incluye la evidencia `EV-d5c128c22542`
