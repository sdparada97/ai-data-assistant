"""Requisitos: Orquestación con contenedores, Datos del host en el backend, Tiempo de espera de la
interfaz en contenedores y Puertos solo en la máquina local."""

from __future__ import annotations

import json
import os
import re
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


# --- Configuración interpolada (copia temporal y entorno limpio) ------------------------------------

CONTAINER_PATHS = {
    "DUCKDB_PATH": "/data/processed/analytics.duckdb",
    "DOCUMENTS_DB_PATH": "/data/processed/documents.duckdb",
    "MODELS_CACHE_DIR": "/models",
    "AGENT_CONFIG_PATH": "/app/config/agent.yaml",
    "SEMANTIC_LAYER_PATH": "/app/config/semantic_layer.yaml",
    "DOCUMENTS_CONFIG_PATH": "/app/config/documents.yaml",
}


def _interpolated(workdir: Path, env_file: str | None = None, **variables: str) -> dict[str, Any]:
    """Resuelve una copia de docker-compose.yml sin heredar DOCKER_*, puertos ni BACKEND_TIMEOUT_S."""
    assert DOCKER is not None
    shutil.copy(ROOT / "docker-compose.yml", workdir / "docker-compose.yml")
    if env_file is not None:
        (workdir / ".env").write_text(env_file, encoding="utf-8")
    env = {name: os.environ[name] for name in ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONFIG") if name in os.environ}
    result = subprocess.run(
        [DOCKER, "compose", "-f", str(workdir / "docker-compose.yml"), "config", "--format", "json"],
        cwd=workdir, capture_output=True, text=True, env={**env, **variables},
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def interpolated(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    return _interpolated(tmp_path_factory.mktemp("compose-interpolado"))


def _mounts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {volume["target"]: volume for volume in config["services"]["backend"]["volumes"]}


def test_backend_mounts_host_data_read_only(interpolated: dict[str, Any]) -> None:
    mounts = _mounts(interpolated)

    assert set(mounts) == {"/data/processed", "/models"}
    assert all(mount["type"] == "bind" and mount["read_only"] for mount in mounts.values())
    assert mounts["/data/processed"]["source"].endswith("data/processed")
    assert mounts["/models"]["source"].endswith(".cache/models")


def test_backend_paths_are_fixed_even_with_env_file(tmp_path: Path) -> None:
    config = _interpolated(tmp_path, env_file="DUCKDB_PATH=otra/ruta.duckdb\n")

    environment = config["services"]["backend"]["environment"]
    assert {name: environment[name] for name in CONTAINER_PATHS} == CONTAINER_PATHS
    assert "otra/ruta.duckdb" not in json.dumps(config)


def test_backend_image_includes_configuration() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    final_stage = dockerfile.rsplit("\nFROM ", 1)[1]

    assert "COPY backend/config /app/config" in final_stage
    config_paths = ("AGENT_CONFIG_PATH", "SEMANTIC_LAYER_PATH", "DOCUMENTS_CONFIG_PATH")
    assert all(CONTAINER_PATHS[name].startswith("/app/config/") for name in config_paths)


def test_directories_passed_by_make_up(tmp_path: Path) -> None:
    make = shutil.which("make")
    if make is None:
        pytest.skip("make no está instalado")
    dry_run = subprocess.run([make, "-n", "up"], cwd=ROOT, capture_output=True, text=True)
    passed = dict(re.findall(r'(DOCKER_(?:DATA|MODELS)_DIR)="([^"]+)"', dry_run.stdout))

    config = _interpolated(tmp_path, **passed)

    assert set(passed) == {"DOCKER_DATA_DIR", "DOCKER_MODELS_DIR"}
    assert all(Path(path).is_absolute() for path in passed.values())
    mounts = _mounts(config)
    assert mounts["/data/processed"]["source"] == passed["DOCKER_DATA_DIR"]
    assert mounts["/models"]["source"] == passed["DOCKER_MODELS_DIR"]
    assert all(mount["read_only"] for mount in mounts.values())


def test_frontend_receives_backend_timeout(tmp_path: Path) -> None:
    config = _interpolated(tmp_path, BACKEND_TIMEOUT_S="600")

    assert config["services"]["frontend"]["environment"]["BACKEND_TIMEOUT_S"] == "600"


def test_ports_only_on_localhost(interpolated: dict[str, Any]) -> None:
    for service in ("backend", "frontend"):
        assert [port["host_ip"] for port in interpolated["services"][service]["ports"]] == ["127.0.0.1"]
