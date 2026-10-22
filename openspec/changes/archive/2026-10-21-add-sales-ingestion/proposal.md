# Proposal

## Why

El asistente necesita una base de ventas confiable sobre la que calcular cifras. El CSV de `data/raw/` tiene inconsistencias documentadas en `docs/EXPLORACION_DATOS.md` (duplicados, espacios, mayúsculas, mes inválido, valores faltantes y negativos), y las reglas para tratarlas ya fueron aprobadas una a una. Falta convertirlas en una ingesta repetible que produzca la base DuckDB y deje explícito todo lo que se corrigió, excluyó o retuvo.

## What Changes

- Ingesta determinista e idempotente del CSV de ventas a un archivo DuckDB (ruta configurable). El CSV original no se modifica y una carga fallida no deja una base a medias.
- Reglas de calidad aprobadas: DQ01, DQ03–DQ08 y DQ13 (actúan sobre los datos) y DQ11–DQ12 (solo avisan). DQ13, nueva, envía a revisión las filas con 0 unidades y venta positiva. DQ02 queda fusionada en DQ01; DQ09 y DQ10 se omiten.
- Cuatro tablas: `sales` (única fuente de cifras), `sales_review` (filas retenidas para revisión), `dq_issues` (cada actuación de una regla) e `ingestion_runs` (trazabilidad de la carga publicada). Tablas y columnas llevan descripciones para que el agente entienda el esquema.
- Catálogo de valores válidos de marca, región, canal y presentación en `semantic_layer.yaml`, creado aquí con la sección de dimensiones. El umbral de precio atípico (DQ12) vive en configuración.
- Validación final del resultado con Pandera antes de publicar la base.
- Comando `make ingest`.

## Capabilities

### New Capabilities

- `sales-ingestion`: carga del CSV a DuckDB, esquema de las tablas, atomicidad, idempotencia, cuadre de filas, trazabilidad de la carga y errores de entrada.
- `data-quality`: reglas DQ aplicadas durante la ingesta, destino de cada fila (ventas, revisión, exclusión o eliminación) y registro en `dq_issues`.

### Modified Capabilities

Ninguna. El objetivo `make ingest` se añade al `Makefile` sin cambiar los requisitos de `project-layout`.

## Impact

- **Código nuevo:** módulo de ingesta en `backend/src/analyst_backend/` y sus pruebas en `backend/tests/`.
- **Configuración nueva:** `backend/config/semantic_layer.yaml` (dimensiones y valores válidos) y `backend/config/data_quality.yaml` (umbral DQ12). Variables `DUCKDB_PATH` y `SALES_CSV_PATH` en `.env.example`.
- **Dependencias del backend (versión fija):** duckdb 1.5.6, pandas 3.0.6, pandera 0.34.1, pyyaml 6.0.3. DuckDB 2.0.0 se descarta por ahora: aún no publica paquetes para Python 3.14.
- **Datos generados:** `data/processed/analytics.duckdb`, ignorado por git.
- **Documentación:** `docs/architecture.md` registra el modelo de tablas y la ubicación del catálogo.

## Fuera de alcance

- Métricas, capa semántica de métricas y herramientas `consultar_metrica` y `calidad_datos` (change 3).
- SQL libre del agente y endurecimiento de la conexión de lectura (change 7).
- Archivo de decisiones humanas sobre `sales_review`: las filas retenidas siguen fuera hasta que se corrija el CSV (posible change futuro).
- Ingesta de documentos (change 4).
- Montar la base en los contenedores Docker.
- Imputación de valores faltantes y política de devoluciones.
- Varios CSV de ventas a la vez y cargas incrementales: se carga un solo archivo y la base se reconstruye completa en cada carga.
