"""Modelos de entrada y salida de las herramientas, y su error estructurado.

Los modelos solo validan la forma de la consulta. La validación contra la capa
semántica (métricas, dimensiones, valores, períodos) la hacen las herramientas.
Las cifras son ``Decimal``: exactas, sin pérdidas de punto flotante.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QueryError(ValueError):
    """Consulta inválida. Lleva el campo, el valor rechazado y las opciones válidas para reintentar."""

    def __init__(
        self,
        field: str,
        message: str,
        invalid_value: Any = None,
        valid_options: Sequence[str] = (),
    ) -> None:
        super().__init__(message)
        self.field = field
        self.message = message
        self.invalid_value = invalid_value
        self.valid_options = tuple(valid_options)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "invalid_value": self.invalid_value,
            "valid_options": list(self.valid_options),
        }


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Entradas ----------------------------------------------------------------------------------


class Comparison(_Strict):
    base: str = Field(description="Período base: AAAA, AAAA-Sn, AAAA-Tn o AAAA-MM")
    target: str = Field(description="Período de comparación: AAAA, AAAA-Sn, AAAA-Tn o AAAA-MM")


class SortSpec(_Strict):
    metric: str
    field: Literal["value", "var_abs", "var_pct"] = "value"
    order: Literal["asc", "desc"] = "desc"


class MetricQuery(_Strict):
    metrics: list[str] = Field(min_length=1, description="Métricas de la capa semántica")
    filters: dict[str, list[str]] = Field(default_factory=dict, description="Dimensión → valores aceptados")
    group_by: list[str] = Field(default_factory=list, description="Dimensiones por las que agrupar")
    period: str | None = Field(default=None, description="Período único (AAAA, AAAA-Sn, AAAA-Tn, AAAA-MM)")
    compare: Comparison | None = Field(default=None, description="Comparación entre dos períodos")
    sort: SortSpec | None = None
    limit: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _period_or_compare(self) -> MetricQuery:
        if (self.period is None) == (self.compare is None):
            raise ValueError("Indica `period` o `compare`: son excluyentes y uno es obligatorio")
        return self


class QualityQuery(_Strict):
    filters: dict[str, list[str]] = Field(default_factory=dict)
    periods: list[str] = Field(default_factory=list)
    rule_codes: list[str] = Field(default_factory=list)
    include_corrections: bool = False


# --- Salidas -----------------------------------------------------------------------------------


class MetricCell(_Strict):
    value: Decimal | None
    value_exact: Decimal | None


class ComparisonCell(_Strict):
    base: Decimal | None
    base_exact: Decimal | None
    target: Decimal | None
    target_exact: Decimal | None
    var_abs: Decimal | None
    var_abs_exact: Decimal | None
    var_pct: Decimal | None
    var_pct_exact: Decimal | None


class MetricRow(_Strict):
    group: dict[str, str]
    is_total: bool = False
    rank: int | None = None
    metrics: dict[str, MetricCell | ComparisonCell]


class QualityNote(_Strict):
    registro_id: str | None
    source_line: int
    rule_code: str
    issue_type: str
    severity: str
    action: str
    affected_net_sales_cop: int | None
    outside_periods: bool
    mes: str | None
    marca: str | None
    region: str | None
    canal: str | None
    presentacion: str | None
    punto_venta_id: str | None
    column_name: str | None = None
    original_value: str | None = None
    new_value: str | None = None
    details: str | None = None


class MetricResult(_Strict):
    evidence_id: str
    ingestion_id: str
    query: dict[str, Any]
    periods: dict[str, list[str]]
    rows: list[MetricRow]
    total: MetricRow
    warnings: list[str]
    quality_notes: list[QualityNote]
    corrections_count: int
    sql: str
    sql_params: list[str]


class IngestionCounts(_Strict):
    rows_read: int
    rows_sales: int
    rows_review: int
    rows_excluded: int
    rows_removed: int


class RuleActionCount(_Strict):
    rule_code: str
    action: str
    count: int


class QualityResult(_Strict):
    evidence_id: str
    ingestion_id: str
    query: dict[str, Any]
    issue_count: int
    corrections_count: int
    by_rule_action: list[RuleActionCount]
    affected_by_action: dict[str, int | None]
    issues: list[QualityNote]
    review_rows: list[dict[str, Any]]
    ingestion: IngestionCounts


# --- Contraste de afirmaciones y evaluación causal (change add-contrast-and-causal-analysis) ----

ClaimKind = Literal["variacion", "ranking", "direccion", "cualitativa"]
ClaimDirection = Literal["mayor_caida", "mayor_crecimiento", "contraccion", "crecimiento"]
ClaimVerdict = Literal["coincide", "aproximado", "no coincide", "verdadera", "falsa", "no verificable con los datos"]
CauseKind = Literal["competencia", "disponibilidad", "metrica_propia"]
CauseDirection = Literal["sube", "baja"]
ObservationKind = Literal["segmento", "atribucion", "limitacion"]
CriterionName = Literal["localizacion", "comparacion", "temporalidad", "alternativas", "diseno"]
CausalVerdict = Literal["contradicha", "no sustentada", "compatible (hipótesis)"]


class SourceFragment(_Strict):
    """Fragmento de documento en que se apoya una afirmación u observación validada (evidencia citable)."""

    chunk_id: str
    doc_id: str
    title: str
    section: str | None
    page: int | None
    primary_evidence_id: str | None
    evidence_ids: list[str]
    text: str


class ValidatedClaim(_Strict):
    """Afirmación de un documento ya validada en código: todos sus campos están en el catálogo y en el texto."""

    kind: ClaimKind
    chunk_id: str
    evidence_ref: str = Field(description="ID de evidencia tomado del fragmento (nunca del LLM)")
    statement: str = Field(description="Enunciado generado en código con los campos validados")
    metric: str | None = None
    dimension: str | None = None
    value: str | None = Field(default=None, description="Valor de la dimensión, del catálogo")
    filters: dict[str, list[str]] = Field(default_factory=dict)
    base: str | None = None
    target: str | None = None
    default_periods: bool = False
    reported: Decimal | None = None
    reported_decimals: int = 0
    direction: ClaimDirection | None = None


class ClaimComparison(_Strict):
    claim: ValidatedClaim
    verdict: ClaimVerdict
    actual: Decimal | None = Field(default=None, description="Variación real (pp), con 2 decimales")
    difference: Decimal | None = Field(default=None, description="Reportado − real (pp)")
    leader: str | None = Field(default=None, description="Ranking: primer valor real")
    leader_value: Decimal | None = None
    metric_evidence_id: str | None = None


class DiscardedItem(_Strict):
    """Elemento extraído que no pasó la validación. `description` la genera el código, no el LLM."""

    chunk_id: str | None
    description: str
    reason: str


class ContrastResult(_Strict):
    evidence_id: str
    doc_id: str
    doc_title: str
    document_sha256: str
    comparisons: list[ClaimComparison]
    discarded: list[DiscardedItem] = Field(default_factory=list)
    omitted: int = 0
    warnings: list[str] = Field(default_factory=list)
    queries: list[MetricResult] = Field(default_factory=list)
    fragments: list[SourceFragment] = Field(default_factory=list, description="Fragmentos de las afirmaciones validadas")


class ValidatedObservation(_Strict):
    """Observación de la causa en un documento, validada: cita literal, segmento y fecha en el fragmento."""

    kind: ObservationKind
    chunk_id: str
    evidence_ref: str
    quote: str
    dimension: str | None = None
    value: str | None = None
    date: str | None = None
    declares_design: bool = False


class CriterionResult(_Strict):
    name: CriterionName
    result: str
    detail: str = Field(description="Explicación generada en código con los valores")
    values: dict[str, Decimal | None] = Field(default_factory=dict, description="Cifras citables del criterio")
    supports: list[str] = Field(default_factory=list, description="evidence_id de consultas o IDs de fragmentos")


class CausalResult(_Strict):
    evidence_id: str
    cause: str
    cause_kind: CauseKind
    metric: str
    filters: dict[str, list[str]]
    compare: Comparison
    locate_by: str
    cause_metric: str | None = None
    cause_direction: CauseDirection | None = None
    claimed_segment: str | None = None
    criteria: list[CriterionResult]
    verdict: CausalVerdict
    observations: list[ValidatedObservation] = Field(default_factory=list)
    discarded: list[DiscardedItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    queries: list[MetricResult] = Field(default_factory=list)
    fragments: list[SourceFragment] = Field(default_factory=list, description="Fragmentos de las observaciones validadas")
