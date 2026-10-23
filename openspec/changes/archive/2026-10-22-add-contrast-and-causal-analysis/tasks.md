# Tasks

## 1. Configuración y modelos

- [x] 1.1 (~1 h) `agent.yaml` y `agent/config.py`:
  - secciones `contrast` (`approx_pp`, `max_claims`, `max_document_chars`, palabras de sentido) y `causal` (`locate_margin_pp`, `differential_pp`, `step_share`, `uniform_spread_pp`, `cause_change_pct`, `open_dimensions`, `search_top_k`, `cause_kind_examples`);
  - `limits.max_calls_by_tool`;
  - `absence_markers`, `absence_exceptions` y `metric_synonyms`.

  Tests de carga y de valores inválidos en `test_config.py`; verificar que pasan
- [x] 1.2 (~1 h) `analytics/models.py`: `ValidatedClaim`, `ClaimComparison`, `DiscardedItem`, `ContrastResult`, `ValidatedObservation`, `CriterionResult` y `CausalResult`, con `evidence_id` de `analytics/evidence.py`. Tests de la huella del requisito "Resultado trazable": misma entrada, mismo id; umbral distinto, otro id. Verificar que pasan

## 2. Contraste (lógica pura)

- [x] 2.1 (~2 h) `analytics/contrast.py`: variaciones (consulta compartida, diferencia, `ROUND_HALF_UP`, signo −/0/+), con tests del requisito "Veredicto de una variación" (tabla regional con una sola consulta; Sur `-30 %` coincide; precio `-0,5 %` signo distinto; umbral 0.5) en `backend/tests/analytics/test_contrast.py`; verificar que pasan
- [x] 2.2 (~1 h 30 min) Rankings con empates, direcciones y cualitativas, con tests de los requisitos "Veredicto de un ranking y de una dirección" (`REP-01` y `OC-CEN-02` falsa con Sur primero; contracción `:002` verdadera con −10.50) y "Afirmaciones cualitativas" (`REP-03`); verificar que pasan

## 3. Evaluación causal (lógica pura)

- [x] 3.1 (~1 h 30 min) `analytics/causal.py`: validación de dimensiones, segmento más afectado, localización y grupo de comparación, con tests de los requisitos "Dimensiones de la evaluación" (localizar por la dimensión filtrada; competencia sin grupo; segmento afirmado `Atlántico`), "Segmento más afectado" (Sur −30.27, total −10.50; empate alfabético; total cero → error), "Criterio de localización" (Centro no encaja; Sur encaja) y "Criterio del grupo de comparación" (las cuatro marcas, sin efecto diferencial) en `backend/tests/analytics/test_causal.py`; verificar que pasan
- [x] 3.2 (~1 h 30 min) Temporalidad (dos consultas por mes), alternativas (dimensiones con valores, dimensiones abiertas, nulos, métrica de la causa) y diseño, con tests de los requisitos "Criterio de temporalidad" (2026-04, 0.965), "Criterio de explicaciones alternativas" (canal, presentación y 24 puntos de venta; precio +0.02 sin cambio) y "Criterio de diseño de la evidencia"; verificar que pasan
- [x] 3.3 (~1 h) Veredicto por tipo y por segmento afirmado, y resultado trazable, con tests de los requisitos "Veredicto por tipo de causa" (promociones solo en Centro y también en Sur → no sustentada; precio relativo → no sustentada; faltantes → compatible), "Veredicto de una métrica propia" (precio propio `sube` → contradicha; `unidades` `sube` → contradicha), "Veredicto con el efecto localizado por la afirmación" (Centro → contradicha, con prioridad) y "Resultado causal trazable"; verificar que pasan

## 4. Extracción validada

- [x] 4.1 (~1 h 30 min) `agent/extraction.py` (contraste): esquema `ExtractedClaim` con filtros en lista, lectura del documento (con `max_document_chars`), prompt con el sándwich de reglas y enunciado generado en código. Tests con `ScriptedChatModel` de los requisitos "Contraste de un documento" (`06_Inexistente`; 12 fragmentos), "Extracción con esquema cerrado" (`OC-EXT-06` delimitado; máximo con aviso) y "Enunciado generado en código" en `backend/tests/agent/test_extraction.py`; verificar que pasan
- [x] 4.2 (~1 h 30 min) Validación de las afirmaciones: línea y signo, ID del fragmento, rankings y direcciones, catálogo y filtros en el documento, métrica fuera del catálogo, anclaje de períodos y métrica. Tests de los requisitos:
  - "Validación literal de las afirmaciones" (válida; `:004`; signo distinto; otra fila);
  - "ID de evidencia tomado del fragmento";
  - "Validación de rankings y direcciones" (sección de `OC-CEN-02`; Norte);
  - "Validación de alcance y catálogo" (`Atlántico`, `Luma`, cuota de formatos);
  - "Períodos y métrica anclados en el texto" (`2025-T1`; `T2 vs. T1`; por defecto).

  Verificar que pasan
