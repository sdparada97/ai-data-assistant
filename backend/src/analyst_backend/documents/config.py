"""Carga y validación de `documents.yaml`.

Todos los parámetros de la ingesta y la recuperación de documentos viven en ese
archivo: extensiones, patrones de IDs, umbrales de PDF, modelo de embeddings y
límites de la búsqueda. Aquí no hay valores por defecto.
"""

from __future__ import annotations

import hashlib
import re
from functools import cached_property
from pathlib import Path

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveFloat,
    PositiveInt,
    ValidationError,
    field_validator,
    model_validator,
)

from analyst_backend.documents.errors import DocumentsConfigError


# Tipos para los que hay conversor a Markdown (documents/markdown.py).
SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".md")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _check_regex(value: str) -> str:
    try:
        re.compile(value)
    except re.error as error:
        raise ValueError(f"expresión regular inválida {value!r}: {error}") from error
    return value


class PdfConfig(_Strict):
    title_min_size: PositiveFloat
    section_min_size: PositiveFloat
    section_pattern: str
    page_label_pattern: str
    paragraph_gap_ratio: PositiveFloat
    min_row_height_pt: PositiveFloat
    row_stack_tolerance_pt: PositiveFloat
    column_tolerance_pt: PositiveFloat

    @field_validator("section_pattern", "page_label_pattern")
    @classmethod
    def _patterns(cls, value: str) -> str:
        return _check_regex(value)


class ModelConfig(_Strict):
    name: str = Field(min_length=1)
    source: str = Field(min_length=1, description="Repositorio del que fastembed descarga el modelo")
    file: str = Field(min_length=1, description="Archivo del modelo dentro de la revisión descargada")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    dimension: PositiveInt


class EmbeddingTemplate(_Strict):
    with_section: str
    without_section: str

    @field_validator("with_section")
    @classmethod
    def _with_section(cls, value: str) -> str:
        for field in ("{title}", "{section}", "{text}"):
            if field not in value:
                raise ValueError(f"debe contener {field}")
        return value

    @field_validator("without_section")
    @classmethod
    def _without_section(cls, value: str) -> str:
        for field in ("{title}", "{text}"):
            if field not in value:
                raise ValueError(f"debe contener {field}")
        if "{section}" in value:
            raise ValueError("no puede contener {section}")
        return value

    def render(self, title: str, section: str | None, text: str) -> str:
        if section:
            return self.with_section.format(title=title, section=section, text=text)
        return self.without_section.format(title=title, text=text)


class DocumentsConfig(_Strict):
    extensions: tuple[str, ...] = Field(min_length=1)
    id_patterns: tuple[str, ...] = Field(min_length=1)
    id_separators: tuple[str, ...] = Field(min_length=1)
    pdf: PdfConfig
    model: ModelConfig
    embedding_template: EmbeddingTemplate
    rrf_k: PositiveInt
    default_top_k: PositiveInt
    max_top_k: PositiveInt
    max_query_chars: PositiveInt
    fingerprint: str = Field(default="", description="SHA-256 del archivo; lo calcula la carga")

    @field_validator("extensions")
    @classmethod
    def _extensions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        lowered = tuple(ext.lower() for ext in value)
        unsupported = [ext for ext in lowered if ext not in SUPPORTED_EXTENSIONS]
        if unsupported:
            raise ValueError(
                f"extensiones sin conversor: {', '.join(unsupported)} (admitidas: {', '.join(SUPPORTED_EXTENSIONS)})"
            )
        return lowered

    @field_validator("id_patterns")
    @classmethod
    def _id_patterns(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_check_regex(pattern) for pattern in value)

    @field_validator("id_separators")
    @classmethod
    def _separators(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not separator.strip() for separator in value):
            raise ValueError("los separadores no pueden estar vacíos")
        return value

    @model_validator(mode="after")
    def _top_k_limits(self) -> DocumentsConfig:
        if self.default_top_k > self.max_top_k:
            raise ValueError("default_top_k no puede ser mayor que max_top_k")
        return self

    @cached_property
    def id_regex(self) -> re.Pattern[str]:
        """Un ID de evidencia en cualquier posición del texto."""
        return re.compile(r"\b(?:" + "|".join(self.id_patterns) + r")\b")

    @cached_property
    def id_start_regex(self) -> re.Pattern[str]:
        """Un ID al inicio, seguido de un separador. El grupo ``id`` es el ID."""
        separators = "|".join(re.escape(separator) for separator in self.id_separators)
        return re.compile(r"^(?P<id>" + "|".join(self.id_patterns) + r")\s*(?:" + separators + ")")


def load_documents_config(path: Path) -> DocumentsConfig:
    if not path.is_file():
        raise DocumentsConfigError(f"No existe la configuración de documentos: {path}")
    content = path.read_bytes()
    try:
        data = yaml.safe_load(content.decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise DocumentsConfigError(f"YAML inválido en {path}: {error}") from error
    if not isinstance(data, dict):
        raise DocumentsConfigError(f"{path} debe contener un objeto YAML")
    try:
        return DocumentsConfig.model_validate({**data, "fingerprint": hashlib.sha256(content).hexdigest()})
    except ValidationError as error:
        raise DocumentsConfigError(f"Configuración inválida en {path}: {error}") from error
