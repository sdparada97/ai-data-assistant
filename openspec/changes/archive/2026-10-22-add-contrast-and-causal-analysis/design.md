# Design

## Context

Ver `proposal.md` (Why). Estado actual:

- **Agente (D8, D9):** plan con `bind_tools` y tres herramientas (`agent/tools.py`), `ToolNode`, una corrección, síntesis estructurada y verificación por afirmación (`agent/verify.py`).
  - `ToolContext` no tiene LLM.
  - Las evidencias se construyen desde los artifacts (`agent/evidence.py`), con título generado en código, y sus cifras se extraen recorriendo todo el resultado (`figures`).
  - `execute` acumula `runs` y `artifacts` y los devuelve al final, así que una excepción a mitad de ronda los pierde.
  - El máximo por herramienta (`max_calls_per_tool`, 5) cuenta solo consultas correctas.
- **Funciones reutilizables:**
  - `consultar_metrica` admite `compare`, `group_by`, filtros y `sort` por `var_pct`; `period` acepta una sola expresión;
  - `doc_chunks` da los fragmentos de un documento con sección y página, y `documents` da su `sha256`;
  - `figures_in` extrae cifras sin signo;
  - `analytics/evidence.py::evidence_id` genera ids `EV-` + 12 hex.
- **Datos reales que fijan los escenarios** (`consultar_metrica` sobre `data/processed`; recalculados por el revisor):
  - Brío por región: Centro −9.03, Norte −3.48, Occidente −5.27, Oriente +4.65, Sur −30.27; total −10.50;
  - competidores en Sur frente a su total: Luma 6.22/6.13, Nativa 3.71/3.63, Rizo −0.78/−0.89, Senda −0.42/−0.28;
  - Brío en Sur: canal −30.26/−30.28; presentación −30.33/−30.26; 24 puntos de venta de −31.01 a −29.70; precio efectivo +0.02;
  - serie de Sur: 120.59/123.54/119.31/83.93/85.83/83.64 M, con un escalón marzo→abril de 0.965 × la diferencia de medias.
- **Documentos:**
  - 12, 21 y 18 fragmentos (reporte, observaciones e investigación); cada documento cabe en un prompt;
  - `OC-CEN-02` tiene la región en su sección (`OC-CEN-02 | Centro`);
  - `CAM-103` registra en Sur, el 2026-04-18, "Exhibición de competidor con descuento visible";
  - la búsqueda real "promociones de la competencia" (top 8) devuelve INV-04, REP-02, OC-CEN-02, REP-04, `05:002`, REP-06, `03:006` y ENT-CEN-04; CAM-103 no sale ni en el top 20;
  - la de "faltantes de producto" (top 8) trae REP-03, OC-SUR-01, `03:006` e INV-02, todos con Sur.

## Goals / Non-Goals

**Goals:**
- Respuestas de contraste y causalidad completas e iguales con la misma extracción, con diferencias y veredictos calculados en código, coherentes con `docs/EXPLORACION_DATOS.md`.
- La síntesis recibe tablas ya comparadas, no decenas de filas y fragmentos.

**Non-Goals:**
- Inferencia estadística, métricas nuevas, contrastar varios documentos en una pregunta (con el máximo de 1, el segundo se descarta).

## Decisions

