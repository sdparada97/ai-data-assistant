# Spec Delta

## Purpose

Recupera los fragmentos de documentos más pertinentes para una pregunta en español, combinando coincidencia de palabras y similitud semántica, y los devuelve como evidencia citable y trazable, sin interpretar su contenido.

## ADDED Requirements

### Requirement: Búsqueda híbrida
`buscar_documentos` SHALL ordenar los fragmentos con BM25 sobre su `text` (IDF de Lucene, `log(1 + (N − n + 0,5)/(n + 0,5))`, nunca 0) y con el coseno de los embeddings, y SHALL fusionarlos con RRF (`score = Σ 1 / (k + rank)`, `k` de `documents.yaml`). Los fragmentos sin ninguna palabra de la consulta SHALL quedar fuera del ranking BM25. Los empates SHALL resolverse por `chunk_id`. Devolverá los `top_k` de mayor puntuación.

#### Scenario: Fusión de rankings
- **WHEN** un fragmento ocupa el puesto 1 en BM25 y el 3 en similitud, con `k = 60`
- **THEN** su puntuación fusionada es 1/61 + 1/63

#### Scenario: Sin coincidencia de palabras
- **WHEN** un fragmento tiene puntuación BM25 0 y es el primero en similitud, con `k = 60`
- **THEN** su puntuación fusionada es 1/61

#### Scenario: Palabra en la mitad de los fragmentos
- **WHEN** en modo léxico se busca `brio` filtrando por `doc_id = 01_Contexto_Negocio`, donde aparece en 2 de sus 4 fragmentos
- **THEN** se devuelven esos 2 fragmentos, sin el aviso `no_matches`

#### Scenario: Empate en BM25
- **WHEN** dos fragmentos tienen la misma puntuación BM25
- **THEN** ocupa el puesto anterior el de menor `chunk_id`

#### Scenario: Ninguna palabra coincide en modo híbrido
- **WHEN** en modo híbrido se busca `zzzz`
- **THEN** el resultado lleva el aviso `no_lexical_matches`

#### Scenario: Limitaciones del estudio con el modelo real
- **WHEN** con el modelo de embeddings disponible se busca `limitaciones de la muestra del estudio` en los documentos reales
- **THEN** el primer resultado es un fragmento con ID principal `INV-LIM-*`
- **AND** el modo de recuperación es `hibrido`

### Requirement: Normalización del texto para BM25
El texto de los fragmentos y de la consulta SHALL compararse en minúsculas y sin tildes, de modo que `Brío`, `brio` y `BRÍO` coincidan.

#### Scenario: Tildes y mayúsculas
- **WHEN** en modo léxico se busca `FORMATOS PEQUENOS en norte`
- **THEN** el resultado es el mismo que al buscar `formatos pequeños en Norte`

#### Scenario: Marca sin tilde
- **WHEN** en modo léxico se busca `brio`
- **THEN** hay resultados, todos contienen `Brío` en su texto y son los mismos que al buscar `BRÍO`

### Requirement: Degradación a BM25
Si el `Embedder` no carga o falla al embeber la consulta (`semantic_unavailable`), o si su modelo, huella o dimensión no coinciden con los de la carga (`model_mismatch`), `buscar_documentos` SHALL ordenar solo con BM25, indicar el modo `lexico` y añadir un aviso con ese código y un texto con el motivo. En modo léxico solo se devuelven puntuaciones BM25 mayores que 0; sin ninguna, el aviso es `no_matches`. Nunca SHALL mezclar embeddings de modelos distintos.

#### Scenario: Modelo no disponible
- **WHEN** el embedder falla y se busca `promociones de la competencia` en los documentos reales
- **THEN** los 3 primeros resultados son, en este orden, los fragmentos de `INV-04`, `REP-02` y `OC-CEN-02`
- **AND** el modo es `lexico` y hay un aviso `semantic_unavailable`

#### Scenario: Modelo distinto del de la carga
- **WHEN** el embedder de la consulta tiene una huella distinta de la registrada en la carga
- **THEN** el modo es `lexico` y hay un aviso `model_mismatch` cuyo texto nombra ambas huellas

#### Scenario: Ninguna palabra coincide
- **WHEN** en modo léxico se busca `zzzz`
- **THEN** el resultado está vacío y lleva el aviso `no_matches`

### Requirement: Resultados citables
Cada resultado SHALL incluir `chunk_id`, `doc_id`, `source_type`, `title`, `section`, `page`, `primary_evidence_id`, `evidence_ids`, el texto literal del fragmento, su posición final y sus posiciones en BM25 y en similitud (nulas cuando no aplican).

#### Scenario: Afirmación del reporte sobre la región con mayor caída
- **WHEN** en modo léxico se busca `región con mayor caída según el reporte comercial`
- **THEN** el primer resultado es el fragmento de `REP-01`, de `05_Reporte_Comercial`, página 1, con su texto completo y posición en similitud nula

### Requirement: Filtros
`buscar_documentos` SHALL aceptar filtros opcionales por `doc_id` y por `source_type`, aplicados antes de puntuar. Un `doc_id` o un tipo desconocido SHALL producir un error estructurado con las opciones válidas. Si los filtros válidos no dejan ningún fragmento, el resultado SHALL estar vacío y llevar el aviso `filters_empty`.

