"""Herramienta ``consultar_metrica``: métricas de un período o comparación entre dos.

El LLM solo elige parámetros; este módulo los valida contra la capa semántica, genera
el SQL (identificadores del YAML, valores enlazados) y calcula variaciones con
``Decimal``. Nunca recibe SQL como entrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from analyst_backend.analytics.database import open_readonly, published_ingestion_id
from analyst_backend.analytics.evidence import evidence_id
from analyst_backend.analytics.models import (
    ComparisonCell,
    MetricCell,
    MetricQuery,
    MetricResult,
    MetricRow,
    QualityNote,
    QueryError,
)
from analyst_backend.analytics.periods import is_valid_month, normalize_period, resolve_period
from analyst_backend.analytics.semantic import AggregateMetric, RatioMetric, SemanticLayer
from analyst_backend.ingestion.rules import CORRECTION, ERROR, WARNING

TOOL = "consultar_metrica"
PCT_DECIMALS = 2
HUNDRED = Decimal(100)
MONTH_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"
NOTE_COLUMNS = (
    "registro_id", "source_line", "rule_code", "issue_type", "severity", "action", "affected_net_sales_cop",
    "mes", "marca", "region", "canal", "presentacion", "punto_venta_id",
    "column_name", "original_value", "new_value", "details",
)  # fmt: skip


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _round(value: Decimal | None, decimals: int) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


# --- Plan: consulta validada y normalizada ----------------------------------------------------


@dataclass(frozen=True)
class Plan:
    metrics: list[str]
    filters: dict[str, list[str]]
    group_by: list[str]
    periods: dict[str, list[str]]  # clave interna (p0, p1) → meses
    labels: dict[str, str]  # clave interna → período normalizado
    compare: bool
    sort: dict[str, str] | None
    limit: int | None
    normalized: dict[str, Any]


def resolve_filters(layer: SemanticLayer, filters: dict[str, list[str]]) -> dict[str, list[str]]:
    """Valida dimensiones y valores; devuelve valores con la escritura del catálogo, ordenados."""
    resolved: dict[str, list[str]] = {}
    for name, values in filters.items():
        dimension = layer.dimension(name, "filters")
        if dimension.time:
            raise QueryError(
                f"filters.{name}",
                f"No se filtra por {name}: los meses se piden con `period` o `compare`",
                name,
            )
        if not values:
            raise QueryError(f"filters.{name}", f"El filtro {name} no tiene valores", values)
        resolved[name] = sorted({dimension.resolve(value, f"filters.{name}") for value in values})
    return dict(sorted(resolved.items()))


def build_plan(query: MetricQuery, layer: SemanticLayer) -> Plan:
    metrics = sorted(set(query.metrics))
    for name in metrics:
        layer.metric(name)
    filters = resolve_filters(layer, query.filters)
    group_by = sorted(set(query.group_by))
    for name in group_by:
        layer.dimension(name, "group_by")
    if query.compare is not None:
        labels = {
            "p0": normalize_period(query.compare.base, "compare.base"),
            "p1": normalize_period(query.compare.target, "compare.target"),
        }
    else:
        labels = {"p0": normalize_period(query.period or "", "period")}
    periods = {key: resolve_period(label) for key, label in labels.items()}
    compare = query.compare is not None
    sort = None
    if query.sort is not None:
        if query.sort.metric not in metrics:
            raise QueryError("sort.metric", "La métrica de orden debe estar entre las pedidas", query.sort.metric, metrics)
        if not compare and query.sort.field != "value":
            raise QueryError("sort.field", "var_abs y var_pct solo existen al comparar períodos", query.sort.field, ["value"])
        sort = {"metric": query.sort.metric, "field": query.sort.field, "order": query.sort.order}
    normalized: dict[str, Any] = {
        "metrics": metrics,
        "filters": filters,
        "group_by": group_by,
        "sort": sort,
        "limit": query.limit,
    }
    if compare:
        normalized["compare"] = {"base": labels["p0"], "target": labels["p1"]}
    else:
        normalized["period"] = labels["p0"]
    return Plan(metrics, filters, group_by, periods, labels, compare, sort, query.limit, normalized)


# --- SQL -------------------------------------------------------------------------------------------


def build_sql(plan: Plan, layer: SemanticLayer) -> tuple[str, list[str], list[AggregateMetric]]:
    """Una rama por período (UNION ALL) y GROUPING SETS para grupos y total.

    Las ramas permiten períodos solapados y expresiones con varias agregaciones.
    """
    aggregates = layer.aggregates_for(plan.metrics)
    params: list[str] = []
    branches = []
    for key, months in plan.periods.items():
        conditions = [f"mes IN ({', '.join('?' for _ in months)})"]
        params.extend(months)
        for dimension, values in plan.filters.items():
            conditions.append(f"{quote_identifier(dimension)} IN ({', '.join('?' for _ in values)})")
            params.extend(values)
        branches.append(f"SELECT '{key}' AS __period, * FROM sales WHERE {' AND '.join(conditions)}")
    dims = [quote_identifier(d) for d in plan.group_by]
    measures = [f"{a.expression} AS {quote_identifier('m__' + a.name)}" for a in aggregates]
    grouping = f"GROUPING({', '.join(dims)})" if dims else "0"
    group_clause = (
        f"GROUP BY GROUPING SETS ((__period, {', '.join(dims)}), (__period))" if dims else "GROUP BY __period"
    )
    sql = (
        "WITH scoped AS (\n  " + "\n  UNION ALL\n  ".join(branches) + "\n)\n"
        f"SELECT __period, {grouping} AS __is_total, "
        + "".join(f"{d}, " for d in dims)
        + ", ".join([*measures, "COUNT(*) AS __rows"])
        + f"\nFROM scoped\n{group_clause}"
    )
    return sql, params, aggregates


# --- Cálculo de celdas ------------------------------------------------------------------------------


def _metric_values(
    layer: SemanticLayer, metrics: list[str], aggregates: dict[str, Any] | None
) -> dict[str, Decimal | None]:
    """Valores exactos por métrica para un grupo y período; ``None`` si no hay filas."""
    values: dict[str, Decimal | None] = {}
    for name in metrics:
        metric = layer.metric(name)
        if aggregates is None:
            values[name] = None
        elif isinstance(metric, RatioMetric):
            numerator, denominator = aggregates[metric.numerator], aggregates[metric.denominator]
            values[name] = (
                None if numerator is None or not denominator else Decimal(numerator) / Decimal(denominator)
            )
        else:
            raw = aggregates[name]
            values[name] = None if raw is None else Decimal(raw)
    return values


def _single_cell(value: Decimal | None, decimals: int) -> MetricCell:
    return MetricCell(value=_round(value, decimals), value_exact=value)


def _comparison_cell(base: Decimal | None, target: Decimal | None, decimals: int) -> tuple[ComparisonCell, bool]:
    var_abs = None if base is None or target is None else target - base
    var_pct = None if base is None or target is None or base == 0 else (target / base - 1) * HUNDRED
    cell = ComparisonCell(
        base=_round(base, decimals),
        base_exact=base,
        target=_round(target, decimals),
        target_exact=target,
        var_abs=_round(var_abs, decimals),
        var_abs_exact=var_abs,
        var_pct=_round(var_pct, PCT_DECIMALS),
        var_pct_exact=var_pct,
    )
    return cell, var_pct is None


def _describe(group: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in group.items()) if group else "el corte consultado"


# --- Herramienta -------------------------------------------------------------------------------------


def consultar_metrica(query: MetricQuery, layer: SemanticLayer, duckdb_path: Path) -> MetricResult:
    plan = build_plan(query, layer)
    sql, params, aggregates = build_sql(plan, layer)
    with open_readonly(duckdb_path) as connection:
        ingestion_id = published_ingestion_id(connection)
        months_with_data = {row[0] for row in connection.execute("SELECT DISTINCT mes FROM sales").fetchall()}
        cursor = connection.execute(sql, params)
        columns = [c[0] for c in cursor.description]
        records = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        notes, corrections = _quality_notes(connection, plan)

    warnings: list[str] = []
    empty_periods: set[str] = set()
    for key, months in plan.periods.items():
        label = plan.labels[key]
        missing = [m for m in months if m not in months_with_data]
        if len(missing) == len(months):
            empty_periods.add(key)
            warnings.append(f"El período {label} no tiene datos en la base")
        elif missing:
            warnings.append(f"El período {label} no tiene datos para los meses: {', '.join(missing)}")

    # Agregados por (grupo, período); los grupos salen de los datos.
    by_group: dict[tuple[str, ...], dict[str, dict[str, Any]]] = {}
    for record in records:
        group_key = () if record["__is_total"] else tuple(str(record[d]) for d in plan.group_by)
        if record["__rows"]:
            by_group.setdefault(group_key, {})[record["__period"]] = {
                a.name: record["m__" + a.name] for a in aggregates
            }
    group_keys = sorted(k for k in by_group if k) if plan.group_by else []

    def make_row(group_key: tuple[str, ...], is_total: bool) -> MetricRow:
        group = dict(zip(plan.group_by, group_key, strict=True)) if not is_total else {}
        per_period = by_group.get(() if is_total else group_key, {})
        for key in plan.periods:
            if key not in per_period and key not in empty_periods:
                warnings.append(f"Sin datos para {_describe(group)} en {plan.labels[key]}")
        cells: dict[str, MetricCell | ComparisonCell] = {}
        for name in plan.metrics:
            decimals = layer.metric(name).decimals
            if plan.compare:
                base = _metric_values(layer, [name], per_period.get("p0"))[name]
                target = _metric_values(layer, [name], per_period.get("p1"))[name]
                cell, undefined = _comparison_cell(base, target, decimals)
                if undefined:
                    warnings.append(f"Variación no definida de {name} para {_describe(group)}")
                cells[name] = cell
            else:
                cells[name] = _single_cell(_metric_values(layer, [name], per_period.get("p0"))[name], decimals)
        return MetricRow(group=group, is_total=is_total, metrics=cells)

    total = make_row((), is_total=True)
    rows = [make_row(key, is_total=False) for key in group_keys] if plan.group_by else [total]
    if plan.group_by:
        rows = _sort_and_rank(rows, plan)

    return MetricResult(
        evidence_id=evidence_id(TOOL, plan.normalized, ingestion_id, layer.fingerprint),
        ingestion_id=ingestion_id,
        query=plan.normalized,
        periods={plan.labels[k]: months for k, months in plan.periods.items()},
        rows=rows,
        total=total,
        warnings=list(dict.fromkeys(warnings)),
        quality_notes=notes,
        corrections_count=corrections,
        sql=sql,
        sql_params=params,
    )


def _sort_value(row: MetricRow, plan: Plan) -> Decimal | None:
    sort = plan.sort
    if sort is None:
        return None
    cell = row.metrics[sort["metric"]]
    field = sort["field"]
    if isinstance(cell, ComparisonCell):
        return {"value": cell.target_exact, "var_abs": cell.var_abs_exact, "var_pct": cell.var_pct_exact}[field]
    return cell.value_exact


def _sort_and_rank(rows: list[MetricRow], plan: Plan) -> list[MetricRow]:
    """Ranking de competición (1, 1, 3); nulos al final sin rank; limit tras ordenar."""
    if plan.sort is None:
        ordered = rows
    else:
        with_value = [(row, _sort_value(row, plan)) for row in rows]
        ranked = [item for item in with_value if item[1] is not None]
        ranked.sort(key=lambda item: item[1], reverse=plan.sort["order"] == "desc")  # type: ignore[arg-type,return-value]
        nulls = [row for row, value in with_value if value is None]
        ordered = []
        previous: Decimal | None = None
        rank = 0
        for position, (row, value) in enumerate(ranked, start=1):
            if value != previous:
                rank, previous = position, value
            ordered.append(row.model_copy(update={"rank": rank}))
        ordered.extend(nulls)
    return ordered[: plan.limit] if plan.limit else ordered


# --- Avisos de calidad -------------------------------------------------------------------------------


def _issue_filter(plan_filters: dict[str, list[str]], months: list[str]) -> tuple[str, list[Any]]:
    """Condición sobre dq_issues: dimensiones del corte y mes en los períodos o inválido."""
    conditions, params = [], []
    for dimension, values in plan_filters.items():
        conditions.append(f"{quote_identifier(dimension)} IN ({', '.join('?' for _ in values)})")
        params.extend(values)
    month_clause = "NOT regexp_full_match(coalesce(mes, ''), ?)"
    params_months: list[Any] = []
    if months:
        month_clause = f"(mes IN ({', '.join('?' for _ in months)}) OR {month_clause})"
        params_months.extend(months)
    conditions.append(month_clause)
    return " AND ".join(conditions), [*params, *params_months, MONTH_REGEX]


def _quality_notes(connection: Any, plan: Plan) -> tuple[list[QualityNote], int]:
    months = sorted({m for period in plan.periods.values() for m in period})
    condition, params = _issue_filter(plan.filters, months)
    rows = connection.execute(
        f"SELECT {', '.join(NOTE_COLUMNS)} FROM dq_issues "
        f"WHERE severity IN (?, ?) AND {condition} ORDER BY source_line, rule_code",
        [ERROR, WARNING, *params],
    ).fetchall()
    notes = [
        QualityNote(**dict(zip(NOTE_COLUMNS, row, strict=True)), outside_periods=not is_valid_month(row[7]))
        for row in rows
    ]
    corrections = connection.execute(
        f"SELECT count(*) FROM dq_issues WHERE severity = ? AND {condition}", [CORRECTION, *params]
    ).fetchone()
    return notes, int(corrections[0]) if corrections else 0
