# Spec Delta

## Purpose

Describe en configuración, y no en código, qué métricas, dimensiones, alias y períodos puede pedir el asistente, para que toda consulta de cifras se construya de forma determinista y verificable a partir de definiciones de negocio explícitas.

## ADDED Requirements

### Requirement: Métricas definidas en configuración
`semantic_layer.yaml` SHALL definir en `metrics` cada métrica con `description`, `unit` y `decimals`, y de uno de dos tipos: agregada (`expression` sobre columnas de `sales`) o cociente (`ratio` con `numerator` y `denominator`, que son métricas agregadas). La carga SHALL validar ambos tipos y fallar con un error que nombre la métrica inválida.

#### Scenario: Métricas del repositorio
- **WHEN** se carga el `semantic_layer.yaml` del repositorio
- **THEN** `venta_neta`, `unidades` y `registros` son agregadas, `precio_efectivo` es el cociente de `venta_neta` entre `unidades`, y todas tienen descripción, unidad y decimales

#### Scenario: Cociente con una métrica inexistente
- **WHEN** una métrica de prueba es `ratio` con `denominator: margen`
- **THEN** la carga falla con un error que nombra `margen`

### Requirement: Expresiones de métricas seguras
Una `expression` SHALL contener solo las funciones `SUM` y `COUNT`, columnas de `sales`, números, paréntesis, comas, `*` y los operadores `+ - * /`. Toda columna SHALL aparecer dentro de una función de agregación. SHALL rechazarse cualquier otra palabra, `;` y los comentarios SQL (`--`, `/*`).

#### Scenario: Sentencia no permitida
- **WHEN** una métrica de prueba tiene `expression: "SUM(unidades); DROP TABLE sales"`
- **THEN** la carga falla con un error que nombra esa métrica

#### Scenario: Comentario SQL
- **WHEN** una métrica de prueba tiene `expression: "SUM(unidades) /*"`
- **THEN** la carga falla con un error que nombra esa métrica

#### Scenario: Columna inexistente
- **WHEN** una métrica de prueba tiene `expression: "SUM(descuento)"`
- **THEN** la carga falla con un error que nombra `descuento`

#### Scenario: Columna fuera de una agregación
- **WHEN** una métrica de prueba tiene `expression: "unidades * 2"`
- **THEN** la carga falla con un error que nombra esa métrica

### Requirement: Dimensiones consultables
La capa semántica SHALL exponer como dimensiones `marca`, `region`, `canal`, `presentacion` (con catálogo de valores válidos), `punto_venta_id` (abierta, sin catálogo) y `mes` (dimensión de tiempo, solo para agrupar). Ninguna otra columna SHALL poder usarse para filtrar o agrupar.

#### Scenario: Dimensiones del repositorio
- **WHEN** se carga el `semantic_layer.yaml` del repositorio
- **THEN** las dimensiones consultables son exactamente `marca`, `region`, `canal`, `presentacion`, `punto_venta_id` y `mes`

#### Scenario: Columna que no es dimensión
- **WHEN** se pide agrupar por `unidades`
- **THEN** se produce un error que lista las dimensiones consultables

### Requirement: Alias y escritura de los valores
Cada dimensión con catálogo SHALL aceptar sus valores sin distinguir mayúsculas y sus alias declarados en `aliases`, y SHALL devolver la escritura del catálogo. Un alias que apunte a un valor fuera del catálogo SHALL impedir la carga.

#### Scenario: Alias de la marca
- **WHEN** se resuelve el valor `Brío` de la dimensión `marca`
- **THEN** el resultado es `Brio`

#### Scenario: Mayúsculas
- **WHEN** se resuelve el valor `sur` de la dimensión `region`
- **THEN** el resultado es `Sur`

#### Scenario: Valor desconocido
- **WHEN** se resuelve el valor `Caribe` de la dimensión `region`
- **THEN** se produce un error que lista los valores válidos de `region`

#### Scenario: Alias inválido
- **WHEN** un `semantic_layer.yaml` de prueba declara el alias `Bryo: Brioo` en `marca`
- **THEN** la carga falla con un error que nombra `Brioo`

### Requirement: Expresiones de período
Un período SHALL expresarse como `AAAA` (año), `AAAA-S1` o `AAAA-S2` (semestre), `AAAA-T1` a `AAAA-T4` (trimestre de calendario) o `AAAA-MM` (mes), y SHALL resolverse por código a la lista ordenada de meses `AAAA-MM` que contiene. Cualquier otra forma SHALL producir un error que indique las formas válidas.

#### Scenario: Trimestre
- **WHEN** se resuelve `2026-T1`
- **THEN** el resultado es `2026-01`, `2026-02` y `2026-03`

#### Scenario: Semestre
- **WHEN** se resuelve `2026-S1`
- **THEN** el resultado son los meses de `2026-01` a `2026-06`

#### Scenario: Año y mes
- **WHEN** se resuelven `2026` y `2026-05`
- **THEN** los resultados son los 12 meses de 2026 y solo `2026-05`

#### Scenario: Formas inválidas
- **WHEN** se resuelven `2026-T5`, `T1`, `2026-13` o `primer trimestre`
- **THEN** cada uno produce un error que indica las formas válidas
