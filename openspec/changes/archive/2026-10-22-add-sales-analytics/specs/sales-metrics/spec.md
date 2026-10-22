# Spec Delta

## Purpose

Responde preguntas cuantitativas sobre las ventas con cifras calculadas por código determinista sobre DuckDB, trazables y acompañadas de los problemas de calidad que las afectan, para que el asistente nunca calcule ni invente números.

## ADDED Requirements

### Requirement: Consulta de métricas en un período
`consultar_metrica` SHALL devolver, para un período, el valor de una o más métricas sobre la tabla `sales`, aplicando filtros por dimensión (uno o varios valores por dimensión) y agrupando por las dimensiones pedidas. Los grupos SHALL salir de los datos. Sin agrupación, SHALL devolver una sola fila con el total del corte.

#### Scenario: Venta neta de Brío por región en T1
- **WHEN** se consulta `venta_neta` con filtro `marca = Brío`, agrupada por `region`, en `2026-T1`
- **THEN** el resultado tiene 5 filas y la de `Sur` vale 363431600 y la de `Centro` 314314900

#### Scenario: Total sin agrupación
- **WHEN** se consulta `venta_neta` con filtro `marca = Brio` en `2026-T2`
- **THEN** el resultado tiene una fila con valor 1282713700

### Requirement: Valores de las métricas
Cada valor SHALL devolverse redondeado a los `decimals` de su métrica (`ROUND_HALF_UP`) y también sin redondear. Las métricas cociente SHALL calcularse en el código a partir del numerador y el denominador exactos.

#### Scenario: Precio efectivo
- **WHEN** se consulta `precio_efectivo` de `marca = Brio` y `region = Sur` en `2026-T1`
- **THEN** el valor redondeado es 9973.42 y el valor sin redondear es exactamente 363431600 / 36440 (venta neta entre unidades del corte)

### Requirement: Comparación entre dos períodos
Con un período base y uno de comparación, `consultar_metrica` SHALL devolver por fila el valor de cada período, `var_abs` (comparación − base) y `var_pct` ((comparación / base − 1) × 100) redondeada a 2 decimales, junto con su valor sin redondear, calculados sobre los valores exactos. También SHALL devolver la fila de total del corte.

#### Scenario: Valor de referencia por región
- **WHEN** se compara `venta_neta` de `marca = Brio` agrupada por `region` entre `2026-T1` y `2026-T2`
- **THEN** la fila `Sur` tiene base 363431600, comparación 253404600, `var_abs` −110027000 y `var_pct` −30.27
- **AND** la fila de total tiene `var_pct` −10.50

#### Scenario: Variación del precio efectivo
- **WHEN** se compara `precio_efectivo` de `marca = Brio` y `region = Sur` entre `2026-T1` y `2026-T2`
- **THEN** la base redondeada es 9973.42, la comparación 9974.99 y `var_pct` 0.02

### Requirement: Orden y ranking
`consultar_metrica` SHALL aceptar un criterio de orden (métrica, campo `value`, `var_abs` o `var_pct`, y sentido) y SHALL asignar `rank` con ranking de competición: los empates comparten posición y la siguiente salta (1, 1, 3). Las filas con valor nulo en el criterio SHALL ir al final sin `rank`. Un `limit` (≥ 1) SHALL recortar las filas sin afectar la fila de total.

#### Scenario: Región con mayor caída
- **WHEN** se compara `venta_neta` de Brio por `region` entre `2026-T1` y `2026-T2`, ordenada por `var_pct` ascendente
- **THEN** la fila con `rank = 1` es `Sur` y la de `rank = 5` es `Oriente`

#### Scenario: Límite de filas
- **WHEN** la consulta anterior pide `limit = 1`
- **THEN** devuelve solo la fila `Sur` y la fila de total

#### Scenario: Empate
- **WHEN** dos grupos tienen el mismo valor en el criterio de orden y un tercero es peor
- **THEN** los dos primeros tienen `rank = 1` y el tercero `rank = 3`

### Requirement: Validación de la consulta
`consultar_metrica` SHALL resolver los valores de los filtros con la capa semántica (alias y mayúsculas) y SHALL rechazar con un error estructurado (campo, valor inválido y opciones válidas) una métrica, dimensión, valor de catálogo o período desconocido, o un filtro por `mes`. Los errores de forma (métricas vacías, `limit` menor que 1, período y comparación a la vez, campos desconocidos) SHALL rechazarse al validar el modelo, indicando el campo. Ninguna entrada SHALL aceptar SQL.

