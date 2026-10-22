"""Rutas y configuración compartidas por las pruebas de documentos."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from analyst_backend.documents.config import DocumentsConfig, load_documents_config

if TYPE_CHECKING:
    from analyst_backend.documents.embeddings import FakeEmbedder
    from analyst_backend.documents.ingest import DocumentsSummary
    from analyst_backend.settings import DocumentsSettings

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data/raw"
CONFIG_PATH = ROOT / "backend/config/documents.yaml"


@pytest.fixture(scope="session")
def config() -> DocumentsConfig:
    return load_documents_config(CONFIG_PATH)


# Embedder de prueba y una configuración que lo declara como modelo esperado.
FAKE_MODEL = {"name": "pruebas/fake-embedder", "sha256": "f" * 64, "dimension": 384}


def fake_embedder() -> "FakeEmbedder":
    from analyst_backend.documents.embeddings import FakeEmbedder

    return FakeEmbedder(FAKE_MODEL["name"], FAKE_MODEL["sha256"], FAKE_MODEL["dimension"])


def write_config(directory: Path, **model: object) -> Path:
    """Copia de documents.yaml con el modelo del embedder de prueba (o los valores dados)."""
    import yaml

    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["model"].update({**FAKE_MODEL, **model})
    path = directory / "documents.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture(scope="session")
def fake_config_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_config(tmp_path_factory.mktemp("config"))


@pytest.fixture(scope="session")
def fake_config(fake_config_path: Path) -> DocumentsConfig:
    return load_documents_config(fake_config_path)


def documents_settings(
    db_path: Path, config_path: Path, documents_dir: Path = RAW_DIR, models_dir: Path | None = None
) -> "DocumentsSettings":
    from analyst_backend.settings import DocumentsSettings

    return DocumentsSettings(documents_dir, db_path, config_path, models_dir or db_path.parent / "sin-modelos")


@pytest.fixture(scope="session")
def fake_db(tmp_path_factory: pytest.TempPathFactory, fake_config_path: Path) -> "DocumentsSummary":
    """Base de documentos real (data/raw) cargada con el embedder de prueba."""
    from analyst_backend.documents.ingest import ingest_documents

    db_path = tmp_path_factory.mktemp("documents") / "documents.duckdb"
    return ingest_documents(documents_settings(db_path, fake_config_path), fake_embedder())


@pytest.fixture(scope="session")
def config_path_real() -> Path:
    return CONFIG_PATH
