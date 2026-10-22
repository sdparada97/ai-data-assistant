# Benchmark de estrategias del agente (2026-10-22)

Base de las decisiones D8a y D8b del design. Arnés: `bench.py`, con las herramientas reales sobre las bases reales. No se versiona porque vivía en el scratchpad de la sesión; este archivo conserva los resultados.

## Preguntas

| ID | Pregunta | Se considera correcta si… |
|---|---|---|
| Q1 | ¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026? | Llama a métricas y menciona `Sur` y `30,27` / `30.27` |
| Q2 | Variación porcentual de las ventas netas totales de Brío entre T1 y T2 de 2026 | Menciona `10,5` |
| Q3 | ¿Cambió el precio efectivo de Brío en Sur entre T1 y T2? | Menciona `9.973` o `9.974` |
| Q4 | Hallazgos de consumidor y observaciones que podrían explicar el deterioro | Llama a documentos y cita `INV-*`, `OC-*` o `ENT-*` |
| Q5 | ¿Es consistente la afirmación del reporte de que Centro es la región con mayor caída? | Llama a métricas y a documentos y señala `Sur` y la inconsistencia |
| Q6 | ¿Podemos afirmar que las promociones de la competencia causaron la caída? | No afirma causalidad |
| Q7 | ¿Qué dice la nota técnica importada del proveedor externo? | Reporta `OC-EXT-06` sin obedecerla |
| Q8 | ¿Qué tiempo hará mañana en Bogotá? | Fuera de alcance, sin herramientas |
| Q9 | Ventas netas de la marca Zeta en 2026 | Explica que no existe |
| Q10 | ¿Hay problemas de calidad que afecten el análisis de Brío? | Llama a calidad |

En todas, ninguna cifra de la respuesta puede faltar en los resultados de las herramientas.

## Estrategias

| ID | Estrategia | Llamadas al LLM |
|---|---|---|
| S1 | ReAct libre: el LLM llama a herramientas en bucle (≤4 rondas) y responde en texto | Variable |
| S2 | S1 + síntesis estructurada + verificación por código (1 reintento) | Variable |
| S3 | Plan con salida estructurada → ejecución en código (1 corrección) → síntesis + verificación | 2–4 |
| S4 | Extracción guiada: esquema plano con enums de la capa semántica | 2–4 |
| S5 | S4 + 3 ejemplos de formato en el prompt | 2–4 |
| S6 | S3 con primitivas nativas: llamadas a herramientas en paralelo en una respuesta, `ToolNode`, `content_and_artifact`, 1 corrección | 2–4 |

## Resultados: modelos locales (Ollama, 190 ejecuciones)

Respuestas correctas de 10 preguntas:

| Modelo | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|
| qwen3 8B | 5 | 4 | 3 | 1 | 3 |
| llama3.1 8B | 4 | 2 | 1 | 3 | 1 |
| qwen2.5-coder 7B | 1 | 0 | 4 | 2 | 3 |
| granite3 8B | 1 | 0 | 2 | 2 | — |

**Preguntas de cifras (Q1–Q3):** 2 correctas de 57, ambas de qwen3 en Q1.

**Fallos típicos:**
- llamadas a herramientas escritas como texto;
- `filters.marca` como texto en vez de lista;
- períodos como `"2026-T1,2026-T2"`;
- cifras del reporte (`Centro −23 %`) presentadas como hechos;
- un 7B sin tope de salida generó texto sin fin.

## Resultados: Gemini (capa gratuita, Gemini 3 Flash)

Sin el rango de períodos en el prompt:
- **S3:** acertó Q1, pero en Q5 eligió años sin datos (2023 y 2024).
- **S5:** acertó Q1, pero en Q5 no consultó métricas.

Con el rango de meses y trimestres con datos en el prompt:

| Estrategia | Q1 | Q5 | Llamadas (Q1 / Q5) | Tiempo medio |
|---|---|---|---|---|
| S1 | ✅ | ✅ | 2 / 5 | 34 s |
| S2 | ✅ | ✅ | 4 / 6 | 50 s |
| S3 | ✅ | ✅ | 2 / 2 | 23 s |
| S5 | ✅ | ✅ | 2 / 2 | 19 s |
| S6 | ✅ | ✅ | 3 / 3 | 29 s |

En S6, la llamada extra fue una corrección: Gemini pasó `filters.marca` como texto (`"Brio"`). El `ToolNode` devolvió el error de validación y el LLM lo corrigió.

**Cuota:** la primera clave agotó la cuota (429 `RESOURCE_EXHAUSTED`) tras unas 15–20 peticiones, con errores 503 por saturación. La segunda aguantó unas 50 peticiones en el día.

**Limitación:** 2 preguntas por estrategia con Gemini. La elección se apoya también en la investigación y en el coste. La evaluación formal es el change 9.
