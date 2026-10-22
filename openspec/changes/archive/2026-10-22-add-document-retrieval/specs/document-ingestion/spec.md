# Spec Delta

## Purpose

Convierte los documentos de `data/raw/` (PDF, Word y Markdown) a un Markdown normalizado y lo divide en fragmentos citables por sección y por ID de evidencia, con sus metadatos y embeddings, que se publican en una base DuckDB propia de forma atómica y trazable.

## ADDED Requirements

### Requirement: Documentos a cargar
La ingesta SHALL cargar, en orden alfabético, los archivos del primer nivel de `DOCUMENTS_DIR` cuya extensión, sin distinguir mayúsculas, esté en la lista de `documents.yaml`. SHALL ignorar subdirectorios, archivos ocultos y archivos de bloqueo de Office (`~$*`). El `doc_id` SHALL ser el nombre sin extensión. SHALL fallar sin publicar si dos archivos comparten `doc_id`, si un archivo no se puede leer o si no hay ningún documento válido.

#### Scenario: Directorio real
- **WHEN** se cargan los documentos de `data/raw/`
- **THEN** se cargan `01_Contexto_Negocio`, `03_Investigacion_Consumidor`, `04_Observaciones_Canales` y `05_Reporte_Comercial`
- **AND** `02_Ventas_2026.csv` no se carga

#### Scenario: Archivos que se ignoran
- **WHEN** el directorio contiene `informe.PDF`, `.oculto.md`, `~$notas.docx` y un subdirectorio con `otro.pdf`
- **THEN** solo se carga `informe`

#### Scenario: doc_id duplicado
- **WHEN** el directorio contiene `informe.pdf` e `informe.md`
- **THEN** la ingesta falla con un error que nombra `informe` y no publica la base

#### Scenario: Archivo dañado
- **WHEN** el directorio contiene un `.pdf` o un `.docx` que no es un archivo válido de su tipo
- **THEN** la ingesta falla con un error que nombra el archivo y no publica la base

#### Scenario: Sin documentos válidos
- **WHEN** el directorio solo contiene archivos `.csv`
- **THEN** la ingesta falla con un error que indica que no hay documentos que cargar

### Requirement: Conversión a Markdown
Cada PDF y cada Word SHALL convertirse a Markdown antes de fragmentarse; los `.md` se usan tal cual. Convenciones: título del documento con `#`, secciones con `##`, subsecciones con `###`, listas con `- `, tablas como tablas Markdown y espacios repetidos reducidos a uno. En Word, `Title` es `#`, `Heading 1` es `##` y `Heading 2` es `###`, y una celda combinada aparece una sola vez. El Markdown de cada documento SHALL guardarse en la base.

#### Scenario: Niveles de título en Word
- **WHEN** se convierte `04_Observaciones_Canales.docx`
- **THEN** el Markdown contiene `# Observaciones de canales`, `## Registro de hallazgos por región` y `### OC-SUR-01 | Sur`

#### Scenario: Celda combinada
- **WHEN** se convierte un `.docx` de prueba con una tabla cuya segunda fila combina dos columnas con el texto `Total`
- **THEN** en esa fila `Total` aparece una sola vez y la otra posición queda vacía

#### Scenario: Espacios repetidos
- **WHEN** se convierte `04_Observaciones_Canales.docx`
- **THEN** la fila de `CAM-101` contiene `CAM-101 2026-04-09`, con un solo espacio

#### Scenario: Markdown guardado
- **WHEN** se cargan los documentos de `data/raw/`
- **THEN** la base guarda el Markdown de los 4 documentos, y el de `01_Contexto_Negocio` es idéntico al archivo

### Requirement: Estructura de los PDF
En PDF, el título SHALL ser la línea con tamaño de letra igual o mayor al umbral de título, y una sección una línea igual o mayor al umbral de sección que cumple el patrón de sección; los umbrales, el patrón y el salto vertical que separa párrafos están en `documents.yaml`. Cada página SHALL empezar con `<!-- page: N -->`. En un PDF de 2 o más páginas, una línea presente en todas las páginas (contada una vez por página) SHALL eliminarse, igual que las que cumplen el patrón de número de página.

#### Scenario: Cabeceras y pies eliminados
- **WHEN** se convierte `05_Reporte_Comercial.pdf`
- **THEN** el Markdown no contiene `ALMENA FOODS / ANÁLISIS COMERCIAL` ni `Página 1`, y contiene `<!-- page: 2 -->` y `## 3. Interpretación preliminar`

