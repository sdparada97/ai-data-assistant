# Exploración de datos

Resultado de la ETAPA 4 sobre las fuentes en `data/raw/` (datos ficticios, versionados). Es la referencia para los escenarios WHEN/THEN de los changes que usan datos. Las cifras salen del script reproducible, no de cálculos manuales.

## Cómo reproducir

```bash
uv sync --all-packages --group explore
uv run --all-packages --group explore python backend/scripts/explore_data.py \
  --raw-dir data/raw --sales-file 02_Ventas_2026.csv --brand Brio \
  --period T1=2026-01,2026-02,2026-03 --period T2=2026-04,2026-05,2026-06 \
  --output-dir data/processed/exploration
```

Genera `data/processed/exploration/report.md` (todas las tablas de este documento) y el texto extraído de cada documento. No modifica `data/raw/`. Dos ejecuciones producen un reporte idéntico.

## Fuentes

| Archivo | Tipo | Contenido |
|---|---|---|
| `01_Contexto_Negocio.md` | Markdown | Situación, diccionario de la base de ventas y convenciones (T1, T2, variación absoluta y porcentual). |
| `02_Ventas_2026.csv` | CSV UTF-8 con BOM | 4.000 filas de ventas mensuales, enero-junio de 2026. |
| `03_Investigacion_Consumidor.pdf` | PDF, 3 páginas | Estudio cualitativo (24 entrevistas en Norte, Centro y Sur). Hallazgos `INV-01`…`INV-05`, límites `INV-LIM-01`…`04`, extractos `ENT-*`. |
| `04_Observaciones_Canales.docx` | Word, 2 tablas | Visitas a puntos de venta abril-junio (51 visitas). Hallazgos por región `OC-*` y registros `CAM-*` con fecha y punto de venta. |
| `05_Reporte_Comercial.pdf` | PDF, 2 páginas | Reporte ejecutivo preliminar con tabla de variación regional y afirmaciones `REP-01`…`REP-06`. |

Las tablas de los PDF se extraen como líneas sueltas (PyMuPDF no detecta tablas); las del Word se leen como tablas.

## Esquema del CSV

| Columna | Tipo (tras limpieza) | Valores / rango |
|---|---|---|
| `registro_id` | texto | `V00001`…`V03999`, consecutivo y sin huecos; 1 repetido. |
| `mes` | texto `AAAA-MM` | `2026-01`…`2026-06` (≈ 666 filas por mes); 1 valor inválido. |
| `marca` | categoría | `Brio` (788), `Senda` (822), `Luma` (805), `Nativa` (798), `Rizo` (786); 1 variante `BRIO`. En los datos, `Brio` representa a Brío. |
| `region` | categoría | Norte, Centro, Sur, Oriente, Occidente (≈ 800 filas cada una). |
| `canal` | categoría | Tradicional (2.000), Moderno (2.000). |
| `punto_venta_id` | texto `RR-C-NNN` | 123 valores: prefijo de región (`NO`, `CE`, `SU`, `OR`, `OC`), letra de canal (`T`, `M`) y número. 120 aparecen de forma regular; 3 solo en filas anómalas. El patrón se deduce de los datos (todas las filas lo cumplen salvo `V02612`), pero ningún documento lo define, así que no se usa en la limpieza. |
| `presentacion` | categoría | Individual (2.498), Familiar (1.502). |
| `unidades` | entero | 1 vacío; resto entre −90 y 833 (mediana 322). |
| `venta_neta_cop` | entero (COP) | 1 `N/D`; resto entre −1.000.000 y 9.338.800 (mediana 3.357.700). |

Observaciones:

- Una misma combinación (mes, marca, región, canal, punto de venta, presentación) puede tener varias filas: 790 filas comparten combinación. El contexto de negocio lo permite, así que **no** se tratan como duplicados.
- El precio efectivo por unidad (venta neta / unidades) es muy estable dentro de cada marca y presentación. Para Brío: Individual ≈ 12.150–12.770 COP y Familiar ≈ 4.800–5.100 COP. **A confirmar con negocio:** que Familiar tenga menor precio por unidad que Individual sugiere que `unidades` no mide lo mismo en ambas presentaciones.

## Inconsistencias y reglas propuestas

Impacto medido sobre la venta neta de Brío. Todas las reglas deben quedar registradas en `dq_issues` (change 2).

