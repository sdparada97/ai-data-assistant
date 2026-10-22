"""Verificación en código de la síntesis del LLM, afirmación por afirmación.

- **Cifras:** toda cifra de una afirmación debe estar en los valores o en el texto literal de
  alguna evidencia que esa afirmación cita (sin signo, redondeo de 0–2 decimales, formatos
  `1.234,5` y `1,234.5`). Se ignoran períodos, años del rango con datos e identificadores de
  evidencia, fragmentos y documentos (`05_Reporte_Comercial` no aporta un 5).
- **Citas:** deben existir en esta ejecución; hechos, hipótesis y contradicciones citan al menos una.
- **Lenguaje:** sin léxico causal en hechos, contradicciones e información insuficiente; hipótesis atenuadas.
- **Información insuficiente** (lo que escribe el LLM): sin cifras.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Literal

from analyst_backend.agent.models import Claim, Evidence, Synthesis
from analyst_backend.agent.prompts import hedge_examples

Section = Literal["facts", "hypotheses", "contradictions", "insufficient"]
SECTION_LABELS: dict[str, str] = {
    "facts": "hecho",
    "hypotheses": "hipótesis",
    "contradictions": "contradicción",
    "insufficient": "información insuficiente",
}

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_EVIDENCE_ID = re.compile(r"\bEV-[0-9a-f]{12}\b")
_CHUNK_ID = re.compile(r"\b[\w-]+:\d{3}\b")
_PERIODS = (
    re.compile(r"\b\d{4}-[TS][1-4]\b"),
    re.compile(r"\b\d{4}-(?:0[1-9]|1[0-2])\b"),
    re.compile(r"\b[TS][1-4]\b"),
)


@dataclass(frozen=True)
class Problem:
    section: Section
    index: int
    message: str


def _plain(text: str) -> str:
    """Minúsculas y sin tildes, para comparar léxico."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _contains_phrase(text: str, phrases: Iterable[str]) -> str | None:
    plain = _plain(text)
    for phrase in phrases:
        if re.search(rf"(?<!\w){re.escape(_plain(phrase))}(?!\w)", plain):
            return phrase
    return None


def _readings(token: str) -> set[Decimal]:
    """Lecturas posibles de un número escrito (punto o coma como separador de miles o decimal)."""
    readings: set[str] = set()
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            readings.add(token.replace(".", "").replace(",", "."))
        else:
            readings.add(token.replace(",", ""))
    elif "," in token or "." in token:
        separator = "," if "," in token else "."
        parts = token.split(separator)
        if all(len(part) == 3 for part in parts[1:]):
            readings.add(token.replace(separator, ""))  # separador de miles
        if len(parts) == 2:
            readings.add(token.replace(separator, "."))  # separador decimal
    else:
        readings.add(token)
    values: set[Decimal] = set()
    for reading in readings:
        try:
            values.add(Decimal(reading))
        except InvalidOperation:
            continue
    return values


def _strip_non_figures(
    text: str, years: Iterable[int], id_pattern: re.Pattern[str] | None, document_ids: Iterable[str]
) -> str:
    text = _EVIDENCE_ID.sub(" ", text)
    text = _CHUNK_ID.sub(" ", text)
    for doc_id in sorted(document_ids, key=len, reverse=True):  # los más largos primero
        text = re.sub(rf"(?<![\w-]){re.escape(doc_id)}(?![\w-])", " ", text, flags=re.IGNORECASE)
    if id_pattern is not None:
        text = id_pattern.sub(" ", text)
    for pattern in _PERIODS:
        text = pattern.sub(" ", text)
    for year in years:
        text = re.sub(rf"(?<![\d.,]){year}(?![\d.,])", " ", text)
    return text


def figures_in(
    text: str,
    years: Iterable[int] = (),
    id_pattern: re.Pattern[str] | None = None,
    document_ids: Iterable[str] = (),
) -> list[set[Decimal]]:
    """Cifras de un texto, cada una con sus lecturas posibles."""
    cleaned = _strip_non_figures(text.replace("−", "-"), list(years), id_pattern, document_ids)
    return [readings for token in _NUMBER.findall(cleaned) if (readings := _readings(token))]