#### Scenario: PDF de una página
- **WHEN** se convierte un PDF de prueba de una sola página con las líneas `Línea A` y `Línea B`
- **THEN** el Markdown contiene `Línea A` y `Línea B`

#### Scenario: Línea repetida en una sola página
- **WHEN** un PDF de prueba de 2 páginas tiene una línea que aparece dos veces en la página 1 y ninguna en la 2
- **THEN** esa línea se conserva

### Requirement: Tablas de PDF
En PDF, una tabla SHALL reconocerse como dos o más rectángulos de fondo del mismo ancho apilados sin hueco, con las tolerancias y la altura mínima de fila de `documents.yaml`: cada rectángulo es una fila y el primero es el encabezado. Cada línea SHALL asignarse a su columna por su posición horizontal, y las líneas de una misma celda SHALL unirse en orden.

#### Scenario: Tabla de PDF sin bordes
- **WHEN** se convierte `05_Reporte_Comercial.pdf`
- **THEN** el Markdown contiene una tabla con el encabezado `Región`, `Variación reportada (T2 vs. T1)` y `Lectura del analista`, y la fila `Centro`, `-23 %`, `Mayor caída porcentual; prioridad principal.`

#### Scenario: Celda de varias líneas
- **WHEN** se convierte `03_Investigacion_Consumidor.pdf`
- **THEN** la tabla de la sección `3. Hallazgos por región` tiene la fila `Centro`, `Algunos comentarios sobre promociones ajenas y faltantes ocasionales.`, `No respalda inferir la mayor caída en ventas.`

### Requirement: Fragmentos por sección
Un único fragmentador de Markdown SHALL procesar los tres formatos. Cada `##` o `###` abre un fragmento cuya `section` es ese título. El texto anterior a la primera sección forma un fragmento con `section` nula. Un fragmento sin texto aparte de su título SHALL descartarse, y un documento sin fragmentos SHALL hacer fallar la ingesta.

#### Scenario: Fragmentos de los documentos reales
- **WHEN** se cargan los documentos de `data/raw/`
- **THEN** hay 55 fragmentos: 4 del contexto de negocio, 18 de la investigación de consumidor, 21 de las observaciones de canales y 12 del reporte comercial

#### Scenario: Preámbulo sin sección
- **WHEN** se carga `05_Reporte_Comercial.pdf`
- **THEN** su primer fragmento tiene `section` nula y empieza por `Análisis: segundo trimestre 2026`

#### Scenario: Sección vacía descartada
- **WHEN** un `.md` de prueba contiene `## A` seguido directamente de `## B` y un párrafo
- **THEN** tiene un solo fragmento, con `section = B`

#### Scenario: Documento sin fragmentos
- **WHEN** el directorio contiene un `.md` que solo tiene títulos o un PDF sin texto
- **THEN** la ingesta falla con un error que nombra el documento y no publica la base

### Requirement: Títulos en el Markdown
El primer `#` SHALL ser el título del documento; si no hay ninguno, el título es el `doc_id`. Los `#` posteriores (títulos de página) SHALL NOT formar parte del texto. `####` y las líneas dentro de bloques de código SHALL tratarse como texto.

#### Scenario: Títulos que no abren sección
- **WHEN** un `.md` de prueba sin `#` contiene `## A`, un párrafo, `#### Detalle` y un bloque de código con la línea `## no es título`
- **THEN** tiene un solo fragmento, con `section = A` y `title` igual a su `doc_id`, cuyo texto contiene `Detalle` y `## no es título`

#### Scenario: Título de página fuera del texto
- **WHEN** se carga `05_Reporte_Comercial.pdf`
- **THEN** el fragmento de `REP-04` tiene `page = 2` y `title = Reporte ejecutivo | Desempeño de Brío`, y ningún fragmento contiene `Recomendaciones y trazabilidad`

### Requirement: Fragmentos por ID de evidencia
Dentro de una sección, SHALL empezar un fragmento nuevo en cada párrafo o elemento de lista que comienza con un ID de evidencia seguido de uno de los separadores de `documents.yaml`, y ese ID es su ID principal; un título `##`/`###` que empieza así también lo es. Los párrafos siguientes sin ID SHALL quedarse en ese fragmento hasta el siguiente ID o título. Un ID mencionado sin separador SHALL NOT dividir el fragmento.

#### Scenario: Afirmaciones del reporte comercial
- **WHEN** se carga `05_Reporte_Comercial.pdf`
- **THEN** cada uno de `REP-01` a `REP-06` es el ID principal de exactamente un fragmento

