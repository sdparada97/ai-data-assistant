"""Requisito: Expresiones de período."""

from __future__ import annotations

import pytest

from analyst_backend.analytics.models import QueryError
from analyst_backend.analytics.periods import VALID_FORMS, is_valid_month, normalize_period, resolve_period


def test_quarter() -> None:
    assert resolve_period("2026-T1") == ["2026-01", "2026-02", "2026-03"]
    assert resolve_period("2026-T4") == ["2026-10", "2026-11", "2026-12"]


def test_semester() -> None:
    assert resolve_period("2026-S1") == [f"2026-{m:02d}" for m in range(1, 7)]
    assert resolve_period("2026-S2") == [f"2026-{m:02d}" for m in range(7, 13)]


def test_year_and_month() -> None:
    assert resolve_period("2026") == [f"2026-{m:02d}" for m in range(1, 13)]
    assert resolve_period("2026-05") == ["2026-05"]


def test_lowercase_and_spaces_are_normalised() -> None:
    assert resolve_period(" 2026-t2 ") == ["2026-04", "2026-05", "2026-06"]
    assert normalize_period(" 2026-t2 ") == "2026-T2"


@pytest.mark.parametrize("expression", ["2026-T5", "T1", "2026-13", "primer trimestre", "2026-S3", ""])
def test_invalid_forms_list_valid_forms(expression: str) -> None:
    with pytest.raises(QueryError) as error:
        resolve_period(expression, "compare.base")

    assert error.value.field == "compare.base"
    assert error.value.valid_options == VALID_FORMS
    assert "AAAA-T1" in str(error.value)


@pytest.mark.parametrize(("value", "valid"), [("2026-05", True), ("2026-13", False), ("", False), (None, False)])
def test_is_valid_month(value: str | None, valid: bool) -> None:
    assert is_valid_month(value) is valid
