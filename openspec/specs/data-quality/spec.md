# data-quality Specification

## Purpose

Define las reglas de calidad que la ingesta aplica a las ventas (DQ01, DQ03–DQ08, DQ11, DQ12 y DQ13, aprobadas en `docs/EXPLORACION_DATOS.md`), a qué destino envía cada fila y cómo deja constancia de cada actuación, para que toda inconsistencia sea explícita y verificable.

## Requirements

### Requirement: Estructura de las incidencias
Cada actuación de una regla SHALL producir una fila en `dq_issues` con `issue_id`, `registro_id`, `source_line`, `rule_code`, `issue_type`, `severity` (`correccion`, `error` o `aviso`), `column_name`, `original_value`, `new_value`, `action`, `affected_net_sales_cop`, `details` (JSON con datos propios de la regla) e `ingestion_id`. `column_name`, `original_value`, `new_value` y `details` pueden ser nulos.

#### Scenario: Columnas de dq_issues
- **WHEN** se consulta el esquema de `dq_issues` tras una carga
- **THEN** contiene exactamente esas columnas y `details` es un JSON válido o nulo en todas las filas

### Requirement: Acción e impacto de cada incidencia
`action` SHALL ser `corregida` en las incidencias de severidad `correccion`, `ninguna` en las de severidad `aviso` y, en las de severidad `error`, el destino final de la fila (`eliminada`, `excluida` o `en_revision`). `affected_net_sales_cop` SHALL ser la venta neta registrada en la fila si es un entero (también si es negativo) y nulo si no lo es.

#### Scenario: Acción según el destino final
- **WHEN** una fila tiene `mes = 2026-13` y `venta_neta_cop = N/D`
- **THEN** sus incidencias DQ05 y DQ07 tienen `action = excluida` y `affected_net_sales_cop` nulo

#### Scenario: Impacto de un valor negativo
- **WHEN** se carga el archivo real
- **THEN** la incidencia DQ08 de `V03998` tiene `affected_net_sales_cop = -1000000`

### Requirement: Incidencias del archivo real
Con el archivo `data/raw/02_Ventas_2026.csv` y la configuración del repositorio, la ingesta SHALL producir exactamente el reparto de incidencias documentado en `docs/EXPLORACION_DATOS.md`.

#### Scenario: Reparto por regla
- **WHEN** se carga `data/raw/02_Ventas_2026.csv`
- **THEN** `dq_issues` contiene 11 filas: 1 de DQ01, 2 de DQ03, 1 de DQ04, 1 de DQ05, 1 de DQ06, 1 de DQ07, 1 de DQ08 y 3 de DQ11
- **AND** no contiene filas de DQ12

### Requirement: Destino único por fila
Cada fila SHALL terminar en un solo destino. Si cumple varias reglas, SHALL registrarse una incidencia por cada una y el destino SHALL decidirse con esta precedencia: eliminada (DQ01) sobre excluida (DQ06, DQ07) sobre en revisión (DQ04 fuera de catálogo, DQ05, DQ08, DQ13) sobre `sales`.

#### Scenario: Fila con mes inválido y venta faltante
- **WHEN** una fila tiene `mes = 2026-13` y `venta_neta_cop = N/D`
- **THEN** la fila queda excluida y no aparece en `sales` ni en `sales_review`
- **AND** `dq_issues` tiene una incidencia DQ05 y una DQ07 para su `source_line`

### Requirement: Filas en revisión
`sales_review` SHALL guardar cada fila retenida tal como llegó en el CSV (sus 9 columnas como texto, sin recortar), con `source_line`, `rule_codes` (códigos de las reglas que la retuvieron, en orden y separados por comas), `reason` (motivo legible), `status = en_revision` e `ingestion_id`. Sus filas SHALL NOT aparecer en `sales`.

#### Scenario: Filas retenidas del archivo real
- **WHEN** se carga el archivo real
- **THEN** `sales_review` contiene exactamente `V03999` con `rule_codes = DQ05` y `V03998` con `rule_codes = DQ08`
- **AND** `V03999` conserva `mes = 2026-13` y `V03998` conserva `unidades = -90`

#### Scenario: Varias reglas de revisión
- **WHEN** una fila tiene `region = Caribe` y `unidades = -5`
- **THEN** su fila en `sales_review` tiene `rule_codes = DQ04,DQ08`

### Requirement: DQ01 registro_id único
Si un `registro_id` (ya recortado por DQ03) aparece más de una vez, la ingesta SHALL conservar la primera aparición por `source_line`, sea cual sea su destino, y eliminar las demás. Cada eliminación SHALL registrarse por fila con severidad `error`, `issue_type` `duplicado_identico` o `duplicado_con_diferencias` y, en `details`, la línea conservada y las columnas que difieren con sus dos valores.