### D10a: dos herramientas del plan con una extracción dentro
- **Herramientas:** `contrastar_afirmaciones(doc_id)` y `evaluar_causalidad(cause, cause_kind, metric, filters, compare, locate_by, cause_metric?, claimed_segment?)` se añaden a `build_tools`, con `content_and_artifact` y entradas tolerantes.
- **Extracción:** `ToolContext.extractor` envuelve `LLMClient.structured`. Cuenta en `llm_calls`, comparte el límite de peticiones y usa el razonamiento de la síntesis (D9g).
- **Fallo del proveedor:** `execute` ejecuta `ToolNode` una llamada cada vez y captura `ProviderError`. Devuelve los `runs` y `artifacts` ya obtenidos con `status: error` y el código, y registra las llamadas posteriores como descartadas; la arista va a `respond` (requisito "Consultas conservadas ante un fallo en una herramienta").
- **Salida no interpretable:** se convierte en `QueryError(field="extraccion", message="La extracción de <herramienta> no devolvió elementos interpretables")`, sin texto de documentos ni la salida del LLM; nombrar la herramienta permite a la corrección saber cuál falló.
- **Errores internos:** la validación de los elementos extraídos usa sus propios tipos, no `ValidationError`, para que `format_tool_error` no lo presente como argumentos del plan.
- **Máximos propios:** `limits.max_calls_by_tool` (`contrastar_afirmaciones: 1`, `evaluar_causalidad: 1`; 1 si faltan y claves validadas contra los nombres de las herramientas) cuenta las ejecuciones que llegaron a llamar al LLM de extracción, correctas o fallidas. Una rechazada antes (doc inexistente, dimensión inválida) no cuenta, para que la corrección pueda arreglarla. Se modifica «Consultas fallidas sin resolver» con esa excepción. Peor caso por pregunta: plan + 2 extracciones + corrección + 2 síntesis = 6 llamadas.
- **Cambio respecto a D8:** el texto de los documentos ahora decide qué consultas se ejecutan, aunque siempre a través de elementos validados en código. El plan sigue sin leer documentos.
- *Descartadas:*
  - un nodo de extracción con enrutador de intención: rechazado por el responsable;
  - que el plan pase las afirmaciones: el plan no lee documentos;
  - que la corrección pueda repetir la extracción: duplicaría llamadas.

### D10b: lógica pura en `analytics/`, extracción en `agent/`
- **`agent/extraction.py`:** esquemas de extracción (`ExtractedClaim`, `ExtractedObservation`), prompts y validación literal (signo, línea, sección, ID del fragmento) y de catálogo y períodos.
- **`analytics/contrast.py`:** `compare_claims(...) -> ContrastResult`.
- **`analytics/causal.py`:** `assess_cause(...) -> CausalResult`.
- Los modelos validados (`ValidatedClaim`, `ValidatedObservation`) viven en `analytics/models.py`. Python puro, sin LLM.
- *Descartado: validar en `analytics/`.* La validación literal usa `figures_in` del agente, y `analytics` no depende de `agent`.

### D10c: extracción y validación
- **Esquema `ExtractedClaim`:**
  - `kind` (`variacion` | `ranking` | `direccion` | `cualitativa`), `chunk_id`;
  - `metric`, `dimension`, `value` y `filters` como lista de `{dimension, values}`, porque un `dict` libre funciona peor con `json_schema` en Gemini;
  - `base`, `target`, `reported` (texto literal) y `direction` (`mayor_caida` | `mayor_crecimiento` | `contraccion` | `crecimiento`).
  - **Sin enunciado del LLM:** el código lo genera (`Centro: venta neta -23 % (2026-T1 frente a 2026-T2)`). En `ExtractedObservation`, `quote` se valida literal y no se pasa a la síntesis.
- **Validación literal:**
  - una sola regla de línea y signo: en la línea del fragmento que contiene el valor de la dimensión debe estar la cifra con el mismo signo (`-`, `−`, `+`; sin signo, positiva). Motivos: "signo distinto" si está con otro signo, "no está en la línea del valor" si no está. En párrafos sin saltos de línea se usa la frase, sin cortar en abreviaturas (`vs.`) ni decimales;
  - el ranking, con su valor en el texto o la sección; la dirección, con su palabra de sentido en el texto (lista en `agent.yaml`: `contraccion`, `caida`, `crecimiento`…);
  - todo sin tildes ni mayúsculas.
