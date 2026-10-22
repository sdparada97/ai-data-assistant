# Design

## Context

Ver proposal.md (Why). Estado actual:
- `data/processed/analytics.duckdb` (change 2) tiene `sales`, `sales_review`, `dq_issues` e `ingestion_runs`.
- `backend/config/semantic_layer.yaml` solo tiene `dimensions` con `values`, que lee `ingestion/catalog.py` para DQ04. Ese lector solo recorre las cuatro dimensiones con catálogo, así que añadir otras secciones no lo rompe.
- `dq_issues` identifica la fila por `registro_id` y `source_line`, pero no guarda sus dimensiones. Sin ellas no se puede saber, por ejemplo, que la fila excluida `V03997` es de Brio en Sur.
- `sales_review` guarda los valores crudos, sin recortar ni normalizar.
- pydantic 2.14.1 está instalada como dependencia transitiva.
- Con DuckDB 1.5.6 se comprobó:
  - funcionan `GROUPING SETS` con `FILTER` y parámetros enlazados;
  - la conexión endurecida bloquea la escritura, `read_csv` y `SET`;
  - no se pueden abrir dos conexiones al mismo archivo con configuraciones distintas en un mismo proceso.

Decisiones del responsable (2026-10-21): avisos automáticos de calidad, períodos como expresiones de calendario y herramientas como funciones Python puras.

## Goals / Non-Goals

**Goals:**
- Que ninguna cifra dependa del LLM: el LLM solo elige parámetros validados.
- Que cada resultado sea reproducible (misma consulta, carga y capa semántica → mismo `evidence_id`) y explícito sobre lo que falta.

**Non-Goals:**
- SQL libre, sqlglot y límites de tiempo (change 7).
- Integración con LangChain o LangGraph (change 5).
- Caché de consultas.

## Decisions

### Módulos
Nuevo paquete `analyst_backend/analytics/`:
- `semantic.py`: métricas, dimensiones, alias y la huella del YAML.
- `periods.py`: gramática de períodos.
- `models.py`: modelos pydantic y `QueryError`.
- `database.py`: conexión de solo lectura y comprobación de esquema.
- `evidence.py`: `evidence_id`.
- `metrics.py`: `consultar_metrica`.
- `quality.py`: `calidad_datos`.

`settings.py` añade `load_analytics_settings()` (`DUCKDB_PATH` y `SEMANTIC_LAYER_PATH`).
- *Descartada: ampliar `ingestion/catalog.py`.* Mezclaría la configuración de la carga con la de consulta.

### Métricas agregadas y cocientes
Dos tipos en el YAML:
- **Agregada:** `expression` SQL (`SUM(venta_neta_cop)`, `SUM(unidades)`, `COUNT(*)`) que DuckDB devuelve como entero.
- **Cociente:** `ratio: {numerator, denominator}` sobre métricas agregadas. Se calcula en Python con `Decimal` a partir de los enteros exactos, y el denominador 0 da nulo.

El precio efectivo es un cociente de sumas, no una media de precios.
- *Descartada: cocientes como expresión SQL con `NULLIF`.* DuckDB devuelve DOUBLE y se pierde exactitud antes de redondear.
- *Descartada: fórmulas en código Python.* Cada métrica nueva exigiría cambiar código.

### Validación de expresiones
Un tokenizador acepta solo `SUM`, `COUNT`, columnas de `sales`, números, `(`, `)`, `,`, `*` y `+ - * /`. Rechaza cualquier otra palabra, `;`, `--` y `/*`, y exige que cada columna esté dentro de los paréntesis de una agregación (profundidad > 0 tras `SUM(`/`COUNT(`).
- *Descartada: validar con sqlglot.* Añade una dependencia que llega en el change 7; las expresiones salen de configuración versionada.

### Generación de SQL
- **Identificadores:** solo salen del YAML validado (métricas y dimensiones).
- **Valores** (marcas, regiones, meses): siempre como parámetros enlazados `?`.
- **Forma de la consulta:** una rama `SELECT '<período>' AS __period, * FROM sales WHERE ...` por período, unidas con `UNION ALL`, y sobre ellas las métricas agregadas y un conteo oculto `COUNT(*)` agrupados con `GROUPING SETS ((__period, dims), (__period))`, que devuelve a la vez los grupos y el total. Ajuste durante la implementación: con `FILTER` habría que inyectar el filtro en cada agregación de una expresión compuesta, y no contaría bien los períodos solapados (por ejemplo `2026-S1` frente a `2026-T1`).
- **Grupos sin filas:** si el conteo de un período es 0, todas las métricas del grupo en ese período son nulas, incluida `registros`. Así nunca aparece un 0 falso.
- **Origen de los grupos:** salen de los datos de cualquiera de los períodos consultados. Un valor de catálogo sin filas en ningún período no aparece como fila; si se filtró explícitamente, se avisa del corte vacío.
- **`mes` en filtros:** se rechaza; los meses se piden con períodos.

- *Descartada: una consulta por período.* Duplica el SQL y complica el total.
- *Descartada: grupos desde el catálogo.* Mezclaría el catálogo con los datos y crearía filas sin datos en todas las consultas.

