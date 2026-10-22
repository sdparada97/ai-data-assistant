# Spec Delta

## Purpose

Convierte el CSV de ventas en una base DuckDB confiable y trazable, de la que salen todas las cifras del asistente, sin modificar el archivo original y sin dejar nunca una base a medias.

## ADDED Requirements

### Requirement: Carga del CSV a DuckDB
La ingesta SHALL leer el CSV indicado por `SALES_CSV_PATH` (UTF-8, con o sin BOM) tratando todas sus columnas como texto, y SHALL escribir el resultado en el archivo DuckDB indicado por `DUCKDB_PATH`. SHALL NOT modificar el CSV de origen. `source_line` SHALL ser la línea física del archivo, con el encabezado en la línea 1.

#### Scenario: Carga del archivo real
- **WHEN** se ejecuta la ingesta sobre `data/raw/02_Ventas_2026.csv`
- **THEN** se crea el archivo DuckDB con las tablas `sales`, `sales_review`, `dq_issues` e `ingestion_runs`
- **AND** la huella SHA-256 del CSV es la misma antes y después de la ingesta

#### Scenario: CSV sin BOM
- **WHEN** se carga una copia del archivo real sin el BOM inicial
- **THEN** el contenido de `sales` es idéntico al de la carga con BOM, salvo `ingestion_id` (que depende de los bytes del archivo)

#### Scenario: Rutas configurables
- **WHEN** se ejecuta la ingesta con `SALES_CSV_PATH` y `DUCKDB_PATH` apuntando a un directorio temporal
- **THEN** el archivo DuckDB se crea en la ruta indicada

### Requirement: Validación de la entrada
La ingesta SHALL verificar que el CSV existe, es UTF-8, tiene al menos una fila de datos, todas sus filas tienen el mismo número de campos que el encabezado y el encabezado contiene exactamente las columnas `registro_id`, `mes`, `marca`, `region`, `canal`, `punto_venta_id`, `presentacion`, `unidades` y `venta_neta_cop`, en cualquier orden. Si no, SHALL terminar con un error que nombre el problema, sin crear ni modificar la base.

#### Scenario: Archivo inexistente
- **WHEN** `SALES_CSV_PATH` apunta a un archivo que no existe
- **THEN** la ingesta termina con un error que incluye la ruta
- **AND** no se crea el archivo DuckDB

#### Scenario: Columna faltante
- **WHEN** el CSV no tiene la columna `venta_neta_cop`
- **THEN** la ingesta termina con un error que nombra `venta_neta_cop`
- **AND** un archivo DuckDB existente de una carga anterior queda intacto

#### Scenario: Columna sobrante
- **WHEN** el CSV tiene además una columna `descuento`
- **THEN** la ingesta termina con un error que nombra `descuento`

#### Scenario: Columnas en otro orden
- **WHEN** el CSV tiene las 9 columnas en otro orden
- **THEN** la carga termina sin errores

#### Scenario: Sin filas de datos
- **WHEN** el CSV solo tiene el encabezado
- **THEN** la ingesta termina con un error que indica que no hay filas de datos

#### Scenario: Fila con campos de más o de menos
- **WHEN** la línea 5 del CSV tiene 8 campos
- **THEN** la ingesta termina con un error que nombra la línea 5

#### Scenario: Codificación no UTF-8
- **WHEN** el CSV está codificado en Latin-1 y contiene `Brío`
- **THEN** la ingesta termina con un error que indica que el archivo no es UTF-8

### Requirement: Carga atómica
La ingesta SHALL construir la base en un archivo temporal del mismo directorio y SHALL reemplazar el destino solo si la carga completa termina sin errores. Si falla en cualquier paso, el destino anterior SHALL quedar intacto y el temporal SHALL eliminarse. Al empezar, SHALL borrar los temporales huérfanos de cargas interrumpidas.

#### Scenario: Fallo a mitad de la carga
- **WHEN** existe una base de una carga anterior y la ingesta falla después de haber empezado a escribir
- **THEN** la base anterior conserva exactamente su contenido
- **AND** no queda ningún archivo temporal en el directorio de destino

#### Scenario: Temporal huérfano
- **WHEN** el directorio de destino contiene un temporal de una carga interrumpida
- **THEN** tras una carga correcta ese temporal ya no existe

### Requirement: Idempotencia
Dos ingestas del mismo CSV con la misma configuración SHALL producir el mismo contenido en `sales`, `sales_review` y `dq_issues`, incluido el `ingestion_id`. Solo la fecha de ejecución de `ingestion_runs` puede variar.

