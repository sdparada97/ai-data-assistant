"""Verificación final de los datos destinados a `sales` (Pandera).

No es el motor de reglas: si algo llega aquí inválido es porque ninguna regla lo
cubrió (por ejemplo, un `registro_id` vacío), y la carga se detiene.
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from analyst_backend.ingestion.catalog import CATALOG_DIMENSIONS, Catalog
from analyst_backend.ingestion.errors import ValidationFailedError
from analyst_backend.ingestion.rules import MONTH_PATTERN

MAX_REPORTED_FAILURES = 20


def _non_empty_text(**kwargs: object) -> pa.Column:
    return pa.Column(str, pa.Check.str_length(min_value=1), nullable=False, **kwargs)


def sales_schema(catalog: Catalog) -> pa.DataFrameSchema:
    columns: dict[str, pa.Column] = {
        "registro_id": _non_empty_text(unique=True),
        "mes": pa.Column(str, pa.Check.str_matches(MONTH_PATTERN.pattern), nullable=False),
        "punto_venta_id": _non_empty_text(),
        "unidades": pa.Column("int64", pa.Check.ge(0), nullable=False),
        "venta_neta_cop": pa.Column("int64", pa.Check.ge(0), nullable=False),
        "source_line": pa.Column("int64", pa.Check.ge(2), nullable=False, unique=True),
        "ingestion_id": _non_empty_text(),
    }
    for dimension in CATALOG_DIMENSIONS:
        columns[dimension] = pa.Column(str, pa.Check.isin(list(catalog.values[dimension])), nullable=False)
    return pa.DataFrameSchema(columns, strict=True)


def validate_sales(frame: pd.DataFrame, catalog: Catalog) -> pd.DataFrame:
    """Valida ``frame`` o lanza ``ValidationFailedError`` con los casos fallidos."""
    try:
        return sales_schema(catalog).validate(frame, lazy=True)
    except pa.errors.SchemaErrors as error:
        cases = error.failure_cases[["column", "check", "failure_case", "index"]].head(MAX_REPORTED_FAILURES)
        listing = "\n".join(
            f"- columna {row.column}: {row.check} (valor {row.failure_case!r}, fila {row.index})"
            for row in cases.itertuples()
        )
        raise ValidationFailedError(
            f"Los datos destinados a `sales` no cumplen el esquema ({len(error.failure_cases)} fallos):\n{listing}"
        ) from error