#### Scenario: Registros por título
- **WHEN** se carga `04_Observaciones_Canales.docx`
- **THEN** `OC-SUR-01`, `OC-CEN-02`, `OC-NOR-03`, `OC-ORI-04` y `OC-OCC-05` son IDs principales y sus fragmentos contienen sus viñetas

#### Scenario: Párrafo posterior sin ID
- **WHEN** se carga `04_Observaciones_Canales.docx`
- **THEN** el fragmento de `OC-EXT-06` contiene también el párrafo `Registro de trazabilidad: extracto del proveedor externo…`

### Requirement: Tablas en los fragmentos
Cada fila de una tabla SHALL escribirse en el texto del fragmento como `encabezado: valor`, con las celdas separadas por ` | `. Una tabla cuya primera columna empieza por un ID de evidencia en todas sus filas SHALL producir un fragmento por fila con ese ID como principal, salvo que un ID se repita en la tabla o ya sea principal en el documento (en un título, un párrafo o una tabla anterior); en ese caso, y en cualquier otra tabla, la tabla queda en el fragmento de su sección.

#### Scenario: Registros de campo
- **WHEN** se carga `04_Observaciones_Canales.docx`
- **THEN** hay 10 fragmentos con ID principal `CAM-*`, uno por fila, y el de `CAM-145` contiene `Región: Occidente`

#### Scenario: Tabla con IDs ya divididos
- **WHEN** un `.md` de prueba tiene dos tablas, en secciones distintas, con una fila `REP-01` cada una
- **THEN** solo la fila de la primera tabla es un fragmento con ID principal `REP-01`, y la segunda tabla queda en el fragmento de su sección

#### Scenario: ID repetido en una tabla
- **WHEN** un `.md` de prueba tiene una tabla con dos filas `REP-01`
- **THEN** la tabla queda en el fragmento de su sección y ningún fragmento tiene `REP-01` como ID principal

#### Scenario: Índice de referencias
- **WHEN** se carga `03_Investigacion_Consumidor.pdf`
- **THEN** la sección `8. Referencias internas de evidencia` es un único fragmento sin ID principal que contiene `ID: INV-01 | Descripción: Percepción de precio en Sur`

#### Scenario: Tabla sin IDs
- **WHEN** se carga `05_Reporte_Comercial.pdf`
- **THEN** el fragmento de la sección `2. Lectura regional presentada al comité` contiene `Región: Centro | Variación reportada (T2 vs. T1): -23 %`

### Requirement: Patrones de IDs en configuración
Los IDs de evidencia SHALL reconocerse con los patrones de `documents.yaml`, sin patrones escritos en el código. Los códigos de punto de venta (por ejemplo `OC-T-001`) SHALL NOT reconocerse como IDs de evidencia.

#### Scenario: Código de punto de venta
- **WHEN** se carga el fragmento de `CAM-145`, que menciona el punto de venta `OC-T-001`
- **THEN** sus IDs de evidencia son solo `CAM-145`

#### Scenario: Patrón configurable
- **WHEN** un `documents.yaml` de prueba no incluye el patrón de `CAM-*`
- **THEN** la tabla de registros de campo queda en el fragmento de su sección y no hay IDs `CAM-*`

### Requirement: Metadatos de cada fragmento
Cada fragmento SHALL guardar `chunk_id` (`<doc_id>:<posición de 3 dígitos>`), `doc_id`, `source_type` (`pdf`, `docx` o `md`), `title`, `section`, `page` (página donde empieza en PDF; nulo en Word y Markdown), `primary_evidence_id` (o nulo), `evidence_ids` (el ID principal, si existe, seguido de los demás IDs del texto, sin repetir y en orden de aparición) y `text`, sin marcas de negrita salvo dentro de bloques de código, que se conservan literales.

#### Scenario: Fragmento de una afirmación del reporte
- **WHEN** se carga `05_Reporte_Comercial.pdf`
- **THEN** el fragmento de `REP-02` tiene `doc_id = 05_Reporte_Comercial`, `source_type = pdf`, `page = 1`, `section = 3. Interpretación preliminar` y `title = Reporte ejecutivo | Desempeño de Brío`

#### Scenario: ID principal solo en el título
- **WHEN** se carga `04_Observaciones_Canales.docx`
- **THEN** el fragmento de `OC-SUR-01` tiene `evidence_ids = [OC-SUR-01]`, aunque su texto solo contiene viñetas

