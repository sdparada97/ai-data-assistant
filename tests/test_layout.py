"""Requisito: Ubicación del código fuente."""

from __future__ import annotations

from pathlib import Path

import analyst_backend
import analyst_frontend

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".venv", ".git", "graphify-out", ".claude", "node_modules", "__pycache__"}
ALLOWED_TOP_DIRS = {"backend", "frontend", "tests"}
ALLOWED_ROOT_FILES = {"conftest.py"}


def _python_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if not EXCLUDED_DIRS.intersection(relative.parts[:-1]):
            files.append(relative)
    return files


def test_packages_resolve_under_their_src_directory() -> None:
    backend_file = Path(analyst_backend.__file__).resolve()
    frontend_file = Path(analyst_frontend.__file__).resolve()

    assert backend_file.is_relative_to(ROOT / "backend" / "src" / "analyst_backend")
    assert frontend_file.is_relative_to(ROOT / "frontend" / "src" / "analyst_frontend")


def test_python_files_live_in_allowed_locations() -> None:
    misplaced = [
        str(path)
        for path in _python_files()
        if path.parts[0] not in ALLOWED_TOP_DIRS
        and not (len(path.parts) == 1 and path.name in ALLOWED_ROOT_FILES)
    ]

    assert misplaced == []


def test_root_src_directory_does_not_exist() -> None:
    assert not (ROOT / "src").exists()
