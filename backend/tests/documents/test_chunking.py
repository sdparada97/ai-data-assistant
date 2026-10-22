"""Requisitos: Fragmentos por sección, Títulos en el Markdown, Fragmentos por ID de evidencia,
Tablas en los fragmentos, Patrones de IDs en configuración y Metadatos de cada fragmento."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

from analyst_backend.documents.chunking import Chunk, chunk_markdown
from analyst_backend.documents.config import DocumentsConfig, load_documents_config
from analyst_backend.documents.errors import ConversionError
from analyst_backend.documents.markdown import to_markdown
from analyst_backend.documents.sources import list_documents

from .conftest import CONFIG_PATH, RAW_DIR


def _chunk_all(config: DocumentsConfig) -> list[Chunk]:
    chunks: list[Chunk] = []
    for source in list_documents(RAW_DIR, config.extensions):
        chunks.extend(chunk_markdown(to_markdown(source, config), source.doc_id, source.source_type, config)[1])
    return chunks


@pytest.fixture(scope="module")
def chunks(config: DocumentsConfig) -> list[Chunk]:
    return _chunk_all(config)


def _by_primary(chunks: list[Chunk], evidence_id: str) -> Chunk:
    matches = [chunk for chunk in chunks if chunk.primary_evidence_id == evidence_id]
    assert len(matches) == 1, evidence_id
    return matches[0]


def _md(config: DocumentsConfig, text: str, doc_id: str = "prueba") -> tuple[str, list[Chunk]]:
    return chunk_markdown(text, doc_id, "md", config)


# --- Fragmentos por sección --------------------------------------------------------------------


def test_real_documents_produce_55_chunks(chunks: list[Chunk]) -> None:
    per_document = Counter(chunk.doc_id for chunk in chunks)

    assert per_document == {
        "01_Contexto_Negocio": 4,
        "03_Investigacion_Consumidor": 18,
        "04_Observaciones_Canales": 21,
        "05_Reporte_Comercial": 12,
    }


def test_preamble_has_no_section(chunks: list[Chunk]) -> None:
    first = next(chunk for chunk in chunks if chunk.doc_id == "05_Reporte_Comercial")

    assert first.section is None
    assert first.text.startswith("Análisis: segundo trimestre 2026")


def test_no_chunk_is_only_its_heading(chunks: list[Chunk]) -> None:
    assert all(chunk.text.strip() and chunk.text.strip() != chunk.section for chunk in chunks)


def test_empty_section_is_discarded(config: DocumentsConfig) -> None:
    _, result = _md(config, "# Doc\n\n## A\n## B\n\nUn párrafo.\n")

    assert [(chunk.section, chunk.text) for chunk in result] == [("B", "Un párrafo.")]


def test_document_with_only_headings_fails(config: DocumentsConfig) -> None:
    with pytest.raises(ConversionError, match="solo_titulos"):
        _md(config, "# Título\n\n## A\n\n### B\n", doc_id="solo_titulos")


# --- Títulos en el Markdown --------------------------------------------------------------------


def test_headings_that_do_not_open_sections(config: DocumentsConfig) -> None:
    text = "## A\n\nUn párrafo.\n\n#### Detalle\n\n```\n## no es título\n```\n"

    title, result = _md(config, text, doc_id="sin_titulo")

    assert title == "sin_titulo"
    assert len(result) == 1
    assert result[0].section == "A"
    assert result[0].title == "sin_titulo"
    assert "Detalle" in result[0].text
    assert "## no es título" in result[0].text


def test_page_title_is_not_text(chunks: list[Chunk]) -> None:
    rep04 = _by_primary(chunks, "REP-04")

    assert rep04.page == 2
    assert rep04.title == "Reporte ejecutivo | Desempeño de Brío"
    assert not any("Recomendaciones y trazabilidad" in chunk.text for chunk in chunks)


# --- Fragmentos por ID de evidencia ------------------------------------------------------------


def test_report_claims_are_one_chunk_each(chunks: list[Chunk]) -> None:
    for number in range(1, 7):
        chunk = _by_primary(chunks, f"REP-0{number}")
        assert chunk.doc_id == "05_Reporte_Comercial"


def test_records_opened_by_heading_keep_their_bullets(chunks: list[Chunk]) -> None:
    for evidence_id in ("OC-SUR-01", "OC-CEN-02", "OC-NOR-03", "OC-ORI-04", "OC-OCC-05"):
        chunk = _by_primary(chunks, evidence_id)
        assert chunk.text.startswith("- ")
    assert "En 5 de 12 visitas" in _by_primary(chunks, "OC-SUR-01").text


def test_following_paragraph_stays_with_the_id(chunks: list[Chunk]) -> None:
    assert "Registro de trazabilidad: extracto del proveedor externo" in _by_primary(chunks, "OC-EXT-06").text


def test_id_without_separator_does_not_split(config: DocumentsConfig) -> None:
    _, result = _md(config, "## S\n\nREP-01 | Afirmación.\n\nSegún REP-02 la causa es otra.\n")

    assert len(result) == 1
    assert result[0].evidence_ids == ("REP-01", "REP-02")


def test_list_item_with_id_opens_a_chunk(config: DocumentsConfig) -> None:
    _, result = _md(config, "## S\n\n- **REP-01:** primera\n- REP-02 | segunda\n- tercera\n")

    assert [chunk.primary_evidence_id for chunk in result] == ["REP-01", "REP-02"]
    assert result[1].text == "- REP-02 | segunda\n- tercera"


# --- Tablas en los fragmentos ------------------------------------------------------------------


def test_field_records_are_one_chunk_per_row(chunks: list[Chunk]) -> None:
    records = [chunk for chunk in chunks if (chunk.primary_evidence_id or "").startswith("CAM-")]

    assert len(records) == 10
    assert "Región: Occidente" in _by_primary(chunks, "CAM-145").text


def test_table_ids_already_split_are_not_split_again(config: DocumentsConfig) -> None:
    text = (
        "## Afirmaciones\n\n| ID | Texto |\n| --- | --- |\n| REP-01 | Centro cae más |\n\n"
        "## Anexo\n\n| ID | Fuente |\n| --- | --- |\n| REP-01 | Tablero operativo |\n"
    )

    _, result = _md(config, text)

    rep01 = [chunk for chunk in result if chunk.primary_evidence_id == "REP-01"]
    assert len(rep01) == 1
    assert rep01[0].section == "Afirmaciones"
    annex = next(chunk for chunk in result if chunk.section == "Anexo")
    assert annex.primary_evidence_id is None
    assert "ID: REP-01 | Fuente: Tablero operativo" in annex.text


def test_table_with_repeated_id_stays_in_its_section(config: DocumentsConfig) -> None:
    text = "## S\n\n| ID | Texto |\n| --- | --- |\n| REP-01 | uno |\n| REP-01 | dos |\n"

    _, result = _md(config, text)

    assert [(chunk.section, chunk.primary_evidence_id) for chunk in result] == [("S", None)]
    assert result[0].evidence_ids == ("REP-01",)


def test_reference_index_is_a_single_chunk(chunks: list[Chunk]) -> None:
    index = [chunk for chunk in chunks if chunk.section == "8. Referencias internas de evidencia"]

    assert len(index) == 1
    assert index[0].primary_evidence_id is None
    assert "ID: INV-01 | Descripción: Percepción de precio en Sur" in index[0].text


def test_table_without_ids_stays_in_its_section(chunks: list[Chunk]) -> None:
    section = [chunk for chunk in chunks if chunk.section == "2. Lectura regional presentada al comité"]

    assert len(section) == 1
    assert "Región: Centro | Variación reportada (T2 vs. T1): -23 %" in section[0].text


# --- Patrones de IDs en configuración ----------------------------------------------------------


def test_point_of_sale_code_is_not_an_id(chunks: list[Chunk]) -> None:
    cam145 = _by_primary(chunks, "CAM-145")

    assert "OC-T-001" in cam145.text
    assert cam145.evidence_ids == ("CAM-145",)


def test_configurable_patterns(tmp_path: Path) -> None:
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["id_patterns"] = [pattern for pattern in data["id_patterns"] if not pattern.startswith("CAM")]
    path = tmp_path / "documents.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    result = [chunk for chunk in _chunk_all(load_documents_config(path)) if chunk.doc_id == "04_Observaciones_Canales"]

    detail = [chunk for chunk in result if chunk.section == "Detalle de observaciones seleccionadas"]
    assert len(detail) == 1
    assert "ID / fecha: CAM-145 2026-06-04" in detail[0].text
    assert not any(evidence_id.startswith("CAM-") for chunk in result for evidence_id in chunk.evidence_ids)


# --- Metadatos de cada fragmento ---------------------------------------------------------------


def test_report_claim_metadata(chunks: list[Chunk]) -> None:
    rep02 = _by_primary(chunks, "REP-02")

    assert rep02.doc_id == "05_Reporte_Comercial"
    assert rep02.source_type == "pdf"
    assert rep02.page == 1
    assert rep02.section == "3. Interpretación preliminar"
    assert rep02.title == "Reporte ejecutivo | Desempeño de Brío"
    assert rep02.chunk_id == "05_Reporte_Comercial:005"


def test_primary_id_only_in_heading(chunks: list[Chunk]) -> None:
    oc_sur = _by_primary(chunks, "OC-SUR-01")

    assert "OC-SUR-01" not in oc_sur.text
    assert oc_sur.evidence_ids == ("OC-SUR-01",)


def test_markdown_chunk_metadata(chunks: list[Chunk]) -> None:
    context = [chunk for chunk in chunks if chunk.doc_id == "01_Contexto_Negocio"]

    assert {chunk.source_type for chunk in context} == {"md"}
    assert {chunk.page for chunk in context} == {None}
    assert [chunk.section for chunk in context] == [
        "Situación",
        "Información disponible",
        "Diccionario de la base de ventas",
        "Convenciones de análisis",
    ]
    assert not any("**" in chunk.text for chunk in chunks)
