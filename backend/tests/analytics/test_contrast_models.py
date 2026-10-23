"""Requisitos "Resultado trazable" y "Resultado causal trazable": la huella del `evidence_id`."""

from __future__ import annotations

from analyst_backend.analytics.evidence import causal_evidence_id, contrast_evidence_id

CLAIMS = [{"kind": "variacion", "chunk_id": "05_Reporte_Comercial:003", "value": "Centro", "reported": "-23"}]


def test_same_contrast_same_id() -> None:
    first = contrast_evidence_id("05_Reporte_Comercial", "abc", {"approx_pp": "1.0"}, CLAIMS, ["EV-000000000001"])
    second = contrast_evidence_id("05_Reporte_Comercial", "abc", {"approx_pp": "1.0"}, CLAIMS, ["EV-000000000001"])

    assert first == second and first.startswith("EV-") and len(first) == 15


def test_contrast_id_changes_with_threshold_document_or_claims() -> None:
    base = contrast_evidence_id("05_Reporte_Comercial", "abc", {"approx_pp": "1.0"}, CLAIMS, ["EV-000000000001"])

    assert base != contrast_evidence_id("05_Reporte_Comercial", "abc", {"approx_pp": "0.5"}, CLAIMS, ["EV-000000000001"])
    assert base != contrast_evidence_id("05_Reporte_Comercial", "otra-version", {"approx_pp": "1.0"}, CLAIMS, ["EV-000000000001"])
    assert base != contrast_evidence_id("05_Reporte_Comercial", "abc", {"approx_pp": "1.0"}, [], ["EV-000000000001"])


def test_causal_id_changes_with_search_mode() -> None:
    args = ({"cause": "promociones"}, {"differential_pp": "1.0"})
    hybrid = causal_evidence_id(*args, {"top_k": 8, "mode": "hibrido"}, [], ["EV-000000000001"])

    assert hybrid == causal_evidence_id(*args, {"top_k": 8, "mode": "hibrido"}, [], ["EV-000000000001"])
    assert hybrid != causal_evidence_id(*args, {"top_k": 8, "mode": "lexico"}, [], ["EV-000000000001"])