#### Scenario: Fragmento de Markdown
- **WHEN** se carga `01_Contexto_Negocio.md`
- **THEN** sus fragmentos tienen `source_type = md`, `page` nulo y secciones `Situación`, `Información disponible`, `Diccionario de la base de ventas` y `Convenciones de análisis`

### Requirement: Embeddings de los fragmentos
La ingesta SHALL calcular con el `Embedder` configurado el embedding de cada fragmento a partir de la plantilla de `documents.yaml` (por defecto título, sección y texto; sin la sección si es nula). Antes SHALL comprobar que el nombre, la huella y la dimensión del embedder coinciden con los de `documents.yaml`; si no, o si el embedder no puede cargarse, SHALL terminar con un error que lo explique, sin publicar la base y sin descargar nada.

#### Scenario: Embeddings guardados
- **WHEN** se cargan los documentos con un embedder de prueba de dimensión 384 y un `documents.yaml` con su nombre, huella y dimensión
- **THEN** cada uno de los 55 fragmentos tiene un embedding de 384 valores

#### Scenario: Modelo no descargado
- **WHEN** `MODELS_CACHE_DIR` no contiene el modelo
- **THEN** la ingesta termina con un error que menciona `make models` y `MODELS_CACHE_DIR`
- **AND** no se crea ni se modifica la base de documentos

#### Scenario: Huella distinta
- **WHEN** la huella del embedder no coincide con la configurada
- **THEN** la ingesta termina con un error que muestra la huella esperada y la encontrada

#### Scenario: Dimensión distinta
- **WHEN** la dimensión del embedder no coincide con la configurada
- **THEN** la ingesta termina con un error que muestra ambas dimensiones

### Requirement: Publicación atómica e idempotente
La base de documentos SHALL publicarse con el mismo mecanismo atómico que la base de ventas. Dos cargas de los mismos archivos con la misma configuración y el mismo modelo SHALL producir tablas idénticas, salvo la fecha de la carga.

#### Scenario: Doble carga
- **WHEN** se cargan dos veces los documentos de `data/raw/` con el mismo embedder de prueba
- **THEN** las tablas de documentos y fragmentos son idénticas fila a fila

#### Scenario: Fallo a mitad de la carga
- **WHEN** existe una base de documentos anterior y la carga falla después de empezar a escribir
- **THEN** la base anterior conserva su contenido y no quedan archivos temporales

### Requirement: Trazabilidad de la carga de documentos
La base SHALL tener una tabla de cargas con una sola fila, la de la carga publicada, con `ingestion_id` (derivado del nombre y el contenido de los archivos, de `documents.yaml` y de la huella del modelo), el nombre y la huella SHA-256 de cada archivo, el nombre, la huella y la dimensión del modelo, la fecha, el número de fragmentos por documento y el total.

#### Scenario: Carga registrada
- **WHEN** se cargan los documentos de `data/raw/`
- **THEN** la tabla de cargas tiene una fila con 4 archivos, sus huellas SHA-256, el modelo, su huella y 55 fragmentos en total

#### Scenario: Archivo renombrado
- **WHEN** se carga un directorio y después el mismo con un archivo renombrado
- **THEN** los `ingestion_id` son distintos

### Requirement: Comando de ingesta de documentos
`make ingest-docs` SHALL ejecutar la ingesta en este orden: rutas y archivos, conversión y fragmentación, comprobación del modelo, embeddings y publicación. SHALL terminar con código 0 si se publica la base, o con código distinto de 0 y un mensaje claro si falla. Las rutas por defecto SHALL definirse en el `Makefile` y en `.env.example`.

#### Scenario: Error desde make
- **WHEN** se ejecuta `make ingest-docs` con `DOCUMENTS_DIR` apuntando a un directorio inexistente
- **THEN** termina con código distinto de 0 y la salida incluye la ruta, aunque el modelo no esté descargado

### Requirement: Descarga del modelo
`make models` SHALL descargar en `MODELS_CACHE_DIR` el modelo de `documents.yaml` solo si no está, y SHALL comprobar su huella. Si el archivo del modelo ya está con otra huella, SHALL terminar con código distinto de 0 mostrando ambas huellas, sin descargar.

#### Scenario: Caché con otra huella
- **WHEN** se ejecuta `make models` con una caché que contiene el archivo del modelo con otro contenido
- **THEN** termina con código distinto de 0 y la salida muestra la huella esperada y la encontrada