- **Alcance:** cada valor de filtro (o su alias) en el título, la sección o el texto del documento; dimensión y valor del catálogo. Una métrica fuera del catálogo deja la afirmación como "no verificable con los datos", con una sola etiqueta.
- **Anclaje:** la expresión de los períodos (`T1`, `segundo trimestre`, mes o semestre) debe aparecer en el fragmento, su sección o el primer fragmento del documento; si no, se usan los dos últimos trimestres con datos (`data_range.quarters[-2:]`) con la marca "períodos por defecto". La métrica (nombre con espacios o `metric_synonyms`) debe aparecer en el documento.
- **Observaciones:** cita literal; el valor del segmento en la misma línea que la cita o en la sección; la fecha, una fecha real `AAAA-MM-DD` y literal en el fragmento (así ningún texto libre del documento pasa como fecha).
- **Documento demasiado largo:** si supera `contrast.max_document_chars`, error de herramienta con el tamaño (hoy el mayor tiene 4 944 caracteres).
- **ID de evidencia:** `primary_evidence_id` del fragmento, o su primer `evidence_ids`, o el `chunk_id`.
- **Máximo de afirmaciones:** `contrast.max_claims` (30), con aviso de las omitidas.
- *Descartado: un parser de tablas.* Decisión del responsable.

### D10d: veredictos y criterios (`agent.yaml`: `contrast` y `causal`)
- **Contraste:**
  - real = `var_pct` con 2 decimales; diferencia = reportado − real;
  - "coincide" si el real cuantizado con `ROUND_HALF_UP` a los decimales del reportado es igual; "aproximado" si `|diferencia| ≤ contrast.approx_pp` (1.0) y el mismo signo (−, 0 o +); si no, "no coincide";
  - ranking: misma consulta ordenada por `var_pct`; "verdadera" si el valor está entre los primeros empatados;
  - dirección: signo del total;
  - cualitativa: sin consulta.
  - Las variaciones y los rankings sobre los mismos datos comparten la consulta ordenada.
- **Segmento más afectado:** el de mayor variación en la dirección del efecto (la más negativa si el total cae; en empate, el primero por orden alfabético). Variación total nula o cero → error "no hay efecto que evaluar". `locate_by` debe tener valores del catálogo o estar en `causal.open_dimensions`, y no puede ser filtrada ni la dimensión temporal del catálogo (`time: true` en la capa semántica). `claimed_segment` debe ser un valor de `locate_by`.
- **Localización:**
  - "encaja" si algún segmento observado es el más afectado o varía ≥ `causal.locate_margin_pp` (1.0) más que el total en la dirección del efecto;
  - "no encaja" si hay observaciones y ninguna encaja;
  - "sin observaciones" si no hay.
- **Comparación** (solo `competencia`; exige filtrar exactamente una dimensión con un valor): dos consultas, por (dimensión del grupo, `locate_by`) y por la dimensión del grupo. Hay "efecto diferencial" si algún valor del grupo varía en el segmento más afectado ≥ `causal.differential_pp` (1.0) más que su total en sentido contrario al efecto.
- **Temporalidad:**
  - dos consultas agrupadas por la dimensión temporal del catálogo (una con `period=base` y otra con `period=target`) en el segmento más afectado; se omiten los meses sin datos y la serie se ordena cronológicamente, aunque los períodos no sean contiguos;
  - mayor cambio entre meses consecutivos en la dirección del efecto, y se informa el mes posterior;
  - "cambio concentrado en <mes>" si ≥ `causal.step_share` (0.8) × |media del objetivo − media de la base|;
  - se informan las fechas de las observaciones de ese segmento.
- **Alternativas:**
  - amplitud de `var_pct` (sin nulos) por cada dimensión con valores, no filtrada, no de localización y no temporal, y por `causal.open_dimensions` (`punto_venta_id`); "uniforme" si ≤ `causal.uniform_spread_pp` (1.5);
  - con `metrica_propia` (que exige `cause_direction`: `sube` o `baja`), "sin cambio" si |`var_pct`| de la métrica de la causa ≤ `causal.cause_change_pct` (1.0), y "en sentido contrario" si cambió al revés de lo esperado.
