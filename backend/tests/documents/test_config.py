"""Configuración de documentos (documents.yaml)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from analyst_backend.documents.config import load_documents_config
from analyst_backend.documents.errors import DocumentsConfigError

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "backend/config/documents.yaml"


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
    path = tmp_path / "documents.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_real_config_loads_with_fingerprint() -> None:
    config = load_documents_config(CONFIG)

    assert config.model.dimension == 384
    assert config.fingerprint == hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    assert config.extensions == (".pdf", ".docx", ".md")


def test_id_regexes_follow_configured_patterns() -> None:
    config = load_documents_config(CONFIG)

    assert config.id_regex.findall("CAM-145 en OC-T-001, INV-LIM e INV-LIM-02") == ["CAM-145", "INV-LIM", "INV-LIM-02"]
    assert config.id_start_regex.match("OC-EXT-06 | Nota")["id"] == "OC-EXT-06"
    assert config.id_start_regex.match("ENT-SUR-03: “texto”")["id"] == "ENT-SUR-03"
    assert config.id_start_regex.match("REP-01 sin separador") is None


def test_extensions_are_lowercased(tmp_path: Path) -> None:
    config = load_documents_config(_write(tmp_path, extensions=[".PDF", ".Md"]))

    assert config.extensions == (".pdf", ".md")


def test_embedding_template_renders_with_and_without_section() -> None:
    template = load_documents_config(CONFIG).embedding_template

    assert template.render("Título", "1. Sección", "texto") == "Título — 1. Sección: texto"
    assert template.render("Título", None, "texto") == "Título: texto"


@pytest.mark.parametrize(
    ("changes", "fragment"),
    [
        ({"id_patterns": ["REP-(\\d{2}"]}, "id_patterns"),
        ({"pdf__section_pattern": "(["}, "section_pattern"),
        ({"model__sha256": "abc"}, "sha256"),
        ({"model__dimension": 0}, "dimension"),
        ({"extensions": ["pdf"]}, "extensions"),
        ({"extensions": [".pdf", ".xlsx"]}, "xlsx"),
        ({"id_separators": [" "]}, "id_separators"),
        ({"embedding_template__with_section": "{title}: {text}"}, "with_section"),
        ({"embedding_template__without_section": "{title} {section} {text}"}, "without_section"),
        ({"default_top_k": 50}, "default_top_k"),
        ({"rrf_k": None}, "rrf_k"),
        ({"unknown_key": 1}, "unknown_key"),
    ],
)
def test_invalid_config_is_rejected(tmp_path: Path, changes: dict[str, object], fragment: str) -> None:
    with pytest.raises(DocumentsConfigError, match=fragment):
        load_documents_config(_write(tmp_path, **changes))


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(DocumentsConfigError, match="No existe"):
        load_documents_config(tmp_path / "nada.yaml")


def test_invalid_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "documents.yaml"
    path.write_text("extensions: [\n", encoding="utf-8")

    with pytest.raises(DocumentsConfigError, match="YAML inválido"):
        load_documents_config(path)
