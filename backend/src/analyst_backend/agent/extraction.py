"""Extracción con el LLM (esquema cerrado) y validación en código, para el contraste y la causalidad.

El LLM solo rellena un esquema. Todo lo que sale de él se valida contra el texto del fragmento
(literal, en la misma línea, con su signo) y contra el catálogo antes de usarse. Los enunciados y los
IDs de evidencia los genera el código: ningún texto libre de la extracción llega a la síntesis.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TypeVar

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from analyst_backend.agent.config import ContrastConfig
from analyst_backend.agent.llm import LLMClient
from analyst_backend.agent.context import DataRange, catalog_text
from analyst_backend.agent.prompts import (
    EXTRACTION_SYSTEM,
    claim_extraction_prompt,
    evidence_block,
    observation_extraction_prompt,
)
from analyst_backend.analytics.models import (
    ClaimDirection,
    ClaimKind,
    DiscardedItem,
    ObservationKind,
    QueryError,
    SourceFragment,
    ValidatedClaim,
    ValidatedObservation,
)
from analyst_backend.analytics.periods import resolve_period
from analyst_backend.analytics.semantic import SemanticLayer
from analyst_backend.documents.config import DocumentsConfig
from analyst_backend.documents.embeddings import Embedder
from analyst_backend.documents.models import DocumentQuery, DocumentResult
from analyst_backend.documents.retrieval import buscar_documentos, open_documents_db

T = TypeVar("T", bound=BaseModel)
Extractor = Callable[[type[T], list[BaseMessage]], T | None]
UNPARSEABLE = "La extracción de {tool} no devolvió elementos interpretables"  # sin texto ni salida del LLM


# --- Lo que rellena el LLM (descripciones en español: es lo que lee) -------------------------------


class FilterItem(BaseModel):
    dimension: str = Field(description="Dimensión del catálogo")
    values: list[str] = Field(description="Valores del catálogo")


class ExtractedClaim(BaseModel):
    kind: ClaimKind = Field(description="variacion, ranking, direccion o cualitativa")
    chunk_id: str = Field(description="Fragmento exacto de donde sale")
    metric: str | None = Field(default=None, description="Métrica del catálogo")
    dimension: str | None = Field(default=None, description="Dimensión del valor (vacía si es el total)")
    value: str | None = Field(default=None, description="Valor de la dimensión")
    filters: list[FilterItem] = Field(default_factory=list, description="Filtros, p. ej. la marca")
    base: str | None = Field(default=None, description="Período base (AAAA-Tn…)")
    target: str | None = Field(default=None, description="Período de comparación (AAAA-Tn…)")
    reported: str | None = Field(default=None, description="Cifra literal con su signo, p. ej. '-23 %'")
    direction: ClaimDirection | None = Field(default=None, description="mayor_caida, mayor_crecimiento, contraccion o crecimiento")


class ClaimExtraction(BaseModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)


class ExtractedObservation(BaseModel):
    kind: ObservationKind = Field(description="segmento, atribucion o limitacion")
    chunk_id: str = Field(description="Fragmento exacto")
    quote: str = Field(description="Frase corta o cifra literal del fragmento")
    dimension: str | None = Field(default=None, description="Dimensión del segmento")
    value: str | None = Field(default=None, description="Valor del segmento")
    date: str | None = Field(default=None, description="Fecha AAAA-MM-DD si el fragmento la da")
    declares_design: bool = Field(default=False, description="La atribución declara un diseño que permite atribuir")


class ObservationExtraction(BaseModel):
    observations: list[ExtractedObservation] = Field(default_factory=list)


# --- Documento ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    sha256: str
    fragments: dict[str, SourceFragment]  # en orden

    @property
    def first(self) -> SourceFragment:
        return next(iter(self.fragments.values()))

    def all_text(self) -> str:
        return " ".join([self.title, *(f"{f.section or ''} {f.text}" for f in self.fragments.values())])


def _fragment(row: tuple) -> SourceFragment:  # type: ignore[type-arg]
    chunk_id, doc_id, title, section, page, primary, ids, text = row
    return SourceFragment(chunk_id=chunk_id, doc_id=doc_id, title=title, section=section, page=page,
                          primary_evidence_id=primary, evidence_ids=list(ids), text=text)


def load_document(documents_db_path: Path, doc_id: str, max_chars: int) -> Document:
    """Todos los fragmentos de un documento cargado. `QueryError` si no existe o no cabe en el prompt."""
    with open_documents_db(documents_db_path) as connection:
        loaded = [row[0] for row in connection.execute("SELECT doc_id FROM documents ORDER BY doc_id").fetchall()]
        if doc_id not in loaded:
            raise QueryError("doc_id", f"Documento no cargado: {doc_id!r}. Documentos cargados: {', '.join(loaded)}",
                             doc_id, loaded)
        title, sha256 = connection.execute("SELECT title, sha256 FROM documents WHERE doc_id = ?", [doc_id]).fetchone()
        rows = connection.execute(
            "SELECT chunk_id, doc_id, title, section, page, primary_evidence_id, evidence_ids, text "
            "FROM doc_chunks WHERE doc_id = ? ORDER BY chunk_id", [doc_id],
        ).fetchall()
    fragments = {row[0]: _fragment(row) for row in rows}
    size = sum(len(f.text) for f in fragments.values())
    if size > max_chars:
        raise QueryError("doc_id", f"El documento {doc_id} tiene {size} caracteres; el máximo es {max_chars}", doc_id)
    return Document(doc_id, title, sha256, fragments)


def evidence_ref(fragment: SourceFragment) -> str:
    """ID de evidencia tomado del fragmento: el principal, el primero que contiene o su `chunk_id`."""
    return fragment.primary_evidence_id or (fragment.evidence_ids[0] if fragment.evidence_ids else fragment.chunk_id)


def _blocks(fragments: Sequence[SourceFragment]) -> list[str]:
    return [
        evidence_block(f.chunk_id, "documento", f.text, f'seccion="{f.section or ""}" pagina="{f.page or ""}"')
        for f in fragments
    ]


def llm_extractor(llm: LLMClient) -> Extractor:
    """Extracción con salida estructurada; `None` si la salida no se puede interpretar."""

    def extract(schema: type[T], messages: list[BaseMessage]) -> T | None:
        result = llm.invoke(llm.structured(schema), messages)
        parsed = result.get("parsed") if isinstance(result, dict) else result
        return parsed if isinstance(parsed, schema) else None

    return extract


def _messages(prompt: str) -> list[BaseMessage]:
    return [SystemMessage(EXTRACTION_SYSTEM), HumanMessage(prompt)]


def extract_claims(extractor: Extractor, document: Document, layer: SemanticLayer, data_range: DataRange,
                   tool: str) -> list[ExtractedClaim]:
    prompt = claim_extraction_prompt(catalog_text(layer), data_range.describe(), document.title,
                                     _blocks(list(document.fragments.values())))
    result = extractor(ClaimExtraction, _messages(prompt))
    if result is None:
        raise QueryError("extraccion", UNPARSEABLE.format(tool=tool))
    return result.claims


def extract_observations(extractor: Extractor, cause: str, fragments: Sequence[SourceFragment],
                         layer: SemanticLayer, tool: str) -> list[ExtractedObservation]:
    prompt = observation_extraction_prompt(cause, catalog_text(layer), _blocks(fragments))
    result = extractor(ObservationExtraction, _messages(prompt))
    if result is None:
        raise QueryError("extraccion", UNPARSEABLE.format(tool=tool))
    return result.observations


# --- Comparación de texto ----------------------------------------------------------------------------


def plain(text: str) -> str:
    """Minúsculas y sin tildes."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def contains(haystack: str, needle: str) -> bool:
    return bool(needle.strip()) and re.search(rf"(?<!\w){re.escape(plain(needle.strip()))}(?!\w)", plain(haystack)) is not None


