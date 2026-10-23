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

    assert config.limits.max_calls_per_tool == 5
    assert config.provider.gemini.unavailable_retries == 2
    assert config.provider.gemini.timeout_s == 240
    assert config.provider.gemini.synthesis_reasoning_for("gemini-3-flash") == "low"
    assert config.provider.gemini.synthesis_reasoning_for("gemini-2.5-flash") is None
    assert config.provider.gemini.plan_reasoning_for("gemini-3-flash") == "low"
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


def test_synthesis_reasoning_by_longest_prefix(tmp_path: Path) -> None:
    path = _write(tmp_path, provider__gemini__synthesis_reasoning_by_prefix={"gemini-3": "low", "gemini-3-pro": "medium"})
    gemini = load_agent_config(path).provider.gemini

    assert gemini.synthesis_reasoning_for("gemini-3-pro-preview") == "medium"
    assert gemini.synthesis_reasoning_for("gemini-3-flash") == "low"
    assert gemini.synthesis_reasoning_for("otro-modelo") is None


def test_plan_reasoning_by_longest_prefix(tmp_path: Path) -> None:
    path = _write(tmp_path, provider__gemini__plan_reasoning_by_prefix={"gemini-3": "low", "gemini-3-pro": "high"})
    gemini = load_agent_config(path).provider.gemini

    assert gemini.plan_reasoning_for("gemini-3-pro-preview") == "high"
    assert gemini.plan_reasoning_for("gemini-3-flash") == "low"
    assert gemini.plan_reasoning_for("otro-modelo") is None


@pytest.mark.parametrize("field", ["plan_reasoning_by_prefix", "synthesis_reasoning_by_prefix"])
def test_invalid_reasoning_is_rejected(tmp_path: Path, field: str) -> None:
    path = _write(tmp_path, **{f"provider__gemini__{field}": {"gemini-3": "maximo"}})

    with pytest.raises(AgentConfigError, match=field):
        load_agent_config(path)


# --- Contraste, causalidad e "información insuficiente" (change add-contrast-and-causal-analysis) ---


def test_contrast_and_causal_sections_load() -> None:
    config = load_agent_config(CONFIG)

    assert str(config.contrast.approx_pp) == "1.0" and config.contrast.max_claims == 30
    assert "contraccion" in config.contrast.direction_words["contraccion"]
    assert str(config.causal.step_share) == "0.8" and config.causal.search_top_k == 8
    assert config.causal.open_dimensions == ("punto_venta_id",)
    assert set(config.causal.cause_kind_examples) == {"competencia", "disponibilidad", "metrica_propia"}
    assert config.limits.max_calls_by_tool == {"contrastar_afirmaciones": 1, "evaluar_causalidad": 1}
    assert "faltan" in config.absence_markers and config.metric_synonyms["ventas"] == "venta_neta"


@pytest.mark.parametrize(("change", "field"), [
    ({"contrast__approx_pp": 0}, "approx_pp"),
    ({"contrast__direction_words": {"contraccion": ["cae"]}}, "direction_words"),
    ({"causal__step_share": 1.5}, "step_share"),
    ({"causal__cause_kind_examples": {"competencia": ["x"]}}, "cause_kind_examples"),
    ({"limits__max_calls_by_tool": {"contrastar_afirmaciones": 0}}, "max_calls_by_tool"),
    ({"absence_markers": []}, "absence_markers"),
])
def test_invalid_contrast_and_causal_values(tmp_path: Path, change: dict[str, object], field: str) -> None:
    path = _write(tmp_path, **change)

    with pytest.raises(AgentConfigError, match=field):
        load_agent_config(path)


def test_extraction_tools_default_to_one(tmp_path: Path) -> None:
    config = load_agent_config(_write(tmp_path, limits__max_calls_by_tool=None))

    assert config.limits.max_calls_by_tool == {"contrastar_afirmaciones": 1, "evaluar_causalidad": 1}


def test_unknown_tool_in_the_maximums(tmp_path: Path) -> None:
    path = _write(tmp_path, limits__max_calls_by_tool={"contrastar_afirmacion": 2})

    with pytest.raises(AgentConfigError, match="herramientas desconocidas: contrastar_afirmacion"):
        load_agent_config(path)


def test_partial_maximums_keep_the_extraction_default(tmp_path: Path) -> None:
    config = load_agent_config(_write(tmp_path, limits__max_calls_by_tool={"consultar_metrica": 2}))

    assert config.limits.max_calls_by_tool == {"contrastar_afirmaciones": 1, "evaluar_causalidad": 1,
                                               "consultar_metrica": 2}
