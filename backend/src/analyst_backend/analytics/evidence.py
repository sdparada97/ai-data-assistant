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
