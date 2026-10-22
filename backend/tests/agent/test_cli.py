"""Comando de consulta (`make ask`) y construcción de las dependencias desde settings."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from analyst_backend.agent.__main__ import main, render
from analyst_backend.agent.models import AgentResponse, Claim, ToolRun, Trace
from analyst_backend.agent.service import CONFIGURATION_ERROR, answer_question, build_deps
from analyst_backend.settings import SettingsError

ROOT = Path(__file__).resolve().parents[3]
MAKE = shutil.which("make")


@pytest.mark.skipif(MAKE is None, reason="make no está instalado")
def test_empty_key() -> None:
    env = {**os.environ, "LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-de-prueba", "GEMINI_API_KEY": ""}
    assert MAKE is not None

    result = subprocess.run([MAKE, "ask", "Q=hola", "ENV_FILE=/dev/null"], cwd=ROOT, env=env,
                            capture_output=True, text=True)

    assert result.returncode != 0
    assert "GEMINI_API_KEY" in result.stdout + result.stderr


def test_llm_configuration_is_checked_before_the_paths(tmp_path: Path) -> None:
    environ = {"LLM_PROVIDER": "ollama", "DUCKDB_PATH": str(tmp_path / "no-existe.duckdb")}

    with pytest.raises(SettingsError, match="LLM_PROVIDER"):
        build_deps(environ, tmp_path)


def test_invalid_configuration_is_a_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "")

    response = answer_question("hola")

    assert (response.status, response.error_code) == ("error", CONFIGURATION_ERROR)
    assert "LLM_PROVIDER" in (response.message or "")
    assert response.trace.llm_calls == 0 and response.facts == []


def test_question_is_required(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("Q", raising=False)

    assert main([]) == 1
    assert "make ask" in capsys.readouterr().err


def test_render_sections_evidence_and_warnings() -> None:
    response = AgentResponse(
        status="ok",
        facts=[Claim(statement="Sur cayó 30,27 %", evidence=["EV-000000000001"])],
        hypotheses=[Claim(statement="Podría deberse a faltantes", evidence=["INV-02"])],
        insufficient=["Se retiró 1 afirmación no verificada"],
        warnings=["El período 2025-T1 no tiene datos en la base"],
        trace=Trace(question="q", model="m", llm_calls=2, llm_attempts=2,
                    tool_runs=[ToolRun(tool="consultar_metrica", args={}, status="ok", round=1,
                                       evidence_id="EV-000000000001")]),
    )

    text = render(response)

    for expected in ("Estado: ok", "Hechos:", "Sur cayó 30,27 % [EV-000000000001]", "Hipótesis:",
                     "Información insuficiente:", "Avisos:", "El período 2025-T1", "2 llamadas al LLM",
                     "consultar_metrica (ok, EV-000000000001)"):
        assert expected in text
