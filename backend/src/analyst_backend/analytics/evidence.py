"""Identificador de evidencia determinista para los resultados de las herramientas."""

from __future__ import annotations

import hashlib
import json
from typing import Any

EVIDENCE_PREFIX = "EV-"
EVIDENCE_LENGTH = 12


def canonical_json(value: Any) -> str:
    """JSON estable: claves ordenadas, sin espacios. Las listas conservan su orden (se normalizan antes)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def evidence_id(tool: str, normalized_query: dict[str, Any], ingestion_id: str, semantic_fingerprint: str) -> str:
    payload = canonical_json(
        {"tool": tool, "query": normalized_query, "ingestion_id": ingestion_id, "semantic": semantic_fingerprint}
    )
    return EVIDENCE_PREFIX + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:EVIDENCE_LENGTH]


def contrast_evidence_id(
    doc_id: str, document_sha256: str, thresholds: dict[str, Any], claims: list[dict[str, Any]], query_ids: list[str]
) -> str:
    """Huella de un contraste: documento (y su versión), umbrales, afirmaciones validadas y consultas."""
    query = {"doc_id": doc_id, "thresholds": thresholds, "claims": claims, "queries": query_ids}
    return evidence_id("contrastar_afirmaciones", query, document_sha256, "")


def causal_evidence_id(
    request: dict[str, Any], thresholds: dict[str, Any], search: dict[str, Any],
    observations: list[dict[str, Any]], query_ids: list[str],
) -> str:
    """Huella de una evaluación causal: entrada, umbrales, búsqueda, observaciones validadas y consultas."""
    query = {"request": request, "thresholds": thresholds, "observations": observations, "queries": query_ids}
    return evidence_id("evaluar_causalidad", query, "", canonical_json(search))
