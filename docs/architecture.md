# Arquitectura

Solo decisiones y límites. La estructura de carpetas se consulta en el grafo (`graphify-out/`), no aquí.

## Decisiones

| # | Decisión | Motivo |
|---|----------|--------|
| D1 | Desarrollo guiado por specs con OpenSpec (`openspec/`) | El comportamiento se acuerda en specs antes de implementarse. |
| D2' | Código fuente en `backend/src/` (API) y `frontend/src/` (interfaz); pruebas en `backend/tests/`, `frontend/tests/` y `tests/` (repositorio). Reemplaza D2 (change `restructure-monorepo-layout`). | Backend y frontend se despliegan en contenedores distintos con dependencias distintas; el layout por aplicación evita mezclar la API con la interfaz. graphify indexa el repositorio completo. |
| D3 | Grafo de código con graphify, regenerado en cada commit | Claude consulta relaciones sin leer todo el repo. |
| D4 | Python 3.14 (`.python-version`) y workspace de uv con un único `uv.lock` versionado; dependencias directas con `==` | Entorno reproducible y una sola resolución de dependencias para backend y frontend. |
| D5 | Base de ventas en DuckDB con cuatro tablas: `sales` (única fuente de cifras), `sales_review` (filas retenidas para revisión), `dq_issues` (cada actuación de una regla de calidad) e `ingestion_runs` (carga publicada). Se reconstruye entera en cada carga y se publica de forma atómica. El catálogo de valores válidos vive en `backend/config/semantic_layer.yaml`. | Cifras trazables y reproducibles; las inconsistencias quedan explícitas y consultables. Change `add-sales-ingestion`. |

<!-- Añade aquí stack, almacenamiento, proveedor de LLM, etc. cuando se decidan (vía un change de OpenSpec). -->

## Límites

- Ningún cambio de comportamiento sin un change de OpenSpec asociado.
- `docs/` no duplica lo que dicen las specs; enlaza a ellas.
- Secretos solo por variables de entorno, nunca en el repo.

## Arquitectura de Brío Analyst

Arquitectura objetivo de referencia. Cada pieza se formaliza en su change de OpenSpec (ver `openspec/ROADMAP.md`); si un change la modifica, actualiza esta sección. Las decisiones D1, D2', D3, D4 y D5 siguen vigentes.

### Propósito

Asistente de análisis comercial con IA para el equipo de mercadeo de Almena Foods. La marca Brío muestra señales de deterioro en el primer semestre de 2026. El equipo necesita entender su desempeño, contrastar la información comercial con las investigaciones de consumidor y explorar factores asociados, sin sacrificar exactitud, evidencia ni criterio humano.

Fuentes (en `data/raw/` cuando se copien): una base de ventas CSV (~4.000 registros, con inconsistencias esperables) y documentos PDF, Word y Markdown (investigación de consumidor, observaciones de puntos de venta y reporte comercial).

Un analista pregunta en lenguaje natural y recibe respuestas fundamentadas. Ejemplos (no es una lista cerrada):

- ¿Cuál fue la región con mayor caída porcentual en ventas netas de Brío entre T1 y T2 de 2026? Muestra valores y cálculo.
- ¿Qué hallazgos de consumidor y observaciones comerciales podrían explicar el deterioro de Brío?
- ¿Son consistentes las conclusiones del reporte comercial con los datos de ventas?
- ¿Podemos afirmar que las promociones de la competencia causaron la caída? ¿Qué evidencia lo sustenta o limita?

### Requisitos transversales

- Todo cálculo numérico se hace con operaciones verificables sobre los datos. El LLM nunca calcula cifras.
- LLM generativo sin costo: Gemini Flash (API gratuita) como principal y Ollama como alternativa.
- Cada respuesta distingue hechos comprobados, hipótesis, contradicciones e información insuficiente, con fuentes citadas. Nunca se afirma causalidad no demostrada.
- Las inconsistencias de datos se detectan, se tratan y se explicitan cuando afectan los resultados.
- Nada hardcodeado: marca, períodos, regiones y canales son parámetros.
- Credenciales en `.env`, manejo de errores y pruebas automatizadas.
- Simple, reproducible y confiable antes que complejo.

### Componentes

- **Backend:** Python 3.14 (D4), FastAPI y LangGraph para la orquestación. LangChain solo para integraciones de modelo (`langchain-google-genai`, `langchain-ollama`), tools y salida estructurada.
- **Frontend:** Streamlit, que consume la API. Todo se levanta con Docker Compose.
- **Datos:** DuckDB embebido (read-only para consultas) y una capa semántica en `semantic_layer.yaml` (métricas, dimensiones, valores válidos, definiciones de negocio).
- **Ingesta** determinista e idempotente (D5): limpieza con las reglas de calidad aprobadas en `docs/EXPLORACION_DATOS.md` y verificación final con Pandera; tablas `sales`, `sales_review`, `dq_issues` e `ingestion_runs`; documentos parseados con PyMuPDF / python-docx / markdown en chunks por sección con metadatos (`doc_id`, `tipo_fuente`, página/sección, `chunk_id`).
- **Recuperación híbrida:** BM25 (`rank-bm25`) más embeddings locales multilingües con `fastembed` (sin PyTorch), combinados con RRF.
- **Herramientas**, cada una con su `evidence_id`:
  - `consultar_metrica`: SQL generado desde el YAML de la capa semántica.
  - `sql_libre`: validado con sqlglot (solo SELECT, allowlist, LIMIT, timeout).
  - `buscar_documentos`.
  - `calidad_datos`.
- **LLMProvider** intercambiable por variable de entorno, con backoff ante 429 y caché.

### Grafo LangGraph

1. **entender** (LLM, salida estructurada).
2. **enrutar** (código), hacia una de estas ramas:
   - herramientas (bucle máx. 4) → evaluar evidencia (código, 1 reintento);
   - subgrafo de contraste (afirmaciones del reporte vs. datos);
   - subgrafo causal (criterios fijos);
   - fuera de alcance.
3. **sintetizar** (LLM, JSON: hechos / hipótesis / contradicciones / insuficiente).
4. **verificar** (código: números ⊂ resultados de tools, citas existentes, sin lenguaje causal en hechos; 1 reintento).
5. **respuesta + traza**.

### Convenciones

- Type hints en todo el código.
- La lógica de negocio es Python puro; LangGraph/LangChain solo la envuelven.
- Prohibido `create_pandas_dataframe_agent`, `create_sql_agent` o ejecutar código o SQL sin validación.
- Dependencias con versión fija.

### Pruebas

- **unit:** sin LLM.
- **agent:** LLM falso (p. ej. `GenericFakeChatModel`).
- **integration:** marcadas con `@pytest.mark.llm`.
- **eval:** `eval/golden_set.yaml`.
