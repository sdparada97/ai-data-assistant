"""`make models`: descarga el modelo de embeddings en MODELS_CACHE_DIR y comprueba su huella.

- Si el archivo del modelo ya está con la huella configurada, no hace nada.
- Si está con otra huella, falla mostrando ambas, sin descargar.
- Si no está, lo descarga y comprueba la huella.
Con ``--check`` solo comprueba (lo usa `make test-embeddings`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analyst_backend.documents.config import ModelConfig, load_documents_config
from analyst_backend.documents.embeddings import DOWNLOAD_HINT, cached_model_file, file_sha256
from analyst_backend.documents.errors import DocumentsError, EmbedderError
from analyst_backend.settings import SettingsError, load_models_settings


def _verify(model: ModelConfig, cache_dir: Path) -> str | None:
    """Huella del archivo en caché si coincide; ``None`` si no está. Falla si es otra."""
    path = cached_model_file(model, cache_dir)
    if path is None:
        return None
    found = file_sha256(path)
    if found != model.sha256:
        raise EmbedderError(
            f"El archivo del modelo en {path} tiene otra huella: esperada {model.sha256}, encontrada {found}. "
            "Borra esa caché y vuelve a ejecutar `make models`."
        )
    return found


def _download(model: ModelConfig, cache_dir: Path) -> None:
    from fastembed import TextEmbedding

    try:
        TextEmbedding(model_name=model.name, cache_dir=str(cache_dir), local_files_only=False)
    except Exception as error:  # fastembed no documenta sus excepciones de descarga
        raise EmbedderError(f"No se pudo descargar el modelo {model.name}: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="solo comprueba que el modelo está y su huella")
    args = parser.parse_args(argv)
    try:
        settings = load_models_settings()
        model = load_documents_config(settings.documents_config_path).model
        cache_dir = settings.models_cache_dir
        if _verify(model, cache_dir) is not None:
            print(f"Modelo {model.name} disponible en {cache_dir} (huella {model.sha256}).")
            return 0
        if args.check:
            raise EmbedderError(f"El modelo {model.name} no está en MODELS_CACHE_DIR ({cache_dir}). {DOWNLOAD_HINT}.")
        print(f"Descargando {model.name} en {cache_dir}…")
        _download(model, cache_dir)
        if _verify(model, cache_dir) is None:
            raise EmbedderError(f"Tras la descarga no se encuentra {model.file} de {model.source} en {cache_dir}")
    except (DocumentsError, SettingsError) as error:
        print(f"Error del modelo de embeddings: {error}", file=sys.stderr)
        return 1
    print(f"Modelo {model.name} descargado y verificado (huella {model.sha256}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