- **Diseño:** "sin diseño que permita atribuir" si hay limitaciones o ninguna atribución declara diseño.
- **Veredicto por tipo** (decisión del responsable, coherente con EXPLORACION):

  | Tipo | "compatible (hipótesis)" si… | "contradicha" si… |
  |---|---|---|
  | `competencia` | localización encaja **y** efecto diferencial | — |
  | `disponibilidad` | localización encaja | — |
  | `metrica_propia` | la métrica cambió en el sentido esperado y la localización encaja | la métrica no cambió o cambió en sentido contrario |

  - En cualquier tipo, "contradicha" (con prioridad sobre los demás) si `claimed_segment` no es el más afectado ni varía `locate_margin_pp` más que el total.
  - En los demás casos, "no sustentada".
- **Con los datos reales:**
  - promociones (`competencia`) → "no sustentada": con la búsqueda real solo hay observaciones en Centro (localización "no encaja"); y aunque una observación como CAM-103 hiciera encajar Sur, seguiría sin efecto diferencial;
  - precio relativo (`competencia`) → "no sustentada";
  - subida del precio propio (`metrica_propia`) → "contradicha";
  - faltantes (`disponibilidad`) → "compatible (hipótesis)";
  - promociones en Centro (con `claimed_segment`) → "contradicha".
- **Búsqueda de la causa:** `causal.search_top_k` = 8, con el modo y el modelo de `buscar_documentos`. Sin resultados, la localización queda "sin observaciones" y el diseño "sin diseño que permita atribuir".
- **Coherencia con EXPLORACION:**
  - el precio relativo, que la exploración cuenta entre las hipótesis compatibles, sale "no sustentada" porque los datos no muestran efecto diferencial; la respuesta lo explica con el criterio;
  - los faltantes salen "compatible (hipótesis)" aunque la caída sea uniforme también en los locales sin faltantes: el criterio de alternativas lo informa.

  Lo sabe el responsable.
- *Descartadas:*
  - una regla única sin tipo: con observaciones en Sur, las promociones pasarían a "compatible" (o faltantes a "no sustentada" con una regla estricta);
  - el precio propio como prueba contra el precio relativo: EXPLORACION lo deja como hipótesis;
  - umbrales en el código.

### D10e: evidencias, cifras, citas y verificación
- **Cifras de cada evidencia:** `evidence_items` construye las de `contraste` y `causalidad` con cifras explícitas, no con `figures(artifact)`:
  - contraste: reportado, real y diferencia de las comparadas; en los rankings, la variación real del afirmado y la del primero;
  - causal: los valores de cada criterio.
- **Evidencias relacionadas:** las consultas internas se convierten en evidencias `metricas` (citables por su `evidence_id`, con `result` en `evidence_views`, que busca también en `queries`). Los fragmentos de afirmaciones y observaciones validadas, en evidencias `documento`, así que `REP-01` se puede citar.
- **`evidence_id`:** se genera con `analytics/evidence.py::evidence_id` sobre doc o causa, `sha256` del documento, umbrales, `search_top_k`, modo de búsqueda, elementos validados y `evidence_id` de las consultas.
- **Resumen para la síntesis:** la tabla compacta de afirmaciones o criterios, con enunciados del código y los `evidence_id` de sus consultas, dentro de un `evidence_block` neutralizado. Las consultas internas no van como bloques.
- **Veredictos citados:**
  - una afirmación que cita una evidencia causal y contiene un término de veredicto debe contener el de esa evidencia;
  - si contiene "no sustentada" o "contradicha" de su evidencia, queda exenta del léxico causal.
- **"Insuficiente" coherente con lo consultado (decisión del responsable):**
  - frase con un `absence_markers`, una métrica (nombre con espacios o `metric_synonyms`) y "por <dimensión>";
  - se rechaza solo si la ejecución tiene una evidencia `metricas` (incluidas las internas) de esa métrica con `group_by` de esa dimensión;
  - `absence_exceptions` son frases concretas que contienen el término de la métrica (`precios de la competencia`, `precios promocionales`); la nota se mantiene solo si la métrica aparece dentro de una de ellas. "Faltan ventas de la competencia por región" se rechaza si se consultó `venta_neta` por marca y región.
