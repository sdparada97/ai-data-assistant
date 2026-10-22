"""Contexto de la planificación, leído en cada ejecución (nada escrito en el código):

- el catálogo de la capa semántica (métricas, dimensiones, valores válidos y alias);
- los documentos cargados;
- el rango de meses y trimestres con datos en la base de ventas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyst_backend.analytics.database import open_readonly
from analyst_backend.analytics.periods import is_valid_month
from analyst_backend.analytics.semantic import RatioMetric, SemanticLayer
from analyst_backend.documents.retrieval import open_documents_db


@dataclass(frozen=True)
class DataRange:
    first_month: str
    last_month: str
    quarters: tuple[str, ...]
    years: frozenset[int]

    def describe(self) -> str:
        return f"Datos disponibles: de {self.first_month} a {self.last_month} (trimestres {', '.join(self.quarters)})."


@dataclass(frozen=True)
class PlanningContext:
    catalog: str
    documents: str
    data_range: DataRange
    document_ids: tuple[str, ...] = ()  # la verificación los ignora al buscar cifras


def data_range(duckdb_path: Path) -> DataRange:
    """Primer y último mes válidos de `sales` y los trimestres que cubren, completos o en parte."""
    with open_readonly(duckdb_path) as connection:
        months = sorted(
            month for (month,) in connection.execute("SELECT DISTINCT mes FROM sales").fetchall() if is_valid_month(month)
        )
    if not months:
        raise ValueError(f"La base de ventas {duckdb_path} no tiene meses válidos")
    quarters = tuple(dict.fromkeys(f"{month[:4]}-T{(int(month[5:7]) - 1) // 3 + 1}" for month in months))
    return DataRange(months[0], months[-1], quarters, frozenset(int(month[:4]) for month in months))


def catalog_text(layer: SemanticLayer) -> str:
    lines = ["Métricas:"]
    for name, metric in layer.metrics.items():
        kind = "cociente" if isinstance(metric, RatioMetric) else "agregada"
        lines.append(f"- {name} ({kind}, {metric.unit}): {metric.description}")
    lines.append("Dimensiones y valores válidos:")
    for name, dimension in layer.dimensions.items():
        if dimension.values:
            values = ", ".join(dimension.values)
        elif dimension.time:
            values = "meses AAAA-MM (filtra con los períodos, no con esta dimensión)"
        else:
            values = "valores libres"
        aliases = f"; alias: {', '.join(f'{a} = {v}' for a, v in dimension.aliases.items())}" if dimension.aliases else ""
        lines.append(f"- {name}: {values}{aliases}. {dimension.description}")
    lines.append("Períodos: AAAA, AAAA-S1/S2 (semestres), AAAA-T1..T4 (trimestres) o AAAA-MM.")
    return "\n".join(lines)


def _document_rows(documents_db_path: Path) -> list[tuple[str, str, str]]:
    with open_documents_db(documents_db_path) as connection:
        return connection.execute("SELECT doc_id, source_type, title FROM documents ORDER BY doc_id").fetchall()


def build_planning_context(layer: SemanticLayer, duckdb_path: Path, documents_db_path: Path) -> PlanningContext:
    rows = _document_rows(documents_db_path)
    documents = "\n".join(f"- {doc_id} ({source_type}): {title}" for doc_id, source_type, title in rows)
    return PlanningContext(catalog_text(layer), documents, data_range(duckdb_path), tuple(doc_id for doc_id, _, _ in rows))
