"""Expresiones de período resueltas con reglas de calendario.

Formas válidas: ``AAAA`` (año), ``AAAA-S1``/``AAAA-S2`` (semestre), ``AAAA-T1`` a
``AAAA-T4`` (trimestre de calendario) y ``AAAA-MM`` (mes). No hay años ni meses
concretos en el código.
"""

from __future__ import annotations

import re

from analyst_backend.analytics.models import QueryError

VALID_FORMS = ("AAAA", "AAAA-S1", "AAAA-S2", "AAAA-T1", "AAAA-T2", "AAAA-T3", "AAAA-T4", "AAAA-MM")
_YEAR = re.compile(r"^(\d{4})$")
_SEMESTER = re.compile(r"^(\d{4})-S([12])$")
_QUARTER = re.compile(r"^(\d{4})-T([1-4])$")
_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
MONTHS_PER_SEMESTER, MONTHS_PER_QUARTER = 6, 3


def _months(year: str, first: int, count: int) -> list[str]:
    return [f"{year}-{month:02d}" for month in range(first, first + count)]


def resolve_period(expression: str, field_name: str = "period") -> list[str]:
    """Devuelve los meses ``AAAA-MM`` del período, en orden."""
    text = expression.strip().upper()
    if match := _YEAR.match(text):
        return _months(match.group(1), 1, 12)
    if match := _SEMESTER.match(text):
        return _months(match.group(1), (int(match.group(2)) - 1) * MONTHS_PER_SEMESTER + 1, MONTHS_PER_SEMESTER)
    if match := _QUARTER.match(text):
        return _months(match.group(1), (int(match.group(2)) - 1) * MONTHS_PER_QUARTER + 1, MONTHS_PER_QUARTER)
    if match := _MONTH.match(text):
        return [f"{match.group(1)}-{match.group(2)}"]
    raise QueryError(
        field_name,
        f"Período inválido: {expression!r}. Formas válidas: {', '.join(VALID_FORMS)}",
        expression,
        VALID_FORMS,
    )


def normalize_period(expression: str, field_name: str = "period") -> str:
    """Forma canónica (mayúsculas, sin espacios) tras comprobar que es válida."""
    resolve_period(expression, field_name)
    return expression.strip().upper()


def is_valid_month(value: str | None) -> bool:
    return bool(value) and bool(_MONTH.match(value or ""))
