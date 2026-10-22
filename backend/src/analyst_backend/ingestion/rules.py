"""Reglas de calidad de la ingesta (aprobadas en docs/EXPLORACION_DATOS.md).

Contrato común: cada regla recibe el DataFrame de trabajo (columnas del CSV como
texto más ``source_line``) y devuelve un ``RuleResult`` con:

- ``mask``: filas que la regla retiene, excluye o elimina (``False`` en las reglas
  que solo corrigen o avisan);
- ``issues``: incidencias para ``dq_issues``;
- ``frame``: el DataFrame corregido, solo en las reglas que corrigen valores.

Las reglas no deciden el destino final ni la ``action`` de las incidencias de
severidad ``error``: eso lo hace ``pipeline.py`` con la precedencia de la spec.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from analyst_backend.ingestion.catalog import CATALOG_DIMENSIONS, Catalog

TEXT_COLUMNS = ("registro_id", "mes", "marca", "region", "canal", "punto_venta_id", "presentacion")
COMPARED_COLUMNS = (*TEXT_COLUMNS, "unidades", "venta_neta_cop")
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
INTEGER_PATTERN = re.compile(r"^-?\d+$")

ISSUE_COLUMNS = (
    "issue_id",
    "registro_id",
    "source_line",
    "rule_code",
    "issue_type",
    "severity",
    "column_name",
    "original_value",
    "new_value",
    "action",
    "affected_net_sales_cop",
    "details",
    "ingestion_id",
)

CORRECTION, ERROR, WARNING = "correccion", "error", "aviso"
CORRECTED, NO_ACTION = "corregida", "ninguna"


@dataclass(frozen=True)
class Issue:
    """Una actuación de una regla sobre una fila (o una columna de una fila)."""

    registro_id: str
    source_line: int
    rule_code: str
    issue_type: str
    severity: str
    column_name: str | None = None
    original_value: str | None = None
    new_value: str | None = None
    details: dict[str, Any] | None = None

    @property
    def action(self) -> str | None:
        """Acción fija para correcciones y avisos; ``None`` para errores (la decide el destino)."""
        return {CORRECTION: CORRECTED, WARNING: NO_ACTION}.get(self.severity)

    def details_json(self) -> str | None:
        return None if self.details is None else json.dumps(self.details, ensure_ascii=False, sort_keys=True)


@dataclass
class RuleResult:
    mask: pd.Series
    issues: list[Issue] = field(default_factory=list)
    frame: pd.DataFrame | None = None


def parse_integer(value: str) -> int | None:
    """Entero estricto (``^-?\\d+$``); ``None`` si el texto no lo es."""
    return int(value) if INTEGER_PATTERN.match(value) else None


def _no_rows(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=frame.index)


def _row_issue(row: pd.Series, **fields: Any) -> Issue:
    return Issue(registro_id=row["registro_id"], source_line=int(row["source_line"]), **fields)


# --- DQ03 -----------------------------------------------------------------------


def trim_whitespace(frame: pd.DataFrame) -> RuleResult:
    """DQ03: recorta espacios al inicio y al final de las columnas de texto."""
    trimmed = frame.copy()
    registro_ids = frame["registro_id"].str.strip()
    issues: list[Issue] = []
    for column in TEXT_COLUMNS:
        stripped = frame[column].str.strip()
        changed = stripped != frame[column]
        for index in frame.index[changed]:
            issues.append(
                Issue(
                    registro_id=registro_ids[index],
                    source_line=int(frame.at[index, "source_line"]),
                    rule_code="DQ03",
                    issue_type="espacios_sobrantes",
                    severity=CORRECTION,
                    column_name=column,
                    original_value=frame.at[index, column],
                    new_value=stripped[index],
                )
            )
        trimmed[column] = stripped
    issues.sort(key=lambda issue: (issue.source_line, TEXT_COLUMNS.index(issue.column_name or "")))
    return RuleResult(mask=_no_rows(frame), issues=issues, frame=trimmed)


# --- DQ01 -----------------------------------------------------------------------


def find_duplicates(frame: pd.DataFrame) -> RuleResult:
    """DQ01: conserva la primera aparición de cada ``registro_id`` y marca las demás."""
    ordered = frame.sort_values("source_line", kind="stable")
    removed = ordered["registro_id"].duplicated(keep="first").reindex(frame.index)
    first_index = ordered.drop_duplicates("registro_id", keep="first").set_index("registro_id", drop=False)
    issues: list[Issue] = []
    for index in ordered.index[removed[ordered.index]]:
        row = frame.loc[index]
        kept = first_index.loc[row["registro_id"]]
        differences = {
            column: [kept[column], row[column]] for column in COMPARED_COLUMNS if kept[column] != row[column]
        }
        issues.append(
            _row_issue(
                row,
                rule_code="DQ01",
                issue_type="duplicado_con_diferencias" if differences else "duplicado_identico",
                severity=ERROR,
                column_name="registro_id",
                original_value=row["registro_id"],
                details={"kept_source_line": int(kept["source_line"]), "differences": differences},
            )
        )
    return RuleResult(mask=removed, issues=issues)


# --- DQ04 -----------------------------------------------------------------------


def apply_catalog(frame: pd.DataFrame, catalog: Catalog) -> RuleResult:
    """DQ04: normaliza la escritura contra el catálogo; lo que no está en él va a revisión."""
    normalized = frame.copy()
    invalid = _no_rows(frame)
    issues: list[Issue] = []
    for index, row in frame.iterrows():
        for column in CATALOG_DIMENSIONS:
            value = row[column]
            canonical = catalog.canonical(column, value)
            if canonical is None:
                invalid[index] = True
                issues.append(
                    _row_issue(
                        row,
                        rule_code="DQ04",
                        issue_type="valor_no_valido",
                        severity=ERROR,
                        column_name=column,
                        original_value=value,
                    )
                )
            elif canonical != value:
                normalized.at[index, column] = canonical
                issues.append(
                    _row_issue(
                        row,
                        rule_code="DQ04",
                        issue_type="escritura_no_canonica",
                        severity=CORRECTION,
                        column_name=column,
                        original_value=value,
                        new_value=canonical,
                    )
                )
    return RuleResult(mask=invalid, issues=issues, frame=normalized)


# --- DQ05 -----------------------------------------------------------------------


def check_month(frame: pd.DataFrame) -> RuleResult:
    """DQ05: ``mes`` debe ser ``AAAA-MM`` con mes 01–12."""
    invalid = ~frame["mes"].map(lambda value: bool(MONTH_PATTERN.match(value)))
    issues = [
        _row_issue(row, rule_code="DQ05", issue_type="mes_invalido", severity=ERROR,
                   column_name="mes", original_value=row["mes"])
        for _, row in frame[invalid].iterrows()
    ]
    return RuleResult(mask=invalid, issues=issues)


# --- DQ06 y DQ07 ----------------------------------------------------------------


def _check_integer(frame: pd.DataFrame, column: str, rule_code: str, issue_type: str) -> RuleResult:
    invalid = frame[column].map(parse_integer).isna()
    issues = [
        _row_issue(row, rule_code=rule_code, issue_type=issue_type, severity=ERROR,
                   column_name=column, original_value=row[column])
        for _, row in frame[invalid].iterrows()
    ]
    return RuleResult(mask=invalid, issues=issues)


def check_units(frame: pd.DataFrame) -> RuleResult:
    """DQ06: unidades vacías o no enteras excluyen la fila."""
    return _check_integer(frame, "unidades", "DQ06", "unidades_faltantes")


def check_sales(frame: pd.DataFrame) -> RuleResult:
    """DQ07: venta neta vacía o no entera excluye la fila."""
    return _check_integer(frame, "venta_neta_cop", "DQ07", "venta_faltante")


# --- DQ08 y DQ13 ----------------------------------------------------------------


def check_negative(frame: pd.DataFrame) -> RuleResult:
    """DQ08: unidades o venta negativas envían la fila a revisión (una incidencia por fila)."""
    flagged = _no_rows(frame)
    issues: list[Issue] = []
    for index, row in frame.iterrows():
        negative = [c for c in ("unidades", "venta_neta_cop") if (parse_integer(row[c]) or 0) < 0]
        if negative:
            flagged[index] = True
            issues.append(_row_issue(row, rule_code="DQ08", issue_type="valor_negativo", severity=ERROR,
                                     details={"columns": negative}))
    return RuleResult(mask=flagged, issues=issues)


def check_sales_without_units(frame: pd.DataFrame) -> RuleResult:
    """DQ13: 0 unidades con venta positiva envía la fila a revisión."""
    units = frame["unidades"].map(parse_integer).astype("Int64")
    sales = frame["venta_neta_cop"].map(parse_integer).astype("Int64")
    flagged = ((units == 0) & (sales > 0)).fillna(False).astype(bool)
    issues = [
        _row_issue(row, rule_code="DQ13", issue_type="venta_sin_unidades", severity=ERROR,
                   column_name="unidades", original_value=row["unidades"])
        for _, row in frame[flagged].iterrows()
    ]
    return RuleResult(mask=flagged, issues=issues)


# --- DQ11 y DQ12 (solo avisan) --------------------------------------------------


def _as_number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else float(value)


def flag_single_point_of_sale(frame: pd.DataFrame) -> list[Issue]:
    """DQ11: aviso por cada fila cuyo ``punto_venta_id`` aparece una sola vez en el CSV."""
    counts = frame["punto_venta_id"].value_counts()
    issues: list[Issue] = []
    for _, row in frame.sort_values("source_line").iterrows():
        point_of_sale = row["punto_venta_id"]
        if counts[point_of_sale] != 1:
            continue
        others = counts.drop(point_of_sale)
        median = _as_number(others.median()) if len(others) else None
        issues.append(
            _row_issue(
                row,
                rule_code="DQ11",
                issue_type="punto_venta_unico",
                severity=WARNING,
                column_name="punto_venta_id",
                original_value=point_of_sale,
                details={"occurrences": 1, "median_occurrences": median},
            )
        )
    return issues


def flag_price_outliers(sales: pd.DataFrame, threshold: float) -> list[Issue]:
    """DQ12: aviso si ``|precio / mediana - 1|`` supera el umbral.

    ``sales`` son las filas destinadas a la tabla ``sales`` (``unidades`` y
    ``venta_neta_cop`` ya enteras). Solo se evalúan las filas con ``unidades > 0``,
    y la mediana se calcula sobre esas mismas filas por marca y presentación.
    """
    evaluated = sales[sales["unidades"] > 0].copy()
    if evaluated.empty:
        return []
    evaluated["price"] = evaluated["venta_neta_cop"] / evaluated["unidades"]
    evaluated["median"] = evaluated.groupby(["marca", "presentacion"])["price"].transform("median")
    evaluated = evaluated[evaluated["median"] > 0]
    evaluated["deviation"] = (evaluated["price"] / evaluated["median"] - 1).abs()
    flagged = evaluated[evaluated["deviation"] > threshold].sort_values("source_line")
    return [
        _row_issue(
            row,
            rule_code="DQ12",
            issue_type="precio_atipico",
            severity=WARNING,
            details={
                "unit_price": round(float(row["price"]), 4),
                "median_unit_price": round(float(row["median"]), 4),
                "deviation": round(float(row["deviation"]), 6),
                "threshold": threshold,
            },
        )
        for _, row in flagged.iterrows()
    ]
