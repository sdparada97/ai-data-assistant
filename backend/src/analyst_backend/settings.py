"""Configuración del backend leída de variables de entorno.

Es la única capa que lee el entorno. No define valores por defecto: viven en el
`Makefile` y en `.env.example`, para que ningún nombre de archivo de datos (que
puede contener un período) quede en el código.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from pydantic import SecretStr

INGESTION_VARIABLES = ("SALES_CSV_PATH", "DUCKDB_PATH", "SEMANTIC_LAYER_PATH", "DATA_QUALITY_PATH")
ANALYTICS_VARIABLES = ("DUCKDB_PATH", "SEMANTIC_LAYER_PATH")
DOCUMENTS_VARIABLES = ("DOCUMENTS_DIR", "DOCUMENTS_DB_PATH", "DOCUMENTS_CONFIG_PATH", "MODELS_CACHE_DIR")
MODELS_VARIABLES = ("DOCUMENTS_CONFIG_PATH", "MODELS_CACHE_DIR")
AGENT_VARIABLES = (
    "AGENT_CONFIG_PATH",
    "DUCKDB_PATH",
    "SEMANTIC_LAYER_PATH",
    "DOCUMENTS_DB_PATH",
    "DOCUMENTS_CONFIG_PATH",
    "MODELS_CACHE_DIR",
)
SUPPORTED_LLM_PROVIDERS = ("gemini",)
LLM_PROVIDER_VARIABLES = {"gemini": ("GEMINI_MODEL", "GEMINI_API_KEY")}


class SettingsError(RuntimeError):
    """Falta una variable de entorno obligatoria o está vacía."""


@dataclass(frozen=True)
class IngestionSettings:
    sales_csv_path: Path
    duckdb_path: Path
    semantic_layer_path: Path
    data_quality_path: Path


def _resolve(value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve()


@dataclass(frozen=True)
class AnalyticsSettings:
    duckdb_path: Path
    semantic_layer_path: Path


@dataclass(frozen=True)
class DocumentsSettings:
    documents_dir: Path
    documents_db_path: Path
    documents_config_path: Path
    models_cache_dir: Path


def _read_paths(
    names: tuple[str, ...], purpose: str, environ: Mapping[str, str] | None, base_dir: Path | None
) -> dict[str, Path]:
    env = os.environ if environ is None else environ
    missing = [name for name in names if not env.get(name, "").strip()]
    if missing:
        raise SettingsError(
            f"Faltan variables de entorno para {purpose}: " + ", ".join(missing)
            + ". Defínelas como en .env.example."
        )
    base = Path.cwd() if base_dir is None else base_dir
    return {name: _resolve(env[name].strip(), base) for name in names}


def load_ingestion_settings(
    environ: Mapping[str, str] | None = None, base_dir: Path | None = None
) -> IngestionSettings:
    """Lee las rutas de la ingesta. Las relativas se resuelven desde ``base_dir`` (por defecto, el directorio de trabajo)."""
    paths = _read_paths(INGESTION_VARIABLES, "la ingesta", environ, base_dir)
    return IngestionSettings(
        sales_csv_path=paths["SALES_CSV_PATH"],
        duckdb_path=paths["DUCKDB_PATH"],
        semantic_layer_path=paths["SEMANTIC_LAYER_PATH"],
        data_quality_path=paths["DATA_QUALITY_PATH"],
    )


def load_analytics_settings(
    environ: Mapping[str, str] | None = None, base_dir: Path | None = None
) -> AnalyticsSettings:
    """Lee las rutas que necesitan las herramientas de consulta."""
    paths = _read_paths(ANALYTICS_VARIABLES, "las consultas", environ, base_dir)
    return AnalyticsSettings(duckdb_path=paths["DUCKDB_PATH"], semantic_layer_path=paths["SEMANTIC_LAYER_PATH"])


def load_documents_settings(
    environ: Mapping[str, str] | None = None, base_dir: Path | None = None
) -> DocumentsSettings:
    """Lee las rutas de la ingesta y la búsqueda de documentos y de la caché de modelos."""
    paths = _read_paths(DOCUMENTS_VARIABLES, "los documentos", environ, base_dir)
    return DocumentsSettings(
        documents_dir=paths["DOCUMENTS_DIR"],
        documents_db_path=paths["DOCUMENTS_DB_PATH"],
        documents_config_path=paths["DOCUMENTS_CONFIG_PATH"],
        models_cache_dir=paths["MODELS_CACHE_DIR"],
    )


@dataclass(frozen=True)
class ModelsSettings:
    documents_config_path: Path
    models_cache_dir: Path


def load_models_settings(environ: Mapping[str, str] | None = None, base_dir: Path | None = None) -> ModelsSettings:
    """Lee las rutas que necesita `make models`: la configuración de documentos y la caché."""
    paths = _read_paths(MODELS_VARIABLES, "la descarga del modelo", environ, base_dir)
    return ModelsSettings(
        documents_config_path=paths["DOCUMENTS_CONFIG_PATH"], models_cache_dir=paths["MODELS_CACHE_DIR"]
    )


@dataclass(frozen=True)
class AgentSettings:
    agent_config_path: Path
    duckdb_path: Path
    semantic_layer_path: Path
    documents_db_path: Path
    documents_config_path: Path
    models_cache_dir: Path


def load_agent_settings(environ: Mapping[str, str] | None = None, base_dir: Path | None = None) -> AgentSettings:
    """Rutas que necesita el agente: su configuración, la base de ventas, la de documentos y la caché de modelos."""
    paths = _read_paths(AGENT_VARIABLES, "el agente", environ, base_dir)
    return AgentSettings(
        agent_config_path=paths["AGENT_CONFIG_PATH"],
        duckdb_path=paths["DUCKDB_PATH"],
        semantic_layer_path=paths["SEMANTIC_LAYER_PATH"],
        documents_db_path=paths["DOCUMENTS_DB_PATH"],
        documents_config_path=paths["DOCUMENTS_CONFIG_PATH"],
        models_cache_dir=paths["MODELS_CACHE_DIR"],
    )


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: SecretStr  # nunca se imprime: SecretStr se muestra como '**********'


def load_llm_settings(environ: Mapping[str, str] | None = None) -> LLMSettings:
    """Proveedor, modelo y clave del LLM. Los errores nombran la variable, nunca su valor si es secreta."""
    env = os.environ if environ is None else environ
    provider = env.get("LLM_PROVIDER", "").strip()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        received = f"'{provider}'" if provider else "(vacía)"
        raise SettingsError(
            f"LLM_PROVIDER no es válida: {received}. Proveedores admitidos: {', '.join(SUPPORTED_LLM_PROVIDERS)}."
        )
    model_var, key_var = LLM_PROVIDER_VARIABLES[provider]
    missing = [name for name in (model_var, key_var) if not env.get(name, "").strip()]
    if missing:
        raise SettingsError(
            f"Faltan variables de entorno para el proveedor {provider}: {', '.join(missing)}. Defínelas en .env."
        )
    return LLMSettings(provider=provider, model=env[model_var].strip(), api_key=SecretStr(env[key_var].strip()))
