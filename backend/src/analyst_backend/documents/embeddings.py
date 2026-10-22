"""Embeddings de los fragmentos.

``Embedder`` es la interfaz; ``FastEmbedEmbedder`` usa fastembed con el modelo
de ``documents.yaml`` desde ``MODELS_CACHE_DIR`` y nunca descarga nada (eso lo hace
``make models``). ``FakeEmbedder`` y ``FailingEmbedder`` sirven para las pruebas.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np

from analyst_backend.documents.config import EmbeddingTemplate, ModelConfig
from analyst_backend.documents.errors import EmbedderError

DOWNLOAD_HINT = "Ejecuta `make models` para descargarlo en MODELS_CACHE_DIR"


class Embedder(ABC):
    """Calcula embeddings. ``fingerprint`` identifica los vectores que produce."""

    model_name: str
    dimension: int

    @abstractmethod
    def fingerprint(self) -> str: ...

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> np.ndarray: ...

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray: ...


def embedding_text(template: EmbeddingTemplate, title: str, section: str | None, text: str) -> str:
    return template.render(title=title, section=section, text=text)


def check_embedder(embedder: Embedder, expected: ModelConfig) -> None:
    """Falla si el embedder no es el modelo configurado (nombre, huella y dimensión)."""
    if embedder.model_name != expected.name:
        raise EmbedderError(f"Modelo de embeddings distinto: esperado {expected.name}, encontrado {embedder.model_name}")
    if embedder.dimension != expected.dimension:
        raise EmbedderError(
            f"Dimensión de embeddings distinta: esperada {expected.dimension}, encontrada {embedder.dimension}"
        )
    found = embedder.fingerprint()
    if found != expected.sha256:
        raise EmbedderError(f"Huella del modelo distinta: esperada {expected.sha256}, encontrada {found}")


# --- fastembed -----------------------------------------------------------------------------------


def cached_model_file(model: ModelConfig, cache_dir: Path) -> Path | None:
    """Archivo del modelo en la caché (estructura de Hugging Face), o ``None`` si no está."""
    repo = cache_dir / f"models--{model.source.replace('/', '--')}"
    snapshots = repo / "snapshots"
    if not snapshots.is_dir():
        return None
    ref = repo / "refs" / "main"
    revisions = [ref.read_text(encoding="utf-8").strip()] if ref.is_file() else []
    revisions += sorted(path.name for path in snapshots.iterdir() if path.is_dir())
    for revision in dict.fromkeys(revisions):
        candidate = snapshots / revision / model.file
        if candidate.is_file():
            return candidate
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class FastEmbedEmbedder(Embedder):
    """Modelo de fastembed cargado solo desde la caché local, de forma perezosa."""

    def __init__(self, model: ModelConfig, cache_dir: Path) -> None:
        self._model = model
        self._cache_dir = cache_dir
        self.model_name = model.name
        self.dimension = model.dimension

    def _model_file(self) -> Path:
        path = cached_model_file(self._model, self._cache_dir)
        if path is None:
            raise EmbedderError(
                f"El modelo {self._model.name} no está en MODELS_CACHE_DIR ({self._cache_dir}). {DOWNLOAD_HINT}."
            )
        return path

    @cached_property
    def _fingerprint(self) -> str:
        return file_sha256(self._model_file())

    def fingerprint(self) -> str:
        return self._fingerprint

    @cached_property
    def _engine(self) -> Any:
        self._model_file()  # error claro si falta, antes de que fastembed intente nada
        from fastembed import TextEmbedding  # import diferido: carga onnxruntime solo si hace falta

        try:
            return TextEmbedding(model_name=self._model.name, cache_dir=str(self._cache_dir), local_files_only=True)
        except Exception as error:  # fastembed no documenta sus excepciones de carga
            raise EmbedderError(f"No se pudo cargar el modelo {self._model.name}: {error}. {DOWNLOAD_HINT}.") from error

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        engine = self._engine
        try:
            vectors = np.asarray(list(engine.embed(list(texts))), dtype=np.float32)
        except Exception as error:  # onnxruntime y fastembed no documentan sus excepciones de inferencia
            raise EmbedderError(f"El modelo {self._model.name} falló al calcular embeddings: {error}") from error
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise EmbedderError(f"El modelo devolvió vectores de forma {vectors.shape}; se esperaba dimensión {self.dimension}")
        return vectors

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]


# --- Pruebas -------------------------------------------------------------------------------------

_WORD = re.compile(r"\w+")


class FakeEmbedder(Embedder):
    """Embedder determinista para pruebas: bolsa de palabras normalizadas proyectada con un hash."""

    def __init__(self, model_name: str, fingerprint: str, dimension: int) -> None:
        self.model_name = model_name
        self.dimension = dimension
        self._fingerprint = fingerprint

    def fingerprint(self) -> str:
        return self._fingerprint

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)
        plain = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
        for word in _WORD.findall(plain):
            index = int.from_bytes(hashlib.blake2b(word.encode(), digest_size=4).digest()) % self.dimension
            vector[index] += 1.0
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return np.stack([self._vector(text) for text in texts]) if texts else np.zeros((0, self.dimension), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self._vector(text)


class FailingEmbedder(Embedder):
    """Embedder que no puede cargarse: para probar la degradación a modo léxico."""

    def __init__(self, model_name: str, dimension: int, reason: str = "modelo no disponible") -> None:
        self.model_name = model_name
        self.dimension = dimension
        self._reason = reason

    def fingerprint(self) -> str:
        raise EmbedderError(self._reason)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        raise EmbedderError(self._reason)

    def embed_query(self, text: str) -> np.ndarray:
        raise EmbedderError(self._reason)