| Código | Inconsistencia | Filas | Ejemplo | Regla propuesta | Impacto en Brío |
|---|---|---|---|---|---|
| DQ01 | `registro_id` repetido (idéntico o con diferencias) | 1 | `V01999` (Brio, Norte, 2026-04) aparece dos veces, idéntico | Conservar la primera aparición del `registro_id` y eliminar las demás | Evita sumar 1.142.900 de más en Norte T2 (Norte: −3,06 % → −3,48 %) |
| DQ02 | Fusionada en DQ01 | — | — | — | — |
| DQ03 | Espacios sobrantes en dimensiones | 2 | `V02929` región `"Sur "`; `V02612` canal `"Moderno "` | Recortar espacios | Recupera 1.046.800 en Sur T2 (sin la regla, Sur queda en −30,56 % y aparece una región `"Sur "` aparte) |
| DQ04 | Valor de dimensión fuera del catálogo o con otra escritura | 1 | `V00667` marca `BRIO` | Normalizar contra el catálogo de valores válidos (marca, región, canal, presentación); excluir lo que no esté en el catálogo | Recupera 1.229.300 en Norte T1 |
| DQ05 | Mes inválido | 1 | `V03999` mes `2026-13` (Brio, Centro) | Excluir del análisis por período y reportar | 1.470.000 fuera de T1/T2. Si fuera T1, Centro −9,46 %; si fuera T2, −8,56 %; el ranking no cambia |
| DQ06 | Unidades vacías | 1 | `V03358` (Luma) | Excluir la fila completa y reportar | Ninguno en Brío; Luma pierde 935.000 COP en Norte T2 (total Luma +6,20 % → +6,13 %) |
| DQ07 | Venta neta no numérica | 1 | `V03997` `N/D` (Brio, Sur, 2026-05, 205 unidades) | Excluir la fila completa, **sin imputar**, y reportar | No cuantificable. Escenario de imputación a precio mediano: ≈ 2.516.580, Sur −29,58 % en lugar de −30,27 % |
| DQ08 | Valores negativos | 1 | `V03998` (Luma, −90 u, −1.000.000) | Excluir y reportar: no hay política para devoluciones | Ninguno (no es Brío) |
| DQ09 | Omitida: canal incoherente con el código del punto de venta | 1 | `V02612`: `OC-T-001` aparece 59 veces como Tradicional y aquí como Moderno | Sin regla: se conserva el canal declarado | Ninguno en Brío |
| DQ10 | Omitida: región incoherente con el código | 0 | — | Sin regla | — |
| DQ11 | Punto de venta que solo aparece una vez | 3 | `SU-T-013`, `CE-M-014`, `CE-T-015` (filas `V03997`…`V03999`) | Solo informativo | Coincide con DQ05, DQ07 y DQ08 |
| DQ12 | Precio unitario atípico (> 50 % de la mediana marca/presentación) | 1 | `V03999`: Individual a 4.900 COP/u frente a ≈ 12.300 | Solo informativo | Coincide con DQ05 |

Las cuatro últimas filas del archivo (la copia de `V01999`, `V03997`, `V03998` y `V03999`) son 4 de las 8 filas anómalas.

### Aprobación de reglas

Revisión una a una con el responsable del proyecto.