#### Scenario: Alias en el filtro
- **WHEN** se consulta con filtro `marca = Brío`
- **THEN** el resultado tiene las mismas filas y el mismo `evidence_id` que con `marca = Brio`

#### Scenario: Métrica desconocida
- **WHEN** se pide la métrica `margen`
- **THEN** se produce un error cuyo campo es `metrics` y cuyas opciones son `venta_neta`, `unidades`, `precio_efectivo` y `registros`

#### Scenario: Valor de catálogo desconocido
- **WHEN** se filtra por `region = Caribe`
- **THEN** se produce un error cuyo campo es `filters.region` y cuyas opciones son las regiones del catálogo

#### Scenario: Dimensión desconocida
- **WHEN** se agrupa por `ciudad`
- **THEN** se produce un error cuyo campo es `group_by` y que lista las dimensiones consultables

#### Scenario: Período y comparación a la vez
- **WHEN** una consulta pide `period = 2026-T1` y una comparación
- **THEN** se produce un error que indica que son excluyentes

#### Scenario: Período inválido
- **WHEN** se pide el período `2026-T5`
- **THEN** se produce un error que indica las formas válidas de período

### Requirement: Datos faltantes
`consultar_metrica` SHALL devolver nulo, nunca 0, el valor de toda métrica (incluida `registros`) de un grupo o corte sin filas en un período, con un aviso que nombre el período y el grupo o corte. Si ningún mes del período tiene filas en `sales`, el aviso SHALL decir que el período no tiene datos en la base; si solo faltan algunos meses, SHALL listarlos y calcular con los disponibles.

#### Scenario: Período sin datos
- **WHEN** se consultan `venta_neta` y `registros` de Brio en `2025-T1`
- **THEN** ambos valores son nulos y los avisos indican que `2025-T1` no tiene datos en la base

#### Scenario: Período con meses parciales
- **WHEN** se consulta `venta_neta` de Brio en `2026`
- **THEN** el valor es 2715963700 y los avisos listan los meses `2026-07` a `2026-12` como sin datos

#### Scenario: Corte vacío
- **WHEN** se consulta `venta_neta` con filtro `punto_venta_id = XX-T-999` en `2026-T1`
- **THEN** el valor es nulo y hay un aviso de corte sin datos en `2026-T1`

### Requirement: Variación no definida
`var_abs` SHALL ser nulo si el valor base o el de comparación es nulo, y `var_pct` SHALL ser nulo si alguno es nulo o la base es 0. En ambos casos SHALL añadirse un aviso de variación no definida que nombre el grupo.

#### Scenario: Comparación contra un período sin datos
- **WHEN** se compara `venta_neta` de Brio entre `2025-T4` y `2026-T1`
- **THEN** la base es nula, `var_abs` y `var_pct` son nulos, y los avisos nombran `2025-T4` y la variación no definida

### Requirement: Avisos de calidad en el resultado
`consultar_metrica` SHALL incluir en `quality_notes` cada incidencia `error` o `aviso` de `dq_issues` cuya fila coincida con los filtros y cuyo `mes` esté en los períodos consultados o no sea un mes válido (`outside_periods = true`), con `registro_id`, regla, tipo, acción, impacto en venta y las dimensiones de la fila. SHALL incluir también `corrections_count`, el número de correcciones del mismo corte.

#### Scenario: Venta faltante en Sur
- **WHEN** se compara `venta_neta` de `marca = Brio` y `region = Sur` entre `2026-T1` y `2026-T2`
- **THEN** `quality_notes` incluye la incidencia DQ07 de `V03997` con `action = excluida`, `mes = 2026-05` y `region = Sur`
- **AND** `corrections_count` es 1 (`V02929`)

#### Scenario: Mes inválido en Centro
- **WHEN** se compara `venta_neta` de `marca = Brio` y `region = Centro` entre `2026-T1` y `2026-T2`
- **THEN** `quality_notes` incluye la incidencia DQ05 de `V03999` con `outside_periods = true`

#### Scenario: Corte sin incidencias
- **WHEN** se consulta `venta_neta` de `marca = Brio` y `region = Oriente` en `2026-T1`
- **THEN** `quality_notes` está vacío