- **Validez y avisos:** un contraste es válido con al menos una afirmación comparada; sus avisos (omitidas, consultas internas) pasan a `warnings`.
- *Descartadas:*
  - `figures(artifact)` para las evidencias nuevas: dejaba pasar casi cualquier cifra (filas de PDV, umbrales, descartadas);
  - comprobar "insuficiente" contra el catálogo sin mirar lo consultado: falsos positivos.

### D10f: prompts
- **`PLAN_RULES`:** la regla 5 pasa a "consistencia de un documento → `contrastar_afirmaciones`; pregunta causal → `evaluar_causalidad`". Añade otra: si la pregunta localiza el efecto en un segmento, este va en `claimed_segment` y no como filtro. Los ejemplos de cada tipo de causa vienen de `agent.yaml` (`causal.cause_kind_examples`), no del código.
- **`SYNTHESIS_RULES`:** "los veredictos de contraste y causalidad son de código: preséntalos tal cual, con su palabra; nunca conviertas un veredicto causal en causa".
- **Prompt de extracción:** reglas, catálogo, rango con datos y fragmentos, con el sándwich.
- *Descartado: elegir el tipo de causa en código por palabras clave.* Frágil y escrito a mano.

### D10g: interfaz
- `render_evidence` añade el contraste (`st.dataframe` de afirmaciones con filtros y períodos, y lista de descartadas) y la causalidad (causa, tipo y veredicto con `st.text`; `st.dataframe` de criterios), como texto plano (D9c).
- *Descartado: gráficos de criterios.* Una tabla basta para auditar.

### D10h: pruebas
- **Lógica pura** con elementos validados construidos a mano sobre la base de prueba.
- **Extracción** con `ScriptedChatModel` (validación, prompts y errores).
- **Búsqueda de la causa:** base de documentos de prueba con `FakeEmbedder`, `search_top_k` de `agent.yaml`. El orden de esa búsqueda no es el del modelo real (con `FakeEmbedder` `INV-04` no entra en los 8 primeros), así que "Declaraciones de diseño" se prueba validando las observaciones con sus fragmentos presentes y, con la búsqueda real, en una prueba `@pytest.mark.embeddings`.
- **Grafo** con guiones de 3 llamadas.
- **`llm`:** 3 preguntas (2 guía y el escenario modificado del reporte), como mucho 6 llamadas por pregunta (18 en total), anotando la duración frente a los 300 s de `BACKEND_TIMEOUT_S`. Si una pasa de 300 s, se anota y se decide con el responsable antes de archivar.
- *Descartado: probar la extracción solo con Gemini.* Ni determinista ni gratuita.

### D10i: documentación
- `docs/architecture.md` (D10 y el grafo con cinco herramientas), `openspec/config.yaml`, README (preguntas guía) y ROADMAP.
- *Descartado: un documento aparte.* La arquitectura ya concentra las decisiones.

## Risks / Trade-offs

- **[Riesgo] El LLM elige mal el tipo de causa o el segmento** → El tipo y los parámetros van en el resultado y en la interfaz; las reglas lo definen con ejemplos y la corrección corrige valores inválidos.
- **[Riesgo] La extracción omite afirmaciones** → Los descartes se listan; las omisiones las medirá el change 9.
- **[Riesgo] Más llamadas por pregunta** (3, y hasta 6) → Máximos propios y síntesis más corta.
- **[Riesgo] Reglas causales simples** → Configurables, con sus valores en la respuesta, y nunca afirman causalidad.
- **[Riesgo] Inyección indirecta en la extracción**, que ahora lee documentos (D8 lo evitaba en el plan) → Esquema cerrado, delimitadores neutralizados, validación literal en código y enunciados generados en código: un texto como `OC-EXT-06` solo puede producir elementos que existen en el fragmento y en el catálogo.
- **[Compromiso] La exención del léxico causal acepta frases como "Las promociones causaron la caída (no sustentada)"** → Lleva el veredicto de código en la misma afirmación; exigirlo en la misma cláusula complicaría la regla sin ganar claridad.

## Migration Plan

Sin migración de datos: solo secciones nuevas en `agent.yaml`. Rollback: revertir el commit.
