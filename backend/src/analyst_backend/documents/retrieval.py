"""`buscar_documentos`: recuperación híbrida (BM25 + similitud de embeddings) con RRF.

- BM25 indexa solo el ``text`` de cada fragmento, en minúsculas y sin tildes, con el
  IDF de Lucene: una palabra presente nunca pesa 0. Los fragmentos con puntuación 0
  (sin ninguna palabra de la consulta) no entran en su ranking.
- La similitud es el coseno entre el embedding de la consulta y el de cada fragmento.
- RRF fusiona los rankings: ``score = Σ 1 / (k + rank)``. Los empates se resuelven por ``chunk_id``.
- Si el modelo no está disponible o no es el de la carga, la búsqueda es solo léxica y lo avisa.
- El texto de los fragmentos se devuelve literal, como evidencia; nada en él cambia la búsqueda.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
from rank_bm25 import BM25Okapi

from analyst_backend.analytics.database import DatabaseError, open_readonly
from analyst_backend.analytics.evidence import evidence_id
from analyst_backend.analytics.models import QueryError
from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import Embedder
from analyst_backend.documents.errors import EmbedderError
from analyst_backend.documents.models import DocumentHit, DocumentQuery, DocumentResult, Mode, SearchWarning
from analyst_backend.documents.storage import REQUIRED_COLUMNS

TOOL_NAME = "buscar_documentos"
RELOAD_HINT = "Ejecuta `make ingest-docs` para crearla o actualizarla."
_WORD = re.compile(r"\w+")


class LuceneBM25(BM25Okapi):
    """BM25 con el IDF de Lucene, ``log(1 + (N - n + 0,5) / (n + 0,5))``.

    El IDF de Okapi vale 0 cuando una palabra está en justo la mitad de los fragmentos
    (y es negativo por encima), así que una palabra presente podía no contar.
    """

    def _calc_idf(self, nd: dict[str, int]) -> None:
        self.idf = {
            word: math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5)) for word, freq in nd.items()
        }


@contextmanager
def open_documents_db(path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    """Base de documentos en solo lectura, con el endurecimiento de la base de ventas."""
    with open_readonly(path, REQUIRED_COLUMNS, "documentos", RELOAD_HINT) as connection:
        yield connection


def tokenize(text: str) -> list[str]:
    """Palabras en minúsculas y sin tildes: `Brío`, `brio` y `BRÍO` coinciden."""
    plain = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return _WORD.findall(plain)


def rank_positions(scores: Mapping[str, float]) -> dict[str, int]:
    """Posición (desde 1) de cada fragmento: mayor puntuación primero y, a igualdad, menor ``chunk_id``."""
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return {chunk_id: position for position, chunk_id in enumerate(ordered, start=1)}


def rrf_fuse(rankings: Sequence[Mapping[str, int]], k: int) -> dict[str, float]:
    """Reciprocal Rank Fusion: suma de ``1 / (k + rank)`` en los rankings donde aparece cada fragmento."""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for chunk_id, rank in ranking.items():
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return fused


@dataclass(frozen=True)
class _Run:
    ingestion_id: str
    model_name: str
    model_sha256: str
    dimension: int


@dataclass(frozen=True)
class _Row:
    chunk_id: str
    doc_id: str
    source_type: str
    title: str
    section: str | None
    page: int | None
    primary_evidence_id: str | None
    evidence_ids: list[str]
    text: str


def _load(connection: duckdb.DuckDBPyConnection) -> tuple[_Run, list[_Row], np.ndarray, list[str]]:
    run_row = connection.execute(
        "SELECT ingestion_id, model_name, model_sha256, embedding_dimension FROM doc_ingestion_runs"
    ).fetchone()
    if run_row is None:
        raise DatabaseError(f"La base de documentos no tiene una carga registrada. {RELOAD_HINT}")
    run = _Run(*run_row)
    records = connection.execute(
        "SELECT chunk_id, doc_id, source_type, title, section, page, primary_evidence_id, evidence_ids, text, "
        "embedding FROM doc_chunks ORDER BY chunk_id"
    ).fetchall()
    rows = [_Row(*record[:9]) for record in records]
    vectors = np.asarray([record[9] for record in records], dtype=np.float32).reshape(len(records), run.dimension)
    doc_ids = [doc_id for (doc_id,) in connection.execute("SELECT doc_id FROM documents ORDER BY doc_id").fetchall()]
    return run, rows, vectors, doc_ids


def _check_filters(query: DocumentQuery, doc_ids: list[str], config: DocumentsConfig) -> None:
    unknown = [doc_id for doc_id in query.doc_ids if doc_id not in doc_ids]
    if unknown:
        raise QueryError("doc_ids", f"Documento desconocido: {', '.join(unknown)}", unknown, doc_ids)
    types = [extension.lstrip(".") for extension in config.extensions]
    unknown = [source_type for source_type in query.source_types if source_type not in types]
    if unknown:
        raise QueryError("source_types", f"Tipo de documento desconocido: {', '.join(unknown)}", unknown, types)


def _semantic_query(embedder: Embedder, run: _Run, text: str) -> tuple[np.ndarray | None, SearchWarning | None]:
    """Embedding de la consulta, o el aviso que explica por qué la búsqueda será solo léxica."""
    if embedder.model_name != run.model_name or embedder.dimension != run.dimension:
        return None, SearchWarning(
            code="model_mismatch",
            message=(
                f"El modelo de la consulta ({embedder.model_name}, dimensión {embedder.dimension}) no es el de la carga "
                f"({run.model_name}, dimensión {run.dimension}): búsqueda solo por palabras."
            ),
        )
    try:
        fingerprint = embedder.fingerprint()
        if fingerprint != run.model_sha256:
            return None, SearchWarning(
                code="model_mismatch",
                message=(
                    f"La huella del modelo de la consulta ({fingerprint}) no es la de la carga ({run.model_sha256}): "
                    "búsqueda solo por palabras."
                ),
            )
        vector = np.asarray(embedder.embed_query(text), dtype=np.float32)
    except (EmbedderError, OSError) as error:
        return None, SearchWarning(
            code="semantic_unavailable",
            message=f"La búsqueda semántica no está disponible ({error}): búsqueda solo por palabras.",
        )
    return vector, None


def _cosine(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1) * float(np.linalg.norm(query))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(norms > 0, vectors @ query / norms, 0.0)


def buscar_documentos(
    query: DocumentQuery, config: DocumentsConfig, documents_db_path: Path, embedder: Embedder
) -> DocumentResult:
    """Fragmentos más pertinentes para ``query``. Ver el docstring del módulo."""
    with open_documents_db(documents_db_path) as connection:
        run, rows, vectors, doc_ids = _load(connection)
    _check_filters(query, doc_ids, config)
    top_k = query.top_k if query.top_k is not None else config.default_top_k

    query_vector, warning = _semantic_query(embedder, run, query.query)
    mode: Mode = "hibrido" if query_vector is not None else "lexico"
    warnings = [warning] if warning else []

    selected = [
        index
        for index, row in enumerate(rows)
        if (not query.doc_ids or row.doc_id in query.doc_ids)
        and (not query.source_types or row.source_type in query.source_types)
    ]
    hits: list[DocumentHit] = []
    if not selected:
        warnings.append(SearchWarning(code="filters_empty", message="Los filtros no dejan ningún fragmento."))
    else:
        chunk_ids = [rows[index].chunk_id for index in selected]
        bm25_scores = LuceneBM25([tokenize(rows[index].text) for index in selected]).get_scores(tokenize(query.query))
        bm25_rank = rank_positions(
            {chunk_id: float(score) for chunk_id, score in zip(chunk_ids, bm25_scores, strict=True) if score > 0}
        )
        semantic_rank: dict[str, int] = {}
        if query_vector is not None:
            similarity = _cosine(vectors[selected], query_vector)
            semantic_rank = rank_positions(dict(zip(chunk_ids, (float(s) for s in similarity), strict=True)))
            scores = rrf_fuse([bm25_rank, semantic_rank], config.rrf_k)
            if not bm25_rank:
                warnings.append(
                    SearchWarning(
                        code="no_lexical_matches",
                        message="Ninguna palabra de la consulta aparece en los documentos: "
                        "los resultados son solo por similitud y pueden no ser pertinentes.",
                    )
                )
        else:
            bm25_by_id = dict(zip(chunk_ids, (float(s) for s in bm25_scores), strict=True))
            scores = {chunk_id: bm25_by_id[chunk_id] for chunk_id in bm25_rank}
            if not scores:
                warnings.append(SearchWarning(code="no_matches", message="Ningún fragmento contiene las palabras de la consulta."))
        by_id = {row.chunk_id: row for row in rows}
        final = rank_positions(scores)
        for chunk_id in sorted(final, key=final.__getitem__)[:top_k]:
            row = by_id[chunk_id]
            hits.append(
                DocumentHit(
                    rank=final[chunk_id],
                    chunk_id=row.chunk_id,
                    doc_id=row.doc_id,
                    source_type=row.source_type,
                    title=row.title,
                    section=row.section,
                    page=row.page,
                    primary_evidence_id=row.primary_evidence_id,
                    evidence_ids=list(row.evidence_ids),
                    text=row.text,
                    score=scores[chunk_id],
                    bm25_rank=bm25_rank.get(chunk_id),
                    semantic_rank=semantic_rank.get(chunk_id),
                )
            )

    normalized = {
        "query": query.query,
        "top_k": top_k,
        "doc_ids": sorted(query.doc_ids),
        "source_types": sorted(query.source_types),
        "mode": mode,
    }
    return DocumentResult(
        evidence_id=evidence_id(TOOL_NAME, normalized, run.ingestion_id, config.fingerprint),
        ingestion_id=run.ingestion_id,
        mode=mode,
        model_name=run.model_name if mode == "hibrido" else None,
        query=query.query,
        top_k=top_k,
        doc_ids=list(query.doc_ids),
        source_types=list(query.source_types),
        hits=hits,
        warnings=warnings,
    )
