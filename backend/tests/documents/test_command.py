"""Requisito: Comando de ingesta de documentos (`make ingest-docs`)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from .conftest import CONFIG_PATH, ROOT

MAKE = shutil.which("make")
pytestmark = pytest.mark.skipif(MAKE is None, reason="make no está instalado")


def test_missing_directory_fails_with_its_path_even_without_model(tmp_path: Path) -> None:
    assert MAKE is not None
    missing = tmp_path / "no-existe"
    env = {
        **os.environ,
        "DOCUMENTS_DIR": str(missing),
        "DOCUMENTS_DB_PATH": str(tmp_path / "documents.duckdb"),
        "DOCUMENTS_CONFIG_PATH": str(CONFIG_PATH),
        "MODELS_CACHE_DIR": str(tmp_path / "sin-modelos"),
    }

    result = subprocess.run([MAKE, "--no-print-directory", "ingest-docs"], cwd=ROOT, env=env, capture_output=True, text=True)

    assert result.returncode != 0
    assert str(missing) in result.stdout + result.stderr
    assert not (tmp_path / "documents.duckdb").exists()
