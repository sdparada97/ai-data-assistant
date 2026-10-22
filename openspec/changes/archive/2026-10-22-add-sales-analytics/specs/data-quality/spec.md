# Spec Delta

## MODIFIED Requirements

### Requirement: Estructura de las incidencias
Cada actuación de una regla SHALL producir una fila en `dq_issues` con `issue_id`, `registro_id`, `source_line`, `rule_code`, `issue_type`, `severity` (`correccion`, `error` o `aviso`), `column_name`, `original_value`, `new_value`, `action`, `affected_net_sales_cop`, `details` (JSON), las dimensiones normalizadas de la fila (`mes`, `marca`, `region`, `canal`, `presentacion`, `punto_venta_id`) e `ingestion_id`. Pueden ser nulos `column_name`, `original_value`, `new_value` y `details`.

#### Scenario: Columnas de dq_issues
- **WHEN** se consulta el esquema de `dq_issues` tras una carga
- **THEN** contiene exactamente esas columnas y `details` es un JSON válido o nulo en todas las filas

#### Scenario: Dimensiones de una fila excluida
- **WHEN** se carga el archivo real
- **THEN** la incidencia DQ07 de `V03997` tiene `mes = 2026-05`, `marca = Brio`, `region = Sur`, `canal = Tradicional`, `presentacion = Individual` y `punto_venta_id = SU-T-013`

#### Scenario: Dimensión normalizada
- **WHEN** se carga el archivo real
- **THEN** la incidencia DQ04 de `V00667` tiene `marca = Brio` y la DQ03 de `V02929` tiene `region = Sur`