#### Scenario: Solo el reporte comercial
- **WHEN** se busca `promociones` filtrando por `doc_id = 05_Reporte_Comercial`
- **THEN** todos los resultados son de `05_Reporte_Comercial`

#### Scenario: Filtros antes de puntuar
- **WHEN** en modo híbrido se busca `promociones` filtrando por `doc_id = 05_Reporte_Comercial` con `top_k = 20`
- **THEN** hay 12 resultados y sus posiciones en similitud van de 1 a 12

#### Scenario: Documento desconocido
- **WHEN** se filtra por `doc_id = 99_Inexistente`
- **THEN** se produce un error cuyo campo es `doc_ids` y cuyas opciones son los cuatro `doc_id` cargados

#### Scenario: Tipo desconocido
- **WHEN** se filtra por `source_type = xlsx`
- **THEN** se produce un error cuyo campo es `source_types` y cuyas opciones son `pdf`, `docx` y `md`

#### Scenario: Filtros sin fragmentos
- **WHEN** se filtra por `doc_id = 05_Reporte_Comercial` y `source_type = docx`
- **THEN** el resultado está vacío y lleva el aviso `filters_empty`

### Requirement: Validación de la consulta de documentos
La consulta SHALL tener texto no vacío de como máximo el número de caracteres de `documents.yaml` (500) y un `top_k` entre 1 y el máximo de `documents.yaml`. Fuera de esos límites SHALL rechazarse indicando el campo.

#### Scenario: Consulta vacía
- **WHEN** se busca un texto vacío o solo con espacios
- **THEN** se produce un error sobre el campo `query`

#### Scenario: Consulta demasiado larga
- **WHEN** se busca un texto de 501 caracteres
- **THEN** se produce un error sobre el campo `query`

#### Scenario: top_k fuera de rango
- **WHEN** se pide `top_k = 0` o un valor mayor que el máximo configurado
- **THEN** se produce un error sobre el campo `top_k`

### Requirement: Contenido documental como evidencia
`buscar_documentos` SHALL devolver el texto de los fragmentos literalmente, con `content_kind = "evidencia_documental"`, sin interpretarlo, ejecutarlo ni dejar que cambie la consulta, los filtros, el número de resultados o el comportamiento de la herramienta.

#### Scenario: Fragmento con instrucciones dirigidas a un asistente
- **WHEN** en modo léxico se busca `nota técnica importada del proveedor externo` con `top_k = 3` en los documentos reales
- **THEN** el primer resultado es el fragmento de `OC-EXT-06`, con su texto literal y `content_kind = "evidencia_documental"`
- **AND** hay exactamente 3 resultados y los filtros son los pedidos

### Requirement: Trazabilidad de la búsqueda
La búsqueda SHALL usar el texto de la consulta con los espacios normalizados, conservando mayúsculas y tildes. El resultado SHALL incluir un `evidence_id` (`EV-` y 12 caracteres hexadecimales) derivado de la consulta normalizada (ese texto, `top_k`, filtros y modo), el `ingestion_id` de la base de documentos y la huella de `documents.yaml`; además, el `ingestion_id`, el modo y el modelo de embeddings usado.

#### Scenario: Misma búsqueda
- **WHEN** se ejecuta dos veces la misma búsqueda en el mismo modo sobre la misma carga
- **THEN** ambas tienen el mismo `evidence_id` y los mismos resultados

#### Scenario: Cambio de modo
- **WHEN** la misma búsqueda se ejecuta en modo `hibrido` y en modo `lexico`
- **THEN** los `evidence_id` son distintos

#### Scenario: Espacios y tildes
- **WHEN** se busca `Brío  en Sur` y después `Brío en Sur`, y después `brio en Sur`
- **THEN** las dos primeras tienen el mismo `evidence_id` y la tercera uno distinto

### Requirement: Acceso de solo lectura a la base de documentos
`buscar_documentos` SHALL abrir la base de documentos en solo lectura, sin acceso a archivos externos ni carga ni instalación de extensiones y con la configuración bloqueada. Si la base no existe, no tiene el esquema esperado o no tiene ninguna carga registrada, SHALL fallar con un error que indique ejecutar `make ingest-docs`.

#### Scenario: Base inexistente
- **WHEN** `DOCUMENTS_DB_PATH` apunta a un archivo que no existe
- **THEN** la herramienta falla con un error que menciona `make ingest-docs`

#### Scenario: Esquema inesperado
- **WHEN** `DOCUMENTS_DB_PATH` apunta a una base DuckDB sin la tabla de fragmentos
- **THEN** la herramienta falla con un error que menciona `make ingest-docs`

#### Scenario: Sin carga registrada
- **WHEN** la tabla de cargas de la base de documentos está vacía
- **THEN** la herramienta falla con un error que menciona `make ingest-docs`

#### Scenario: Intento de escritura
- **WHEN** se intenta ejecutar una sentencia de escritura con la conexión de la herramienta
- **THEN** DuckDB la rechaza y la base no cambia

#### Scenario: Acceso externo y configuración
- **WHEN** con esa conexión se intenta `read_csv('/etc/passwd')`, `INSTALL httpfs` o `SET enable_external_access = true`
- **THEN** las tres operaciones son rechazadas