### Variaciones y redondeo
`var_abs` y `var_pct` se calculan en Python con `Decimal` sobre los valores exactos. Cada valor se devuelve redondeado a los `decimals` de su métrica y sin redondear; `var_pct` se redondea a 2 decimales. Se usa `ROUND_HALF_UP`, el redondeo que espera un lector de negocio (por ejemplo, 0.125 → 0.13).
- *Descartada: `ROUND_HALF_EVEN`.* Redondea 0.125 a 0.12, lo que sorprendería al comparar con una hoja de cálculo.

### Ranking
Ranking de competición (1, 1, 3) sobre el criterio pedido. Las filas con criterio nulo van al final sin `rank`. `limit` (≥ 1) recorta tras ordenar y nunca quita la fila de total.

### Períodos y cobertura
La gramática (`AAAA`, `AAAA-Sn`, `AAAA-Tn`, `AAAA-MM`) se resuelve con reglas de calendario. No hay meses ni años concretos en el código. Antes de consultar se obtienen los meses con datos en `sales` (`SELECT DISTINCT mes`). Si un período no tiene ningún mes con datos, se avisa de que no tiene datos en la base; si le faltan algunos, se listan los que faltan.
- *Descartada: períodos con nombre en el YAML.* Serían valores concretos que habría que mantener por año.

### Avisos de calidad
- **Origen:** la ingesta guarda en `dq_issues` las dimensiones de la fila afectada (requisito MODIFIED), recortadas y con la escritura del catálogo si el valor es válido.
- **`quality_notes`:** reúne las incidencias `error` y `aviso` cuyas dimensiones cumplen los filtros y cuyo `mes` está en los períodos o es inválido (`outside_periods = true`). Cada nota lleva sus dimensiones, para asociarla a su grupo.
- **Correcciones:** solo se cuentan (`corrections_count`).
- **`calidad_datos` sobre `sales_review`:** filtra uniendo por `source_line` con las dimensiones de `dq_issues`, nunca por los valores crudos.

- *Descartada: unir con el CSV crudo.* Rompe el principio de que la base es la única fuente consultable.

### Modelos y errores
- **Entradas pydantic:** `MetricQuery` y `QualityQuery`. Validan tipos, `metrics` no vacío, `limit ≥ 1` y que período y comparación sean excluyentes.
- **Salidas:** `MetricResult` y `QualityResult`.
- **Errores:** los de la capa semántica se lanzan como `QueryError(field, invalid_value, valid_options, message)`, para que el agente del change 5 pueda corregir y reintentar.
- **Dependencia:** pydantic pasa a ser directa (`pydantic==2.14.1`).
- *Descartada: dataclasses.* El change 5 necesita esquemas JSON de las tools, y pydantic los genera.

### Evidencia y trazabilidad
- **`evidence_id`:** `EV-` + los 12 primeros caracteres hexadecimales del SHA-256 de `{herramienta, consulta normalizada en JSON canónico, ingestion_id, huella SHA-256 de semantic_layer.yaml}`.
- **Normalización:** resuelve alias y mayúsculas y ordena las métricas, las dimensiones de agrupación, las dimensiones de los filtros y sus valores. Dos consultas equivalentes comparten evidencia aunque se pidan en otro orden.
- **Trazabilidad:** `consultar_metrica` devuelve el SQL y la lista de parámetros enlazados.
- *Descartada: UUID.* No sería reproducible ni verificable.
- *Descartada: excluir la capa semántica de la huella.* Un cambio en la definición de una métrica dejaría la misma evidencia con otra cifra.

### Conexión de solo lectura
- **Apertura:** `duckdb.connect(path, read_only=True, config={"enable_external_access": False, "autoinstall_known_extensions": False, "autoload_known_extensions": False})` y después `SET lock_configuration = true`.
- **Ciclo de vida:** cada llamada abre y cierra su conexión, así que siempre ve la carga publicada.
- **Esquema:** al abrir se comprueba que existan las columnas esperadas de `dq_issues`. Si falta el archivo o una columna, el error pide ejecutar `make ingest`.
- *Descartada: conexión compartida de larga vida.* `make ingest` reemplaza el archivo y la conexión vería una carga vieja.

### Arquitectura
`docs/architecture.md` registra D6: capa semántica con métricas agregadas y cociente, períodos de calendario y herramientas puras de solo lectura con `evidence_id`.

## Risks / Trade-offs

- [Cambiar `dq_issues` exige volver a cargar] → `make ingest` es idempotente; la tarea de cierre lo ejecuta y las herramientas detectan una base vieja.
- [La lista permitida de tokens es más restrictiva que SQL] → Aceptado: las métricas que necesiten más funciones ampliarán la lista en su propio change.
- [Un mes inválido se avisa en todos los períodos del corte] → Es intencional: el analista debe saber que existe un registro de su corte que no se pudo asignar.
- [DuckDB no admite dos conexiones al mismo archivo con configuraciones distintas en un proceso] → Cada llamada abre y cierra la suya, y los tests no mantienen otras conexiones abiertas a esa base.

## Migration Plan

1. Implementar las columnas nuevas de `dq_issues` y volver a ejecutar `make ingest`.
2. Desplegar el paquete `analytics`. Rollback: revertir el commit y volver a cargar.
