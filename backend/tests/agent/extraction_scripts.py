"""Extracciones de prueba (lo que devolvería el LLM de extracción) para las herramientas y el grafo."""

from __future__ import annotations

from typing import Any

from analyst_backend.agent.extraction import (
    ClaimExtraction,
    ExtractedClaim,
    ExtractedObservation,
    FilterItem,
    ObservationExtraction,
)

from .fakes import json_message

REPORT = "05_Reporte_Comercial"
REPORT_TITLE = "Reporte ejecutivo | Desempeño de Brío"
TABLE = f"{REPORT}:003"
PROMOTIONS = "promociones de la competencia"
BRAND = [FilterItem(dimension="marca", values=["Brío"])]
ROWS = [("Centro", "-23 %"), ("Sur", "-7 %"), ("Norte", "-4 %"), ("Oriente", "+4 %"), ("Occidente", "-6 %")]


def variation(value: str, reported: str, **fields: Any) -> ExtractedClaim:
    base: dict[str, Any] = {"kind": "variacion", "chunk_id": TABLE, "metric": "venta_neta", "dimension": "region",
                            "value": value, "filters": BRAND, "base": "2026-T1", "target": "2026-T2",
                            "reported": reported}
    return ExtractedClaim(**{**base, **fields})


REP_01 = ExtractedClaim(kind="ranking", chunk_id=f"{REPORT}:004", metric="venta_neta", dimension="region",
                        value="Centro", filters=BRAND, direction="mayor_caida")

REPORT_CLAIMS = ClaimExtraction(claims=[*(variation(value, reported) for value, reported in ROWS), REP_01])
# Solo la primera es válida: las demás nombran un valor que no está en su línea.
MOSTLY_INVALID = ClaimExtraction(claims=[variation("Sur", "-7 %"), variation("Sur", "-23 %"),
                                         variation("Norte", "-6 %"), variation("Atlántico", "-4 %")])
ALL_INVALID = ClaimExtraction(claims=[variation("Sur", "-23 %"), variation("Atlántico", "-4 %")])

PROMOTION_OBSERVATIONS = ObservationExtraction(observations=[
    ExtractedObservation(kind="segmento", chunk_id="04_Observaciones_Canales:004", dimension="region",
                         value="Centro", quote="promociones de marcas competidoras"),
    ExtractedObservation(kind="atribucion", chunk_id=f"{REPORT}:005", quote="aproximadamente el 70 %"),
])

CAUSAL_ARGS = {
    "cause": PROMOTIONS, "cause_kind": "competencia", "metric": "venta_neta", "filters": {"marca": "Brío"},
    "compare": {"base": "2026-T1", "target": "2026-T2"}, "locate_by": "region",
}


def report_extraction() -> Any:
    return json_message(REPORT_CLAIMS)


def promotions_extraction() -> Any:
    return json_message(PROMOTION_OBSERVATIONS)
