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
| D6 | Capa semántica en `semantic_layer.yaml` (métricas agregadas con expresión validada y métricas cociente, alias y dimensiones) y herramientas `consultar_metrica` y `calidad_datos` como funciones Python puras de solo lectura: el LLM elige parámetros, el código genera el SQL con valores enlazados, los períodos son expresiones de calendario y cada resultado lleva `evidence_id`, `ingestion_id` y los avisos de calidad de su corte. | Ninguna cifra depende del LLM; resultados reproducibles y trazables. Change `add-sales-analytics`. |
| D7 | Documentos: PDF y Word se convierten con código propio (PyMuPDF, python-docx) a un Markdown normalizado (`#`/`##`/`###`, tablas GFM, marcas de página; las tablas de PDF sin bordes se reconstruyen con los rectángulos de fondo de cada fila) y un único fragmentador de Markdown corta por sección y por ID de evidencia. Embeddings con fastembed (`paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones) detrás de una interfaz `Embedder`, fijados por la huella SHA-256 del archivo del modelo y cargados solo desde la caché (`make models`). Base propia `documents.duckdb` (`documents`, `doc_chunks`, `doc_ingestion_runs`) con publicación atómica. `buscar_documentos`: BM25 (`rank-bm25` con el IDF de Lucene, que nunca da peso 0 a una palabra presente) + coseno con RRF; sin modelo o con otro modelo, solo BM25 con aviso. Qdrant en modo local se evaluó y se descartó: misma calidad, más dependencias y bloqueo de su almacén a un solo proceso. | Un solo juego de reglas de fragmentación; fragmentos citables por su ID; búsqueda reproducible y sin red; el contenido documental se devuelve como evidencia, nunca como instrucciones. Change `add-document-retrieval`. |
| D8 | Agente de consulta con LangGraph, estrategia "plan y ejecución": el LLM (`bind_tools`) pide en una sola respuesta todas las consultas; `ToolNode` las ejecuta (`@tool` con `content_and_artifact`: el LLM lee un resumen y el resultado completo va a la verificación y la traza; entradas tolerantes); una corrección con los errores; síntesis con salida estructurada (hechos, hipótesis, contradicciones, información insuficiente, cada afirmación con su evidencia); verificación en código por afirmación (cifras dentro de la evidencia que cita, citas de la ejecución, léxico causal y atenuado) con 1 reintento y fallo cerrado; respuesta con traza. El prompt de planificación incluye el catálogo, los documentos y el rango de meses con datos leído de DuckDB. Proveedor: solo Gemini (`langchain-google-genai`), con límite de peticiones, tiempo máximo, reintentos acotados ante 5xx y ninguno ante cuota (429). | Medido en un benchmark de estrategias y modelos: 2 llamadas por pregunta, sin bucle ReAct ni lectura de documentos antes de decidir las consultas (inyección indirecta), y ninguna cifra sin verificar. Los modelos locales de 7–8B acertaron 2 de 57 preguntas de cifras. Change `add-query-agent`. |
| D9 | API e interfaz: `POST /ask` (FastAPI) devuelve la respuesta del agente con sus evidencias ya resueltas (citables por cualquiera de sus ids) y un estado HTTP por código de error. Las dependencias del agente se crean una vez al arrancar y las preguntas se responden de una en una. La interfaz Streamlit muestra los apartados, el detalle de cada evidencia, los avisos y la traza, siempre como texto plano, con un historial solo visual. `make up` monta los datos y el modelo del host en solo lectura, los comprueba antes de arrancar y publica los puertos solo en `127.0.0.1`. | Aplicación usable de punta a punta sin repetir la lógica del agente en la interfaz; límite de peticiones a Gemini compartido; el texto de documentos y del LLM nunca se interpreta como formato; nadie más en la red consume la cuota. Change `add-api-and-ui`. |

<!-- Añade aquí stack, almacenamiento, proveedor de LLM, etc. cuando se decidan (vía un change de OpenSpec). -->

## Límites

- Ningún cambio de comportamiento sin un change de OpenSpec asociado.
- `docs/` no duplica lo que dicen las specs; enlaza a ellas.
- Secretos solo por variables de entorno, nunca en el repo.

## Arquitectura de Brío Analyst

Arquitectura objetivo de referencia. Cada pieza se formaliza en su change de OpenSpec (ver `openspec/ROADMAP.md`); si un change la modifica, actualiza esta sección. Las decisiones D1, D2', D3, D4, D5, D6, D7, D8 y D9 siguen vigentes.

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
- LLM generativo sin costo: Gemini (API gratuita), el único proveedor por ahora (D8). Ollama u otros proveedores quedan para un change futuro.
- Cada respuesta distingue hechos comprobados, hipótesis, contradicciones e información insuficiente, con fuentes citadas. Nunca se afirma causalidad no demostrada.
- Las inconsistencias de datos se detectan, se tratan y se explicitan cuando afectan los resultados.
- Nada hardcodeado: marca, períodos, regiones y canales son parámetros.
- Credenciales en `.env`, manejo de errores y pruebas automatizadas.
- Simple, reproducible y confiable antes que complejo.

### Componentes

- **Backend:** Python 3.14 (D4), FastAPI y LangGraph para la orquestación. LangChain solo para la integración del modelo (`langchain-google-genai`), tools y salida estructurada.
- **API:** `POST /ask` responde con el agente (D9); `GET /health` no depende de datos ni credenciales.
- **Frontend:** Streamlit, que consume la API (D9). Todo se levanta con `make up` (Docker Compose), con los datos del host en solo lectura y los puertos solo en `127.0.0.1`.
- **Datos:** DuckDB embebido (read-only para consultas) y una capa semántica en `semantic_layer.yaml` (métricas, dimensiones, valores válidos, definiciones de negocio).
- **Ingesta** determinista e idempotente (D5): limpieza con las reglas de calidad aprobadas en `docs/EXPLORACION_DATOS.md` y verificación final con Pandera; tablas `sales`, `sales_review`, `dq_issues` e `ingestion_runs`; documentos convertidos a Markdown y fragmentados por sección y por ID de evidencia con metadatos (`doc_id`, `source_type`, página/sección, `primary_evidence_id`, `chunk_id`) (D7).
- **Recuperación híbrida:** BM25 (`rank-bm25`) más embeddings locales multilingües con `fastembed` (sin PyTorch), combinados con RRF; degradación a BM25 con aviso (D7).
- **Herramientas**, cada una con su `evidence_id`:
  - `consultar_metrica`: SQL generado desde el YAML de la capa semántica.
  - `sql_libre`: validado con sqlglot (solo SELECT, allowlist, LIMIT, timeout).
  - `buscar_documentos`.
  - `calidad_datos`.
- **Proveedor de LLM** (`agent/llm.py`): Gemini elegido por `LLM_PROVIDER`, con límite de peticiones por minuto, tiempo máximo, reintentos acotados ante 500/503/504 y ninguno ante cuota agotada (429); sin caché. Los fallos se convierten en códigos estables (`quota_exhausted`, `provider_unavailable`, `timeout`, `provider_error`) sin la clave en el texto.

### Grafo LangGraph

Implementado en `backend/src/analyst_backend/agent/` (D8):

1. **validar la pregunta** y **cargar el contexto** (código): catálogo de la capa semántica, documentos cargados y rango de meses con datos leído de DuckDB.
2. **planificar** (LLM con `bind_tools`): todas las consultas en una sola respuesta. Sin consultas → fuera de alcance, con un mensaje fijo.
3. **ejecutar** (`ToolNode`, como mucho N consultas por herramienta) → **corregir** (LLM, 1 vez, solo ve los errores) → ejecutar.
4. **recoger la evidencia** (código). Sin evidencia válida → insuficiente, sin síntesis.
5. **sintetizar** (LLM, salida estructurada: hechos / hipótesis / contradicciones / insuficiente, cada afirmación con su evidencia; la evidencia va delimitada y las reglas se repiten al final).
6. **verificar** (código, por afirmación: cifras dentro de la evidencia que cita, citas de esta ejecución, sin lenguaje causal en hechos, hipótesis atenuadas). 1 reintento con los problemas; si persisten, se retiran las afirmaciones que fallan (fallo cerrado).
7. **respuesta + traza** (consultas con su resultado completo, llamadas e intentos al LLM, problemas de verificación, modelo y duración). Cualquier fallo de un nodo termina aquí con estado `error` y su código.

Pendiente en otros changes: el subgrafo de contraste y el causal (change 6) y `sql_libre` (change 7).

### Convenciones

- Type hints en todo el código.
- La lógica de negocio es Python puro; LangGraph/LangChain solo la envuelven.
- Prohibido `create_pandas_dataframe_agent`, `create_sql_agent` o ejecutar código o SQL sin validación.
- Dependencias con versión fija.

### Pruebas

- **unit:** sin LLM.
- **agent:** LLM falso con guion (`ScriptedChatModel`, subclase de `GenericFakeChatModel` con `bind_tools` y `with_structured_output`).
- **integration:** marcadas con `@pytest.mark.llm`.
- **eval:** `eval/golden_set.yaml`.
