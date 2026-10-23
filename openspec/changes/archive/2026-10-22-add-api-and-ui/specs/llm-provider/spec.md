# Spec Delta

## ADDED Requirements

### Requirement: Razonamiento configurable por paso
El nivel de razonamiento del modelo SHALL configurarse en `agent.yaml` por prefijo del modelo (el prefijo más largo que coincide) y por paso: planificación y corrección por un lado, síntesis por otro. Los valores admitidos son `minimal`, `low`, `medium` y `high`. Un paso sin prefijo que coincida SHALL usar el razonamiento del modelo.

#### Scenario: Gemini 3 con razonamiento bajo
- **WHEN** el modelo es `gemini-3-flash` y `agent.yaml` asigna `low` al prefijo `gemini-3` en la planificación y en la síntesis
- **THEN** las llamadas de planificación y de síntesis usan razonamiento `low`, y el modelo compartido no cambia

#### Scenario: Solo la síntesis configurada
- **WHEN** solo la síntesis tiene valor para el prefijo `gemini-3`
- **THEN** la síntesis usa `low` y la planificación no fija ningún nivel

#### Scenario: Modelo sin prefijo configurado
- **WHEN** el modelo es `gemini-2.5-flash` y solo hay valores para `gemini-3`
- **THEN** ni la planificación ni la síntesis fijan ningún nivel de razonamiento

#### Scenario: Valor no admitido
- **WHEN** `agent.yaml` asigna `maximo` a un prefijo
- **THEN** la carga de la configuración falla y el error nombra el campo
