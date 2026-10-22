"""Lectura y validación de la configuración de la ingesta.

- ``semantic_layer.yaml``: catálogo de valores válidos por dimensión (DQ04).
- ``data_quality.yaml``: parámetros técnicos de calidad (umbral de DQ12).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from analyst_backend.ingestion.errors import ConfigError

# Columnas del CSV que se validan contra el catálogo. Son nombres de columna, no valores de negocio.
CATALOG_DIMENSIONS = ("marca", "region", "canal", "presentacion")


@dataclass(frozen=True)
class Catalog:
    """Valores válidos por dimensión, con búsqueda sin distinguir mayúsculas."""

    values: dict[str, tuple[str, ...]]

    def canonical(self, dimension: str, value: str) -> str | None:
        """Devuelve la escritura del catálogo para ``value`` o ``None`` si no es válido."""
        for candidate in self.values[dimension]:
            if candidate.casefold() == value.casefold():
                return candidate
        return None


@dataclass(frozen=True)
class QualityConfig:
    price_deviation_threshold: float


def read_config_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise ConfigError(f"No existe el archivo de configuración: {path}")
    return path.read_bytes()


def _parse_yaml(content: bytes, path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(content.decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise ConfigError(f"YAML inválido en {path}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{path} debe contener un objeto YAML")
    return data


def load_catalog(path: Path) -> Catalog:
    return parse_catalog(read_config_bytes(path), path)


def parse_catalog(content: bytes, path: Path) -> Catalog:
    dimensions = _parse_yaml(content, path).get("dimensions")
    if not isinstance(dimensions, dict):
        raise ConfigError(f"{path}: falta la sección `dimensions`")
    values: dict[str, tuple[str, ...]] = {}
    for dimension in CATALOG_DIMENSIONS:
        entry = dimensions.get(dimension)
        raw = entry.get("values") if isinstance(entry, dict) else None
        if not isinstance(raw, list) or not raw or not all(isinstance(v, str) and v.strip() for v in raw):
            raise ConfigError(f"{path}: `dimensions.{dimension}.values` debe ser una lista de textos no vacía")
        folded = [v.casefold() for v in raw]
        repeated = sorted({v for v in raw if folded.count(v.casefold()) > 1})
        if repeated:
            raise ConfigError(
                f"{path}: `dimensions.{dimension}` tiene valores que solo difieren en mayúsculas: "
                + ", ".join(repeated)
            )
        values[dimension] = tuple(raw)
    return Catalog(values=values)


def load_quality_config(path: Path) -> QualityConfig:
    return parse_quality_config(read_config_bytes(path), path)


def parse_quality_config(content: bytes, path: Path) -> QualityConfig:
    threshold = _parse_yaml(content, path).get("price_deviation_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, int | float) or threshold <= 0:
        raise ConfigError(f"{path}: `price_deviation_threshold` debe ser un número positivo")
    return QualityConfig(price_deviation_threshold=float(threshold))