def _supported(readings: set[Decimal], pool: Iterable[Decimal]) -> bool:
    targets = {abs(reading) for reading in readings}
    for value in pool:
        magnitude = abs(value)
        for decimals in (0, 1, 2):
            rounded = magnitude.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
            if rounded in targets:
                return True
        if magnitude in targets:
            return True
    return False


def _pool(items: Iterable[Evidence], id_pattern: re.Pattern[str] | None, document_ids: tuple[str, ...]) -> list[Decimal]:
    pool: list[Decimal] = []
    for item in items:
        pool.extend(item.numbers)
        if item.text:
            for readings in figures_in(item.text, (), id_pattern, document_ids):
                pool.extend(readings)
    return pool


def verify_synthesis(
    synthesis: Synthesis,
    evidence: Mapping[str, Evidence],
    aliases: Mapping[str, list[str]],
    *,
    years: Iterable[int],
    causal_lexicon: Iterable[str],
    hedges: Iterable[str],
    id_pattern: re.Pattern[str] | None = None,
    document_ids: Iterable[str] = (),
) -> list[Problem]:
    years = list(years)
    documents = tuple(document_ids)
    causal = list(causal_lexicon)
    hedge_list = list(hedges)
    examples = hedge_examples(hedge_list)
    problems: list[Problem] = []

    def check_claim(section: Section, index: int, claim: Claim) -> None:
        label = SECTION_LABELS[section]
        quoted = f"«{claim.statement}»"
        if not claim.evidence:
            problems.append(Problem(section, index, f"{label} sin evidencia citada: {quoted}"))
        unknown = [cited for cited in claim.evidence if cited not in aliases]
        if unknown:
            problems.append(Problem(section, index, f"{label} cita evidencia inexistente {', '.join(unknown)}: {quoted}"))
        cited = [evidence[item_id] for cited in claim.evidence for item_id in aliases.get(cited, [])]
        pool = _pool(cited, id_pattern, documents)
        missing = [
            min(readings)
            for readings in figures_in(claim.statement, years, id_pattern, documents)
            if not _supported(readings, pool)
        ]
        if missing:
            numbers = ", ".join(format(value, "f") for value in missing)
            problems.append(Problem(section, index, f"{label} con cifras que no están en su evidencia ({numbers}): {quoted}"))
        if section in ("facts", "contradictions") and (phrase := _contains_phrase(claim.statement, causal)):
            problems.append(Problem(section, index, f"{label} con lenguaje causal ('{phrase}'): {quoted}"))
        if section == "hypotheses" and _contains_phrase(claim.statement, hedge_list) is None:
            problems.append(Problem(section, index, f"{label} sin atenuar (usa, por ejemplo, {examples}): {quoted}"))

    for section in ("facts", "hypotheses", "contradictions"):
        for index, claim in enumerate(getattr(synthesis, section)):
            check_claim(section, index, claim)
    for index, text in enumerate(synthesis.insufficient):
        if figures_in(text, years, id_pattern, documents):
            problems.append(Problem("insufficient", index, f"información insuficiente con cifras: «{text}»"))
        if phrase := _contains_phrase(text, causal):
            problems.append(Problem("insufficient", index, f"información insuficiente con lenguaje causal ('{phrase}'): «{text}»"))
    return problems


def drop_failing(synthesis: Synthesis, problems: Iterable[Problem]) -> tuple[Synthesis, int]:
    """Fallo cerrado: retira las afirmaciones con problemas. Devuelve la síntesis y cuántas se retiraron."""
    failing: dict[str, set[int]] = {}
    for problem in problems:
        failing.setdefault(problem.section, set()).add(problem.index)

    def keep(section: str, items: list) -> list:  # type: ignore[type-arg]
        return [item for index, item in enumerate(items) if index not in failing.get(section, set())]

    kept = Synthesis(
        facts=keep("facts", synthesis.facts),
        hypotheses=keep("hypotheses", synthesis.hypotheses),
        contradictions=keep("contradictions", synthesis.contradictions),
        insufficient=keep("insufficient", synthesis.insufficient),
    )
    return kept, sum(len(indexes) for indexes in failing.values())


def removed_note(count: int) -> str:
    return "Se retiró 1 afirmación no verificada" if count == 1 else f"Se retiraron {count} afirmaciones no verificadas"
