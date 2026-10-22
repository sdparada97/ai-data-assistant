# Tasks

## 1. Dependencias y configuración

- [x] 1.1 (~15 min) Añadir `pydantic==2.14.1` como dependencia directa en `backend/pyproject.toml`; verificar con `uv lock --check` y `make test`
- [x] 1.2 (~30 min) Añadir `load_analytics_settings()` en `settings.py` (`DUCKDB_PATH`, `SEMANTIC_LAYER_PATH`, sin valores por defecto) con sus tests en `backend/tests/test_settings.py`; verificar que pasan

## 2. Dimensiones en dq_issues (requisito MODIFIED "Estructura de las incidencias")

- [x] 2.1 (~1 h) Guardar en cada incidencia las dimensiones de su fila (`mes`, `marca`, `region`, `canal`, `presentacion`, `punto_venta_id`, recortadas y con la escritura del catálogo si el valor es válido): `rules.ISSUE_COLUMNS`, `pipeline._issues_frame`, DDL y comentarios en `storage.py`
- [x] 2.2 (~45 min) Tests del requisito "Estructura de las incidencias" (columnas exactas, dimensiones de `V03997`, `marca = Brio` en `V00667`, `region = Sur` en `V02929`) y actualizar el conteo de columnas comentadas en `test_storage.py`; ejecutar `make ingest`; verificar que pasan

## 3. Capa semántica

- [x] 3.1 (~30 min) Ampliar `backend/config/semantic_layer.yaml` con `metrics` (agregadas `venta_neta`, `unidades`, `registros`; cociente `precio_efectivo`; `unit` y `decimals`), `aliases` (`Brío: Brio`) y las dimensiones `punto_venta_id` y `mes`; verificar que `make ingest` sigue funcionando
- [x] 3.2 (~45 min) Implementar en `analytics/semantic.py` la carga de métricas agregadas y cociente y la huella SHA-256 del YAML
- [x] 3.3 (~20 min) Tests del requisito "Métricas definidas en configuración" (cuatro métricas y sus tipos, cociente con métrica inexistente) en `backend/tests/analytics/test_semantic.py`; verificar que pasan
- [x] 3.4 (~45 min) Implementar el tokenizador que valida las expresiones (lista permitida, sin `;`, `--` ni `/*`, columnas dentro de una agregación)
- [x] 3.5 (~30 min) Tests del requisito "Expresiones de métricas seguras" (sentencia, comentario, columna inexistente, columna fuera de agregación); verificar que pasan
- [x] 3.6 (~30 min) Implementar las dimensiones consultables y la resolución de valores (mayúsculas y alias), validando los alias al cargar
- [x] 3.7 (~20 min) Tests del requisito "Dimensiones consultables" (seis dimensiones, rechazo de `unidades`); verificar que pasan
- [x] 3.8 (~30 min) Tests del requisito "Alias y escritura de los valores" (`Brío`, `sur`, `Caribe`, alias inválido); verificar que pasan
- [x] 3.9 (~45 min) Implementar `analytics/periods.py` con la gramática `AAAA`, `AAAA-Sn`, `AAAA-Tn` y `AAAA-MM`
- [x] 3.10 (~30 min) Tests del requisito "Expresiones de período" (trimestre, semestre, año, mes y formas inválidas) en `backend/tests/analytics/test_periods.py`; verificar que pasan

## 4. Modelos, conexión y evidencia

- [x] 4.1 (~1 h) Implementar `analytics/models.py` (`MetricQuery`, `MetricResult`, `QualityQuery`, `QualityResult`, `QueryError`) con sus validaciones de forma (métricas no vacías, `limit ≥ 1`, período y comparación excluyentes) y tests unitarios de esas validaciones; verificar que pasan
- [x] 4.2 (~45 min) Implementar `analytics/evidence.py` (normalización canónica y `evidence_id`) con tests unitarios de formato, orden de listas y sensibilidad a la huella del YAML; verificar que pasan
- [x] 4.3 (~45 min) Implementar `analytics/database.py` (solo lectura, sin acceso externo ni extensiones, `lock_configuration`, comprobación de columnas de `dq_issues`, error que pide `make ingest`)
- [x] 4.4 (~30 min) Tests del requisito "Acceso de solo lectura" (escritura rechazada y base intacta; `read_csv`, `INSTALL` y `SET` rechazados; base inexistente; base sin la columna `marca` en `dq_issues`) en `backend/tests/analytics/test_database.py`; verificar que pasan

## 5. consultar_metrica

