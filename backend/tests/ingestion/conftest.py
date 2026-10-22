"""Utilidades compartidas por los tests de la ingesta."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REAL_CSV = ROOT / "data/raw/02_Ventas_2026.csv"
SEMANTIC_LAYER = ROOT / "backend/config/semantic_layer.yaml"
DATA_QUALITY = ROOT / "backend/config/data_quality.yaml"
HEADER = "registro_id,mes,marca,region,canal,punto_venta_id,presentacion,unidades,venta_neta_cop"

# Fila válida de referencia para construir CSV sintéticos (valores solo de prueba).
VALID = {
    "registro_id": "V00001",
    "mes": "2026-01",
    "marca": "Brio",
    "region": "Norte",
    "canal": "Tradicional",
    "punto_venta_id": "NO-T-001",
    "presentacion": "Individual",
    "unidades": "100",
    "venta_neta_cop": "1230000",
}

WriteCsv = Callable[..., Path]


@dataclass(frozen=True)
class Paths:
    root: Path = ROOT
    real_csv: Path = REAL_CSV
    semantic_layer: Path = SEMANTIC_LAYER
    data_quality: Path = DATA_QUALITY
    header: str = HEADER


@pytest.fixture(scope="session")
def paths() -> Paths:
    return Paths()


@pytest.fixture(scope="session")
def valid_row() -> dict[str, str]:
    return dict(VALID)


@pytest.fixture
def write_csv(tmp_path: Path) -> WriteCsv:
    """Escribe un CSV sintético. Cada fila es un dict que sobrescribe campos de ``VALID``."""

    def _write(rows: Sequence[dict[str, str]], name: str = "ventas.csv", header: str = HEADER) -> Path:
        columns = header.split(",")
        lines = [header]
        for index, overrides in enumerate(rows, start=1):
            row = {**VALID, "registro_id": f"V{index:05d}", **overrides}
            lines.append(",".join(row.get(c, "") for c in columns))
        path = tmp_path / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return _write