| Código | Estado | Fecha | Comportamiento acordado |
|---|---|---|---|
| DQ01 | Aprobada (ampliada) | 2026-10-21 | `registro_id` es único. Si se repite, se conserva la primera aparición y se eliminan las demás. Cada eliminación va a `dq_issues` con su venta neta y un tipo: `duplicado_identico` o `duplicado_con_diferencias` (con las columnas y valores que difieren). Las filas con distinto `registro_id` que comparten combinación no son duplicados. |
| DQ02 | Fusionada en DQ01 | 2026-10-21 | Se descartó la cuarentena de todas las versiones. **Pendiente:** valorar más adelante dejar ciertos datos en revisión en lugar de eliminarlos (ver ROADMAP). |
| DQ03 | Aprobada | 2026-10-21 | Recortar espacios al inicio y al final de `registro_id`, `mes`, `marca`, `region`, `canal`, `punto_venta_id` y `presentacion`, sin tocar los intermedios. La fila se conserva; cada valor corregido va a `dq_issues` con columna, valor original y valor corregido. |
| DQ04 | Aprobada (ampliada) | 2026-10-21 | `marca`, `region`, `canal` y `presentacion` se comparan, sin distinguir mayúsculas, contra un catálogo de valores válidos definido en configuración (no en código). Si coincide, se reescribe con la forma del catálogo y se registra la corrección. Si no coincide, la fila se excluye y va a `dq_issues` como `valor_no_valido`. |
| DQ05 | Aprobada | 2026-10-21 | `mes` debe cumplir `AAAA-MM` con mes 01–12 (tras recortar espacios). Si no, la fila se excluye de todas las métricas y va a `dq_issues` como `mes_invalido` con su venta neta. Un mes válido fuera de los períodos consultados no es un error. Candidata a "en revisión" (ver pendiente). |
| DQ06 | Aprobada (revisada) | 2026-10-21 | Si `unidades` está vacío o no es entero, la fila completa se excluye de todas las métricas (no es un registro con calidad de dato) y va a `dq_issues` como `unidades_faltantes` con su venta neta. Sin imputación. |
| DQ07 | Aprobada | 2026-10-21 | Si `venta_neta_cop` está vacía o no es numérica, la fila completa se excluye de todas las métricas, sin imputar, y va a `dq_issues` como `venta_faltante` (venta no cuantificable). Criterio común con DQ06: una fila sin todos sus datos numéricos no entra en ninguna métrica. |
| DQ08 | Aprobada | 2026-10-21 | Si `unidades` o `venta_neta_cop` es negativo, la fila completa se excluye de todas las métricas y va a `dq_issues` como `valor_negativo`. No se interpreta como devolución ni ajuste hasta que negocio defina una política. Los ceros quedan fuera de esta regla. Candidata a "en revisión" (ver pendiente). |
| DQ09 | Omitida | 2026-10-21 | El patrón `RR-C-NNN` del código del punto de venta se deduce de la correlación en los datos, pero ningún documento lo define. No se usa para validar ni corregir. `V02612` queda como Moderno (solo DQ03 recorta su espacio). |
| DQ10 | Omitida | 2026-10-21 | Mismo motivo que DQ09: no se valida la región contra el prefijo del código. |
| DQ11 | Aprobada (opción A, informativa) | 2026-10-21 | Si un `punto_venta_id` aparece una sola vez en el archivo, la fila va a `dq_issues` como `punto_venta_unico` con severidad "aviso" (incluye cuántas veces aparece y la mediana del resto). No excluye ni corrige. |
| DQ12 | Aprobada (opción A, informativa) | 2026-10-21 | En las filas que pasaron DQ01–DQ08, si el precio por unidad (`venta_neta_cop / unidades`) se desvía más de un umbral (50 %, configurable, no en código) de la mediana de su marca y presentación, la fila va a `dq_issues` como `precio_atipico` con severidad "aviso", su precio y la mediana. No excluye. |
| DQ13 | Aprobada (nueva) | 2026-10-21 | Si `unidades` es 0 y `venta_neta_cop` es positiva, la fila va a revisión (`sales_review`) como `venta_sin_unidades`. Venta 0 con unidades positivas, o ambos en 0, no la activan. Sin casos en el archivo actual. |
| — | Decisión | 2026-10-21 | `registro_id` o `punto_venta_id` vacío: sin regla propia; la validación final detiene la carga. |

## Valor de referencia: región con mayor caída de Brío (T2 vs T1)

Fórmula del contexto de negocio: variación % = (venta neta T2 / venta neta T1 − 1) × 100, sobre venta neta en COP con todas las reglas propuestas aplicadas.

| Región | T1 | T2 | Variación absoluta | Variación % |
|---|---:|---:|---:|---:|
| **Sur** | 363.431.600 | 253.404.600 | −110.027.000 | **−30,27** |
| Centro | 314.314.900 | 285.924.400 | −28.390.500 | −9,03 |
| Occidente | 253.170.900 | 239.821.500 | −13.349.400 | −5,27 |
| Norte | 272.236.000 | 262.773.400 | −9.462.600 | −3,48 |
| Oriente | 230.096.600 | 240.789.800 | +10.693.200 | +4,65 |
| **Total Brío** | 1.433.250.000 | 1.282.713.700 | −150.536.300 | −10,50 |

**Respuesta:** Sur, con −30,27 % (363.431.600 → 253.404.600 COP; (253.404.600 / 363.431.600 − 1) × 100).

El ranking es robusto: no cambia sin deduplicar, sin normalizar ni imputando el `N/D`. Solo varían los decimales de Norte y Sur (ver la tabla de sensibilidad en el reporte).

### Otros cortes de Brío

