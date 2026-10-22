"""Requisito: Contexto de la planificación."""

from __future__ import annotations

from dataclasses import replace

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.context import build_planning_context, catalog_text, data_range
from analyst_backend.agent.prompts import PLAN_RULES, planning_system_prompt
from analyst_backend.analytics.semantic import Dimension

from .conftest import Bases


def test_real_data_range(bases: Bases, agent_config: AgentConfig) -> None:
    available = data_range(bases.sales)

    assert (available.first_month, available.last_month) == ("2026-01", "2026-06")
    assert available.quarters == ("2026-T1", "2026-T2")
    assert available.years == frozenset({2026})
    context = build_planning_context(bases.layer, bases.sales, bases.documents)
    prompt = planning_system_prompt(context, agent_config.assistant_name)
    assert "Datos disponibles: de 2026-01 a 2026-06 (trimestres 2026-T1, 2026-T2)." in prompt


def test_catalog_comes_from_configuration(bases: Bases, agent_config: AgentConfig) -> None:
    brand = bases.layer.dimensions["marca"]
    layer = replace(
        bases.layer,
        dimensions={**bases.layer.dimensions, "marca": Dimension(brand.name, brand.description, (*brand.values, "Prueba"), brand.aliases)},
    )

    prompt = planning_system_prompt(build_planning_context(layer, bases.sales, bases.documents), agent_config.assistant_name)

    assert "Prueba" in prompt
    assert "Prueba" not in planning_system_prompt(
        build_planning_context(bases.layer, bases.sales, bases.documents), agent_config.assistant_name
    )


def test_planning_prompt_lists_catalog_documents_and_period_rule(bases: Bases, agent_config: AgentConfig) -> None:
    context = build_planning_context(bases.layer, bases.sales, bases.documents)

    prompt = planning_system_prompt(context, agent_config.assistant_name)

    assert prompt.startswith(f"Eres {agent_config.assistant_name},")
    assert PLAN_RULES in prompt and catalog_text(bases.layer) in prompt and context.documents in prompt
    assert "venta_neta" in prompt and "Brío = Brio" in prompt
    assert "Si la pregunta no indica el período, usa los períodos con datos o los que cite el documento." in prompt
    assert context.document_ids == (
        "01_Contexto_Negocio", "03_Investigacion_Consumidor", "04_Observaciones_Canales", "05_Reporte_Comercial",
    )
    assert all(doc_id in prompt for doc_id in context.document_ids)
