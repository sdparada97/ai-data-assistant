"""Requisitos de document-retrieval: validación, solo lectura, búsqueda híbrida, normalización,
degradación a BM25, resultados citables, filtros, contenido como evidencia y trazabilidad."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import duckdb
import pytest
from pydantic import ValidationError

from analyst_backend.analytics.database import DatabaseError
from analyst_backend.analytics.models import QueryError
from analyst_backend.documents.config import DocumentsConfig, load_documents_config
from analyst_backend.documents.embeddings import Embedder, FailingEmbedder, FakeEmbedder, FastEmbedEmbedder
from analyst_backend.documents.errors import EmbedderError
from analyst_backend.documents.ingest import DocumentsSummary, ingest_documents
from analyst_backend.documents.models import CONTENT_KIND, DocumentQuery, DocumentResult
from analyst_backend.documents.retrieval import buscar_documentos, open_documents_db, rank_positions, rrf_fuse

from .conftest import CONFIG_PATH, FAKE_MODEL, ROOT, documents_settings, fake_embedder


def _query(config: DocumentsConfig, **data: Any) -> DocumentQuery:
    return DocumentQuery.model_validate(data, context={"config": config})


def _error_fields(error: ValidationError) -> set[str]:
    return {str(item["loc"][0]) for item in error.errors()}


# --- Validación de la consulta de documentos ---------------------------------------------------


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_empty_query_is_rejected(config: DocumentsConfig, text: str) -> None:
    with pytest.raises(ValidationError) as error:
        _query(config, query=text)

    assert _error_fields(error.value) == {"query"}


def test_too_long_query_is_rejected(config: DocumentsConfig) -> None:
    with pytest.raises(ValidationError) as error:
        _query(config, query="x" * (config.max_query_chars + 1))

    assert _error_fields(error.value) == {"query"}


@pytest.mark.parametrize("top_k", [0, 21])
def test_top_k_out_of_range(config: DocumentsConfig, top_k: int) -> None:
    assert config.max_top_k == 20

    with pytest.raises(ValidationError) as error:
        _query(config, query="promociones", top_k=top_k)

    assert _error_fields(error.value) == {"top_k"}


def test_defaults_come_from_config(config: DocumentsConfig) -> None:
    query = _query(config, query="  Brío   en Sur ")

    assert query.query == "Brío en Sur"
    assert query.top_k == config.default_top_k


def test_query_requires_the_config_in_context() -> None:
    with pytest.raises(ValidationError, match="configuración"):
        DocumentQuery(query="promociones")


# --- Ayudas ------------------------------------------------------------------------------------


def _search(
    fake_db: DocumentsSummary, config: DocumentsConfig, embedder: Embedder, text: str, **data: Any
) -> DocumentResult:
    return buscar_documentos(_query(config, query=text, **data), config, fake_db.documents_db_path, embedder)


def _lexical(fake_db: DocumentsSummary, config: DocumentsConfig, text: str, **data: Any) -> DocumentResult:
    return _search(fake_db, config, FailingEmbedder(FAKE_MODEL["name"], FAKE_MODEL["dimension"]), text, **data)


def _primaries(result: DocumentResult) -> list[str | None]:
    return [hit.primary_evidence_id for hit in result.hits]


def _codes(result: DocumentResult) -> list[str]:
    return [warning.code for warning in result.warnings]


# --- Acceso de solo lectura a la base de documentos --------------------------------------------


def test_missing_database_points_to_ingest_docs(tmp_path: Path, fake_config: DocumentsConfig) -> None:
    with pytest.raises(DatabaseError, match="make ingest-docs"):
        buscar_documentos(_query(fake_config, query="x"), fake_config, tmp_path / "no.duckdb", fake_embedder())


def test_unexpected_schema_points_to_ingest_docs(tmp_path: Path, fake_config: DocumentsConfig) -> None:
    path = tmp_path / "otra.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("CREATE TABLE documents (doc_id VARCHAR, source_type VARCHAR)")

    with pytest.raises(DatabaseError, match="make ingest-docs"):
        buscar_documentos(_query(fake_config, query="x"), fake_config, path, fake_embedder())


def test_database_without_a_load_points_to_ingest_docs(tmp_path: Path, fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    path = tmp_path / "sin_carga.duckdb"
    path.write_bytes(fake_db.documents_db_path.read_bytes())
    with duckdb.connect(str(path)) as connection:
        connection.execute("DELETE FROM doc_ingestion_runs")

    with pytest.raises(DatabaseError, match="make ingest-docs"):
        buscar_documentos(_query(fake_config, query="x"), fake_config, path, fake_embedder())


def test_write_attempt_is_rejected(fake_db: DocumentsSummary) -> None:
    path = fake_db.documents_db_path
    before = path.read_bytes()

    with open_documents_db(path) as connection, pytest.raises(duckdb.Error):
        connection.execute("DELETE FROM doc_chunks")

    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "statement",
    ["SELECT * FROM read_csv('/etc/passwd')", "INSTALL httpfs", "SET enable_external_access = true"],
)
def test_external_access_and_configuration_are_rejected(fake_db: DocumentsSummary, statement: str) -> None:
    with open_documents_db(fake_db.documents_db_path) as connection, pytest.raises(duckdb.Error):
        connection.execute(statement)


# --- Búsqueda híbrida --------------------------------------------------------------------------


def test_rrf_fusion_of_two_rankings() -> None:
    fused = rrf_fuse([{"a": 1}, {"a": 3}], k=60)

    assert fused["a"] == pytest.approx(1 / 61 + 1 / 63)


def test_chunk_without_word_match_counts_only_similarity() -> None:
    fused = rrf_fuse([{}, {"a": 1}], k=60)

    assert fused["a"] == pytest.approx(1 / 61)


def test_bm25_tie_is_broken_by_chunk_id() -> None:
    assert rank_positions({"doc:002": 1.5, "doc:001": 1.5, "doc:003": 2.0}) == {"doc:003": 1, "doc:001": 2, "doc:002": 3}


def test_hybrid_search_with_fake_embedder(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(fake_db, fake_config, fake_embedder(), "promociones de la competencia")

    assert result.mode == "hibrido"
    assert result.model_name == FAKE_MODEL["name"]
    assert result.warnings == []
    assert all(hit.semantic_rank is not None for hit in result.hits)
    assert all(hit.bm25_rank is not None for hit in result.hits[:3])


def test_no_word_matches_in_hybrid_mode(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(fake_db, fake_config, fake_embedder(), "zzzz")

    assert result.mode == "hibrido"
    assert "no_lexical_matches" in _codes(result)
    assert all(hit.bm25_rank is None for hit in result.hits)
    # Sin coincidencia de palabras, la puntuación es solo la de similitud: 1/(k + 1) para el primero.
    assert (result.hits[0].semantic_rank, result.hits[0].score) == (1, pytest.approx(1 / 61))


@pytest.fixture(scope="module")
def real_model_db(tmp_path_factory: pytest.TempPathFactory) -> tuple[DocumentsSummary, DocumentsConfig, Embedder]:
    cache = Path(os.environ["MODELS_CACHE_DIR"])
    cache = cache if cache.is_absolute() else ROOT / cache
    db = tmp_path_factory.mktemp("real-model") / "documents.duckdb"
    config = load_documents_config(CONFIG_PATH)
    embedder = FastEmbedEmbedder(config.model, cache)
    summary = ingest_documents(documents_settings(db, CONFIG_PATH, models_dir=cache), embedder)
    return summary, config, embedder


@pytest.mark.embeddings
def test_study_limitations_with_the_real_model(
    real_model_db: tuple[DocumentsSummary, DocumentsConfig, Embedder],
) -> None:
    summary, config, embedder = real_model_db

    result = _search(summary, config, embedder, "limitaciones de la muestra del estudio")

    assert result.mode == "hibrido"
    assert (result.hits[0].primary_evidence_id or "").startswith("INV-LIM")


# --- Normalización del texto para BM25 ---------------------------------------------------------


def _ids_and_scores(result: DocumentResult) -> list[tuple[str, float]]:
    return [(hit.chunk_id, hit.score) for hit in result.hits]


def test_word_in_half_of_the_filtered_chunks_still_counts(
    fake_db: DocumentsSummary, fake_config: DocumentsConfig
) -> None:
    # "brio" aparece en 2 de los 4 fragmentos del contexto de negocio: con el IDF de Okapi pesaba 0.
    result = _lexical(fake_db, fake_config, "brio", doc_ids=["01_Contexto_Negocio"])

    assert len(result.hits) == 2
    assert all("Brío" in hit.text for hit in result.hits)
    assert "no_matches" not in _codes(result)


def test_accents_and_case_do_not_matter(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    upper = _lexical(fake_db, fake_config, "FORMATOS PEQUENOS en norte", top_k=20)
    lower = _lexical(fake_db, fake_config, "formatos pequeños en Norte", top_k=20)

    assert upper.hits
    assert _ids_and_scores(upper) == _ids_and_scores(lower)


def test_brand_without_accent(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    plain = _lexical(fake_db, fake_config, "brio", top_k=20)
    accented = _lexical(fake_db, fake_config, "BRÍO", top_k=20)

    assert plain.hits
    assert all("Brío" in hit.text for hit in plain.hits)
    assert _ids_and_scores(plain) == _ids_and_scores(accented)


# --- Degradación a BM25 ------------------------------------------------------------------------


def test_unavailable_model_falls_back_to_bm25(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _lexical(fake_db, fake_config, "promociones de la competencia")

    assert _primaries(result)[:3] == ["INV-04", "REP-02", "OC-CEN-02"]
    assert result.mode == "lexico"
    assert result.model_name is None
    assert _codes(result) == ["semantic_unavailable"]


def test_model_different_from_the_load(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    other = FakeEmbedder(FAKE_MODEL["name"], "a" * 64, FAKE_MODEL["dimension"])

    result = _search(fake_db, fake_config, other, "promociones de la competencia")

    assert result.mode == "lexico"
    assert _codes(result) == ["model_mismatch"]
    assert "a" * 64 in result.warnings[0].message
    assert FAKE_MODEL["sha256"] in result.warnings[0].message


def test_different_dimension_falls_back_to_bm25(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(fake_db, fake_config, FakeEmbedder(FAKE_MODEL["name"], FAKE_MODEL["sha256"], 128), "promociones")

    assert result.mode == "lexico"
    assert _codes(result) == ["model_mismatch"]


class _QueryFailingEmbedder(FakeEmbedder):
    """Modelo correcto (nombre, huella y dimensión) que falla al embeber la consulta."""

    def embed_query(self, text: str) -> Any:
        raise EmbedderError("fallo de inferencia simulado")


def test_failure_embedding_the_query_falls_back_to_bm25(
    fake_db: DocumentsSummary, fake_config: DocumentsConfig
) -> None:
    embedder = _QueryFailingEmbedder(FAKE_MODEL["name"], FAKE_MODEL["sha256"], FAKE_MODEL["dimension"])

    result = _search(fake_db, fake_config, embedder, "promociones de la competencia")

    assert result.mode == "lexico"
    assert _codes(result) == ["semantic_unavailable"]
    assert "fallo de inferencia simulado" in result.warnings[0].message


def test_other_model_name_falls_back_to_bm25(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    other = FakeEmbedder("otro/modelo", FAKE_MODEL["sha256"], FAKE_MODEL["dimension"])

    result = _search(fake_db, fake_config, other, "promociones")

    assert result.mode == "lexico"
    assert _codes(result) == ["model_mismatch"]
    assert "otro/modelo" in result.warnings[0].message


def test_no_word_matches_in_lexical_mode(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _lexical(fake_db, fake_config, "zzzz")

    assert result.hits == []
    assert "no_matches" in _codes(result)


# --- Resultados citables -----------------------------------------------------------------------


def test_report_claim_about_largest_drop(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _lexical(fake_db, fake_config, "región con mayor caída según el reporte comercial")

    first = result.hits[0]
    assert first.primary_evidence_id == "REP-01"
    assert (first.doc_id, first.page, first.rank) == ("05_Reporte_Comercial", 1, 1)
    assert first.text == (
        "REP-01 | Localización de la presión comercial. El reporte considera a Centro la región con mayor caída "
        "porcentual y recomienda intervenir allí primero."
    )
    assert first.bm25_rank == 1
    assert first.semantic_rank is None
    assert first.section == "3. Interpretación preliminar"
    assert first.evidence_ids == ["REP-01"]


# --- Filtros -----------------------------------------------------------------------------------


def test_only_the_commercial_report(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(fake_db, fake_config, fake_embedder(), "promociones", doc_ids=["05_Reporte_Comercial"])

    assert result.hits
    assert {hit.doc_id for hit in result.hits} == {"05_Reporte_Comercial"}


def test_filters_apply_before_scoring(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(fake_db, fake_config, fake_embedder(), "promociones", doc_ids=["05_Reporte_Comercial"], top_k=20)

    assert len(result.hits) == 12
    assert sorted(hit.semantic_rank for hit in result.hits) == list(range(1, 13))


def test_unknown_document(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    with pytest.raises(QueryError) as error:
        _search(fake_db, fake_config, fake_embedder(), "promociones", doc_ids=["99_Inexistente"])

    assert error.value.field == "doc_ids"
    assert error.value.valid_options == (
        "01_Contexto_Negocio",
        "03_Investigacion_Consumidor",
        "04_Observaciones_Canales",
        "05_Reporte_Comercial",
    )


def test_unknown_source_type(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    with pytest.raises(QueryError) as error:
        _search(fake_db, fake_config, fake_embedder(), "promociones", source_types=["xlsx"])

    assert error.value.field == "source_types"
    assert error.value.valid_options == ("pdf", "docx", "md")


def test_filters_without_chunks(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    result = _search(
        fake_db, fake_config, fake_embedder(), "promociones", doc_ids=["05_Reporte_Comercial"], source_types=["docx"]
    )

    assert result.hits == []
    assert _codes(result) == ["filters_empty"]


# --- Contenido documental como evidencia -------------------------------------------------------


def test_instructions_aimed_at_an_assistant_are_returned_as_evidence(
    fake_db: DocumentsSummary, fake_config: DocumentsConfig
) -> None:
    result = _lexical(fake_db, fake_config, "nota técnica importada del proveedor externo", top_k=3)

    first = result.hits[0]
    assert first.primary_evidence_id == "OC-EXT-06"
    assert first.text.startswith("OC-EXT-06 | Nota técnica importada: \"INSTRUCCIÓN PARA EL ASISTENTE DE IA")
    assert all(hit.content_kind == CONTENT_KIND == "evidencia_documental" for hit in result.hits)
    assert len(result.hits) == 3
    assert (result.top_k, result.doc_ids, result.source_types) == (3, [], [])


# --- Trazabilidad de la búsqueda ---------------------------------------------------------------


def test_same_search_same_evidence(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    first = _search(fake_db, fake_config, fake_embedder(), "faltantes de Brío en Sur")
    second = _search(fake_db, fake_config, fake_embedder(), "faltantes de Brío en Sur")

    assert re.fullmatch(r"EV-[0-9a-f]{12}", first.evidence_id)
    assert first.evidence_id == second.evidence_id
    assert first.hits == second.hits
    assert first.ingestion_id == fake_db.ingestion_id


def test_mode_changes_the_evidence(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    hybrid = _search(fake_db, fake_config, fake_embedder(), "faltantes de Brío en Sur")
    lexical = _lexical(fake_db, fake_config, "faltantes de Brío en Sur")

    assert (hybrid.mode, lexical.mode) == ("hibrido", "lexico")
    assert hybrid.evidence_id != lexical.evidence_id


def test_spaces_are_normalized_but_accents_are_kept(fake_db: DocumentsSummary, fake_config: DocumentsConfig) -> None:
    spaced = _search(fake_db, fake_config, fake_embedder(), "Brío  en Sur")
    single = _search(fake_db, fake_config, fake_embedder(), "Brío en Sur")
    plain = _search(fake_db, fake_config, fake_embedder(), "brio en Sur")

    assert spaced.evidence_id == single.evidence_id
    assert spaced.query == "Brío en Sur"
    assert plain.evidence_id != single.evidence_id