- [x] 5.1 (~1 h) Implementar en `analytics/metrics.py` la validación y normalización contra la capa semántica (métricas, dimensiones, valores, períodos, rechazo de `mes` en filtros) con `QueryError` estructurado
- [x] 5.2 (~30 min) Tests del requisito "Validación de la consulta" (alias, métrica, valor y dimensión desconocidos, período y comparación a la vez, período inválido) en `backend/tests/analytics/test_metrics.py`; verificar que pasan
- [x] 5.3 (~1 h) Implementar la generación y ejecución del SQL para un período (filtros enlazados, agrupación, `GROUPING SETS` con total, conteo oculto por período, una rama `UNION ALL` por período)
- [x] 5.4 (~30 min) Tests del requisito "Consulta de métricas en un período" (Brio por región en T1, total en T2); verificar que pasan
- [x] 5.5 (~45 min) Implementar las métricas cociente en `Decimal` y el doble valor (redondeado `ROUND_HALF_UP` y exacto)
- [x] 5.6 (~20 min) Tests del requisito "Valores de las métricas" (precio efectivo de Brio en Sur T1: 9973.42 y 363431600 / 36440); verificar que pasan
- [x] 5.7 (~1 h) Implementar la comparación entre dos períodos (una rama por período), `var_abs` y `var_pct` (redondeada y exacta) y la fila de total
- [x] 5.8 (~30 min) Tests del requisito "Comparación entre dos períodos" (Sur −30.27, total −10.50, precio 9973.42 → 9974.99, 0.02); verificar que pasan
- [x] 5.9 (~45 min) Implementar orden con ranking de competición, nulos al final sin `rank` y `limit` sin afectar el total
- [x] 5.10 (~30 min) Tests del requisito "Orden y ranking" (Sur rank 1, Oriente rank 5, `limit = 1`, empate 1-1-3 con una base de prueba); verificar que pasan
- [x] 5.11 (~45 min) Implementar la cobertura de meses por período, los nulos por grupo o corte sin filas y sus avisos
- [x] 5.12 (~30 min) Tests del requisito "Datos faltantes" (`2025-T1` con `venta_neta` y `registros`, `2026` con meses parciales y 2715963700, corte `XX-T-999`); verificar que pasan
- [x] 5.13 (~20 min) Implementar los nulos de `var_abs` y `var_pct` y el aviso de variación no definida
- [x] 5.14 (~20 min) Tests del requisito "Variación no definida" (`2025-T4` frente a `2026-T1`); verificar que pasan
- [x] 5.15 (~1 h) Implementar `quality_notes` (incidencias `error` y `aviso` del corte con sus dimensiones, `outside_periods` para meses inválidos) y `corrections_count`
- [x] 5.16 (~30 min) Tests del requisito "Avisos de calidad en el resultado" (`V03997` en Sur con 1 corrección, `V03999` en Centro fuera de período, Oriente sin avisos); verificar que pasan
- [x] 5.17 (~30 min) Añadir al resultado `evidence_id`, `ingestion_id`, consulta normalizada, meses por período, SQL y parámetros
- [x] 5.18 (~30 min) Tests del requisito "Trazabilidad de los resultados" para `consultar_metrica` (consultas equivalentes, consultas distintas, cambio en la capa semántica); verificar que pasan

## 6. calidad_datos

- [x] 6.1 (~45 min) Implementar en `analytics/quality.py` los filtros por dimensión, período (meses inválidos con `outside_periods`) y regla, y el filtrado de `sales_review` por las dimensiones de `dq_issues`
- [x] 6.2 (~20 min) Tests del requisito "Filtros de calidad de datos" (Brio en `2026-T2`) en `backend/tests/analytics/test_quality.py`; verificar que pasan
- [x] 6.3 (~45 min) Implementar el resultado: `issue_count`, `corrections_count`, conteos por regla y acción, venta afectada por acción, `issues`, `review_rows`, `ingestion` y la trazabilidad
- [x] 6.4 (~30 min) Tests del requisito "Resultado de calidad de datos" (sin filtros, Brío en Sur, regla DQ05) y del escenario "Evidencia de calidad_datos"; verificar que pasan

## 7. Documentación

- [x] 7.1 (~30 min) Registrar D6 en `docs/architecture.md` (capa semántica, métricas agregadas y cociente, períodos de calendario, herramientas puras de solo lectura con `evidence_id`) y documentar en `README.md` cómo probar las herramientas desde Python; verificar que el ejemplo documentado se ejecuta

## 8. Cierre

- [x] 8.1 (~10 min) Ejecutar `make ingest` y `make test`; verificar que todo pasa
- [x] 8.2 (~10 min) Ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores
