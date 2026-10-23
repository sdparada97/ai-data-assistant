# Spec Delta

## Purpose

Evalúa una afirmación causal sobre la variación de una métrica con cinco criterios fijos, calculados en código sobre los datos o extraídos y validados de los documentos, y da un veredicto que nunca afirma causalidad: contradicha, no sustentada o compatible (hipótesis).

## ADDED Requirements

### Requirement: Evaluación de una afirmación causal
La herramienta `evaluar_causalidad` SHALL recibir la causa en texto, su tipo (`competencia`, `disponibilidad` o `metrica_propia`), el efecto (métrica, filtros y comparación de períodos), la dimensión donde localizar el efecto y, opcionalmente, el segmento donde la afirmación localiza el efecto. Con `metrica_propia` SHALL recibir además la métrica de la causa y el sentido esperado de su cambio (`sube` o `baja`). Los valores SHALL validarse contra el catálogo como en `consultar_metrica`.

#### Scenario: Entrada válida
- **WHEN** se evalúa "promociones de la competencia" de tipo `competencia` sobre `venta_neta` de la marca Brío, `2026-T1` frente a `2026-T2`, localizando por `region`
- **THEN** la evaluación se ejecuta y el grupo de comparación es Luma, Nativa, Rizo y Senda

#### Scenario: Dimensión fuera del catálogo
- **WHEN** se pide localizar por `ciudad`
- **THEN** la herramienta devuelve un error que nombra `ciudad` y las dimensiones por las que se puede localizar

#### Scenario: Métrica propia incompleta
- **WHEN** se evalúa una causa de tipo `metrica_propia` sin métrica de la causa o sin sentido esperado
- **THEN** la herramienta devuelve un error que nombra el campo que falta

### Requirement: Dimensiones de la evaluación
La dimensión de localización SHALL tener valores en el catálogo o estar en las dimensiones abiertas de `agent.yaml`, y SHALL ser distinta de las dimensiones filtradas y de la dimensión temporal del catálogo. El segmento afirmado SHALL ser un valor de esa dimensión. Con `competencia`, el efecto SHALL filtrar exactamente una dimensión con un valor; el grupo de comparación son los demás valores de esa dimensión.

#### Scenario: Localizar por la dimensión filtrada
- **WHEN** se localiza por `marca` con el filtro `marca = Brío`
- **THEN** la herramienta devuelve un error que explica que la dimensión de localización no puede estar filtrada

#### Scenario: Competencia sin grupo de comparación
- **WHEN** se evalúa una causa de tipo `competencia` sin filtro de marca
- **THEN** la herramienta devuelve un error que explica que hace falta filtrar un valor para comparar con los demás

#### Scenario: Segmento afirmado inválido
- **WHEN** el segmento afirmado es `Atlántico` localizando por `region`
- **THEN** la herramienta devuelve un error que nombra `Atlántico` y las regiones válidas

### Requirement: Observaciones de la causa en los documentos
Dónde, cuándo y con qué diseño se observó la causa SHALL extraerse con una llamada al LLM con salida estructurada sobre los fragmentos que devuelve una búsqueda de la causa (los primeros `causal.search_top_k` de `agent.yaml`), delimitados como evidencia. Cada observación es un segmento con fecha opcional, una atribución o una limitación, con una cita del fragmento.

#### Scenario: Promociones con la búsqueda real
- **WHEN** se busca "promociones de la competencia" en la base de documentos de prueba
- **THEN** entre las observaciones válidas está Centro (`OC-CEN-02`) y no hay ninguna de Sur

#### Scenario: Declaraciones de diseño
- **WHEN** se evalúa "promociones de la competencia"
- **THEN** entre las observaciones válidas están la atribución del 70 % de `REP-02` y la limitación de `INV-04`

### Requirement: Validación de las observaciones
Cada observación SHALL validarse en código y descartarse, con su motivo, si su cita no aparece literal (sin tildes ni mayúsculas) en el fragmento; si en un segmento el valor de la dimensión no está en el catálogo o no aparece en la misma línea que la cita ni en la sección del fragmento; o si su fecha no es una fecha real con el formato `AAAA-MM-DD` o no aparece literal en el fragmento.

#### Scenario: Observación de Sur con fecha
- **WHEN** la extracción devuelve Sur con fecha `2026-04-18` y la cita `descuento visible` del fragmento de `CAM-103`
- **THEN** la observación es válida

