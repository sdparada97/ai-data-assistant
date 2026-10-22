"""Validaciones de forma de los modelos y evidence_id (base de los requisitos de
Validación de la consulta y Trazabilidad de los resultados)."""

from __future__ import annotations

import re

import pytest
from pydantic import ValidationError

from analyst_backend.analytics.evidence import evidence_id
from analyst_backend.analytics.models import MetricQuery, QueryError


def test_period_and_compare_are_exclusive() -> None:
    with pytest.raises(ValidationError, match="excluyentes"):
        MetricQuery(metrics=["venta_neta"], period="2026-T1", compare={"base": "2026-T1", "target": "2026-T2"})


def test_one_of_period_or_compare_is_required() -> None:
    with pytest.raises(ValidationError, match="excluyentes"):
        MetricQuery(metrics=["venta_neta"])


def test_metrics_cannot_be_empty() -> None:
    with pytest.raises(ValidationError, match="metrics"):
        MetricQuery(metrics=[], period="2026-T1")


def test_limit_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="limit"):
        MetricQuery(metrics=["venta_neta"], period="2026-T1", limit=0)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="sql"):
        MetricQuery(metrics=["venta_neta"], period="2026-T1", sql="SELECT 1")


def test_tool_schema_has_no_concrete_periods() -> None:
    schema = str(MetricQuery.model_json_schema())

    assert not re.search(r"\d{4}-(T|S)?\d", schema)
    assert "AAAA-Tn" in schema


def test_query_error_is_structured() -> None:
    error = QueryError("filters.region", "Valor desconocido", "Caribe", ("Norte", "Sur"))

    assert error.to_dict() == {
        "field": "filters.region",
        "message": "Valor desconocido",
        "invalid_value": "Caribe",
        "valid_options": ["Norte", "Sur"],
    }


def test_evidence_id_format_and_determinism() -> None:
    first = evidence_id("consultar_metrica", {"b": 1, "a": [1, 2]}, "ing", "sem")
    second = evidence_id("consultar_metrica", {"a": [1, 2], "b": 1}, "ing", "sem")

    assert re.fullmatch(r"EV-[0-9a-f]{12}", first)
    assert first == second


@pytest.mark.parametrize(
    "changed",
    [
        ("calidad_datos", {"a": [1, 2]}, "ing", "sem"),
        ("consultar_metrica", {"a": [2, 1]}, "ing", "sem"),
        ("consultar_metrica", {"a": [1, 2]}, "otra", "sem"),
        ("consultar_metrica", {"a": [1, 2]}, "ing", "otra"),
    ],
)
def test_evidence_id_changes_with_each_input(changed: tuple) -> None:
    assert evidence_id("consultar_metrica", {"a": [1, 2]}, "ing", "sem") != evidence_id(*changed)