- **Canal:** Moderno −10,59 %, Tradicional −10,43 %. En cada región, ambos canales caen casi igual (Sur: −30,28 % y −30,26 %).
- **Presentación:** Familiar −10,84 %, Individual −10,44 %. En Sur: −30,33 % y −30,26 %.
- **Unidades:** misma variación que la venta neta (Sur −30,29 %). El precio efectivo por unidad no cambió en ninguna región ni presentación (0,0 %).
- **Puntos de venta:** en Sur, los 24 puntos de venta de Brío caen entre −29,70 % y −31,01 %. La caída no se concentra en unos pocos locales.
- **Mensual en Sur:** ≈ 120 M COP/mes en enero-marzo y ≈ 84 M desde abril. Es un escalón, no un deterioro gradual.
- **Otras marcas (total):** Luma +6,13 %, Nativa +3,63 %, Rizo −0,89 %, Senda −0,28 %. Cada una varía casi igual en todas las regiones; en Sur no ganan más que en el resto.

## Documentos y afirmaciones verificables

### 01 Contexto de negocio
Define T1/T2, la fórmula de variación y el diccionario de datos. Verificado contra el CSV: 5 marcas, 5 regiones, 2 canales, 2 presentaciones y enero-junio de 2026. Advierte que no hay política para faltantes ni negativos (de ahí DQ07 y DQ08 sin imputación).

### 03 Investigación de consumidor
Cualitativa, por conveniencia, 24 entrevistas, sin Oriente ni Occidente. Se declara a sí misma no apta para cuantificar ni probar causalidad (`INV-LIM-01`…`04`).

| ID | Afirmación | Contraste con datos |
|---|---|---|
| INV-01 | Sensibilidad al precio en Sur | No verificable como causa. El precio efectivo de Brío en Sur no cambió (0,0 %); no hay precios de competidores. |
| INV-02 | Faltantes percibidos en Sur y Centro | No verificable (no hay inventarios). La caída de Sur es uniforme en todos sus puntos de venta. |
| INV-03 | Preferencia por formatos pequeños en Norte | No se refleja en los datos: la cuota de unidades Individual en Norte es 70,23 % en T1 y 70,20 % en T2 (si Individual es el formato pequeño). |
| INV-04 | Promociones de competidores sin causalidad atribuible | Coherente con los datos: no hay forma de atribuir un porcentaje. |
| INV-05 | La región con mayor caída debe salir de registros comerciales | Los registros dan Sur. |

### 04 Observaciones de canales
51 visitas, sin aleatorización. Tabla de faltantes por región: Sur 5/12, Centro 2/11, Norte 1/10, Oriente 0/9, Occidente 1/9. Hay 10 registros `CAM-*` con punto de venta; todos existen en el CSV.

| ID | Afirmación | Contraste con datos |
|---|---|---|
| OC-SUR-01 | Más faltantes en Sur, sobre todo en tradicional | Sur cae −30 %, pero igual en Moderno que en Tradicional, y los locales con faltante reportado (`SU-T-003`, `SU-T-004`, `SU-T-005`) caen lo mismo que el resto (−30,2 % a −30,4 %). |
| OC-CEN-02 | Promociones de competidores en 4/11 locales; una supervisora sugiere que Centro es la más afectada | La sugerencia contradice los datos: Centro es segunda (−9,03 %). |
| OC-NOR-03 | Disponibilidad estable; interés en formatos pequeños | Norte cae poco (−3,48 %); sin cambio en la mezcla de formatos. |
| OC-ORI-04 | Sin faltantes; exhibición estable | Coherente: Oriente es la única región que crece (+4,65 %). |
| OC-OCC-05 | Dificultad para reponer el formato familiar | Familiar en Occidente −5,58 % frente a Individual −5,22 %: diferencia pequeña. |

### 05 Reporte comercial
Preliminar, elaborado antes de conciliar la base. Pide verificarse contra fuentes primarias.

| Región | Reportado | Datos | ¿Coincide? |
|---|---:|---:|---|
| Centro | −23 % | −9,03 % | **No** |
| Sur | −7 % | −30,27 % | **No** |
| Norte | −4 % | −3,48 % | Aproximado |
| Oriente | +4 % | +4,65 % | Aproximado |
| Occidente | −6 % | −5,27 % | Aproximado |

| ID | Afirmación | Contraste con datos |
|---|---|---|
| Síntesis | Brío se contrae en T2 vs T1 | Sí: −10,50 %. |
| REP-01 | Centro es la región con mayor caída | **Falso**: es Sur. |
| REP-02 | Las promociones de competidores explican ≈ 70 % de la caída | **No sustentado**: sin diseño experimental ni precios promocionales. Los competidores crecen igual en todas las regiones. |
| REP-03 | Alertas de faltantes, sobre todo en Sur | Cualitativo, sin cuantificar. |
| REP-04 | Promociones tácticas en Centro | Basada en REP-01, que es falsa. |
| REP-06 | Revisar presentación, canal y precio efectivo | Hecho aquí: la caída es transversal a canal y presentación, y el precio efectivo no cambió. |

