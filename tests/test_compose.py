"""Requisito: Orquestación con contenedores."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCKER = shutil.which("docker")

pytestmark = pytest.mark.skipif(
    DOCKER is None, reason="Docker no está instalado: no se puede ejecutar docker compose config"
)


def _compose_config(compose_file: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    assert DOCKER is not None
    return subprocess.run(
        [DOCKER, "compose", "-f", str(compose_file), "config", "--format", "json", *extra],
        cwd=compose_file.parent,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def resolved(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    # Copia aislada: el .env del desarrollador no interviene ni se modifica.
    # --no-interpolate conserva env_file, que compose omite una vez procesado.
    workdir = tmp_path_factory.mktemp("compose")
    shutil.copy(ROOT / "docker-compose.yml", workdir / "docker-compose.yml")
    result = _compose_config(workdir / "docker-compose.yml", "--no-interpolate")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_config_is_valid_without_env_file(tmp_path: Path) -> None:
    shutil.copy(ROOT / "docker-compose.yml", tmp_path / "docker-compose.yml")
    assert not (tmp_path / ".env").exists()

    result = _compose_config(tmp_path / "docker-compose.yml")

    assert result.returncode == 0, result.stderr


def test_defines_backend_and_frontend(resolved: dict[str, Any]) -> None:
    assert set(resolved["services"]) == {"backend", "frontend"}


def test_frontend_points_to_backend_and_depends_on_it(resolved: dict[str, Any]) -> None:
    frontend = resolved["services"]["frontend"]

    assert frontend["environment"]["BACKEND_URL"] == "http://backend:8000"
    assert "backend" in frontend["depends_on"]


def test_only_backend_loads_env_file(resolved: dict[str, Any]) -> None:
    services = resolved["services"]

    assert "env_file" in services["backend"]
    assert "env_file" not in services["frontend"]
