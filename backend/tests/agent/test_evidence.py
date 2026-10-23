"""Requisito: Título de cada evidencia (con resultados reales de las bases de prueba)."""

from __future__ import annotations

from typing import Any

from analyst_backend.agent.evidence import evidence_items
from analyst_backend.agent.tools import ToolContext, build_tools

from .test_graph import LARGEST_DROP


def _artifact(tool_context: ToolContext, name: str, args: dict[str, Any]) -> Any:
    tools = {t.name: t for t in build_tools(tool_context)}
    message = tools[name].invoke({"type": "tool_call", "name": name, "args": args, "id": "c1"})
    assert message.status != "error", message.content
    return message.artifact


def _titles(tool_context: ToolContext, name: str, args: dict[str, Any]) -> dict[str, str]:
    return {item.id: item.title for item in evidence_items(_artifact(tool_context, name, args))}


def test_metric_query_title(tool_context: ToolContext) -> None:
    [title] = _titles(tool_context, "consultar_metrica", LARGEST_DROP).values()

    assert title == "Venta neta por region · marca Brio · 2026-T1 frente a 2026-T2"


def test_fragment_title(tool_context: ToolContext) -> None:
    query = "Localización de la presión comercial: Centro, mayor caída porcentual, intervenir primero"
    titles = _titles(tool_context, "buscar_documentos", {"query": query})

    assert titles["REP-01"] == "Reporte ejecutivo | Desempeño de Brío · 3. Interpretación preliminar · p. 1"


def test_fragment_without_page_title(tool_context: ToolContext) -> None:
    artifact = _artifact(tool_context, "buscar_documentos",
                         {"query": "faltantes en Sur canal tradicional", "doc_ids": ["04_Observaciones_Canales"]})
    fragments = [item for item in evidence_items(artifact) if item.kind == "documento"]

    assert fragments and all(item.title.endswith("sin página") for item in fragments)


def test_search_and_quality_titles(tool_context: ToolContext) -> None:
    search = _titles(tool_context, "buscar_documentos", {"query": "Sensibilidad al precio en Sur"})
    quality = _titles(tool_context, "calidad_datos", {"rule_codes": ["DQ11"]})

    assert "Búsqueda en documentos: «Sensibilidad al precio en Sur»" in search.values()
    assert list(quality.values()) == ["Calidad de datos · reglas DQ11"]