### Estructura de los documentos (verificada para la ingesta)

Estos hechos sustentan la conversión a Markdown y la fragmentación del change `add-document-retrieval` (parámetros en `backend/config/documents.yaml`):

- **IDs de evidencia:** `REP-01`…`REP-06`, `INV-01`…`INV-05`, `INV-LIM-01`…`INV-LIM-04` (y `INV-LIM` suelto en el índice de referencias), `ENT-SUR-03`, `ENT-SUR-07`, `ENT-CEN-04`, `ENT-NOR-02`, `OC-SUR-01`…`OC-OCC-05`, `OC-EXT-06` y 10 `CAM-*`. Los códigos de punto de venta (`OC-T-001`, `SU-T-003`…) no son IDs de evidencia.
- **PDF (03 y 05):** un título por página en 17 pt (el primero es el del documento), secciones numeradas (`N. Título`) en unos 11,2 pt, y la misma cabecera y pie (`ALMENA FOODS / …`, `… · BRÍO`, `Página N`) en cada página.
- **Tablas de PDF:** no tienen líneas; cada fila es un rectángulo de fondo (el encabezado, oscuro) y hay celdas de dos líneas centradas en vertical. `find_tables()` de PyMuPDF no las detecta.
- **Word (04):** `INSUMO DE NEGOCIO` aparece antes del estilo `Title`; secciones con `Heading 1`, registros `OC-*` con `Heading 2`, viñetas con estilo de lista y 2 tablas. La de registros tiene la columna `ID / fecha` (`CAM-101  2026-04-09`, con doble espacio).
- **`OC-EXT-06`:** texto importado de un proveedor con instrucciones dirigidas a "el asistente de IA". Es un dato de prueba: se carga y se devuelve como evidencia, sin efecto en la búsqueda.
- **Markdown (01):** secciones `##`, a veces sin línea en blanco tras el título, y una tabla (diccionario de datos).

## Contradicciones entre fuentes

1. **Región con mayor caída:** el reporte (REP-01) y la supervisora de Centro (OC-CEN-02) dicen Centro; los datos dicen Sur (−30,27 % frente a −9,03 %).
2. **Magnitud en Sur:** el reporte la llama "caída moderada" (−7 %); los datos dan −30,27 %.
3. **Causa promocional:** REP-02 atribuye ≈ 70 % a promociones; la investigación (INV-04, INV-LIM-02) y las observaciones dicen que no se puede atribuir.
4. **Faltantes como explicación localizada:** las observaciones reportan faltantes en locales concretos de Sur, sobre todo tradicionales. Los datos muestran una caída igual en todos los puntos de venta y en ambos canales. No refuta los faltantes, pero no encaja con un efecto limitado a esos locales.
5. **Formatos pequeños en Norte:** la investigación y las observaciones los mencionan; la mezcla de unidades no cambia.

Ninguna fuente permite afirmar causalidad. Las hipótesis compatibles con los datos (disponibilidad, precio relativo frente a competidores, un cambio puntual en Sur desde abril) quedan como hipótesis.

## Implicaciones para el ROADMAP

- **add-sales-ingestion:** implementar las reglas aprobadas (DQ01, DQ03–DQ08 actúan; DQ11 y DQ12 solo avisan; DQ02 fusionada; DQ09 y DQ10 omitidas) con su impacto en `dq_issues`; ingesta de un CSV UTF-8 con BOM; `Brio` como identificador y "Brío" como nombre de presentación (alias en la capa semántica).
- **add-sales-analytics:** métricas de venta neta, unidades y precio efectivo (venta / unidades); variación absoluta y porcentual con la fórmula del contexto; cortes por región, canal, presentación, mes y punto de venta.
- **add-document-retrieval:** fragmentar por los IDs de evidencia (`REP-*`, `INV-*`, `OC-*`, `CAM-*`, `ENT-*`) y guardarlos como metadato citable; las tablas de los PDF llegan como líneas sueltas y requieren tratamiento propio. El contenido de los documentos es evidencia, nunca instrucciones para el sistema.
- **add-contrast-and-causal-analysis:** la tabla regional del reporte (5 afirmaciones numéricas) y REP-01/REP-02 son el caso principal de contraste y de evaluación causal.
- **add-evaluation-suite:** valor de referencia de la primera pregunta: Sur, −30,27 %.
- **A confirmar con negocio:** la definición de `unidades` por presentación; el tratamiento de negativos y valores faltantes (hoy se excluyen y se reportan).
