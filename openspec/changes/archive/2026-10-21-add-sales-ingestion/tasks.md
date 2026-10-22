# Tasks

## 1. Dependencias y configuración

- [x] 1.1 (~30 min) Añadir a `backend/pyproject.toml` duckdb==1.5.6, pandas==3.0.6, pandera==0.34.1 y pyyaml==6.0.3; regenerar `uv.lock`; verificar con `uv sync --all-packages --locked` y con `make test` (el test de versiones exactas sigue pasando)
- [x] 1.2 (~45 min) Crear `analyst_backend/settings.py` (única capa que lee `SALES_CSV_PATH`, `DUCKDB_PATH`, `SEMANTIC_LAYER_PATH` y `DATA_QUALITY_PATH`; sin valores por defecto, con error que nombra la variable que falta; rutas relativas resueltas desde la raíz), `backend/config/semantic_layer.yaml` (sección `dimensions` con los valores válidos de `docs/EXPLORACION_DATOS.md`), `backend/config/data_quality.yaml` (`price_deviation_threshold: 0.5`), las variables con sus valores en `.env.example` y en el `Makefile` (`?=`), con sus tests unitarios; verificar que pasan
- [x] 1.3 (~45 min) Implementar `ingestion/catalog.py` (lectura y validación de ambos YAML: dimensiones obligatorias, umbral numérico positivo, sin valores repetidos que solo difieran en mayúsculas) y sus tests unitarios con YAML de prueba; verificar que pasan

## 2. Lectura y validación de la entrada (requisito "Validación de la entrada")

- [x] 2.1 (~1 h) Implementar la lectura del CSV como texto (bytes leídos una vez, `utf-8-sig`, módulo `csv`, sin conversión de vacíos), `source_line` como línea física y las validaciones de existencia, codificación UTF-8, filas de datos y encabezado (mismo conjunto de columnas, en cualquier orden), con errores que nombran el problema
- [x] 2.2 (~45 min) Tests del requisito "Validación de la entrada" en `backend/tests/ingestion/test_input.py`: archivo inexistente, columna faltante (con base previa intacta), columna sobrante, otro orden, solo encabezado, fila con 8 campos y Latin-1; verificar que pasan

## 3. Modelo de incidencias y reglas que actúan

- [x] 3.1 (~45 min) Definir en `ingestion/rules.py` el modelo de incidencia (columnas de `dq_issues`, `details` como JSON) y el contrato común de las reglas (DataFrame → incidencias + máscaras de destino)
- [x] 3.2 (~20 min) Tests del requisito "Estructura de las incidencias" (columnas exactas, `details` JSON válido o nulo); verificar que pasan
- [x] 3.3 (~30 min) Implementar DQ03 (recorte en las 7 columnas de texto, una incidencia por columna corregida)
- [x] 3.4 (~30 min) Tests del requisito "DQ03 recorte de espacios" en `backend/tests/ingestion/test_rules.py` (`"Sur "`, `"Moderno "`, espacios intermedios intactos); verificar que pasan
- [x] 3.5 (~45 min) Implementar DQ01 (`registro_id` recortado único; conserva la primera línea sea cual sea su destino; `details` con la línea conservada y las diferencias)
- [x] 3.6 (~30 min) Tests del requisito "DQ01 registro_id único" (duplicado idéntico, duplicado con diferencias, primera aparición no válida); verificar que pasan
- [x] 3.7 (~45 min) Implementar DQ04 (comparación sin mayúsculas contra el catálogo; corrección por columna o `valor_no_valido` hacia revisión)
- [x] 3.8 (~30 min) Tests del requisito "DQ04 catálogo de valores válidos" (`BRIO` → `Brio`, `Caribe` fuera de catálogo, `Caribe` válido con un catálogo de prueba); verificar que pasan
- [x] 3.9 (~30 min) Implementar DQ05 (formato `AAAA-MM`, mes 01–12)
- [x] 3.10 (~20 min) Tests del requisito "DQ05 mes inválido" (`2026-13` a revisión con motivo, `2025-12` válido); verificar que pasan
- [x] 3.11 (~45 min) Implementar DQ06 y DQ07 con el patrón entero estricto `^-?\d+$`
- [x] 3.12 (~20 min) Tests del requisito "DQ06 unidades faltantes" (vacío y `12.5`); verificar que pasan
- [x] 3.13 (~20 min) Tests del requisito "DQ07 venta neta faltante" (`N/D`, venta afectada nula); verificar que pasan
- [x] 3.14 (~30 min) Implementar DQ08 (negativos en unidades o venta, una incidencia por fila con las columnas en `details`; los ceros no cuentan)
- [x] 3.15 (~20 min) Tests del requisito "DQ08 valores negativos" (una incidencia para −90/−1.000.000, 0/0 en `sales`); verificar que pasan
- [x] 3.16 (~30 min) Implementar DQ13 (0 unidades con venta positiva → revisión, `issue_type = venta_sin_unidades`)
- [x] 3.17 (~20 min) Tests del requisito "DQ13 venta sin unidades" (0/1.200.000 a revisión, 5/0 en `sales`, sin casos en el archivo real); verificar que pasan

## 4. Destino de las filas, avisos y reparto de incidencias