#### Scenario: Doble ingesta
- **WHEN** se ejecuta la ingesta dos veces sobre `data/raw/02_Ventas_2026.csv`
- **THEN** las tablas `sales`, `sales_review` y `dq_issues` son idénticas fila a fila entre ambas ejecuciones

### Requirement: Esquema de la tabla de ventas
La tabla `sales` SHALL contener una fila por `registro_id`, con `registro_id` como clave única, `mes` en formato `AAAA-MM`, `marca`, `region`, `canal`, `presentacion` y `punto_venta_id` como texto no nulo, `unidades` como entero no nulo mayor o igual que 0, `venta_neta_cop` como entero no nulo mayor o igual que 0, `source_line` e `ingestion_id`.

#### Scenario: Tipos y restricciones
- **WHEN** se consulta la tabla `sales` tras cargar el archivo real
- **THEN** `unidades` y `venta_neta_cop` son de tipo entero y ninguna fila tiene valores nulos o negativos en ellas
- **AND** no hay dos filas con el mismo `registro_id`

### Requirement: Validación final con Pandera
Antes de publicar la base, la ingesta SHALL validar los datos destinados a `sales` con un esquema Pandera: tipos, unicidad de `registro_id`, formato de `mes`, valores del catálogo, rangos no negativos y textos no vacíos. Si falla, SHALL terminar con un error que liste los casos fallidos y SHALL NOT publicar la base. Así se detiene cualquier caso no cubierto por las reglas, como un `registro_id` vacío.

#### Scenario: Fila inválida que escapó a las reglas
- **WHEN** los datos destinados a `sales` contienen una fila con `unidades` negativas
- **THEN** la ingesta termina con un error de validación que identifica la columna `unidades`
- **AND** el archivo DuckDB de destino no se crea ni se modifica

#### Scenario: Identificador vacío
- **WHEN** una fila del CSV tiene `registro_id` vacío y el resto de valores válidos
- **THEN** la ingesta termina con un error de validación que identifica `registro_id`

### Requirement: Cuadre de filas
Cada fila del CSV SHALL terminar en exactamente un destino: `sales`, `sales_review`, excluida o eliminada. La suma de los cuatro destinos SHALL ser igual a las filas leídas; si no lo es, la ingesta SHALL terminar con un error y SHALL NOT publicar la base.

#### Scenario: Cuadre con el archivo real
- **WHEN** se carga `data/raw/02_Ventas_2026.csv`
- **THEN** `ingestion_runs` registra 4.000 filas leídas, 3.995 en `sales`, 2 en `sales_review`, 2 excluidas y 1 eliminada

#### Scenario: Cuadre roto
- **WHEN** un defecto hace que una fila no llegue a ningún destino
- **THEN** la ingesta termina con un error de cuadre que muestra los cinco conteos
- **AND** no se publica la base

### Requirement: Trazabilidad de la carga
`ingestion_runs` SHALL contener una sola fila, la de la carga publicada, con `ingestion_id`, la ruta del CSV, su huella SHA-256, la fecha de ejecución y los conteos por destino. El `ingestion_id` SHALL derivarse del contenido del CSV y de la configuración, y SHALL aparecer en cada fila de `sales`, `sales_review` y `dq_issues`.

#### Scenario: Identificador de carga
- **WHEN** se carga el archivo real
- **THEN** `ingestion_runs` tiene una única fila cuya huella SHA-256 coincide con la del CSV
- **AND** todas las filas de `sales`, `sales_review` y `dq_issues` tienen ese mismo `ingestion_id`

### Requirement: Descripción del esquema
Cada tabla y cada columna de `sales`, `sales_review`, `dq_issues` e `ingestion_runs` SHALL tener un comentario descriptivo en DuckDB. El comentario de `sales` SHALL indicar que es la única fuente de cifras y que no incluye filas en revisión ni excluidas.

#### Scenario: Comentarios presentes
- **WHEN** se consultan `duckdb_tables()` y `duckdb_columns()` de la base cargada
- **THEN** ninguna de las cuatro tablas ni de sus columnas tiene el comentario vacío

### Requirement: Comando de ingesta
`make ingest` SHALL ejecutar la ingesta y SHALL terminar con código 0 si la carga se publica, o con código distinto de 0 y un mensaje claro si falla. Las rutas por defecto SHALL definirse en el `Makefile` y en `.env.example`, no en el código.

#### Scenario: Ingesta desde make
- **WHEN** se ejecuta `make ingest` con `DUCKDB_PATH` apuntando a un directorio temporal
- **THEN** termina con código 0 y el archivo DuckDB existe en esa ruta

#### Scenario: Error desde make
- **WHEN** se ejecuta `make ingest` con `SALES_CSV_PATH` apuntando a un archivo inexistente
- **THEN** termina con código distinto de 0 y la salida incluye la ruta
