"""Esquema de la base de documentos y escritura de sus tablas.

La publicación atómica es la de la base de ventas (``ingestion.storage.publish``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

import duckdb
import numpy as np

from analyst_backend.documents.chunking import Chunk

TABLE_COMMENTS = {
    "documents": "Documentos cargados (uno por archivo), con su Markdown normalizado",
    "doc_chunks": "Fragmentos citables de los documentos, con sus metadatos y su embedding",
    "doc_ingestion_runs": "Carga publicada de la base de documentos (una sola fila)",
}

COLUMN_COMMENTS: dict[str, dict[str, str]] = {
    "documents": {
        "doc_id": "Nombre del archivo sin extensión",
        "source_type": "Tipo de origen: pdf, docx o md",
        "title": "Título del documento (primer # del Markdown, o el doc_id)",
        "file_name": "Nombre del archivo cargado",
        "sha256": "Huella SHA-256 del archivo",
        "chunk_count": "Fragmentos del documento",
        "markdown": "Markdown normalizado del que salen los fragmentos",
    },
    "doc_chunks": {
        "chunk_id": "Identificador del fragmento: <doc_id>:<posición de 3 dígitos>",
        "doc_id": "Documento del fragmento",
        "source_type": "Tipo de origen: pdf, docx o md",
        "title": "Título del documento",
        "section": "Título de la sección (nulo en el preámbulo)",
        "page": "Página donde empieza el fragmento (solo PDF)",
        "primary_evidence_id": "ID de evidencia que abre el fragmento (o nulo)",
        "evidence_ids": "IDs de evidencia del fragmento: el principal primero y luego los del texto",
        "text": "Texto literal del fragmento",
        "embedding": "Embedding de título, sección y texto con el modelo de doc_ingestion_runs",
    },
    "doc_ingestion_runs": {
        "ingestion_id": "Identificador determinista de la carga (archivos, configuración y modelo)",
        "started_at": "Fecha y hora de la carga (UTC)",
        "model_name": "Modelo de embeddings",
        "model_sha256": "Huella SHA-256 del archivo del modelo",
        "embedding_dimension": "Dimensión de los embeddings",
        "config_sha256": "Huella SHA-256 de documents.yaml",
        "chunk_count": "Fragmentos en total",
        "files": "Archivos cargados: nombre, doc_id, huella SHA-256 y fragmentos",
    },
}

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "doc_chunks": tuple(COLUMN_COMMENTS["doc_chunks"]),
    "doc_ingestion_runs": ("ingestion_id", "model_name", "model_sha256", "embedding_dimension"),
    "documents": ("doc_id", "source_type"),
}


def _ddl(dimension: int) -> dict[str, str]:
    return {
        "documents": """
            CREATE TABLE documents (
                doc_id VARCHAR PRIMARY KEY,
                source_type VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                file_name VARCHAR NOT NULL,
                sha256 VARCHAR NOT NULL,
                chunk_count INTEGER NOT NULL,
                markdown VARCHAR NOT NULL
            )""",
        "doc_chunks": f"""
            CREATE TABLE doc_chunks (
                chunk_id VARCHAR PRIMARY KEY,
                doc_id VARCHAR NOT NULL,
                source_type VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                section VARCHAR,
                page INTEGER,
                primary_evidence_id VARCHAR,
                evidence_ids VARCHAR[] NOT NULL,
                text VARCHAR NOT NULL,
                embedding FLOAT[{dimension}] NOT NULL
            )""",
        "doc_ingestion_runs": """
            CREATE TABLE doc_ingestion_runs (
                ingestion_id VARCHAR NOT NULL,
                started_at TIMESTAMP NOT NULL,
                model_name VARCHAR NOT NULL,
                model_sha256 VARCHAR NOT NULL,
                embedding_dimension INTEGER NOT NULL,
                config_sha256 VARCHAR NOT NULL,
                chunk_count INTEGER NOT NULL,
                files STRUCT(file_name VARCHAR, doc_id VARCHAR, sha256 VARCHAR, chunk_count INTEGER)[] NOT NULL
            )""",
    }


@dataclass(frozen=True)
class LoadedDocument:
    doc_id: str
    source_type: str
    title: str
    file_name: str
    sha256: str
    markdown: str
    chunks: tuple[Chunk, ...]


@dataclass(frozen=True)
class RunRecord:
    ingestion_id: str
    started_at: datetime
    model_name: str
    model_sha256: str
    embedding_dimension: int
    config_sha256: str


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def write_tables(
    connection: duckdb.DuckDBPyConnection,
    documents: Sequence[LoadedDocument],
    embeddings: Mapping[str, np.ndarray],
    run: RunRecord,
) -> None:
    """Crea las tres tablas, inserta las filas y añade las descripciones."""
    for ddl in _ddl(run.embedding_dimension).values():
        connection.execute(ddl)
    connection.executemany(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(d.doc_id, d.source_type, d.title, d.file_name, d.sha256, len(d.chunks), d.markdown) for d in documents],
    )
    connection.executemany(
        "INSERT INTO doc_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                c.chunk_id,
                c.doc_id,
                c.source_type,
                c.title,
                c.section,
                c.page,
                c.primary_evidence_id,
                list(c.evidence_ids),
                c.text,
                embeddings[c.chunk_id].astype(float).tolist(),
            )
            for d in documents
            for c in d.chunks
        ],
    )
    files = [
        {"file_name": d.file_name, "doc_id": d.doc_id, "sha256": d.sha256, "chunk_count": len(d.chunks)}
        for d in documents
    ]
    connection.execute(
        "INSERT INTO doc_ingestion_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.ingestion_id,
            run.started_at,
            run.model_name,
            run.model_sha256,
            run.embedding_dimension,
            run.config_sha256,
            sum(len(d.chunks) for d in documents),
            files,
        ),
    )
    for table, comment in TABLE_COMMENTS.items():
        connection.execute(f"COMMENT ON TABLE {table} IS {_quote(comment)}")
        for column, column_comment in COLUMN_COMMENTS[table].items():
            connection.execute(f"COMMENT ON COLUMN {table}.{column} IS {_quote(column_comment)}")
