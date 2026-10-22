"""Lectura y validación de semantic_layer.yaml y data_quality.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

from analyst_backend.ingestion.catalog import CATALOG_DIMENSIONS, load_catalog, load_quality_config
from analyst_backend.ingestion.errors import ConfigError

ROOT = Path(__file__).resolve().parents[3]


def _semantic(tmp_path: Path, region_values: str = "[Norte, Sur]", drop: str | None = None) -> Path:
    blocks = {
        "marca": "[Brio, Luma]",
        "region": region_values,
        "canal": "[Tradicional, Moderno]",
        "presentacion": "[Individual, Familiar]",
    }
    lines = ["dimensions:"]
    for name, values in blocks.items():
        if name != drop:
            lines += [f"  {name}:", f"    values: {values}"]
    path = tmp_path / "semantic_layer.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_repository_catalog_loads_all_dimensions() -> None:
    catalog = load_catalog(ROOT / "backend/config/semantic_layer.yaml")

    assert set(catalog.values) == set(CATALOG_DIMENSIONS)
    assert all(catalog.values[d] for d in CATALOG_DIMENSIONS)


def test_canonical_ignores_case(tmp_path: Path) -> None:
    catalog = load_catalog(_semantic(tmp_path))

    assert catalog.canonical("marca", "BRIO") == "Brio"
    assert catalog.canonical("region", "Caribe") is None


def test_missing_dimension_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="dimensions.canal"):
        load_catalog(_semantic(tmp_path, drop="canal"))


def test_values_differing_only_in_case_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Sur, SUR|SUR, Sur"):
        load_catalog(_semantic(tmp_path, region_values="[Sur, SUR]"))


def test_missing_file_names_the_path(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="no_existe.yaml"):
        load_catalog(tmp_path / "no_existe.yaml")


def test_repository_threshold_is_loaded() -> None:
    assert load_quality_config(ROOT / "backend/config/data_quality.yaml").price_deviation_threshold == 0.5


@pytest.mark.parametrize("value", ["0", "-1", "abc", "true"])
def test_invalid_threshold_is_rejected(tmp_path: Path, value: str) -> None:
    path = tmp_path / "data_quality.yaml"
    path.write_text(f"price_deviation_threshold: {value}\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="price_deviation_threshold"):
        load_quality_config(path)
