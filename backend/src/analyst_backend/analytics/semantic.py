"""Capa semántica: métricas, dimensiones y alias definidos en ``semantic_layer.yaml``.

Las métricas son de dos tipos:

- agregadas: una expresión SQL validada con una lista permitida de tokens;
- cociente: numerador y denominador que son métricas agregadas (se calculan en Python).

Ningún valor de negocio vive aquí: todo sale del YAML.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from analyst_backend.analytics.models import QueryError

# Estructura de la tabla `sales` (nombres de columna, no valores de negocio).
SALES_COLUMNS = (
    "registro_id",
    "mes",
    "marca",
    "region",
    "canal",
    "punto_venta_id",
    "presentacion",
    "unidades",
    "venta_neta_cop",
    "source_line",
    "ingestion_id",
)
# Columnas que pueden declararse como dimensión.
DIMENSION_COLUMNS = ("marca", "region", "canal", "presentacion", "punto_venta_id", "mes")
AGGREGATE_FUNCTIONS = ("SUM", "COUNT")
_TOKEN = re.compile(r"\s*(?:(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<number>\d+(?:\.\d+)?)|(?P<symbol>[(),*+\-/]))")


class SemanticLayerError(ValueError):
    """`semantic_layer.yaml` ausente o inválido."""


@dataclass(frozen=True)
class AggregateMetric:
    name: str
    description: str
    unit: str
    decimals: int
    expression: str


@dataclass(frozen=True)
class RatioMetric:
    name: str
    description: str
    unit: str
    decimals: int
    numerator: str
    denominator: str


Metric = AggregateMetric | RatioMetric


@dataclass(frozen=True)
class Dimension:
    name: str
    description: str
    values: tuple[str, ...] | None = None
    aliases: dict[str, str] = field(default_factory=dict)
    time: bool = False

    def resolve(self, value: str, field_name: str) -> str:
        """Devuelve la escritura del catálogo para ``value`` (mayúsculas y alias)."""
        text = value.strip()
        if self.values is None:
            if not text:
                raise QueryError(field_name, f"Valor vacío en {self.name}", value)
            return text
        folded = text.casefold()
        for candidate in self.values:
            if candidate.casefold() == folded:
                return candidate
        for alias, target in self.aliases.items():
            if alias.casefold() == folded:
                return target
        raise QueryError(
            field_name,
            f"Valor desconocido en {self.name}: {value!r}. Valores válidos: {', '.join(self.values)}",
            value,
            self.values,
        )


@dataclass(frozen=True)
class SemanticLayer:
    metrics: dict[str, Metric]
    dimensions: dict[str, Dimension]
    fingerprint: str

    def metric(self, name: str) -> Metric:
        if name not in self.metrics:
            raise QueryError(
                "metrics",
                f"Métrica desconocida: {name!r}. Métricas válidas: {', '.join(self.metrics)}",
                name,
                tuple(self.metrics),
            )
        return self.metrics[name]

    def dimension(self, name: str, field_name: str) -> Dimension:
        if name not in self.dimensions:
            raise QueryError(
                field_name,
                f"Dimensión desconocida: {name!r}. Dimensiones consultables: {', '.join(self.dimensions)}",
                name,
                tuple(self.dimensions),
            )
        return self.dimensions[name]

    def aggregates_for(self, names: list[str]) -> list[AggregateMetric]:
        """Métricas agregadas que hay que calcular en SQL para ``names`` (sin repetir, en orden)."""
        needed: dict[str, AggregateMetric] = {}
        for name in names:
            metric = self.metric(name)
            parts = [metric.numerator, metric.denominator] if isinstance(metric, RatioMetric) else [name]
            for part in parts:
                aggregate = self.metrics[part]
                if not isinstance(aggregate, AggregateMetric):
                    raise SemanticLayerError(f"{part!r} no es una métrica agregada")
                needed.setdefault(part, aggregate)
        return list(needed.values())


# --- Validación de expresiones ---------------------------------------------------------------


def validate_expression(metric: str, expression: str) -> None:
    """Acepta solo SUM/COUNT, columnas de `sales` dentro de una agregación, números y aritmética."""
    if not expression.strip() or ";" in expression or "--" in expression or "/*" in expression:
        raise SemanticLayerError(f"Métrica {metric}: expresión no permitida: {expression!r}")
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if match is None or match.end() == position:
            if expression[position:].strip() == "":
                break
            raise SemanticLayerError(f"Métrica {metric}: carácter no permitido en {expression!r}")
        kind = match.lastgroup or ""
        tokens.append((kind, match.group(kind)))
        position = match.end()
    depth_stack: list[bool] = []  # True si el paréntesis abre una agregación
    for index, (kind, text) in enumerate(tokens):
        following = tokens[index + 1][1] if index + 1 < len(tokens) else ""
        if kind == "ident" and text.upper() in AGGREGATE_FUNCTIONS:
            if following != "(":
                raise SemanticLayerError(f"Métrica {metric}: {text} debe ir seguido de paréntesis")
            if any(depth_stack):
                raise SemanticLayerError(f"Métrica {metric}: no se permiten agregaciones anidadas ({text} dentro de otra)")
        elif kind == "ident":
            if text not in SALES_COLUMNS:
                raise SemanticLayerError(f"Métrica {metric}: columna o palabra no permitida: {text}")
            if not any(depth_stack):
                raise SemanticLayerError(f"Métrica {metric}: la columna {text} debe estar dentro de SUM o COUNT")
        elif text == "(":
            previous = tokens[index - 1][1].upper() if index else ""
            depth_stack.append(previous in AGGREGATE_FUNCTIONS)
        elif text == ")":
            if not depth_stack:
                raise SemanticLayerError(f"Métrica {metric}: paréntesis desbalanceados")
            depth_stack.pop()
    if depth_stack:
        raise SemanticLayerError(f"Métrica {metric}: paréntesis desbalanceados")
    if not any(t[1].upper() in AGGREGATE_FUNCTIONS for t in tokens):
        raise SemanticLayerError(f"Métrica {metric}: la expresión debe usar SUM o COUNT")


# --- Carga ---------------------------------------------------------------------------------------


def _text(entry: dict[str, Any], key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SemanticLayerError(f"{where}: `{key}` debe ser un texto no vacío")
    return value.strip()


def _load_metric(name: str, entry: Any) -> Metric:
    where = f"metrics.{name}"
    if not isinstance(entry, dict):
        raise SemanticLayerError(f"{where} debe ser un objeto")
    description, unit = _text(entry, "description", where), _text(entry, "unit", where)
    decimals = entry.get("decimals")
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        raise SemanticLayerError(f"{where}: `decimals` debe ser un entero ≥ 0")
    if ("expression" in entry) == ("ratio" in entry):
        raise SemanticLayerError(f"{where}: define `expression` o `ratio`, no ambos ni ninguno")
    if "expression" in entry:
        expression = _text(entry, "expression", where)
        validate_expression(name, expression)
        return AggregateMetric(name, description, unit, decimals, expression)
    ratio = entry["ratio"]
    if not isinstance(ratio, dict):
        raise SemanticLayerError(f"{where}: `ratio` debe tener `numerator` y `denominator`")
    return RatioMetric(
        name, description, unit, decimals, _text(ratio, "numerator", where), _text(ratio, "denominator", where)
    )


def _load_dimension(name: str, entry: Any) -> Dimension:
    where = f"dimensions.{name}"
    if name not in DIMENSION_COLUMNS:
        raise SemanticLayerError(f"{where}: no es una columna consultable ({', '.join(DIMENSION_COLUMNS)})")
    if not isinstance(entry, dict):
        raise SemanticLayerError(f"{where} debe ser un objeto")
    values = entry.get("values")
    if values is not None and (not isinstance(values, list) or not all(isinstance(v, str) for v in values)):
        raise SemanticLayerError(f"{where}: `values` debe ser una lista de textos")
    aliases = entry.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise SemanticLayerError(f"{where}: `aliases` debe ser un objeto alias: valor")
    for alias, target in aliases.items():
        if values is None or target not in values:
            raise SemanticLayerError(f"{where}: el alias {alias!r} apunta a {target!r}, que no está en el catálogo")
    return Dimension(
        name=name,
        description=_text(entry, "description", where),
        values=tuple(values) if values is not None else None,
        aliases={str(k): str(v) for k, v in aliases.items()},
        time=bool(entry.get("time", False)),
    )


def load_semantic_layer(path: Path) -> SemanticLayer:
    if not path.is_file():
        raise SemanticLayerError(f"No existe la capa semántica: {path}")
    content = path.read_bytes()
    try:
        data = yaml.safe_load(content.decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise SemanticLayerError(f"YAML inválido en {path}: {error}") from error
    if not isinstance(data, dict):
        raise SemanticLayerError(f"{path} debe contener un objeto YAML")
    raw_metrics, raw_dimensions = data.get("metrics"), data.get("dimensions")
    if not isinstance(raw_metrics, dict) or not raw_metrics:
        raise SemanticLayerError(f"{path}: falta la sección `metrics`")
    if not isinstance(raw_dimensions, dict) or not raw_dimensions:
        raise SemanticLayerError(f"{path}: falta la sección `dimensions`")
    metrics = {name: _load_metric(name, entry) for name, entry in raw_metrics.items()}
    for metric in metrics.values():
        if isinstance(metric, RatioMetric):
            for part in (metric.numerator, metric.denominator):
                if not isinstance(metrics.get(part), AggregateMetric):
                    raise SemanticLayerError(
                        f"metrics.{metric.name}: {part!r} no es una métrica agregada definida"
                    )
    dimensions = {name: _load_dimension(name, entry) for name, entry in raw_dimensions.items()}
    return SemanticLayer(metrics=metrics, dimensions=dimensions, fingerprint=hashlib.sha256(content).hexdigest())