#### Scenario: Segmento de otra línea
- **WHEN** la extracción atribuye a Sur una cita que en `04_Observaciones_Canales:002` está en la línea de Centro
- **THEN** la observación se descarta porque `Sur` no está en la línea de la cita

#### Scenario: Fecha que no está en el fragmento
- **WHEN** la extracción devuelve para `OC-CEN-02` la fecha `2026-05-01`, que no aparece en el fragmento
- **THEN** la observación se descarta

#### Scenario: Fecha en texto libre
- **WHEN** la extracción devuelve para `CAM-103` la fecha `ID / fecha: CAM-103`, que sí aparece en el fragmento
- **THEN** la observación se descarta porque la fecha no tiene el formato `AAAA-MM-DD`

### Requirement: Segmento más afectado
El código SHALL calcular la variación de la métrica por la dimensión de localización y tomar como segmento más afectado el de mayor variación en la dirección del efecto: la más negativa si el total cae, la más positiva si crece (en empate, el primero por orden alfabético). Si la variación total es nula o cero, SHALL devolver un error (no hay efecto que evaluar) antes de buscar observaciones y de llamar al LLM de extracción.

#### Scenario: Caída de Brío
- **WHEN** se evalúa la caída de Brío entre `2026-T1` y `2026-T2` por región
- **THEN** el total es −10.50 y el segmento más afectado es Sur, con −30.27

#### Scenario: Sin efecto que evaluar
- **WHEN** se evalúa la marca Brío comparando `2026-T1` con `2026-T1`
- **THEN** la herramienta devuelve el error "no hay efecto que evaluar" sin llamar al LLM de extracción

### Requirement: Criterio de localización
El código SHALL dar como resultado "encaja" si algún segmento donde se observó la causa es el más afectado o varía al menos `causal.locate_margin_pp` más que el total en la dirección del efecto; "no encaja" si hay observaciones y ninguna cumple lo anterior; "sin observaciones" si no hay ninguna.

#### Scenario: Promociones solo en Centro
- **WHEN** la causa solo se observó en Centro (−9.03, con un total de −10.50)
- **THEN** la localización es "no encaja"

#### Scenario: Observación en Sur
- **WHEN** la causa se observó en Sur
- **THEN** la localización es "encaja"

### Requirement: Criterio del grupo de comparación
Con el tipo `competencia`, el código SHALL comparar la variación de cada valor del grupo en el segmento más afectado con su variación total. Resultado: "efecto diferencial" si alguno varía en ese segmento al menos `causal.differential_pp` (1 pp) más que su total en sentido contrario al efecto; si no, "sin efecto diferencial". Con los otros tipos, el resultado es "no aplica".

#### Scenario: Competidores en Sur
- **WHEN** se evalúa la caída de Brío con Sur como segmento más afectado
- **THEN** el resultado es "sin efecto diferencial": Luma +6.22 en Sur y +6.13 en total, Nativa +3.71 y +3.63, Rizo −0.78 y −0.89, Senda −0.42 y −0.28

### Requirement: Criterio de temporalidad
El código SHALL obtener la serie mensual de la métrica en el segmento más afectado con una consulta por período (base y objetivo), omitiendo los meses sin datos, y localizar el mayor cambio entre meses consecutivos en la dirección del efecto. Resultado: "cambio concentrado en <mes posterior>" si ese cambio supone al menos `causal.step_share` de la diferencia entre las medias de los dos períodos; si no, "cambio gradual". Las fechas de las observaciones del segmento se informan junto al resultado.

#### Scenario: Escalón en Sur
- **WHEN** se evalúa la caída de Brío en Sur entre `2026-T1` y `2026-T2`
- **THEN** el resultado es "cambio concentrado en 2026-04", con un cambio de marzo a abril de 0.965 veces la diferencia de medias

### Requirement: Criterio de explicaciones alternativas
El código SHALL medir, en el segmento más afectado, la amplitud de la variación (máximo − mínimo, sin valores nulos) entre los valores de cada dimensión con valores del catálogo que no sea de localización, filtrada ni temporal, y de las dimensiones abiertas de `agent.yaml`. Es "uniforme" si no supera `causal.uniform_spread_pp`. Con `metrica_propia`, SHALL comprobar si la métrica de la causa cambió más que `causal.cause_change_pct` en ese segmento.

#### Scenario: Caída uniforme en Sur
- **WHEN** se evalúa la caída de Brío en Sur
- **THEN** el resultado informa caída uniforme por canal (Moderno −30.26, Tradicional −30.28), por presentación (Familiar −30.33, Individual −30.26) y por punto de venta (24 puntos entre −31.01 y −29.70)

