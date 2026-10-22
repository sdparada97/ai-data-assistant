"""Herramienta ``calidad_datos``: incidencias y filas en revisión de un corte."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from analyst_backend.analytics.database import DatabaseError, RELOAD_HINT, open_readonly, published_ingestion_id
from analyst_backend.analytics.evidence import evidence_id
from analyst_backend.analytics.metrics import MONTH_REGEX, NOTE_COLUMNS, quote_identifier, resolve_filters
from analyst_backend.analytics.models import (
    IngestionCounts,
    QualityNote,
    QualityQuery,
    QualityResult,
    QueryError,
    RuleActionCount,
)
from analyst_backend.analytics.periods import is_valid_month, normalize_period, resolve_period
from analyst_backend.analytics.semantic import SemanticLayer
from analyst_backend.ingestion.pipeline import REVIEW as REVIEW_ACTION
from analyst_backend.ingestion.rules import CORRECTION

TOOL = "calidad_datos"
RULE_CODE = re.compile(r"^DQ\d{2}$")
REVIEW_COLUMNS = (
    "registro_id", "mes", "marca", "region", "canal", "punto_venta_id", "presentacion",
    "unidades", "venta_neta_cop", "source_line", "rule_codes", "reason", "status",
)  # fmt: skip
COUNT_COLUMNS = ("rows_read", "rows_sales", "rows_review", "rows_excluded", "rows_removed")


def _normalize(query: QualityQuery, layer: SemanticLayer) -> dict[str, Any]:
    rule_codes = sorted({code.strip().upper() for code in query.rule_codes})
    invalid = [code for code in rule_codes if not RULE_CODE.match(code)]
    if invalid:
        raise QueryError("rule_codes", f"Códigos de regla inválidos: {', '.join(invalid)} (forma DQnn)", invalid)
    periods = sorted({normalize_period(p, "periods") for p in query.periods})
    return {
        "filters": resolve_filters(layer, query.filters),
        "periods": periods,
        "rule_codes": rule_codes,
        "include_corrections": query.include_corrections,
    }


def _condition(normalized: dict[str, Any]) -> tuple[str, list[Any]]:
    """Filtro sobre dq_issues: dimensiones de la fila, meses (o mes inválido) y reglas."""
    conditions: list[str] = ["TRUE"]
    params: list[Any] = []
    for dimension, values in normalized["filters"].items():
        conditions.append(f"{quote_identifier(dimension)} IN ({', '.join('?' for _ in values)})")
        params.extend(values)
    months = sorted({m for period in normalized["periods"] for m in resolve_period(period)})
    if months:
        conditions.append(
            f"(mes IN ({', '.join('?' for _ in months)}) OR NOT regexp_full_match(coalesce(mes, ''), ?))"
        )
        params.extend([*months, MONTH_REGEX])
    if normalized["rule_codes"]:
        conditions.append(f"rule_code IN ({', '.join('?' for _ in normalized['rule_codes'])})")
        params.extend(normalized["rule_codes"])
    return " AND ".join(conditions), params


def calidad_datos(query: QualityQuery, layer: SemanticLayer, duckdb_path: Path) -> QualityResult:
    normalized = _normalize(query, layer)
    condition, params = _condition(normalized)
    with open_readonly(duckdb_path) as connection:
        ingestion_id = published_ingestion_id(connection)
        issue_rows = connection.execute(
            f"SELECT {', '.join(NOTE_COLUMNS)} FROM dq_issues WHERE {condition} ORDER BY source_line, rule_code",
            params,
        ).fetchall()
        by_rule_action = connection.execute(
            f"SELECT rule_code, action, count(*) FROM dq_issues WHERE {condition} "
            "GROUP BY rule_code, action ORDER BY rule_code, action",
            params,
        ).fetchall()
        affected = connection.execute(
            f"SELECT action, sum(affected_net_sales_cop) FROM dq_issues WHERE {condition} GROUP BY action ORDER BY action",
            params,
        ).fetchall()
        review = connection.execute(
            f"SELECT {', '.join(REVIEW_COLUMNS)} FROM sales_review WHERE source_line IN ("
            f"SELECT source_line FROM dq_issues WHERE {condition} AND action = ?) ORDER BY source_line",
            [*params, REVIEW_ACTION],
        ).fetchall()
        counts = connection.execute(f"SELECT {', '.join(COUNT_COLUMNS)} FROM ingestion_runs").fetchone()
    if counts is None:
        raise DatabaseError(f"La base no tiene una carga registrada en ingestion_runs. {RELOAD_HINT}")

    severity_index = NOTE_COLUMNS.index("severity")
    month_index = NOTE_COLUMNS.index("mes")
    notes = [
        QualityNote(**dict(zip(NOTE_COLUMNS, row, strict=True)), outside_periods=not is_valid_month(row[month_index]))
        for row in issue_rows
    ]
    corrections = sum(1 for row in issue_rows if row[severity_index] == CORRECTION)
    listed = notes if query.include_corrections else [n for n in notes if n.severity != CORRECTION]
    return QualityResult(
        evidence_id=evidence_id(TOOL, normalized, ingestion_id, layer.fingerprint),
        ingestion_id=ingestion_id,
        query=normalized,
        issue_count=len(notes),
        corrections_count=corrections,
        by_rule_action=[RuleActionCount(rule_code=r, action=a, count=c) for r, a, c in by_rule_action],
        affected_by_action={action: (None if total is None else int(total)) for action, total in affected},
        issues=listed,
        review_rows=[dict(zip(REVIEW_COLUMNS, row, strict=True)) for row in review],
        ingestion=IngestionCounts(**dict(zip(COUNT_COLUMNS, counts, strict=True))),
    )
