"""Base de prueba para las herramientas: la ingesta real en un directorio temporal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from analyst_backend.analytics.semantic import SemanticLayer, load_semantic_layer
from analyst_backend.ingestion.pipeline import ingest
from analyst_backend.settings import IngestionSettings

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class RealDatabase:
    path: Path
    ingestion_id: str
    semantic_layer_path: Path


@pytest.fixture(scope="session")
def real_db(tmp_path_factory: pytest.TempPathFactory) -> RealDatabase:
    db = tmp_path_factory.mktemp("analytics") / "analytics.duckdb"
    semantic = ROOT / "backend/config/semantic_layer.yaml"
    summary = ingest(
        IngestionSettings(ROOT / "data/raw/02_Ventas_2026.csv", db, semantic, ROOT / "backend/config/data_quality.yaml")
    )
    return RealDatabase(path=db, ingestion_id=summary.ingestion_id, semantic_layer_path=semantic)


@pytest.fixture(scope="session")
def layer(real_db: RealDatabase) -> SemanticLayer:
    return load_semantic_layer(real_db.semantic_layer_path)