#### Scenario: Precio propio sin cambio
- **WHEN** se evalúa "subida del precio de Brío" de tipo `metrica_propia` con `precio_efectivo` y sentido `sube`
- **THEN** el resultado informa que el precio efectivo de Brío en Sur varió +0.02, sin cambio frente al umbral

### Requirement: Criterio de diseño de la evidencia
El código SHALL resumir las atribuciones y limitaciones válidas. Resultado: "sin diseño que permita atribuir" si hay alguna limitación o ninguna atribución declara diseño; si no, "con diseño declarado".

#### Scenario: Promociones sin diseño
- **WHEN** se evalúa "promociones de la competencia"
- **THEN** el resultado es "sin diseño que permita atribuir", con `REP-02` e `INV-04` como evidencias

### Requirement: Veredicto por tipo de causa
El veredicto SHALL calcularse en código según el tipo:
- `competencia`: "compatible (hipótesis)" si la localización encaja y hay efecto diferencial;
- `disponibilidad`: "compatible (hipótesis)" si la localización encaja;
- `metrica_propia`: ver «Veredicto de una métrica propia».

En los demás casos, "no sustentada". Nunca SHALL existir un veredicto de causa demostrada.

#### Scenario: Promociones de la competencia
- **WHEN** se evalúa "promociones de la competencia" de tipo `competencia` con las observaciones de la base de prueba (solo Centro)
- **THEN** el veredicto es "no sustentada"

#### Scenario: Promociones observadas también en Sur
- **WHEN** se evalúa la misma causa con observaciones válidas en Centro y en Sur
- **THEN** el veredicto sigue siendo "no sustentada": la localización encaja por Sur, pero no hay efecto diferencial

#### Scenario: Precio relativo frente a competidores
- **WHEN** se evalúa "precios de la competencia más bajos" de tipo `competencia`
- **THEN** el veredicto es "no sustentada"

#### Scenario: Faltantes en Sur
- **WHEN** se evalúa "faltantes de producto" de tipo `disponibilidad`, observados en Sur
- **THEN** el veredicto es "compatible (hipótesis)"

### Requirement: Veredicto de una métrica propia
Con el tipo `metrica_propia`, el veredicto SHALL ser "contradicha" si la métrica de la causa no cambió en el segmento más afectado o cambió en sentido contrario al esperado, y "compatible (hipótesis)" si cambió en el sentido esperado y la localización encaja; si no, o si no hay datos de la métrica de la causa, "no sustentada".

#### Scenario: Subida del precio propio
- **WHEN** se evalúa "subida del precio de Brío" de tipo `metrica_propia` con `precio_efectivo` y sentido `sube`
- **THEN** el veredicto es "contradicha"

#### Scenario: Métrica propia en sentido contrario
- **WHEN** se evalúa una causa de prueba de tipo `metrica_propia` con `unidades` y sentido `sube`, observada en Sur
- **THEN** el veredicto es "contradicha", porque las unidades de Brío en Sur bajaron (−30.29)

#### Scenario: Métrica de la causa sin datos
- **WHEN** la variación de la métrica de la causa en el segmento más afectado no se puede calcular
- **THEN** el veredicto es "no sustentada", no "contradicha"

### Requirement: Veredicto con el efecto localizado por la afirmación
Si la afirmación localiza el efecto en un segmento, el veredicto SHALL ser "contradicha", en cualquier tipo de causa y por encima de los demás veredictos, cuando ese segmento no es el más afectado ni varía al menos `causal.locate_margin_pp` más que el total en la dirección del efecto.

#### Scenario: Efecto localizado en Centro
- **WHEN** se evalúa "promociones de la competencia en Centro" con el segmento afirmado Centro
- **THEN** el veredicto es "contradicha"

### Requirement: Resultado causal trazable
El resultado SHALL incluir la causa y su tipo, cada criterio con su resultado, sus valores y los `evidence_id` de las consultas o los IDs de fragmentos en que se apoya, las observaciones descartadas con su motivo y el veredicto. Su `evidence_id` SHALL derivarse de la entrada, de los umbrales, de `search_top_k`, del modo de búsqueda, de las observaciones validadas y de los `evidence_id` de las consultas.

#### Scenario: Criterios con su evidencia
- **WHEN** se evalúa "promociones de la competencia"
- **THEN** cada uno de los cinco criterios trae su resultado y al menos un `evidence_id` o ID de fragmento, salvo los que no aplican