_SENTENCE_END = re.compile(r"(?<!\bvs)(?<!\bp)(?<!\d)\.\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")
_SIGNED_NUMBER = re.compile(r"(?<![\w.,])([+\-−]?)\s?(\d+(?:[.,]\d+)?)(?![\w])")


def units(text: str) -> list[str]:
    """Líneas del fragmento; un párrafo sin saltos se parte en frases (sin cortar en `vs.` ni decimales)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        return lines
    return [part for part in _SENTENCE_END.split(text) if part.strip()]


@dataclass(frozen=True)
class Reported:
    value: Decimal
    decimals: int
    explicit_plus: bool


def parse_reported(text: str) -> Reported | None:
    match = _SIGNED_NUMBER.search(text.replace("−", "-"))
    if match is None:
        return None
    sign, number = match.groups()
    number = number.replace(",", ".")
    try:
        magnitude = Decimal(number)
    except InvalidOperation:
        return None
    decimals = len(number.split(".")[1]) if "." in number else 0
    return Reported(-magnitude if sign == "-" else magnitude, decimals, sign == "+")


def _signed_numbers(line: str) -> list[Decimal]:
    numbers = []
    for sign, number in _SIGNED_NUMBER.findall(line.replace("−", "-")):
        try:
            magnitude = Decimal(number.replace(",", "."))
        except InvalidOperation:
            continue
        numbers.append(-magnitude if sign == "-" else magnitude)
    return numbers


def line_check(fragment: SourceFragment, value: str | None, reported: Reported) -> str | None:
    """`None` si la cifra está, con su signo, en la línea del valor; si no, el motivo del descarte."""
    lines = [line for line in units(fragment.text) if value is None or contains(line, value)]
    numbers = [n for line in lines for n in _signed_numbers(line)]
    if reported.value in numbers:
        return None
    if -reported.value in numbers and reported.value != 0:
        return "signo distinto"
    return "no está en la línea del valor"


# --- Validación de afirmaciones -------------------------------------------------------------------


_ORDINALS = {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto"}
_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"]


def period_anchors(period: str) -> list[str]:
    """Expresiones del texto que anclan un período del catálogo."""
    if re.fullmatch(r"\d{4}-T[1-4]", period):
        quarter = int(period[-1])
        return [f"T{quarter}", f"{_ORDINALS[quarter]} trimestre", period]
    if re.fullmatch(r"\d{4}-S[12]", period):
        half = int(period[-1])
        return [f"S{half}", f"{_ORDINALS[half]} semestre", period]
    if re.fullmatch(r"\d{4}-\d{2}", period):
        return [_MONTHS[int(period[5:]) - 1], period]
    return [period]


def _has_data(period: str, data_range: DataRange) -> bool:
    return any(data_range.first_month <= month <= data_range.last_month for month in resolve_period(period))


@dataclass
class ClaimValidation:
    valid: list[ValidatedClaim] = field(default_factory=list)
    discarded: list[DiscardedItem] = field(default_factory=list)
    fragments: dict[str, SourceFragment] = field(default_factory=dict)
    omitted: int = 0
    warnings: list[str] = field(default_factory=list)


def _metric_words(metric: str, synonyms: dict[str, str]) -> list[str]:
    return [metric.replace("_", " "), *(word for word, target in synonyms.items() if target == metric)]


def _describe(claim: ExtractedClaim) -> str:
    parts = [claim.kind, claim.value or "", claim.reported or ""]
    return " ".join(part for part in parts if part).strip()


def _statement(claim: ValidatedClaim, reported_text: str | None) -> str:
    metric = (claim.metric or "").replace("_", " ")
    periods = f"({claim.base} frente a {claim.target})"
    scope = claim.value or ", ".join(v for values in claim.filters.values() for v in values) or "Total"
    if claim.kind == "variacion":
        return f"{scope}: {metric} {reported_text} {periods}"
    if claim.kind == "ranking":
        which = "mayor caída" if claim.direction == "mayor_caida" else "mayor crecimiento"
        return f"{claim.value}: {which} de {metric} por {claim.dimension} {periods}"
    if claim.kind == "direccion":
        which = "en contracción" if claim.direction == "contraccion" else "en crecimiento"
        return f"{scope}: {metric} {which} {periods}"
    return f"{claim.evidence_ref}: afirmación cualitativa"


def _reported_text(reported: Reported) -> str:
    sign = "-" if reported.value < 0 else ("+" if reported.explicit_plus else "")
    return f"{sign}{abs(reported.value)} %"


def validate_claims(
    claims: Sequence[ExtractedClaim],
    document: Document,
    layer: SemanticLayer,
    data_range: DataRange,
    config: ContrastConfig,
    metric_synonyms: dict[str, str],
) -> ClaimValidation:
    out = ClaimValidation()
    if len(claims) > config.max_claims:
        out.omitted = len(claims) - config.max_claims
        out.warnings.append(f"Se omitieron {out.omitted} afirmaciones del documento (máximo {config.max_claims})")
    document_text = document.all_text()
    for claim in claims[: config.max_claims]:
        try:
            validated = _validate_claim(claim, document, document_text, layer, data_range, config, metric_synonyms)
        except _Discard as discard:
            out.discarded.append(DiscardedItem(chunk_id=claim.chunk_id, description=_describe(claim), reason=str(discard)))
            continue
        out.valid.append(validated)
        out.fragments[validated.chunk_id] = document.fragments[validated.chunk_id]
    defaulted = [claim for claim in out.valid if claim.default_periods]
    if defaulted:
        base, target = defaulted[0].base, defaulted[0].target
        subject = "1 afirmación" if len(defaulted) == 1 else f"{len(defaulted)} afirmaciones"
        out.warnings.append(f"Períodos por defecto ({base} frente a {target}) en {subject} sin períodos en el texto")
    return out


class _Discard(Exception):
    """Motivo de descarte de un elemento extraído (no es un error del plan)."""


def _resolve(layer: SemanticLayer, dimension: str, value: str, field_name: str) -> str:
    try:
        return layer.dimension(dimension, field_name).resolve(value, field_name)
    except QueryError as error:
        raise _Discard(error.message) from None


def _validate_claim(claim: ExtractedClaim, document: Document, document_text: str, layer: SemanticLayer,
                    data_range: DataRange, config: ContrastConfig, synonyms: dict[str, str]) -> ValidatedClaim:
    fragment = document.fragments.get(claim.chunk_id)
    if fragment is None:
        raise _Discard(f"el fragmento {claim.chunk_id} no pertenece al documento {document.doc_id}")
    ref = evidence_ref(fragment)
    if claim.kind == "cualitativa" or claim.metric is None or claim.metric not in layer.metrics:
        cualitativa = ValidatedClaim(kind="cualitativa", chunk_id=fragment.chunk_id, evidence_ref=ref, statement="")
        return cualitativa.model_copy(update={"statement": _statement(cualitativa, None)})
    if not any(contains(document_text, word) for word in _metric_words(claim.metric, synonyms)):
        raise _Discard(f"la métrica {claim.metric} no aparece en el documento")

    dimension, value = claim.dimension, None
    if dimension is not None:
        if claim.value is None:
            raise _Discard(f"falta el valor de {dimension}")
        value = _resolve(layer, dimension, claim.value, "dimension")
    filters: dict[str, list[str]] = {}
    for item in claim.filters:
        resolved = [_resolve(layer, item.dimension, v, f"filters.{item.dimension}") for v in item.values]
        for original, canonical in zip(item.values, resolved, strict=True):
            aliases = [a for a, t in layer.dimensions[item.dimension].aliases.items() if t == canonical]
            if not any(contains(document_text, word) for word in [original, canonical, *aliases]):
                raise _Discard(f"{original} no aparece en el documento")
        filters[item.dimension] = resolved

    base, target, default_periods = _periods(claim, fragment, document, data_range)
    reported, reported_text, direction = None, None, claim.direction
    if claim.kind == "variacion":
        parsed = parse_reported(claim.reported or "")
        if parsed is None:
            raise _Discard("falta la cifra reportada")
        reason = line_check(fragment, value, parsed)
        if reason:
            raise _Discard(reason)
        reported, reported_text = parsed, _reported_text(parsed)
    elif claim.kind == "ranking":
        if dimension is None or direction not in ("mayor_caida", "mayor_crecimiento"):
            raise _Discard("un ranking necesita dimensión y dirección (mayor caída o mayor crecimiento)")
        aliases = [a for a, t in layer.dimensions[dimension].aliases.items() if t == value]
        where = f"{fragment.section or ''} {fragment.text}"
        if not any(contains(where, word) for word in [claim.value or "", value or "", *aliases]):
            raise _Discard(f"{claim.value} no aparece en el texto ni en la sección del fragmento")
    elif claim.kind == "direccion":
        if direction not in ("contraccion", "crecimiento"):
            raise _Discard("una dirección necesita contracción o crecimiento")
        if not any(contains(fragment.text, word) for word in config.direction_words[direction]):
            raise _Discard("la palabra de sentido no aparece en el fragmento")
        dimension = value = None

    validated = ValidatedClaim(
        kind=claim.kind, chunk_id=fragment.chunk_id, evidence_ref=ref, statement="", metric=claim.metric,
        dimension=dimension, value=value, filters=filters, base=base, target=target, default_periods=default_periods,
        reported=reported.value if reported else None, reported_decimals=reported.decimals if reported else 0,
        direction=direction,
    )
    return validated.model_copy(update={"statement": _statement(validated, reported_text)})


def _periods(claim: ExtractedClaim, fragment: SourceFragment, document: Document,
             data_range: DataRange) -> tuple[str, str, bool]:
    default = data_range.quarters[-2], data_range.quarters[-1]
    if not claim.base or not claim.target:
        return *default, True
    where = " ".join([fragment.section or "", fragment.text, document.first.text])
    anchored = all(any(contains(where, anchor) for anchor in period_anchors(p)) for p in (claim.base, claim.target))
    if not anchored:
        return *default, True
    if claim.base == claim.target:
        raise _Discard(f"el período base y el de comparación son el mismo ({claim.base})")
    for period in (claim.base, claim.target):
        try:
            has_data = _has_data(period, data_range)
        except QueryError as error:
            raise _Discard(error.message) from None
        if not has_data:
            raise _Discard(f"el período {period} no tiene datos")
    return claim.base, claim.target, False


# --- Observaciones de la causa -----------------------------------------------------------------------


@dataclass(frozen=True)
class CauseSearch:
    fragments: dict[str, SourceFragment]  # en el orden de la búsqueda
    result: DocumentResult

    def summary(self) -> dict[str, object]:
        """Lo que entra en la huella de la evaluación causal."""
        return {"evidence_id": self.result.evidence_id, "query": self.result.query, "top_k": self.result.top_k,
                "mode": self.result.mode}


def search_cause(cause: str, top_k: int, config: DocumentsConfig, documents_db_path: Path,
                 embedder: Embedder) -> CauseSearch:
    """Fragmentos que devuelve la búsqueda de la causa (los primeros `top_k`)."""
    query = DocumentQuery.model_validate({"query": cause, "top_k": top_k}, context={"config": config})
    result = buscar_documentos(query, config, documents_db_path, embedder)
    fragments = {
        hit.chunk_id: SourceFragment(chunk_id=hit.chunk_id, doc_id=hit.doc_id, title=hit.title, section=hit.section,
                                     page=hit.page, primary_evidence_id=hit.primary_evidence_id,
                                     evidence_ids=list(hit.evidence_ids), text=hit.text)
        for hit in result.hits
    }
    return CauseSearch(fragments, result)


# --- Validación de observaciones ------------------------------------------------------------------


@dataclass
class ObservationValidation:
    valid: list[ValidatedObservation] = field(default_factory=list)
    discarded: list[DiscardedItem] = field(default_factory=list)
    fragments: dict[str, SourceFragment] = field(default_factory=dict)


def validate_observations(observations: Sequence[ExtractedObservation], fragments: dict[str, SourceFragment],
                          layer: SemanticLayer) -> ObservationValidation:
    out = ObservationValidation()
    for observation in observations:
        description = " ".join(p for p in (observation.kind, observation.value or "", observation.date or "") if p)
        fragment = fragments.get(observation.chunk_id)
        try:
            if fragment is None:
                raise _Discard(f"el fragmento {observation.chunk_id} no está entre los recuperados")
            validated = _validate_observation(observation, fragment, layer)
        except _Discard as discard:
            out.discarded.append(DiscardedItem(chunk_id=observation.chunk_id, description=description, reason=str(discard)))
            continue
        out.valid.append(validated)
        out.fragments[fragment.chunk_id] = fragment
    return out


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _is_date(text: str) -> bool:
    """Una fecha real con el formato AAAA-MM-DD (nada de texto libre del fragmento)."""
    if not _ISO_DATE.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _validate_observation(observation: ExtractedObservation, fragment: SourceFragment,
                          layer: SemanticLayer) -> ValidatedObservation:
    if not contains(fragment.text, observation.quote):
        raise _Discard("la cita no aparece literal en el fragmento")
    dimension = value = None
    if observation.kind == "segmento":
        if observation.dimension is None or observation.value is None:
            raise _Discard("un segmento necesita dimensión y valor")
        dimension = observation.dimension
        value = _resolve(layer, dimension, observation.value, "dimension")
        aliases = [a for a, t in layer.dimensions[dimension].aliases.items() if t == value]
        words = [observation.value, value, *aliases]
        quote_lines = [line for line in units(fragment.text) if contains(line, observation.quote)]
        in_line = any(contains(line, word) for line in quote_lines for word in words)
        in_section = any(contains(fragment.section or "", word) for word in words)
        if not (in_line or in_section):
            raise _Discard(f"{observation.value} no está en la línea de la cita ni en la sección del fragmento")
    if observation.date is not None:
        if not _is_date(observation.date):
            raise _Discard("la fecha no tiene el formato AAAA-MM-DD")
        if observation.date not in fragment.text:
            raise _Discard(f"la fecha {observation.date} no aparece en el fragmento")
    return ValidatedObservation(
        kind=observation.kind, chunk_id=fragment.chunk_id, evidence_ref=evidence_ref(fragment), quote=observation.quote,
        dimension=dimension, value=value, date=observation.date,
        declares_design=observation.declares_design if observation.kind == "atribucion" else False,
    )
