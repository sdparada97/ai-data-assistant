"""Requisitos: Suite de pruebas sin servicios externos, Pruebas con LLM separadas
y Evaluación reservada."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAKE = shutil.which("make")

pytestmark = pytest.mark.skipif(MAKE is None, reason="make no está instalado")

SAMPLE_TESTS = """
import pytest

@pytest.mark.llm
def test_with_llm():
    pass

def test_without_marker():
    pass
"""


def _make(*args: str) -> subprocess.CompletedProcess[str]:
    assert MAKE is not None
    return subprocess.run([MAKE, *args], cwd=ROOT, capture_output=True, text=True)


def _marker_filter(target: str) -> str:
    """Extrae el filtro ``-m`` que usa un objetivo del Makefile (sin ejecutarlo)."""
    dry_run = _make("-n", target)
    match = re.search(r'pytest -m "([^"]+)"', dry_run.stdout)
    assert match, dry_run.stdout
    return match.group(1)


def _collect_sample(pytester: pytest.Pytester, marker_filter: str) -> list[str]:
    pytester.makeini("[pytest]\nmarkers =\n    llm: prueba con LLM real\n")
    pytester.makepyfile(test_sample=SAMPLE_TESTS)
    result = pytester.runpytest("--collect-only", "-q", "-m", marker_filter)
    return [line for line in result.outlines if "::" in line]


# --- Suite de pruebas sin servicios externos ---------------------------------


def test_default_filter_collects_from_all_three_locations() -> None:
    marker_filter = _marker_filter("test")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-m", marker_filter],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    node_ids = [line for line in result.stdout.splitlines() if "::" in line]
    for location in ("backend/tests/", "frontend/tests/", "tests/"):
        assert any(node_id.startswith(location) for node_id in node_ids), location


def test_default_filter_excludes_llm_tests(pytester: pytest.Pytester) -> None:
    collected = _collect_sample(pytester, _marker_filter("test"))

    assert collected == ["test_sample.py::test_without_marker"]


# --- Pruebas con LLM separadas -----------------------------------------------


def test_make_test_llm_succeeds_without_llm_tests() -> None:
    result = _make("test-llm")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "No hay pruebas llm" in result.stdout


def test_llm_filter_collects_only_marked_tests(pytester: pytest.Pytester) -> None:
    collected = _collect_sample(pytester, _marker_filter("test-llm"))

    assert collected == ["test_sample.py::test_with_llm"]


# --- Evaluación reservada ----------------------------------------------------


def test_make_eval_fails_explicitly() -> None:
    result = _make("eval")

    assert result.returncode != 0
    assert "add-evaluation-suite" in result.stdout + result.stderr
