# Spec Delta

## ADDED Requirements

### Requirement: Detalle del contraste y de la evaluación causal
El desplegable de un contraste SHALL mostrar una tabla con una fila por afirmación (enunciado, ID de evidencia, filtros, períodos, reportado, real, diferencia, primero real en un ranking y veredicto) y, aparte, las descartadas con su motivo. El de una evaluación causal SHALL mostrar la causa, su tipo, el veredicto y una tabla con una fila por criterio (criterio, resultado y detalle). Cifras y textos SHALL mostrarse tal como vienen.

#### Scenario: Tabla del contraste
- **WHEN** se despliega la evidencia del contraste de `05_Reporte_Comercial`
- **THEN** se ve una tabla con la fila de Sur (reportado −7, real −30.27, diferencia 23.27, "no coincide") y la de `REP-01` con el veredicto "falsa"

#### Scenario: Afirmación descartada
- **WHEN** el contraste trae una afirmación descartada porque `23` no aparece en su fragmento
- **THEN** el desplegable la muestra aparte con ese motivo

#### Scenario: Criterios causales
- **WHEN** se despliega una evaluación causal de "promociones de la competencia" con veredicto "no sustentada"
- **THEN** se ven la causa, el veredicto "no sustentada" y una tabla con los cinco criterios y sus resultados
