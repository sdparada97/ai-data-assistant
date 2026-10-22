# Design

## Context

Ver proposal.md (Why). Estado actual: `backend/src/analyst_backend/` solo tiene la app FastAPI con `/health`; no hay acceso a datos. `data/raw/02_Ventas_2026.csv` (4.000 filas, UTF-8 con BOM) está versionado. Las reglas y su comportamiento están en `docs/EXPLORACION_DATOS.md`, sección "Aprobación de reglas". `backend/scripts/explore_data.py` implementa una versión exploratoria de las reglas: sirve de referencia, pero no se reutiliza como código de producción. Se comprobó en Python 3.14 que pandas 3.0.6, Pandera 0.34.1 y DuckDB 1.5.6 funcionan juntos (validación, `COMMENT ON` y `lock_configuration`).

## Goals / Non-Goals

**Goals:**
- Que cada regla sea una función pura y probable de forma aislada.
- Que la base publicada sea siempre consistente: completa o inexistente.

**Non-Goals:**
- Conexión de lectura endurecida para consultas del agente (change 7) y herramientas de consulta (change 3).
- Rendimiento con volúmenes grandes: el CSV tiene 4.000 filas.

## Decisions

### Flujo de la ingesta
1. Leer los bytes del CSV una sola vez (la huella SHA-256 corresponde exactamente a lo procesado) e interpretarlos como texto `utf-8-sig` con el módulo `csv` de Python. Validar la codificación, que cada fila tenga tantos campos como el encabezado, el encabezado (mismo conjunto de 9 columnas, en cualquier orden) y que haya al menos una fila.
   - *Descartada: `pandas.read_csv` con `on_bad_lines="error"`.* Rellena en silencio las filas con campos de menos.
2. DQ03: recortar espacios.
3. DQ01: marcar duplicados de `registro_id` ya recortado (se conserva la primera línea, sea cual sea su destino). "Idéntico" se compara después de DQ03 y antes de DQ04.
4. Evaluar DQ04–DQ08 y DQ13 sobre cada fila y registrar todas las incidencias.
5. Asignar destino con la precedencia de la spec: eliminada > excluida > revisión > `sales`.
6. DQ11 sobre todas las filas leídas; DQ12 sobre las filas destinadas a `sales`.
7. Validar `sales` con Pandera.
8. Escribir en un DuckDB temporal, añadir comentarios, cerrar y reemplazar el destino.

- *Descartada: detenerse en la primera regla que falla.* Perdería trazabilidad cuando una fila tiene varios problemas.
- *Descartada: transformar con SQL dentro de DuckDB.* Cada regla sería más difícil de probar de forma aislada. DuckDB queda solo como almacenamiento.

### Módulos
`analyst_backend/settings.py` (única capa que lee variables de entorno) y el paquete `analyst_backend/ingestion/`:
- `catalog.py`: lectura de `semantic_layer.yaml` y `data_quality.yaml`.
- `rules.py`: una función por regla; cada una recibe un DataFrame y devuelve incidencias y máscaras.
- `pipeline.py`: orquesta el flujo y el destino de cada fila.
- `schema.py`: esquema Pandera.
- `storage.py`: DDL, comentarios y escritura atómica.
- `__main__.py`: punto de entrada de `make ingest`.

Toda la lógica es Python puro con pandas.
- *Descartada: un único módulo.* Mezclaría reglas, almacenamiento y configuración y dificultaría las pruebas.

### Configuración fuera del código
- `backend/config/semantic_layer.yaml` con la sección `dimensions`: valores válidos de marca, región, canal y presentación.
- `backend/config/data_quality.yaml` con `price_deviation_threshold: 0.5`.
- Rutas por variables de entorno: `SALES_CSV_PATH`, `DUCKDB_PATH`, `SEMANTIC_LAYER_PATH` y `DATA_QUALITY_PATH`. `settings.py` no tiene valores por defecto: si falta una variable, termina con un error que la nombra. Los valores por defecto viven en el `Makefile` (`VAR ?= ...`, sobrescribibles) y en `.env.example`. Las rutas relativas se resuelven desde el directorio de trabajo, que es la raíz del repositorio al usar `make`. Resolverlas desde la ubicación del paquete fallaría con una instalación no editable.
- `catalog.py` rechaza un catálogo con valores repetidos que solo difieren en mayúsculas (por ejemplo `Sur` y `SUR`), porque harían ambigua la reescritura de DQ04.

Los valores de negocio, incluido el nombre del archivo de ventas (que contiene un período), solo viven en configuración y en los tests.
- *Descartada: constantes en el código.* Contradice "nada hardcodeado".
- *Descartada: valores por defecto de las rutas en `settings.py`.* El nombre del CSV incluye un período (2026), y eso no debe estar en el código.
- *Descartada: un solo YAML para todo.* La capa semántica describe el negocio; el umbral es un parámetro técnico de calidad.

### El catálogo vive ya en `semantic_layer.yaml`
Este change crea el archivo solo con la sección `dimensions`; el change 3 añadirá métricas y alias (por ejemplo "Brío" → `Brio`) en el mismo archivo.
- *Descartada: un archivo de catálogo aparte que luego se fusiona.* Habría dos fuentes de verdad durante un tiempo.
- *Descartada: adelantar toda la capa semántica.* Amplía el alcance del change sin necesidad.

### Números enteros estrictos
`unidades` y `venta_neta_cop` solo se aceptan si cumplen `^-?\d+$`. El signo se acepta para que DQ08 pueda detectar los negativos.
- *Descartada: `pandas.to_numeric`.* Acepta `12.5` o `1e3` y ocultaría errores de formato.

