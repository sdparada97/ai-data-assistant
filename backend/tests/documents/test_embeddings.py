"""Requisito: Embeddings de los fragmentos (comprobación del embedder y texto embebido)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import (
    FakeEmbedder,
    FastEmbedEmbedder,
    cached_model_file,
    check_embedder,
    embedding_text,
)
from analyst_backend.documents.errors import EmbedderError

from .conftest import FAKE_MODEL, fake_embedder


def test_embedding_text_uses_title_and_section(config: DocumentsConfig) -> None:
    template = config.embedding_template

    assert embedding_text(template, "Reporte", "3. Interpretación", "REP-02 | x") == "Reporte — 3. Interpretación: REP-02 | x"
    assert embedding_text(template, "Reporte", None, "Análisis") == "Reporte: Análisis"


def test_fake_embedder_matches_its_config(fake_config: DocumentsConfig) -> None:
    check_embedder(fake_embedder(), fake_config.model)


def test_missing_model_in_cache(tmp_path: Path, config: DocumentsConfig) -> None:
    embedder = FastEmbedEmbedder(config.model, tmp_path / "vacia")

    with pytest.raises(EmbedderError) as error:
        check_embedder(embedder, config.model)

    assert "make models" in str(error.value)
    assert "MODELS_CACHE_DIR" in str(error.value)


def test_different_fingerprint_shows_both(fake_config: DocumentsConfig) -> None:
    other = FakeEmbedder(FAKE_MODEL["name"], "a" * 64, FAKE_MODEL["dimension"])

    with pytest.raises(EmbedderError) as error:
        check_embedder(other, fake_config.model)

    assert "f" * 64 in str(error.value)
    assert "a" * 64 in str(error.value)


def test_different_dimension_shows_both(fake_config: DocumentsConfig) -> None:
    other = FakeEmbedder(FAKE_MODEL["name"], FAKE_MODEL["sha256"], 128)

    with pytest.raises(EmbedderError, match=r"esperada 384, encontrada 128"):
        check_embedder(other, fake_config.model)


def test_different_model_name(fake_config: DocumentsConfig) -> None:
    with pytest.raises(EmbedderError, match="otro/modelo"):
        check_embedder(FakeEmbedder("otro/modelo", FAKE_MODEL["sha256"], 384), fake_config.model)


def test_fingerprint_reads_the_cached_file(tmp_path: Path, config: DocumentsConfig) -> None:
    snapshot = tmp_path / f"models--{config.model.source.replace('/', '--')}" / "snapshots" / "rev1"
    snapshot.mkdir(parents=True)
    (snapshot / config.model.file).write_bytes(b"contenido")

    embedder = FastEmbedEmbedder(config.model, tmp_path)

    assert cached_model_file(config.model, tmp_path) == snapshot / config.model.file
    assert embedder.fingerprint() == hashlib.sha256(b"contenido").hexdigest()
    with pytest.raises(EmbedderError, match="Huella del modelo distinta"):
        check_embedder(embedder, config.model)
