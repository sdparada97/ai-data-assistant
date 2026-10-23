"""Verificación en código: cifras por afirmación, citas y lenguaje.

La evidencia es real: la consulta de la región con mayor caída sobre la base de ventas de
prueba y fragmentos leídos de la base de documentos de prueba.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.context import build_planning_context
from analyst_backend.agent.evidence import evidence_items, index
from analyst_backend.agent.models import Claim, Evidence, Synthesis
from analyst_backend.agent.verify import Problem, drop_failing, figures_in, removed_note, verify_synthesis
from analyst_backend.analytics.metrics import consultar_metrica
from analyst_backend.analytics.models import MetricQuery
from analyst_backend.documents.models import DocumentHit, DocumentResult
from analyst_backend.documents.retrieval import open_documents_db

from .conftest import Bases
from .test_graph import LARGEST_DROP, LARGEST_DROP_ID

REPORT_TABLE = "05_Reporte_Comercial:003"  # tabla con -23 % para Centro (sin ID propio)
REPORT_REP01 = "05_Reporte_Comercial:004"  # fragmento de REP-01 (sin cifras)
RESEARCH_INDEX = "03_Investigacion_Consumidor:018"  # índice de referencias INV-01…INV-05, INV-LIM
YEARS = {2026}


def _hits(bases: Bases, chunk_ids: list[str]) -> list[DocumentHit]:
    with open_documents_db(bases.documents) as connection:
        rows = connection.execute(
            "SELECT chunk_id, doc_id, source_type, title, section, page, primary_evidence_id, evidence_ids, text "
            "FROM doc_chunks WHERE chunk_id IN (SELECT unnest(?)) ORDER BY chunk_id",
            [chunk_ids],
        ).fetchall()
    return [
        DocumentHit(rank=rank, chunk_id=c, doc_id=d, source_type=s, title=t, section=sec, page=p,
                    primary_evidence_id=pid, evidence_ids=list(ids), text=text, score=1.0, bm25_rank=rank,
                    semantic_rank=None)
        for rank, (c, d, s, t, sec, p, pid, ids, text) in enumerate(rows, start=1)
    ]


@pytest.fixture(scope="module")
def run_evidence(bases: Bases) -> tuple[dict[str, Evidence], dict[str, list[str]]]:
    metric = consultar_metrica(MetricQuery.model_validate(LARGEST_DROP), bases.layer, bases.sales)
    assert metric.evidence_id == LARGEST_DROP_ID
    search = DocumentResult(
        evidence_id="EV-000000000001", ingestion_id="prueba", mode="lexico", model_name=None, query="reporte",
        top_k=5, doc_ids=[], source_types=[], warnings=[],
        hits=_hits(bases, [REPORT_TABLE, REPORT_REP01, RESEARCH_INDEX]),
    )
    return index([*evidence_items(metric), *evidence_items(search)])


@pytest.fixture
def check(run_evidence: tuple[dict[str, Evidence], dict[str, list[str]]], bases: Bases, agent_config: AgentConfig):  # noqa: ANN201
    evidence, aliases = run_evidence

    document_ids = build_planning_context(bases.layer, bases.sales, bases.documents).document_ids

    def run(synthesis: Synthesis) -> list[Problem]:
        return verify_synthesis(
            synthesis, evidence, aliases, years=YEARS, causal_lexicon=agent_config.causal_lexicon,
            hedges=agent_config.hedges, id_pattern=bases.documents_config.id_regex, document_ids=document_ids,
        )

    return run


def fact(statement: str, *cited: str) -> Synthesis:
    return Synthesis(facts=[Claim(statement=statement, evidence=list(cited))])


def hypothesis(statement: str, *cited: str) -> Synthesis:
    return Synthesis(hypotheses=[Claim(statement=statement, evidence=list(cited))])


# --- Verificación de cifras --------------------------------------------------------------------


def test_report_figure_presented_as_sales_data(check) -> None:  # noqa: ANN001
    problems = check(fact("Centro tuvo la mayor caída, con -23 %", LARGEST_DROP_ID))

    assert [p.section for p in problems] == ["facts"]
    assert "23" in problems[0].message and "no están en su evidencia" in problems[0].message


def test_report_figure_cited_with_its_fragment(check) -> None:  # noqa: ANN001
    assert check(fact("El reporte afirma que Centro cayó -23 %", "REP-01", REPORT_TABLE)) == []


def test_figure_cited_with_a_fragment_without_it(check) -> None:  # noqa: ANN001
    problems = check(fact("El reporte afirma que Centro cayó -23 %", "REP-01"))

    assert len(problems) == 1 and "23" in problems[0].message


def test_four_digit_figure_without_support(check) -> None:  # noqa: ANN001
    problems = check(fact("Brío vendió 1500 unidades más en Norte", LARGEST_DROP_ID))

    assert len(problems) == 1 and "1500" in problems[0].message


def test_drop_without_sign(check) -> None:  # noqa: ANN001
    assert check(fact("Sur cayó 30,27 % entre 2026-T1 y 2026-T2", LARGEST_DROP_ID)) == []


def test_documented_risk_right_figure_wrong_region(check) -> None:  # noqa: ANN001
    """Riesgo aceptado (design): la cifra está en la evidencia citada, aunque sea de otra región."""
    assert check(fact("Norte cayó 30,27 %", LARGEST_DROP_ID)) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Sur cayó 30,27 % en 2026-T2 frente a T1", [{Decimal("30.27")}]),
        ("entre 2026-S1, 2026-04 y S2 de 2026", []),
        (f"según {LARGEST_DROP_ID}, {REPORT_TABLE} y REP-01", []),
        ("1.234,5 frente a 1,234.5", [{Decimal("1234.5")}, {Decimal("1234.5")}]),
        ("1.500 unidades", [{Decimal("1500"), Decimal("1.500")}]),
    ],
)
def test_figures_in(bases: Bases, text: str, expected: list[set[Decimal]]) -> None:
    assert figures_in(text, YEARS, bases.documents_config.id_regex) == expected


def test_figures_in_ignores_document_ids(bases: Bases) -> None:
    documents = ("03_Investigacion_Consumidor", "05_Reporte_Comercial")

    assert figures_in("Según 05_Reporte_Comercial, Centro cayó -23 %", YEARS, None, documents) == [{Decimal("23")}]
    assert figures_in("Lo recoge 03_investigacion_consumidor", YEARS, None, documents) == []
    assert figures_in("Según 05_Reporte_Comercial", YEARS, None, ()) == [{Decimal("5")}]  # sin la lista


def test_document_name_in_a_fact(check) -> None:  # noqa: ANN001
    assert check(fact("Según 05_Reporte_Comercial, Centro cayó -23 %", REPORT_TABLE)) == []


def test_document_name_in_a_hypothesis(check) -> None:  # noqa: ANN001
    statement = "Los faltantes en Sur que recoge 03_Investigacion_Consumidor podrían pesar en la caída"

    assert check(hypothesis(statement, "INV-02")) == []


def test_figure_next_to_a_document_name_is_still_checked(check) -> None:  # noqa: ANN001
    problems = check(fact("Según 05_Reporte_Comercial, Centro cayó 5 %", REPORT_TABLE))

    assert len(problems) == 1 and "(5)" in problems[0].message


def test_insufficient_without_figures(check) -> None:  # noqa: ANN001
    problems = check(Synthesis(insufficient=["Faltan datos de 2025 y del 15 % de las tiendas"]))

    assert [p.section for p in problems] == ["insufficient"]


# --- Verificación de citas y lenguaje ----------------------------------------------------------


def test_unknown_citation(check) -> None:  # noqa: ANN001
    problems = check(fact("El reporte prioriza Centro", "REP-99"))

    assert len(problems) == 1 and "inexistente REP-99" in problems[0].message


def test_id_cited_inside_a_fragment(check) -> None:  # noqa: ANN001
    assert check(hypothesis("La percepción de precio podría pesar en Sur", "INV-01")) == []


def test_claim_without_citation(check) -> None:  # noqa: ANN001
    problems = check(fact("Sur fue la región con mayor caída"))

    assert len(problems) == 1 and "sin evidencia citada" in problems[0].message


def test_causal_language_in_a_fact(check) -> None:  # noqa: ANN001
    problems = check(fact("Las promociones de la competencia causaron la caída", "REP-01"))

    assert len(problems) == 1 and "lenguaje causal" in problems[0].message


def test_hypothesis_without_hedge(check, agent_config: AgentConfig) -> None:  # noqa: ANN001
    problems = check(hypothesis("La caída se explica por los faltantes en Sur", "INV-01"))

    assert len(problems) == 1 and "sin atenuar" in problems[0].message
    assert ", ".join(f'"{hedge}"' for hedge in agent_config.hedges[:3]) in problems[0].message


# --- Fallo cerrado -----------------------------------------------------------------------------


def test_drop_failing_keeps_the_rest(check) -> None:  # noqa: ANN001
    synthesis = Synthesis(facts=[
        Claim(statement="Sur cayó 30,27 %", evidence=[LARGEST_DROP_ID]),
        Claim(statement="Brío vendió 1500 unidades más en Norte", evidence=[LARGEST_DROP_ID]),
    ])

    kept, removed = drop_failing(synthesis, check(synthesis))

    assert [claim.statement for claim in kept.facts] == ["Sur cayó 30,27 %"]
    assert removed == 1 and removed_note(removed) == "Se retiró 1 afirmación no verificada"
    assert removed_note(2) == "Se retiraron 2 afirmaciones no verificadas"


# --- Contraste y causalidad: cifras citables, veredictos e "insuficiente" coherente -----------------


@pytest.fixture(scope="module")
def judged(bases: Bases, agent_config: AgentConfig) -> dict[str, object]:
    """Evidencias de un contraste (solo Sur válida), una evaluación causal y consultas de métricas."""
    from analyst_backend.agent.verify import Consulted
    from analyst_backend.analytics.models import Comparison
    from analyst_backend.agent.extraction import llm_extractor
    from analyst_backend.agent.llm import LLMClient
    from analyst_backend.agent.tools import build_tools

    from .conftest import fake_embedder
    from .extraction_scripts import CAUSAL_ARGS, MOSTLY_INVALID, REPORT, promotions_extraction
    from .fakes import ScriptedChatModel, json_message
    from analyst_backend.agent.tools import ToolContext

    def tools(*script: object) -> dict[str, object]:
        llm = LLMClient(ScriptedChatModel.from_script(*script), model_name="prueba", unavailable_retries=0, backoff_s=0)
        context = ToolContext(
            layer=bases.layer, duckdb_path=bases.sales, documents_config=bases.documents_config,
            documents_db_path=bases.documents, embedder=fake_embedder(), docs_top_k=5, max_quality_issues=5,
            contrast=agent_config.contrast, causal=agent_config.causal, metric_synonyms=agent_config.metric_synonyms,
            extractor=llm_extractor(llm),
        )
        return {t.name: t for t in build_tools(context)}

    def call(name: str, args: dict[str, object], *script: object) -> object:
        return tools(*script)[name].invoke({"type": "tool_call", "name": name, "args": args, "id": "x"})

    contrast = call("contrastar_afirmaciones", {"doc_id": REPORT}, json_message(MOSTLY_INVALID))
    causal = call("evaluar_causalidad", CAUSAL_ARGS, promotions_extraction())
    compare = Comparison(base="2026-T1", target="2026-T2")

    def metric(metric_name: str, group_by: list[str]) -> object:
        return consultar_metrica(MetricQuery(metrics=[metric_name], group_by=group_by, compare=compare),
                                 bases.layer, bases.sales)

    queries = {
        "ventas_region": metric("venta_neta", ["region"]),
        "ventas_marca_region": metric("venta_neta", ["marca", "region"]),
        "precio_region": metric("precio_efectivo", ["region"]),
    }
    consulted = Consulted.build(
        absence_markers=agent_config.absence_markers, absence_exceptions=agent_config.absence_exceptions,
        metrics=bases.layer.metrics, metric_synonyms=agent_config.metric_synonyms, dimensions=bases.layer.dimensions,
    )
    return {"contrast": contrast.artifact, "causal": causal.artifact, "queries": queries, "consulted": consulted}


def _verify(judged: dict[str, object], agent_config: AgentConfig, synthesis: Synthesis,
            *artifacts: object) -> list[Problem]:
    items = [item for artifact in artifacts for item in evidence_items(artifact, "")]  # type: ignore[arg-type]
    evidence, aliases = index(items)
    return verify_synthesis(synthesis, evidence, aliases, years=YEARS, causal_lexicon=agent_config.causal_lexicon,
                            hedges=agent_config.hedges, consulted=judged["consulted"])  # type: ignore[arg-type]


def test_contrast_figure_cited(judged: dict[str, object], agent_config: AgentConfig) -> None:
    contrast = judged["contrast"]
    statement = "En Sur, el reporte indica -7 % y los datos -30.27 %: 23.27 puntos de diferencia"

    assert _verify(judged, agent_config, fact(statement, contrast.evidence_id), contrast) == []  # type: ignore[attr-defined]


def test_figure_of_a_discarded_claim(judged: dict[str, object], agent_config: AgentConfig) -> None:
    contrast = judged["contrast"]
    assert any(d.description.endswith("-6 %") for d in contrast.discarded)  # type: ignore[attr-defined]

    [problem] = _verify(judged, agent_config, fact("El reporte da -6 % para Norte", contrast.evidence_id), contrast)  # type: ignore[attr-defined]

    assert "cifras que no están en su evidencia (6)" in problem.message


def test_internal_query_is_citable_by_its_id(judged: dict[str, object], agent_config: AgentConfig) -> None:
    contrast = judged["contrast"]
    query_id = contrast.queries[0].evidence_id  # type: ignore[attr-defined]

    assert _verify(judged, agent_config, fact("Norte cayó -3.48 %", query_id), contrast) == []


def test_altered_causal_verdict(judged: dict[str, object], agent_config: AgentConfig) -> None:
    causal = judged["causal"]
    synthesis = Synthesis(contradictions=[Claim(statement="La hipótesis de las promociones es compatible con los datos",
                                                evidence=[causal.evidence_id])])  # type: ignore[attr-defined]

    [problem] = _verify(judged, agent_config, synthesis, causal)

    assert "veredicto distinto" in problem.message and '"no sustentada"' in problem.message


def test_cause_described_with_its_verdict(judged: dict[str, object], agent_config: AgentConfig) -> None:
    causal = judged["causal"]
    statement = "Que las promociones causaron la caída es una afirmación no sustentada"

    assert _verify(judged, agent_config, fact(statement, causal.evidence_id), causal) == []  # type: ignore[attr-defined]


def test_causal_lexicon_without_verdict(judged: dict[str, object], agent_config: AgentConfig) -> None:
    causal = judged["causal"]

    [problem] = _verify(judged, agent_config, fact("Las promociones causaron la caída", causal.evidence_id), causal)  # type: ignore[attr-defined]

    assert "lenguaje causal" in problem.message


def _insufficient(judged: dict[str, object], agent_config: AgentConfig, text: str, *queries: str) -> list[Problem]:
    artifacts = [judged["queries"][name] for name in queries]  # type: ignore[index]
    return _verify(judged, agent_config, Synthesis(insufficient=[text]), *artifacts)


def test_sales_by_region_were_consulted(judged: dict[str, object], agent_config: AgentConfig) -> None:
    [problem] = _insufficient(judged, agent_config, "Faltan registros consolidados de ventas por región", "ventas_region")

    assert "venta_neta" in problem.message and "region" in problem.message


def test_competitor_sales_were_consulted(judged: dict[str, object], agent_config: AgentConfig) -> None:
    assert _insufficient(judged, agent_config, "Faltan ventas de la competencia por región", "ventas_marca_region")


def test_sales_by_region_not_consulted(judged: dict[str, object], agent_config: AgentConfig) -> None:
    assert _insufficient(judged, agent_config, "Faltan registros consolidados de ventas por región", "precio_region") == []


def test_competitor_prices(judged: dict[str, object], agent_config: AgentConfig) -> None:
    text = "Faltan datos de precios de la competencia por región"

    assert _insufficient(judged, agent_config, text, "precio_region") == []


def test_inventories_by_region(judged: dict[str, object], agent_config: AgentConfig) -> None:
    assert _insufficient(judged, agent_config, "Faltan datos de inventarios por región", "ventas_region") == []


def test_absence_through_an_internal_query(judged: dict[str, object], agent_config: AgentConfig) -> None:
    contrast = judged["contrast"]  # su consulta interna es venta_neta por región

    problems = _verify(judged, agent_config, Synthesis(insufficient=["No hay datos de ventas por región"]), contrast)

    assert [p.section for p in problems] == ["insufficient"]