- [x] 4.1 (~1 h) Implementar en `ingestion/pipeline.py` el destino con la precedencia eliminada > excluida > revisión > `sales`, la `action` final de cada incidencia, `affected_net_sales_cop` y la construcción de `sales_review` (fila original, `rule_codes`, `reason`, `status`)
- [x] 4.2 (~30 min) Tests del requisito "Destino único por fila" (mes inválido + `N/D` → excluida, con dos incidencias); verificar que pasan
- [x] 4.3 (~30 min) Tests del requisito "Acción e impacto de cada incidencia" (acción según el destino final; impacto −1.000.000 en DQ08); verificar que pasan
- [x] 4.4 (~30 min) Tests del requisito "Filas en revisión" (`V03999` y `V03998` con sus valores originales; `rule_codes = DQ04,DQ08`); verificar que pasan
- [x] 4.5 (~30 min) Implementar DQ11 (puntos de venta con una aparición; `details` con apariciones y mediana)
- [x] 4.6 (~20 min) Tests del requisito "DQ11 aviso de punto de venta único" (`SU-T-013`, `CE-M-014` y `CE-T-015`, 1 aparición, mediana 30); verificar que pasan
- [x] 4.7 (~45 min) Implementar DQ12 (fórmula `|precio / mediana − 1|` sobre las filas destinadas a `sales` con `unidades > 0`, mediana por marca y presentación, umbral desde `data_quality.yaml`)
- [x] 4.8 (~30 min) Tests del requisito "DQ12 aviso de precio atípico" (sin avisos en el archivo real, error de escala con tres filas de referencia, umbral 1.0 sin aviso); verificar que pasan
- [x] 4.9 (~20 min) Tests del requisito "Incidencias del archivo real" (11 incidencias con el reparto por regla y sin DQ12); verificar que pasan

## 5. Validación final y almacenamiento

- [x] 5.1 (~45 min) Implementar el esquema Pandera de `sales` en `ingestion/schema.py` (tipos, unicidad, formato de mes, catálogo, rangos, textos no vacíos; `strict` y `lazy`)
- [x] 5.2 (~30 min) Tests del requisito "Validación final con Pandera" (unidades negativas inyectadas tras las reglas; `registro_id` vacío; ninguna base publicada); verificar que pasan
- [x] 5.3 (~1 h) Implementar en `ingestion/storage.py` el DDL de las cuatro tablas con tipos explícitos y la carga de los DataFrames
- [x] 5.4 (~30 min) Tests del requisito "Esquema de la tabla de ventas" (tipos enteros, sin nulos ni negativos, `registro_id` único); verificar que pasan
- [x] 5.5 (~30 min) Añadir `COMMENT ON` a cada tabla y columna (el de `sales` indica que es la única fuente de cifras)
- [x] 5.6 (~20 min) Tests del requisito "Descripción del esquema" (ningún comentario vacío); verificar que pasan
- [x] 5.7 (~1 h) Implementar la escritura atómica: limpieza de temporales huérfanos al empezar, temporal en el mismo directorio, `CHECKPOINT`, cierre, `os.replace` y limpieza del temporal y su `.wal` ante error
- [x] 5.8 (~45 min) Tests del requisito "Carga atómica" (fallo forzado tras empezar a escribir: base anterior intacta y sin temporales; temporal huérfano eliminado); verificar que pasan
- [x] 5.9 (~45 min) Implementar `ingestion_runs` (una fila), el `ingestion_id` determinista (SHA-256 del CSV y de los dos YAML) y la comprobación del cuadre antes de escribir
- [x] 5.10 (~30 min) Tests del requisito "Trazabilidad de la carga" (una fila, huella SHA-256, mismo `ingestion_id` en todas las tablas); verificar que pasan
- [x] 5.11 (~30 min) Tests del requisito "Cuadre de filas" (4.000 = 3.995 + 2 + 2 + 1; cuadre roto forzado → error con los conteos y sin base); verificar que pasan

## 6. Punto de entrada y pruebas de extremo a extremo

- [x] 6.1 (~45 min) Implementar `ingestion/__main__.py` (carga con `settings`, resumen de conteos, código 1 con mensaje claro ante errores) y el objetivo `make ingest`
- [x] 6.2 (~30 min) Tests del requisito "Carga del CSV a DuckDB" (cuatro tablas, CSV sin modificar por SHA-256, CSV sin BOM con el mismo resultado, rutas en directorio temporal); verificar que pasan
- [x] 6.3 (~20 min) Tests del requisito "Idempotencia" (dos cargas, tablas idénticas fila a fila); verificar que pasan
- [x] 6.4 (~30 min) Tests del requisito "Comando de ingesta" (`make ingest` con `DUCKDB_PATH` temporal termina en 0; con CSV inexistente termina en distinto de 0 y muestra la ruta); verificar que pasan

## 7. Documentación

- [x] 7.1 (~30 min) Registrar D5 en `docs/architecture.md` (tablas `sales`, `sales_review`, `dq_issues`, `ingestion_runs` y catálogo en `semantic_layer.yaml`), corregir la línea de componentes sobre Pandera y añadir `make ingest` al `README.md`; verificar que cada comando documentado existe en el `Makefile`

## 8. Cierre

- [x] 8.1 (~10 min) Ejecutar `make test` y verificar que todo pasa
- [x] 8.2 (~10 min) Ejecutar `graphify update .` y `openspec validate --all`; verificar que ambos terminan sin errores
