"""Requisito: Entorno Python reproducible."""

from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYPROJECTS = [ROOT / "pyproject.toml", ROOT / "backend" / "pyproject.toml", ROOT / "frontend" / "pyproject.toml"]
EXACT_PIN = re.compile(r"^[A-Za-z0-9._\-\[\],]+==[A-Za-z0-9.+!\-]+$")


def _declared_dependencies(pyproject: Path) -> list[str]:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    deps = list(data.get("project", {}).get("dependencies", []))
    for group in data.get("dependency-groups", {}).values():
        deps.extend(item for item in group if isinstance(item, str))
    return deps


def test_python_version_is_pinned() -> None:
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.14"


def test_lockfile_is_in_sync_offline() -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv no está instalado: no se puede comprobar uv.lock")
    lock = ROOT / "uv.lock"
    before = lock.read_bytes()

    result = subprocess.run(
        [uv, "lock", "--check", "--offline"], cwd=ROOT, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    assert lock.read_bytes() == before


@pytest.mark.parametrize("pyproject", PYPROJECTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_direct_dependencies_use_exact_versions(pyproject: Path) -> None:
    loose = [dep for dep in _declared_dependencies(pyproject) if not EXACT_PIN.match(dep.replace(" ", ""))]

    assert loose == []
