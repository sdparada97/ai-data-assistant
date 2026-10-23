"""Extracción con esquema cerrado y validación en código (contraste y observaciones de la causa).

El LLM es un `ScriptedChatModel`: devuelve la extracción del guion y registra el prompt que recibe.
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from analyst_backend.agent.config import AgentConfig
from analyst_backend.agent.context import DataRange, data_range
from analyst_backend.agent.extraction import (
    UNPARSEABLE,
    ClaimExtraction,
    ClaimValidation,
    Document,
    ExtractedClaim,
    ExtractedObservation,
    FilterItem,
    ObservationExtraction,
    extract_claims,
    extract_observations,
    llm_extractor,
    load_document,
    search_cause,
    validate_claims,
    validate_observations,
)
from analyst_backend.agent.llm import LLMClient
from analyst_backend.agent.prompts import EVIDENCE_CLOSE, EVIDENCE_OPEN
from analyst_backend.analytics.contrast import compare_claims
from analyst_backend.analytics.models import QueryError
from analyst_backend.documents.config import load_documents_config
from analyst_backend.documents.embeddings import FastEmbedEmbedder

from .conftest import ROOT, Bases, fake_embedder
from .fakes import ScriptedChatModel, json_message

REPORT = "05_Reporte_Comercial"
CHANNELS = "04_Observaciones_Canales"
TABLE = f"{REPORT}:003"
OC_CEN_02 = f"{CHANNELS}:004"
TOOL = "contrastar_afirmaciones"
BRAND = [FilterItem(dimension="marca", values=["Brío"])]


def scripted_extractor(*items: Any) -> tuple[Any, ScriptedChatModel]:
    model = ScriptedChatModel.from_script(*items)
    llm = LLMClient(model, model_name="modelo-de-prueba", unavailable_retries=0, backoff_s=0, secrets=())
    return llm_extractor(llm), model


def prompt_of(model: ScriptedChatModel) -> str:
    return str(model.received[-1][-1].content)


def document(bases: Bases, agent_config: AgentConfig, doc_id: str = REPORT) -> Document:
    return load_document(bases.documents, doc_id, agent_config.contrast.max_document_chars)


def claim(**fields: Any) -> ExtractedClaim:
    base: dict[str, Any] = {"kind": "variacion", "chunk_id": TABLE, "metric": "venta_neta", "dimension": "region",
                            "value": "Centro", "filters": BRAND, "base": "2026-T1", "target": "2026-T2",
                            "reported": "-23 %"}
    base.update(fields)
    return ExtractedClaim(**base)


@pytest.fixture(scope="module")
def dates(bases: Bases) -> DataRange:
    return data_range(bases.sales)


def validate(bases: Bases, agent_config: AgentConfig, dates: DataRange, *claims: ExtractedClaim,
             doc_id: str = REPORT, config: Any = None) -> ClaimValidation:
    return validate_claims(claims, document(bases, agent_config, doc_id), bases.layer, dates,
                           config or agent_config.contrast, agent_config.metric_synonyms)


def reason(result: ClaimValidation) -> str:
    [discarded] = result.discarded
    return discarded.reason


# --- Contraste de un documento -----------------------------------------------------------------


def test_unknown_document(bases: Bases, agent_config: AgentConfig) -> None:
    with pytest.raises(QueryError) as error:
        document(bases, agent_config, "06_Inexistente")

    assert "06_Inexistente" in error.value.message and REPORT in error.value.message


def test_extraction_receives_every_fragment(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    report = document(bases, agent_config)
    extractor, model = scripted_extractor(json_message(ClaimExtraction(claims=[])))

    extract_claims(extractor, report, bases.layer, dates, TOOL)

    expected = [f"{REPORT}:{index:03d}" for index in range(1, 13)]
    assert list(report.fragments) == expected
    assert all(f'id="{chunk_id}"' in prompt_of(model) for chunk_id in expected)


def test_document_too_long(bases: Bases) -> None:
    with pytest.raises(QueryError, match="máximo es 100"):
        load_document(bases.documents, REPORT, 100)


# --- Extracción con esquema cerrado ------------------------------------------------------------


def test_fragments_are_delimited(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    extractor, model = scripted_extractor(json_message(ClaimExtraction(claims=[])))

    extract_claims(extractor, document(bases, agent_config, CHANNELS), bases.layer, dates, TOOL)

    prompt = prompt_of(model)
    injected = prompt.index("INSTRUCCIÓN PARA EL ASISTENTE")
    assert prompt.rfind(EVIDENCE_OPEN, 0, injected) > prompt.rfind(EVIDENCE_CLOSE, 0, injected)
    assert prompt.rfind("Recuerda las reglas") > prompt.rfind(EVIDENCE_CLOSE)


def test_unparseable_extraction(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    extractor, _ = scripted_extractor("esto no es JSON")

    with pytest.raises(QueryError) as error:
        extract_claims(extractor, document(bases, agent_config), bases.layer, dates, TOOL)

    assert error.value.message == UNPARSEABLE.format(tool=TOOL)


def test_maximum_number_of_claims(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    config = agent_config.contrast.model_copy(update={"max_claims": 2})
    rows = [("Centro", "-23 %"), ("Sur", "-7 %"), ("Norte", "-4 %")]

    result = validate(bases, agent_config, dates, *(claim(value=v, reported=r) for v, r in rows), config=config)

    assert [c.value for c in result.valid] == ["Centro", "Sur"]
    assert result.omitted == 1 and "Se omitieron 1" in result.warnings[0]


# --- Enunciado generado en código --------------------------------------------------------------


def test_statement_built_from_validated_fields(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    [valid] = validate(bases, agent_config, dates, claim(value="centro")).valid

    assert valid.statement == "Centro: venta neta -23 % (2026-T1 frente a 2026-T2)"


# --- Validación literal de las afirmaciones -----------------------------------------------------


def test_valid_claim(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    [valid] = validate(bases, agent_config, dates, claim()).valid

    assert (valid.value, valid.reported, valid.filters) == ("Centro", Decimal("-23"), {"marca": ["Brio"]})


def test_value_not_in_the_fragment(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(chunk_id=f"{REPORT}:004"))

    assert reason(result) == "no está en la línea del valor"


def test_inverted_sign(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    assert reason(validate(bases, agent_config, dates, claim(value="Oriente", reported="-4 %"))) == "signo distinto"


def test_value_of_another_row(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(value="Sur", reported="-23 %"))

    assert reason(result) == "no está en la línea del valor"


def test_fragment_of_another_document(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    assert "no pertenece" in reason(validate(bases, agent_config, dates, claim(chunk_id=OC_CEN_02)))


def test_positive_without_sign_and_unicode_minus(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(value="Oriente", reported="4"),
                      claim(value="Norte", reported="−4 %"))

    assert [c.reported for c in result.valid] == [Decimal("4"), Decimal("-4")]


# --- ID de evidencia tomado del fragmento --------------------------------------------------------


def test_evidence_id_from_the_fragment(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    ranking = claim(kind="ranking", chunk_id=f"{REPORT}:004", reported=None, direction="mayor_caida")

    [valid] = validate(bases, agent_config, dates, ranking).valid

    assert valid.evidence_ref == "REP-01"
    assert validate(bases, agent_config, dates, claim()).valid[0].evidence_ref == TABLE


# --- Validación de rankings y direcciones -------------------------------------------------------


def most_affected(value: str) -> ExtractedClaim:
    return claim(kind="ranking", chunk_id=OC_CEN_02, value=value, reported=None, direction="mayor_caida",
                 base=None, target=None)


def test_region_in_the_fragment_section(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    [valid] = validate(bases, agent_config, dates, most_affected("Centro"), doc_id=CHANNELS).valid

    assert (valid.value, valid.evidence_ref) == ("Centro", "OC-CEN-02")


def test_region_not_in_the_fragment(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, most_affected("Norte"), doc_id=CHANNELS)

    assert reason(result) == "Norte no aparece en el texto ni en la sección del fragmento"


def test_direction_needs_its_word(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    contraction = claim(kind="direccion", chunk_id=f"{REPORT}:002", dimension=None, value=None, reported=None,
                        direction="contraccion")
    growth = contraction.model_copy(update={"direction": "crecimiento"})

    result = validate(bases, agent_config, dates, contraction, growth)

    assert [c.statement for c in result.valid] == ["Brio: venta neta en contracción (2026-T1 frente a 2026-T2)"]
    assert reason(result) == "la palabra de sentido no aparece en el fragmento"


# --- Validación de alcance y catálogo ------------------------------------------------------------


def test_region_outside_the_catalog(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    text = reason(validate(bases, agent_config, dates, claim(value="Atlántico")))

    assert "region" in text and "Atlántico" in text and "Centro, " in text


def test_filter_the_document_does_not_mention(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(filters=[FilterItem(dimension="marca", values=["Luma"])]))

    assert reason(result) == "Luma no aparece en el documento"


def test_metric_outside_the_catalog(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    share = claim(chunk_id=f"{CHANNELS}:005", metric="cuota_formatos_pequenos", value="Norte", reported="5 %")

    result = validate(bases, agent_config, dates, share, doc_id=CHANNELS)
    contrast = compare_claims(result.valid, doc_id=CHANNELS, doc_title="Canales", document_sha256="abc",
                              layer=bases.layer, duckdb_path=bases.sales, approx_pp=Decimal("1.0"))

    assert [c.verdict for c in contrast.comparisons] == ["no verificable con los datos"]
    assert contrast.queries == []


# --- Períodos y métrica anclados en el texto ----------------------------------------------------


def test_period_without_data(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(base="2025-T1", target="2025-T2"))

    assert reason(result) == "el período 2025-T1 no tiene datos"


def test_equal_periods(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(base="2026-T2", target="2026-T2"))

    assert reason(result) == "el período base y el de comparación son el mismo (2026-T2)"


def test_periods_anchored_in_the_fragment(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    [valid] = validate(bases, agent_config, dates, claim()).valid

    assert (valid.base, valid.target, valid.default_periods) == ("2026-T1", "2026-T2", False)


def test_default_periods(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    anchored_elsewhere = most_affected("Centro").model_copy(update={"base": "2026-01", "target": "2026-06"})

    result = validate(bases, agent_config, dates, most_affected("Centro"), anchored_elsewhere, doc_id=CHANNELS)

    assert [(c.base, c.target, c.default_periods) for c in result.valid] == [("2026-T1", "2026-T2", True)] * 2
    assert result.warnings == ["Períodos por defecto (2026-T1 frente a 2026-T2) en 2 afirmaciones sin períodos en el texto"]


def test_default_periods_warning_reaches_the_contrast(bases: Bases, agent_config: AgentConfig,
                                                      dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, most_affected("Centro"), doc_id=CHANNELS)
    contrast = compare_claims(result.valid, doc_id=CHANNELS, doc_title="Canales", document_sha256="abc",
                              layer=bases.layer, duckdb_path=bases.sales, approx_pp=Decimal("1.0"),
                              warnings=result.warnings)

    assert "Períodos por defecto (2026-T1 frente a 2026-T2) en 1 afirmación sin períodos en el texto" in contrast.warnings


def test_no_warning_with_anchored_periods(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    assert validate(bases, agent_config, dates, claim()).warnings == []


def test_metric_the_document_does_not_mention(bases: Bases, agent_config: AgentConfig, dates: DataRange) -> None:
    result = validate(bases, agent_config, dates, claim(metric="unidades"))

    assert reason(result) == "la métrica unidades no aparece en el documento"


# --- Observaciones de la causa ---------------------------------------------------------------------


PROMOTIONS = "promociones de la competencia"


def observation(**fields: Any) -> ExtractedObservation:
    base: dict[str, Any] = {"kind": "segmento", "chunk_id": f"{CHANNELS}:010", "quote": "descuento visible",
                            "dimension": "region", "value": "Sur", "date": "2026-04-18"}
    base.update(fields)
    return ExtractedObservation(**base)


SCRIPTED_OBSERVATIONS = ObservationExtraction(observations=[
    observation(chunk_id=OC_CEN_02, quote="promociones de marcas competidoras", value="Centro", date=None),
    observation(),  # CAM-103 (Sur): la búsqueda no lo devuelve
    observation(kind="atribucion", chunk_id=f"{REPORT}:005", quote="aproximadamente el 70 %", dimension=None,
                value=None, date=None),
    observation(kind="limitacion", chunk_id="03_Investigacion_Consumidor:011",
                quote="no permiten atribuir un porcentaje", dimension=None, value=None, date=None),
])


def observe(bases: Bases, agent_config: AgentConfig, embedder: Any, documents: Path, config: Any) -> Any:
    search = search_cause(PROMOTIONS, agent_config.causal.search_top_k, config, documents, embedder)
    extractor, model = scripted_extractor(json_message(SCRIPTED_OBSERVATIONS))
    extracted = extract_observations(extractor, PROMOTIONS, list(search.fragments.values()), bases.layer,
                                     "evaluar_causalidad")
    return search, validate_observations(extracted, search.fragments, bases.layer), prompt_of(model)


def test_promotions_with_the_test_search(bases: Bases, agent_config: AgentConfig) -> None:
    search, result, prompt = observe(bases, agent_config, fake_embedder(), bases.documents, bases.documents_config)

    assert len(search.fragments) == agent_config.causal.search_top_k
    assert all(f'id="{chunk_id}"' in prompt for chunk_id in search.fragments)
    segments = [(o.value, o.evidence_ref) for o in result.valid if o.kind == "segmento"]
    assert segments == [("Centro", "OC-CEN-02")]
    assert any("no está entre los recuperados" in d.reason for d in result.discarded)
    assert "REP-02" in [o.evidence_ref for o in result.valid if o.kind == "atribucion"]


@pytest.fixture(scope="module")
def real_documents(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, Path, Any]:
    from analyst_backend.documents.ingest import ingest_documents
    from analyst_backend.settings import DocumentsSettings

    cache = Path(os.environ["MODELS_CACHE_DIR"])
    cache = cache if cache.is_absolute() else ROOT / cache
    config_path = ROOT / "backend/config/documents.yaml"
    config = load_documents_config(config_path)
    embedder = FastEmbedEmbedder(config.model, cache)
    db = tmp_path_factory.mktemp("real-model") / "documents.duckdb"
    ingest_documents(DocumentsSettings(ROOT / "data/raw", db, config_path, cache), embedder)
    return embedder, db, config


@pytest.mark.embeddings
def test_promotions_with_the_real_search(bases: Bases, agent_config: AgentConfig,
                                         real_documents: tuple[Any, Path, Any]) -> None:
    embedder, db, config = real_documents

    _, result, _ = observe(bases, agent_config, embedder, db, config)

    segments = [o.value for o in result.valid if o.kind == "segmento"]
    assert "Centro" in segments and "Sur" not in segments
    design = {(o.kind, o.evidence_ref) for o in result.valid}
    assert {("atribucion", "REP-02"), ("limitacion", "INV-04")} <= design


# --- Validación de las observaciones ---------------------------------------------------------------


def check(bases: Bases, agent_config: AgentConfig, *items: ExtractedObservation) -> Any:
    fragments = document(bases, agent_config, CHANNELS).fragments
    return validate_observations(items, fragments, bases.layer)


def test_sur_observation_with_date(bases: Bases, agent_config: AgentConfig) -> None:
    [valid] = check(bases, agent_config, observation()).valid

    assert (valid.value, valid.date, valid.evidence_ref) == ("Sur", "2026-04-18", "CAM-103")


def test_segment_of_another_line(bases: Bases, agent_config: AgentConfig) -> None:
    other_line = observation(chunk_id=f"{CHANNELS}:002", quote="Promociones puntuales de competidores", date=None)

    [discarded] = check(bases, agent_config, other_line).discarded

    assert discarded.reason == "Sur no está en la línea de la cita ni en la sección del fragmento"


def test_date_not_in_the_fragment(bases: Bases, agent_config: AgentConfig) -> None:
    invented = observation(chunk_id=OC_CEN_02, quote="promociones de marcas competidoras", value="Centro",
                           date="2026-05-01")

    [discarded] = check(bases, agent_config, invented).discarded

    assert discarded.reason == "la fecha 2026-05-01 no aparece en el fragmento"


@pytest.mark.parametrize("value", ["ID / fecha: CAM-103", "2026-02-30"])
def test_date_must_be_a_real_date(bases: Bases, agent_config: AgentConfig, value: str) -> None:
    [discarded] = check(bases, agent_config, observation(date=value)).discarded

    assert discarded.reason == "la fecha no tiene el formato AAAA-MM-DD"


def test_design_statements_with_the_fragments_present(bases: Bases, agent_config: AgentConfig) -> None:
    """Declaraciones de diseño sin depender del orden de la búsqueda: REP-02 (atribución) e INV-04 (limitación)."""
    fragments = {**document(bases, agent_config).fragments,
                 **document(bases, agent_config, "03_Investigacion_Consumidor").fragments}

    result = validate_observations(SCRIPTED_OBSERVATIONS.observations, fragments, bases.layer)

    design = {(o.kind, o.evidence_ref) for o in result.valid}
    assert {("atribucion", "REP-02"), ("limitacion", "INV-04")} <= design


def test_quote_must_be_literal(bases: Bases, agent_config: AgentConfig) -> None:
    [discarded] = check(bases, agent_config, observation(quote="descuento agresivo")).discarded

    assert discarded.reason == "la cita no aparece literal en el fragmento"


def test_design_only_for_attributions(bases: Bases, agent_config: AgentConfig) -> None:
    [valid] = check(bases, agent_config, observation(declares_design=True)).valid

    assert valid.declares_design is False