- [x] 4.3 (~1 h 30 min) Extracción y validación de observaciones de la causa (`ExtractedObservation`, búsqueda con `search_top_k`, cita, segmento en la línea, fecha) y entrada de `evaluar_causalidad`. Tests de los requisitos:
  - "Evaluación de una afirmación causal" (entrada válida; `ciudad`; métrica propia incompleta);
  - "Observaciones de la causa en los documentos" (búsqueda real: solo Centro; `REP-02` e `INV-04`), con la base de documentos de prueba;
  - "Validación de las observaciones" (Sur de `CAM-103` con fecha; segmento de otra línea; fecha inventada).

  Verificar que pasan

## 5. Herramientas y grafo

- [x] 5.1 (~1 h 30 min) `agent/tools.py`: `contrastar_afirmaciones` y `evaluar_causalidad`, `extractor` en `ToolContext`, salida no interpretable → `QueryError` sin texto, resúmenes compactos; y en `graph.py`, `execute` llamada a llamada, con `ProviderError` capturado conservando `runs`/`artifacts` y `max_calls_by_tool`. Tests de los requisitos:
  - "Herramientas del agente" (cinco herramientas y reglas; contraste del reporte con 3 llamadas);
  - "Máximo propio de las herramientas con extracción" (dos contrastes; documento inexistente corregido; extracción fallida y corrección);
  - "Consultas fallidas sin resolver" (escenarios existentes);
  - "Errores de la extracción" (sin texto del documento; descartes que no son error del plan);
  - "Consultas conservadas ante un fallo en una herramienta" (`EV-d5c128c22542` con `quota_exhausted` y la tercera consulta descartada).

  En `test_tools.py` y `test_graph.py`; verificar que pasan
- [x] 5.2 (~1 h 30 min) `agent/evidence.py` y `evidence_views`: evidencias `contraste` y `causalidad` con cifras explícitas, títulos, evidencias `metricas` internas con `result` y `documento` de los fragmentos validados; validez y avisos. Tests de los requisitos "Tipos de evidencia", "Títulos de contraste y causalidad", "Validez y avisos de contraste y causalidad" y los escenarios existentes de "Evidencias en la respuesta"; verificar que pasan
- [x] 5.3 (~1 h 30 min) `agent/prompts.py` (`PLAN_RULES` con tipos de causa, `SYNTHESIS_RULES` con veredictos) y `agent/verify.py` (cifras citables, veredictos citados con exención del léxico, "insuficiente" contra lo consultado). Tests de los requisitos:
  - "Cifras citables de contraste y causalidad" (Sur 23.27 aceptada; cifra de una descartada rechazada);
  - "Veredictos causales citados" (alterado, con veredicto y sin veredicto);
  - "Verificación de citas y lenguaje" (escenarios existentes);
  - "Información insuficiente coherente con lo consultado" (ventas por región consultadas; ventas de la competencia consultadas; sin consultar; precios de la competencia; inventarios).

  En `test_verify.py` y `test_graph.py`; verificar que pasan con `make test`

## 6. Interfaz

- [x] 6.1 (~1 h) `render.py`: detalle del contraste (afirmaciones con filtros y períodos; descartadas) y de la evaluación causal (causa, tipo, veredicto y criterios), como texto plano. Tests con `AppTest` del requisito "Detalle del contraste y de la evaluación causal" en `frontend/tests/test_page.py`; verificar que pasan todas las pruebas de `frontend/tests/`

## 7. Pruebas con Gemini y documentación

- [x] 7.1 (~45 min) Tests `@pytest.mark.llm` de "Preguntas guía con el modelo real" y del escenario modificado "Consistencia del reporte con Gemini" en `backend/tests/agent/test_gemini.py`; verificar con `make test-llm` (3 preguntas, como mucho 6 llamadas por pregunta, 18 en total) y anotar las duraciones frente a los 300 s de `BACKEND_TIMEOUT_S`; si alguna los supera, decidir con el responsable antes de archivar
- [x] 7.2 (~45 min) `docs/architecture.md` (D10, el grafo con cinco herramientas y el cambio respecto a D8), `openspec/config.yaml` (resumen del agente), README (preguntas guía como ejemplos) y ROADMAP; verificar que los ejemplos del README son preguntas de los escenarios

## 8. Cierre

- [x] 8.1 (~15 min) Ejecutar `make test`; verificar que todo pasa
- [x] 8.2 (~10 min) Ejecutar `graphify update .` y `openspec validate --all --strict`; verificar que ambos terminan sin errores

## Workflow follow-up

- `/verify-change add-contrast-and-causal-analysis` y punto de control 5B.
- `/opsx:archive add-contrast-and-causal-analysis` solo con la aprobación explícita del responsable; después, ROADMAP y mensaje de commit (punto de control 5C).
