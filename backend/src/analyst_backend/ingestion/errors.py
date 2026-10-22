"""Errores de la ingesta. Todos detienen la carga sin publicar la base."""

from __future__ import annotations


class IngestionError(RuntimeError):
    """Base de los errores que impiden publicar la base."""


class ConfigError(IngestionError):
    """Configuración (YAML) ausente o inválida."""


class InputError(IngestionError):
    """El CSV no existe, no es UTF-8 o no tiene la forma esperada."""


class ValidationFailedError(IngestionError):
    """Los datos destinados a `sales` no cumplen el esquema final."""


class ReconciliationError(IngestionError):
    """Las filas por destino no suman las filas leídas."""
