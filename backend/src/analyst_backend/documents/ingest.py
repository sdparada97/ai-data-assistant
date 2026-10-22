"""Carga de documentos: archivos → Markdown → fragmentos → modelo → embeddings → publicación.

El orden importa: los errores de rutas, archivos y conversión aparecen antes que
los del modelo, así que un directorio mal configurado se detecta aunque el modelo
no esté descargado. Ningún error publica la base.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from analyst_backend.analytics.evidence import canonical_json
from analyst_backend.documents.chunking import chunk_markdown
from analyst_backend.documents.config import load_documents_config
from analyst_backend.documents.embeddings import Embedder, FastEmbedEmbedder, check_embedder, embedding_text
from analyst_backend.documents.errors import SourceError
from analyst_backend.documents.markdown import to_markdown
from analyst_backend.documents.sources import list_documents
from analyst_backend.documents.storage import LoadedDocument, RunRecord, write_tables
from analyst_backend.ingestion.storage import publish
from analyst_backend.settings import DocumentsSettings


@dataclass(frozen=True)
class DocumentsSummary:
    documents_db_path: Path
    ingestion_id: str
    chunks_per_document: dict[str, int]
    model_name: str

    @property
    def chunk_count(self) -> int:
        return sum(self.chunks_per_document.values())


def documents_ingestion_id(documents: list[LoadedDocument], config_sha256: str, model_sha256: str) -> str:
    """SHA-256 de los nombres y contenidos de los archivos, de documents.yaml y de la huella del modelo."""
    payload = canonical_json(
        {
            "files": [[d.file_name, d.sha256] for d in documents],
            "config": config_sha256,
            "model": model_sha256,
        }
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise SourceError(f"No se puede leer {path.name}: {error}") from error


def ingest_documents(settings: DocumentsSettings, embedder: Embedder | None = None) -> DocumentsSummary:
    config = load_documents_config(settings.documents_config_path)
    documents: list[LoadedDocument] = []
    sources = list_documents(settings.documents_dir, config.extensions)
    # Por etapas, para que los errores salgan en el orden de la spec: archivos, conversión, fragmentos.
    hashes = {source.doc_id: _file_sha256(source.path) for source in sources}
    markdowns = {source.doc_id: to_markdown(source, config) for source in sources}
    for source in sources:
        title, chunks = chunk_markdown(markdowns[source.doc_id], source.doc_id, source.source_type, config)
        documents.append(
            LoadedDocument(
                doc_id=source.doc_id,
                source_type=source.source_type,
                title=title,
                file_name=source.path.name,
                sha256=hashes[source.doc_id],
                markdown=markdowns[source.doc_id],
                chunks=tuple(chunks),
            )
        )

    embedder = embedder or FastEmbedEmbedder(config.model, settings.models_cache_dir)
    check_embedder(embedder, config.model)
    all_chunks = [chunk for document in documents for chunk in document.chunks]
    vectors = embedder.embed_documents(
        [embedding_text(config.embedding_template, c.title, c.section, c.text) for c in all_chunks]
    )
    embeddings = {chunk.chunk_id: vectors[index] for index, chunk in enumerate(all_chunks)}

    run = RunRecord(
        ingestion_id=documents_ingestion_id(documents, config.fingerprint, config.model.sha256),
        started_at=datetime.now(UTC).replace(tzinfo=None),
        model_name=config.model.name,
        model_sha256=config.model.sha256,
        embedding_dimension=config.model.dimension,
        config_sha256=config.fingerprint,
    )
    publish(settings.documents_db_path, lambda connection: write_tables(connection, documents, embeddings, run))
    return DocumentsSummary(
        documents_db_path=settings.documents_db_path,
        ingestion_id=run.ingestion_id,
        chunks_per_document={d.doc_id: len(d.chunks) for d in documents},
        model_name=config.model.name,
    )