### Contrato de `dq_issues` y `sales_review`
- Granularidad: DQ03 y DQ04 registran una incidencia por columna; las demás reglas, una por fila (DQ08, una sola aunque las dos columnas sean negativas).
- `action`: `corregida` para `correccion`, `ninguna` para `aviso` y el destino final de la fila para `error`.
- `affected_net_sales_cop`: la venta registrada en la fila si es un entero, también si es negativo; si no, nulo.
- `details` (JSON) guarda lo propio de cada regla: en DQ01, la línea conservada y las diferencias; en DQ08, las columnas negativas; en DQ11, las apariciones y la mediana; en DQ12, el precio, la mediana y la desviación.
- `sales_review.rule_codes` lista todas las reglas de revisión que retuvieron la fila, ordenadas y separadas por comas.
- *Descartada: una columna por cada dato propio de una regla.* El esquema crecería con cada regla nueva.
- *Descartada: guardar en `sales_review` solo la primera regla.* Se perdería información cuando una fila tiene varios motivos.

### DQ12: fórmula y población
Desviación = `|precio / mediana − 1|`, con precio = `venta_neta_cop / unidades`. La mediana se calcula por marca y presentación sobre las filas destinadas a `sales` con `unidades > 0`, que son también las únicas evaluadas. Las filas con 0 unidades que llegan a `sales` son solo las de venta 0 (DQ13 envía a revisión las de venta positiva), así que no hay precio que evaluar.
Los grupos de marca y presentación con mediana 0 (todas sus ventas en 0) no se evalúan: no hay precio de referencia con el que comparar.
- *Descartada: calcular la mediana sobre todas las filas numéricas.* Mezclaría filas en revisión o excluidas con las válidas.

### Pandera como verificación final, no como motor de reglas
Las reglas deciden el destino y registran incidencias. El esquema Pandera (`strict=True`, `lazy=True`) solo comprueba que lo que va a `sales` cumple las invariantes, incluidos los textos no vacíos; si algo escapa, la carga falla. Así un caso que ninguna regla aprobada cubre, como un `registro_id` vacío, detiene la carga en vez de entrar en silencio.
- *Descartada: expresar las reglas como checks de Pandera.* Pandera valida y falla, pero no enruta filas ni produce `dq_issues`.

### Almacenamiento y atomicidad
- La base se escribe en `<destino>.tmp-<pid>`, en el mismo directorio, con tipos explícitos (`BIGINT` para venta, `INTEGER` para unidades) y `COMMENT ON` en cada tabla y columna.
- Se ejecuta `CHECKPOINT`, se cierra la conexión y se publica con `os.replace` (atómico en el mismo sistema de archivos). Un `<destino>.wal` antiguo se aparta antes del reemplazo (se aplicaría a la base nueva al abrirla) y se borra después; si el reemplazo falla, vuelve a su sitio.
- Los dos YAML y el CSV se leen una sola vez: el `ingestion_id` corresponde exactamente a lo aplicado.
- Ante cualquier error, el temporal y su `.wal` se borran.
- Al empezar, se borran los `<destino>.tmp-*` que hayan quedado de una carga interrumpida (por ejemplo, un proceso matado).
- Antes de escribir se comprueba el cuadre de filas (`sales` + revisión + excluidas + eliminadas = leídas); si no cuadra, la carga falla.
- *Descartada: escribir directamente en el destino.* Un fallo dejaría una base a medias.
- *Descartada: `CREATE OR REPLACE` tabla por tabla.* Un lector podría ver tablas de cargas distintas.

### Identificador de carga determinista
`ingestion_id` = primeros 16 caracteres del SHA-256 de los bytes del CSV y de los dos YAML. `ingestion_runs.started_at` es lo único que varía entre cargas iguales. Como la base se reconstruye entera, `ingestion_runs` tiene una sola fila: la de la carga publicada. Un historial de cargas queda fuera de alcance.
- *Descartada: conservar el historial copiando `ingestion_runs` de la base anterior.* Añade una dependencia entre cargas que hoy no aporta valor.
- *Descartada: UUID o marca de tiempo.* Rompería la idempotencia de `sales` y `dq_issues`.

### Arquitectura
`docs/architecture.md` registra como D5 el modelo de tablas (opción B) y la ubicación del catálogo. También se corrige la línea de componentes que dice "limpieza y validación con Pandera": la limpieza la hacen las reglas DQ y Pandera es la verificación final.

## Risks / Trade-offs

- [pandas 3 cambia el tipo de texto por defecto] → Se leen todas las columnas como `str` y Pandera valida los tipos finales; ya se comprobó la compatibilidad.
- [DuckDB 1.5.6 y no 2.0.0] → 2.0.0 aún no tiene paquetes para Python 3.14; se actualizará en un change posterior.
- [`os.replace` no es atómico entre sistemas de archivos distintos] → El temporal siempre se crea en el directorio del destino.
- [Una regla nueva puede romper el cuadre de filas] → El cuadre se comprueba en cada carga; si no cuadra, la carga falla.
- [`sales_review` no tiene flujo de decisiones] → Aceptado: las filas siguen fuera hasta que se corrija el CSV; ver "Fuera de alcance" del proposal.
- [Filas con 0 unidades y venta positiva] → Resuelto con DQ13 (aprobada por el responsable el 2026-10-21): van a revisión.
- [`registro_id` o `punto_venta_id` vacío] → Sin regla propia, por decisión del responsable: la validación final con Pandera detiene la carga.
- [Si la primera aparición de un `registro_id` no es válida, el registro desaparece de `sales` aunque otra copia sí lo sea] → Consecuencia directa de DQ01 tal como se aprobó; queda explícita en la spec y probada.

## Migration Plan

Primera base de datos, sin migración. Rollback: borrar `data/processed/analytics.duckdb` y revertir el commit.