### Requirement: Trazabilidad de los resultados
Cada resultado de `consultar_metrica` y `calidad_datos` SHALL incluir: `evidence_id` (`EV-` y 12 caracteres hexadecimales) derivado de la herramienta, la consulta normalizada (valores resueltos y listas ordenadas), el `ingestion_id` y la huella del `semantic_layer.yaml`; el `ingestion_id`; y la consulta normalizada. `consultar_metrica` SHALL incluir además los meses de cada período, el SQL ejecutado y sus parámetros.

#### Scenario: Consultas equivalentes
- **WHEN** se ejecuta la misma consulta con `Brío` y con `Brio`, o con filtros en distinto orden
- **THEN** ambas tienen el mismo `evidence_id`

#### Scenario: Consultas distintas
- **WHEN** se consultan `2026-T1` y `2026-T2` con los mismos filtros
- **THEN** los `evidence_id` son distintos y cada resultado lista los meses de su período, el SQL y sus parámetros

#### Scenario: Cambio en la capa semántica
- **WHEN** se ejecuta la misma consulta con un `semantic_layer.yaml` cuya descripción de `venta_neta` cambió
- **THEN** el `evidence_id` es distinto

#### Scenario: Evidencia de calidad_datos
- **WHEN** se ejecuta dos veces `calidad_datos` con los mismos filtros
- **THEN** ambas tienen el mismo `evidence_id` con la forma `EV-` y 12 caracteres hexadecimales, y el mismo `ingestion_id`

### Requirement: Acceso de solo lectura
Las herramientas SHALL abrir la base en modo solo lectura, sin acceso a archivos externos ni carga ni instalación de extensiones, con la configuración bloqueada, y SHALL ejecutar únicamente SQL generado por el código con parámetros enlazados. Si la base no existe o no tiene las columnas esperadas, SHALL fallar con un error que indique ejecutar `make ingest`.

#### Scenario: Intento de escritura
- **WHEN** se intenta ejecutar una sentencia de escritura con la conexión de las herramientas
- **THEN** DuckDB la rechaza y la base no cambia

#### Scenario: Acceso externo y configuración
- **WHEN** con esa conexión se intenta `read_csv('/etc/passwd')`, `INSTALL httpfs` o `SET enable_external_access = true`
- **THEN** las tres operaciones son rechazadas

#### Scenario: Base inexistente
- **WHEN** `DUCKDB_PATH` apunta a un archivo que no existe
- **THEN** la herramienta falla con un error que menciona `make ingest`

#### Scenario: Base anterior sin dimensiones en dq_issues
- **WHEN** la base fue cargada antes de este change y `dq_issues` no tiene la columna `marca`
- **THEN** la herramienta falla con un error que menciona `make ingest`

### Requirement: Filtros de calidad de datos
`calidad_datos` SHALL aceptar filtros opcionales por dimensión (resueltos con la capa semántica), período y regla. Un mes inválido SHALL incluirse en cualquier filtro de período con `outside_periods = true`. Las filas de `sales_review` SHALL filtrarse por las dimensiones que `dq_issues` guarda para su `source_line`, no por sus valores crudos.

#### Scenario: Filtro por período
- **WHEN** se consulta `calidad_datos` con `marca = Brio` y el período `2026-T2`
- **THEN** `issues` incluye `V03997` (2026-05) y `V03999` (mes inválido, `outside_periods = true`), y no incluye incidencias de meses de T1

### Requirement: Resultado de calidad de datos
`calidad_datos` SHALL devolver `issue_count` (todas las incidencias del corte, correcciones incluidas), `corrections_count`, el conteo por regla y acción, la venta afectada por acción, `issues` (sin correcciones salvo que se pidan), `review_rows` (filas en revisión del corte) e `ingestion` (`rows_read`, `rows_sales`, `rows_review`, `rows_excluded`, `rows_removed`).

#### Scenario: Sin filtros
- **WHEN** se consulta `calidad_datos` sin filtros
- **THEN** `issue_count` es 11, `corrections_count` es 3, `issues` tiene 8 elementos y `review_rows` 2
- **AND** `ingestion` tiene `rows_read` 4000, `rows_sales` 3995, `rows_review` 2, `rows_excluded` 2 y `rows_removed` 1

#### Scenario: Corte de Brío en Sur
- **WHEN** se consulta `calidad_datos` con `marca = Brío` y `region = Sur`
- **THEN** `issues` incluye la incidencia DQ07 de `V03997` y `corrections_count` es 1

#### Scenario: Filtro por regla
- **WHEN** se consulta `calidad_datos` con la regla `DQ05`
- **THEN** `issues` contiene solo la incidencia de `V03999` y `review_rows` solo `V03999`