#### Scenario: Duplicado idéntico del archivo real
- **WHEN** se carga el archivo real, donde `V01999` aparece en las líneas 2000 y 3998
- **THEN** `sales` contiene una sola fila `V01999`, con `source_line = 2000`
- **AND** `dq_issues` registra la línea 3998 con `duplicado_identico`, `action = eliminada`, `affected_net_sales_cop = 1142900` y `details` con la línea conservada 2000

#### Scenario: Duplicado con diferencias
- **WHEN** un CSV contiene `V00001` en la línea 2 con 250 unidades y en la línea 3 con 260 unidades
- **THEN** `sales` conserva la fila de la línea 2
- **AND** `dq_issues` registra la línea 3 con `duplicado_con_diferencias` y `details` con `unidades` 250 frente a 260

#### Scenario: Primera aparición no válida
- **WHEN** la primera aparición de un `registro_id` tiene `mes = 2026-13` y la segunda es válida
- **THEN** la primera va a `sales_review`, la segunda se elimina y el `registro_id` no aparece en `sales`

### Requirement: DQ03 recorte de espacios
La ingesta SHALL quitar los espacios al inicio y al final de `registro_id`, `mes`, `marca`, `region`, `canal`, `punto_venta_id` y `presentacion` antes de las demás reglas, sin tocar los intermedios. La fila SHALL conservarse. Cada valor recortado SHALL registrarse por columna con severidad `correccion` e `issue_type = espacios_sobrantes`.

#### Scenario: Región con espacio del archivo real
- **WHEN** se carga el archivo real, donde `V02929` tiene `region = "Sur "`
- **THEN** `V02929` está en `sales` con `region = Sur`
- **AND** `dq_issues` registra DQ03 en `region` con valor original `"Sur "`, nuevo `"Sur"` y `action = corregida`

#### Scenario: Canal con espacio del archivo real
- **WHEN** se carga el archivo real, donde `V02612` tiene `canal = "Moderno "`
- **THEN** `V02612` está en `sales` con `canal = Moderno`

#### Scenario: Espacios intermedios intactos
- **WHEN** una fila tiene `punto_venta_id = " NO T 001 "`
- **THEN** el valor queda como `"NO T 001"`

### Requirement: DQ04 catálogo de valores válidos
`marca`, `region`, `canal` y `presentacion` SHALL compararse, sin distinguir mayúsculas, contra el catálogo de `semantic_layer.yaml`, sin valores escritos en el código. Si coincide con otra escritura, SHALL reescribirse con la del catálogo (severidad `correccion`, `issue_type = escritura_no_canonica`). Si no está en el catálogo, la fila SHALL ir a revisión (severidad `error`, `issue_type = valor_no_valido`). El registro es por columna.

#### Scenario: Marca en mayúsculas del archivo real
- **WHEN** se carga el archivo real, donde `V00667` tiene `marca = BRIO`
- **THEN** `V00667` está en `sales` con `marca = Brio`
- **AND** `dq_issues` registra DQ04 en `marca` con valor original `BRIO`, nuevo `Brio` y `action = corregida`

#### Scenario: Valor fuera del catálogo
- **WHEN** una fila tiene `region = Caribe`
- **THEN** la fila está en `sales_review` con `rule_codes = DQ04`
- **AND** `dq_issues` registra `valor_no_valido` en `region` con `action = en_revision`

#### Scenario: Catálogo leído de configuración
- **WHEN** se añade `Caribe` a las regiones válidas de un `semantic_layer.yaml` de prueba y se carga la misma fila
- **THEN** la fila está en `sales` con `region = Caribe`

### Requirement: DQ05 mes inválido
`mes` SHALL cumplir `AAAA-MM` con mes entre 01 y 12. Si no lo cumple, la fila SHALL ir a revisión con un registro por fila de severidad `error` e `issue_type = mes_invalido`. Un mes válido fuera de cualquier período de análisis SHALL NOT considerarse inválido.

#### Scenario: Mes 13 del archivo real
- **WHEN** se carga el archivo real, donde `V03999` tiene `mes = 2026-13`
- **THEN** `V03999` está en `sales_review` con un `reason` que contiene `2026-13`
- **AND** `dq_issues` registra DQ05 con `action = en_revision` y `affected_net_sales_cop = 1470000`

#### Scenario: Mes válido fuera del semestre
- **WHEN** una fila tiene `mes = 2025-12`
- **THEN** la fila está en `sales`

### Requirement: DQ06 unidades faltantes
Si `unidades` está vacío o no cumple el patrón entero `^-?\d+$`, la fila SHALL excluirse de `sales` y de `sales_review`, con un registro por fila de severidad `error`, `issue_type = unidades_faltantes` y `column_name = unidades`. No SHALL imputarse ningún valor.

#### Scenario: Unidades vacías del archivo real
- **WHEN** se carga el archivo real, donde `V03358` tiene `unidades` vacío y `venta_neta_cop = 935000`
- **THEN** `V03358` no está en `sales` ni en `sales_review`
- **AND** `dq_issues` registra DQ06 con `action = excluida` y `affected_net_sales_cop = 935000`

