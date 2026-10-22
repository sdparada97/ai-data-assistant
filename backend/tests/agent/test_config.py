"""Configuración del agente (agent.yaml)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from analyst_backend.agent.config import AgentConfigError, load_agent_config

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "backend/config/agent.yaml"


def _write(tmp_path: Path, **changes: object) -> Path:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for dotted, value in changes.items():
        target = data
        *parents, leaf = dotted.split("__")
        for parent in parents:
            target = target[parent]
        if value is None:
            del target[leaf]
        else:
            target[leaf] = value
    path = tmp_path / "agent.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_real_config_loads() -> None:
    config = load_agent_config(CONFIG)

    assert config.limits.max_calls_per_tool == 3
    assert config.provider.gemini.unavailable_retries == 2
    assert "causó" in config.causal_lexicon
    assert "podría" in config.hedges


def test_temperature_by_longest_prefix(tmp_path: Path) -> None:
    path = _write(tmp_path, provider__gemini__temperature_by_prefix={"gemini-3": 1.0, "gemini-3-pro": 0.5})
    gemini = load_agent_config(path).provider.gemini

    assert gemini.temperature_for("gemini-3-flash") == 1.0
    assert gemini.temperature_for("gemini-3-pro-preview") == 0.5
    assert gemini.temperature_for("gemini-2.5-flash") == 0.0


@pytest.mark.parametrize(
    ("changes", "fragment"),
    [
        ({"limits__max_calls_per_tool": 0}, "max_calls_per_tool"),
        ({"provider__gemini__unavailable_retries": -1}, "unavailable_retries"),
        ({"hedges": []}, "hedges"),
        ({"causal_lexicon": ["  "]}, "causal_lexicon"),
        ({"out_of_scope_message": ""}, "out_of_scope_message"),
        ({"limits__docs_top_k": None}, "docs_top_k"),
        ({"extra_key": 1}, "extra_key"),
    ],
)
def test_invalid_config_is_rejected(tmp_path: Path, changes: dict[str, object], fragment: str) -> None:
    with pytest.raises(AgentConfigError, match=fragment):
        load_agent_config(_write(tmp_path, **changes))


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(AgentConfigError, match="No existe"):
        load_agent_config(tmp_path / "nada.yaml")
