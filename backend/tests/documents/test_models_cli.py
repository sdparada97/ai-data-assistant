"""Requisito: Descarga del modelo (`make models`)."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from analyst_backend.documents.config import DocumentsConfig

from .conftest import CONFIG_PATH, ROOT

MAKE = shutil.which("make")
pytestmark = pytest.mark.skipif(MAKE is None, reason="make no está instalado")


def _make(target: str, cache_dir: Path) -> subprocess.CompletedProcess[str]:
    assert MAKE is not None
    env = {**os.environ, "MODELS_CACHE_DIR": str(cache_dir), "DOCUMENTS_CONFIG_PATH": str(CONFIG_PATH)}
    return subprocess.run([MAKE, "--no-print-directory", target], cwd=ROOT, env=env, capture_output=True, text=True)


def _fake_cached_model(cache_dir: Path, config: DocumentsConfig, content: bytes) -> None:
    snapshot = cache_dir / f"models--{config.model.source.replace('/', '--')}" / "snapshots" / "rev1"
    snapshot.mkdir(parents=True)
    (snapshot / config.model.file).write_bytes(content)


def test_cache_with_other_fingerprint_fails_without_downloading(tmp_path: Path, config: DocumentsConfig) -> None:
    _fake_cached_model(tmp_path, config, b"otro contenido")

    result = _make("models", tmp_path)

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert config.model.sha256 in output
    assert hashlib.sha256(b"otro contenido").hexdigest() in output
    assert "Descargando" not in output


def test_check_without_model_points_to_make_models(tmp_path: Path) -> None:
    result = _make("test-embeddings", tmp_path / "vacia")

    assert result.returncode != 0
    assert "make models" in result.stdout + result.stderr
