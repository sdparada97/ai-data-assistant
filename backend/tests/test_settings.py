"""Configuración de la ingesta (settings.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from analyst_backend.settings import (
    ANALYTICS_VARIABLES,
    DOCUMENTS_VARIABLES,
    INGESTION_VARIABLES,
    SettingsError,
    AGENT_VARIABLES,
    load_agent_settings,
    load_analytics_settings,
    load_llm_settings,
    load_documents_settings,
    load_ingestion_settings,
)

FULL_ENV = {
    "SALES_CSV_PATH": "data/raw/ventas.csv",
    "DUCKDB_PATH": "/tmp/x/analytics.duckdb",
    "SEMANTIC_LAYER_PATH": "backend/config/semantic_layer.yaml",
    "DATA_QUALITY_PATH": "backend/config/data_quality.yaml",
}


def test_relative_paths_resolve_from_base_dir(tmp_path: Path) -> None:
    settings = load_ingestion_settings(FULL_ENV, base_dir=tmp_path)

    assert settings.sales_csv_path == tmp_path / "data/raw/ventas.csv"
    assert settings.semantic_layer_path == tmp_path / "backend/config/semantic_layer.yaml"


def test_absolute_paths_are_kept(tmp_path: Path) -> None:
    settings = load_ingestion_settings(FULL_ENV, base_dir=tmp_path)

    assert settings.duckdb_path == Path("/tmp/x/analytics.duckdb")


@pytest.mark.parametrize("missing", INGESTION_VARIABLES)
def test_missing_variable_is_named(missing: str) -> None:
    env = {k: v for k, v in FULL_ENV.items() if k != missing}

    with pytest.raises(SettingsError, match=missing):
        load_ingestion_settings(env)


def test_blank_variable_counts_as_missing() -> None:
    with pytest.raises(SettingsError, match="DUCKDB_PATH"):
        load_ingestion_settings({**FULL_ENV, "DUCKDB_PATH": "  "})


def test_reads_process_environment_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name, value in FULL_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)

    assert load_ingestion_settings().sales_csv_path == tmp_path / "data/raw/ventas.csv"


def test_env_example_declares_every_variable() -> None:
    env_example = Path(__file__).resolve().parents[2] / ".env.example"
    declared = {line.split("=", 1)[0] for line in env_example.read_text(encoding="utf-8").splitlines() if "=" in line}

    assert set(INGESTION_VARIABLES) | set(DOCUMENTS_VARIABLES) | set(AGENT_VARIABLES) <= declared
    assert {"LLM_PROVIDER", "GEMINI_MODEL", "GEMINI_API_KEY"} <= declared
    assert not any(name.startswith("OLLAMA") for name in declared)


def test_analytics_settings_read_two_paths(tmp_path: Path) -> None:
    settings = load_analytics_settings(FULL_ENV, base_dir=tmp_path)

    assert settings.duckdb_path == Path("/tmp/x/analytics.duckdb")
    assert settings.semantic_layer_path == tmp_path / "backend/config/semantic_layer.yaml"


@pytest.mark.parametrize("missing", ANALYTICS_VARIABLES)
def test_analytics_missing_variable_is_named(missing: str) -> None:
    env = {k: v for k, v in FULL_ENV.items() if k != missing}

    with pytest.raises(SettingsError, match=missing):
        load_analytics_settings(env)


DOCUMENTS_ENV = {
    "DOCUMENTS_DIR": "data/raw",
    "DOCUMENTS_DB_PATH": "data/processed/documents.duckdb",
    "DOCUMENTS_CONFIG_PATH": "backend/config/documents.yaml",
    "MODELS_CACHE_DIR": "/var/cache/models",
}


def test_documents_settings_read_four_paths(tmp_path: Path) -> None:
    settings = load_documents_settings(DOCUMENTS_ENV, base_dir=tmp_path)

    assert settings.documents_dir == tmp_path / "data/raw"
    assert settings.documents_db_path == tmp_path / "data/processed/documents.duckdb"
    assert settings.documents_config_path == tmp_path / "backend/config/documents.yaml"
    assert settings.models_cache_dir == Path("/var/cache/models")


@pytest.mark.parametrize("missing", DOCUMENTS_VARIABLES)
def test_documents_missing_variable_is_named(missing: str) -> None:
    env = {k: v for k, v in DOCUMENTS_ENV.items() if k != missing}

    with pytest.raises(SettingsError, match=missing):
        load_documents_settings(env)


AGENT_ENV = {
    "AGENT_CONFIG_PATH": "backend/config/agent.yaml",
    "DUCKDB_PATH": "data/processed/analytics.duckdb",
    "SEMANTIC_LAYER_PATH": "backend/config/semantic_layer.yaml",
    "DOCUMENTS_DB_PATH": "data/processed/documents.duckdb",
    "DOCUMENTS_CONFIG_PATH": "backend/config/documents.yaml",
    "MODELS_CACHE_DIR": ".cache/models",
}


def test_agent_settings_read_six_paths(tmp_path: Path) -> None:
    settings = load_agent_settings(AGENT_ENV, base_dir=tmp_path)

    assert settings.agent_config_path == tmp_path / "backend/config/agent.yaml"
    assert settings.documents_db_path == tmp_path / "data/processed/documents.duckdb"


@pytest.mark.parametrize("missing", AGENT_VARIABLES)
def test_agent_missing_variable_is_named(missing: str) -> None:
    env = {k: v for k, v in AGENT_ENV.items() if k != missing}

    with pytest.raises(SettingsError, match=missing):
        load_agent_settings(env)


def test_llm_settings_keep_the_key_secret() -> None:
    settings = load_llm_settings({"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-x", "GEMINI_API_KEY": "secreto-123"})

    assert (settings.provider, settings.model) == ("gemini", "gemini-x")
    assert settings.api_key.get_secret_value() == "secreto-123"
    assert "secreto-123" not in repr(settings) and "secreto-123" not in str(settings)