#### Scenario: Unidades no enteras
- **WHEN** una fila tiene `unidades = 12.5`
- **THEN** la fila queda excluida con una incidencia DQ06

### Requirement: DQ07 venta neta faltante
Si `venta_neta_cop` está vacía o no cumple el patrón entero `^-?\d+$`, la fila SHALL excluirse de `sales` y de `sales_review`, con un registro por fila de severidad `error`, `issue_type = venta_faltante` y `column_name = venta_neta_cop`. No SHALL imputarse ningún valor.

#### Scenario: Venta N/D del archivo real
- **WHEN** se carga el archivo real, donde `V03997` tiene `venta_neta_cop = N/D`
- **THEN** `V03997` no está en `sales` ni en `sales_review`
- **AND** `dq_issues` registra DQ07 con `original_value = N/D`, `action = excluida` y `affected_net_sales_cop` nulo

### Requirement: DQ08 valores negativos
Si `unidades` o `venta_neta_cop` es un entero negativo, la fila SHALL ir a revisión con un único registro por fila de severidad `error`, `issue_type = valor_negativo` y, en `details`, las columnas negativas. No SHALL interpretarse como devolución ni ajuste. Los valores en 0 SHALL NOT activar esta regla.

#### Scenario: Negativos del archivo real
- **WHEN** se carga el archivo real, donde `V03998` tiene `unidades = -90` y `venta_neta_cop = -1000000`
- **THEN** `V03998` está en `sales_review` con `rule_codes = DQ08`
- **AND** `dq_issues` tiene una sola incidencia DQ08 para `V03998`, con `details` que lista `unidades` y `venta_neta_cop`

#### Scenario: Cero no es negativo
- **WHEN** una fila tiene `unidades = 0` y `venta_neta_cop = 0`
- **THEN** la fila está en `sales` y no hay incidencia DQ08

### Requirement: DQ13 venta sin unidades
Si `unidades` es 0 y `venta_neta_cop` es un entero mayor que 0, la fila SHALL ir a revisión con un registro por fila de severidad `error`, `issue_type = venta_sin_unidades` y `column_name = unidades`. Una venta en 0 con unidades positivas, o ambos valores en 0, SHALL NOT activar esta regla.

#### Scenario: Venta positiva con cero unidades
- **WHEN** una fila tiene `unidades = 0` y `venta_neta_cop = 1200000`
- **THEN** la fila está en `sales_review` con `rule_codes = DQ13`
- **AND** `dq_issues` registra DQ13 con `action = en_revision` y `affected_net_sales_cop = 1200000`

#### Scenario: Venta cero con unidades
- **WHEN** una fila tiene `unidades = 5` y `venta_neta_cop = 0`
- **THEN** la fila está en `sales` y no hay incidencia DQ13

#### Scenario: Sin casos en el archivo real
- **WHEN** se carga el archivo real
- **THEN** `dq_issues` no contiene incidencias DQ13

### Requirement: DQ11 aviso de punto de venta único
Si un `punto_venta_id` (recortado) aparece una sola vez entre todas las filas del CSV, la ingesta SHALL registrar por fila un `aviso` con `issue_type = punto_venta_unico`, `column_name = punto_venta_id` y, en `details`, las apariciones y la mediana de apariciones de los demás puntos de venta, sin cambiar el destino de la fila.

#### Scenario: Puntos de venta únicos del archivo real
- **WHEN** se carga el archivo real
- **THEN** `dq_issues` tiene avisos DQ11 para `SU-T-013`, `CE-M-014` y `CE-T-015`, con `action = ninguna`
- **AND** cada uno tiene en `details` 1 aparición y una mediana de 30

### Requirement: DQ12 aviso de precio atípico
Sobre las filas destinadas a `sales` con `unidades > 0`, la ingesta SHALL calcular el precio por unidad y su desviación `|precio / mediana − 1|`, con la mediana de las mismas filas por marca y presentación. Si la desviación supera el umbral de `data_quality.yaml`, SHALL registrar un `aviso` (`issue_type = precio_atipico`, con precio, mediana y desviación en `details`) sin cambiar el destino. Las filas con 0 unidades no se evalúan.

#### Scenario: Sin precios atípicos en el archivo real
- **WHEN** se carga el archivo real con el umbral configurado en 0.5
- **THEN** `dq_issues` no contiene incidencias DQ12

#### Scenario: Error de escala
- **WHEN** un CSV contiene tres filas de Brio Individual a unos 12.300 COP por unidad y una cuarta con 310 unidades y `venta_neta_cop = 3810`, con el umbral en 0.5
- **THEN** la cuarta fila está en `sales`
- **AND** `dq_issues` registra para ella un aviso DQ12 con precio, mediana y desviación en `details`

#### Scenario: Umbral leído de configuración
- **WHEN** se carga el CSV del escenario anterior con el umbral configurado en 1.0
- **THEN** no se registra ningún aviso DQ12
