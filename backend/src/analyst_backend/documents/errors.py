"""Errores de la ingesta de documentos. Todos detienen la carga sin publicar la base."""

from __future__ import annotations


class DocumentsError(RuntimeError):
    """Base de los errores que impiden publicar la base de documentos."""


class DocumentsConfigError(DocumentsError):
    """`documents.yaml` ausente o inválido."""


class SourceError(DocumentsError):
    """El directorio de documentos no existe, no tiene documentos válidos o tiene `doc_id` repetidos."""


class ConversionError(DocumentsError):
    """Un documento no se puede abrir o no produce ningún fragmento."""


class EmbedderError(DocumentsError):
    """El modelo de embeddings no está disponible o no es el configurado."""
