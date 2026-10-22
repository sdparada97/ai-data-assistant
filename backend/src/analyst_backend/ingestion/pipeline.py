"""Orquestación de la ingesta: lectura, reglas, destino de cada fila y publicación."""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from analyst_backend.ingestion import rules, storage
from analyst_backend.ingestion.catalog import (
    Catalog,
    QualityConfig,
    parse_catalog,
    parse_quality_config,
    read_config_bytes,
)
from analyst_backend.ingestion.errors import IngestionError, InputError, ReconciliationError
from analyst_backend.ingestion.schema import validate_sales
from analyst_backend.settings import IngestionSettings

# Estructura del CSV de ventas (nombres de columna, no valores de negocio).
RAW_COLUMNS = (
    "registro_id",
    "mes",
    "marca",
    "region",
    "canal",
    "punto_venta_id",
    "presentacion",
    "unidades",
    "venta_neta_cop",
)
SOURCE_LINE = "source_line"


def read_csv_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise InputError(f"No existe el archivo de ventas: {path}")
    return path.read_bytes()


def read_sales_csv(path: Path) -> pd.DataFrame:
    """Lee y valida el CSV de ``path`` (ver ``parse_sales_csv``)."""
    return parse_sales_csv(read_csv_bytes(path), path)


def parse_sales_csv(content: bytes, path: Path) -> pd.DataFrame:
    """Interpreta el contenido del CSV como texto y valida su forma.

    Usa el módulo ``csv`` y no ``pandas.read_csv`` porque pandas rellena en silencio
    las filas con campos de menos. Devuelve las 9 columnas en el orden de
    ``RAW_COLUMNS`` más ``source_line`` (línea física del archivo, con el encabezado
    en la línea 1). Las líneas vacías se ignoran.
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InputError(f"El archivo de ventas no es UTF-8: {path} ({error.reason} en el byte {error.start})") from error

    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader, None)
    if header is None:
        raise InputError(f"El archivo de ventas está vacío: {path}")
    header = [name.strip() for name in header]
    _check_header(header, path)

    rows: list[list[str]] = []
    lines: list[int] = []
    for row in reader:
        if not row:
            continue
        if len(row) != len(header):
            raise InputError(
                f"La línea {reader.line_num} de {path} tiene {len(row)} campos y se esperaban {len(header)}"
            )
        rows.append(row)
        lines.append(reader.line_num)
    if not rows:
        raise InputError(f"El archivo de ventas no tiene filas de datos: {path}")

    frame = pd.DataFrame(rows, columns=header, dtype=str)[list(RAW_COLUMNS)]
    frame[SOURCE_LINE] = pd.Series(lines, dtype="int64")
    return frame


def _check_header(header: list[str], path: Path) -> None:
    duplicated = sorted({name for name in header if header.count(name) > 1})
    missing = [name for name in RAW_COLUMNS if name not in header]
    extra = [name for name in header if name not in RAW_COLUMNS]
    problems = []
    if missing:
        problems.append("faltan columnas: " + ", ".join(missing))
    if extra:
        problems.append("sobran columnas: " + ", ".join(extra))
    if duplicated:
        problems.append("columnas repetidas: " + ", ".join(duplicated))
    if problems:
        raise InputError(f"Encabezado inválido en {path}: " + "; ".join(problems))


# --- Reglas y destino de cada fila ------------------------------------------------

SALES, REVIEW, EXCLUDED, REMOVED = "sales", "en_revision", "excluida", "eliminada"
REVIEW_RULES = ("DQ04", "DQ05", "DQ08", "DQ13")
REVIEW_STATUS = "en_revision"
SALES_COLUMNS = (*rules.TEXT_COLUMNS, "unidades", "venta_neta_cop", SOURCE_LINE)
REVIEW_COLUMNS = (*RAW_COLUMNS, SOURCE_LINE, "rule_codes", "reason", "status")


@dataclass(frozen=True)
class RulesOutcome:
    """Resultado de aplicar las reglas, antes de asignar ``ingestion_id``."""

    sales: pd.DataFrame
    review: pd.DataFrame
    issues: pd.DataFrame
    destinations: pd.Series

    def counts(self) -> dict[str, int]:
        by_destination = self.destinations.value_counts()
        return {
            "rows_read": len(self.destinations),
            "rows_sales": len(self.sales),
            "rows_review": len(self.review),
            "rows_excluded": int(by_destination.get(EXCLUDED, 0)),
            "rows_removed": int(by_destination.get(REMOVED, 0)),
        }


def apply_rules(raw: pd.DataFrame, catalog: Catalog, quality: QualityConfig) -> RulesOutcome:
    """Aplica DQ03, DQ01, DQ04–DQ08 y DQ13, asigna destino y añade los avisos DQ11 y DQ12."""
    trimmed = rules.trim_whitespace(raw)
    working = _corrected_frame(trimmed, "DQ03")
    duplicates = rules.find_duplicates(working)
    catalog_result = rules.apply_catalog(working, catalog)
    working = _corrected_frame(catalog_result, "DQ04")
    month = rules.check_month(working)
    units = rules.check_units(working)
    sales_value = rules.check_sales(working)
    negative = rules.check_negative(working)
    without_units = rules.check_sales_without_units(working)

    # Precedencia: eliminada > excluida > en revisión > sales.
    removed = duplicates.mask
    excluded = (units.mask | sales_value.mask) & ~removed
    review = (catalog_result.mask | month.mask | negative.mask | without_units.mask) & ~removed & ~excluded
    destinations = pd.Series(SALES, index=working.index)
    destinations[review] = REVIEW
    destinations[excluded] = EXCLUDED
    destinations[removed] = REMOVED

    sales = _sales_frame(working[destinations == SALES])
    issues = [
        *trimmed.issues,
        *duplicates.issues,
        *catalog_result.issues,
        *month.issues,
        *units.issues,
        *sales_value.issues,
        *negative.issues,
        *without_units.issues,
        *rules.flag_single_point_of_sale(working),
        *rules.flag_price_outliers(sales, quality.price_deviation_threshold),
    ]
    line_destination = dict(zip(working[SOURCE_LINE], destinations, strict=True))
    line_sales = dict(zip(working[SOURCE_LINE], working["venta_neta_cop"].map(rules.parse_integer), strict=True))
    review_rows = raw[destinations == REVIEW]
    return RulesOutcome(
        sales=sales,
        review=_review_frame(review_rows, issues),
        issues=_issues_frame(issues, line_destination, line_sales),
        destinations=destinations,
    )


def _corrected_frame(result: rules.RuleResult, rule_code: str) -> pd.DataFrame:
    if result.frame is None:
        raise IngestionError(f"La regla {rule_code} no devolvió el DataFrame corregido")
    return result.frame


def _sales_frame(rows: pd.DataFrame) -> pd.DataFrame:
    sales = rows[list(SALES_COLUMNS)].copy()
    sales["unidades"] = sales["unidades"].map(rules.parse_integer).astype("int64")
    sales["venta_neta_cop"] = sales["venta_neta_cop"].map(rules.parse_integer).astype("int64")
    return sales.sort_values(SOURCE_LINE).reset_index(drop=True)


def _reason(issue: rules.Issue) -> str:
    if issue.rule_code == "DQ04":
        return f"valor fuera del catálogo en {issue.column_name}: {issue.original_value}"
    if issue.rule_code == "DQ05":
        return f"mes inválido: {issue.original_value}"
    if issue.rule_code == "DQ08":
        columns = ", ".join((issue.details or {}).get("columns", []))
        return f"valores negativos en {columns}"
    return f"venta positiva con {issue.original_value} unidades"


def _review_frame(rows: pd.DataFrame, issues: list[rules.Issue]) -> pd.DataFrame:
    by_line: dict[int, list[rules.Issue]] = {}
    for issue in issues:
        if issue.rule_code in REVIEW_RULES and issue.severity == rules.ERROR:
            by_line.setdefault(issue.source_line, []).append(issue)
    review = rows[list(RAW_COLUMNS) + [SOURCE_LINE]].copy()
    retained = [sorted(by_line.get(int(line), []), key=lambda i: i.rule_code) for line in review[SOURCE_LINE]]
    review["rule_codes"] = [",".join(dict.fromkeys(i.rule_code for i in found)) for found in retained]
    review["reason"] = ["; ".join(_reason(i) for i in found) for found in retained]
    review["status"] = REVIEW_STATUS
    return review[list(REVIEW_COLUMNS)].sort_values(SOURCE_LINE).reset_index(drop=True)


def _issues_frame(
    issues: list[rules.Issue], line_destination: dict[int, str], line_sales: dict[int, int | None]
) -> pd.DataFrame:
    ordered = sorted(issues, key=lambda i: (i.source_line, i.rule_code, i.column_name or ""))
    records = [
        {
            "issue_id": position,
            "registro_id": issue.registro_id,
            "source_line": issue.source_line,
            "rule_code": issue.rule_code,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "column_name": issue.column_name,
            "original_value": issue.original_value,
            "new_value": issue.new_value,
            "action": issue.action or line_destination[issue.source_line],
            "affected_net_sales_cop": line_sales[issue.source_line],
            "details": issue.details_json(),
        }
        for position, issue in enumerate(ordered, start=1)
    ]
    frame = pd.DataFrame(records, columns=[c for c in rules.ISSUE_COLUMNS if c != "ingestion_id"])
    frame["affected_net_sales_cop"] = frame["affected_net_sales_cop"].astype("Int64")
    frame["source_line"] = frame["source_line"].astype("int64")
    frame["issue_id"] = frame["issue_id"].astype("int64")
    return frame


# --- Carga completa -----------------------------------------------------------------

INGESTION_ID_LENGTH = 16


@dataclass(frozen=True)
class IngestionSummary:
    ingestion_id: str
    duckdb_path: Path
    counts: dict[str, int]


def compute_ingestion_id(*contents: bytes) -> str:
    """Identificador determinista: huella SHA-256 del CSV y de la configuración."""
    digest = hashlib.sha256()
    for content in contents:
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()[:INGESTION_ID_LENGTH]


def check_reconciliation(counts: dict[str, int]) -> None:
    """Cada fila leída debe terminar en exactamente un destino."""
    placed = counts["rows_sales"] + counts["rows_review"] + counts["rows_excluded"] + counts["rows_removed"]
    if placed != counts["rows_read"]:
        detail = ", ".join(f"{name}={value}" for name, value in counts.items())
        raise ReconciliationError(f"Las filas no cuadran ({placed} ubicadas de {counts['rows_read']} leídas): {detail}")


def ingest(settings: IngestionSettings, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> IngestionSummary:
    """Carga el CSV, aplica las reglas, valida y publica la base de forma atómica."""
    started_at = now().replace(tzinfo=None)
    # Cada archivo se lee una sola vez: el ingestion_id corresponde exactamente a lo aplicado.
    semantic_bytes = read_config_bytes(settings.semantic_layer_path)
    quality_bytes = read_config_bytes(settings.data_quality_path)
    catalog = parse_catalog(semantic_bytes, settings.semantic_layer_path)
    quality = parse_quality_config(quality_bytes, settings.data_quality_path)
    csv_bytes = read_csv_bytes(settings.sales_csv_path)
    raw = parse_sales_csv(csv_bytes, settings.sales_csv_path)
    outcome = apply_rules(raw, catalog, quality)
    counts = outcome.counts()
    check_reconciliation(counts)

    ingestion_id = compute_ingestion_id(csv_bytes, semantic_bytes, quality_bytes)
    sales = validate_sales(outcome.sales.assign(ingestion_id=ingestion_id), catalog)
    runs = pd.DataFrame(
        [
            {
                "ingestion_id": ingestion_id,
                "source_path": str(settings.sales_csv_path),
                "source_sha256": hashlib.sha256(csv_bytes).hexdigest(),
                "started_at": started_at,
                **counts,
            }
        ]
    )
    tables = {
        "sales": sales,
        "sales_review": outcome.review.assign(ingestion_id=ingestion_id),
        "dq_issues": outcome.issues.assign(ingestion_id=ingestion_id),
        "ingestion_runs": runs,
    }
    storage.publish(settings.duckdb_path, lambda connection: storage.write_tables(connection, tables))
    return IngestionSummary(ingestion_id=ingestion_id, duckdb_path=settings.duckdb_path, counts=counts)
