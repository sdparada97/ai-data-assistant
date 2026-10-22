"""Requisito: Documentos a cargar."""

from __future__ import annotations

from pathlib import Path

import pytest

from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.errors import SourceError
from analyst_backend.documents.sources import list_documents

from .conftest import RAW_DIR


def test_real_directory_loads_the_four_documents(config: DocumentsConfig) -> None:
    sources = list_documents(RAW_DIR, config.extensions)

    assert [s.doc_id for s in sources] == [
        "01_Contexto_Negocio",
        "03_Investigacion_Consumidor",
        "04_Observaciones_Canales",
        "05_Reporte_Comercial",
    ]
    assert [s.source_type for s in sources] == ["md", "pdf", "docx", "pdf"]
    assert "02_Ventas_2026" not in {s.doc_id for s in sources}


def test_ignored_files(tmp_path: Path, config: DocumentsConfig) -> None:
    for name in ("informe.PDF", ".oculto.md", "~$notas.docx", "datos.csv"):
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "otro.pdf").write_bytes(b"x")

    sources = list_documents(tmp_path, config.extensions)

    assert [(s.doc_id, s.source_type) for s in sources] == [("informe", "pdf")]


def test_duplicated_doc_id_is_rejected(tmp_path: Path, config: DocumentsConfig) -> None:
    (tmp_path / "informe.pdf").write_bytes(b"x")
    (tmp_path / "informe.md").write_text("# x\n", encoding="utf-8")

    with pytest.raises(SourceError, match="informe"):
        list_documents(tmp_path, config.extensions)


def test_directory_without_documents(tmp_path: Path, config: DocumentsConfig) -> None:
    (tmp_path / "ventas.csv").write_text("a,b\n", encoding="utf-8")

    with pytest.raises(SourceError, match="No hay documentos que cargar"):
        list_documents(tmp_path, config.extensions)


def test_missing_directory_names_the_path(tmp_path: Path, config: DocumentsConfig) -> None:
    missing = tmp_path / "no-existe"

    with pytest.raises(SourceError, match=str(missing)):
        list_documents(missing, config.extensions)
