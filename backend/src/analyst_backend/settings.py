"""Configuración del backend leída de variables de entorno.

Es la única capa que lee el entorno. No define valores por defecto: viven en el
`Makefile` y en `.env.example`, para que ningún nombre de archivo de datos (que
puede contener un período) quede en el código.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

INGESTION_VARIABLES = ("SALES_CSV_PATH", "DUCKDB_PATH", "SEMANTIC_LAYER_PATH", "DATA_QUALITY_PATH")


class SettingsError(RuntimeError):
    """Falta una variable de entorno obligatoria o está vacía."""


@dataclass(frozen=True)
class IngestionSettings:
    sales_csv_path: Path
    duckdb_path: Path
    semantic_layer_path: Path
    data_quality_path: Path


def _resolve(value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve()


def load_ingestion_settings(
    environ: Mapping[str, str] | None = None, base_dir: Path | None = None
) -> IngestionSettings:
    """Lee las rutas de la ingesta. Las relativas se resuelven desde ``base_dir`` (por defecto, el directorio de trabajo)."""
    env = os.environ if environ is None else environ
    missing = [name for name in INGESTION_VARIABLES if not env.get(name, "").strip()]
    if missing:
        raise SettingsError(
            "Faltan variables de entorno para la ingesta: " + ", ".join(missing)
            + ". Usa `make ingest` o defínelas como en .env.example."
        )
    base = Path.cwd() if base_dir is None else base_dir
    paths = {name: _resolve(env[name].strip(), base) for name in INGESTION_VARIABLES}
    return IngestionSettings(
        sales_csv_path=paths["SALES_CSV_PATH"],
        duckdb_path=paths["DUCKDB_PATH"],
        semantic_layer_path=paths["SEMANTIC_LAYER_PATH"],
        data_quality_path=paths["DATA_QUALITY_PATH"],
    )
