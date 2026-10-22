"""Punto de entrada de `make ask Q="<pregunta>"`: `python -m analyst_backend.agent`.

La pregunta llega en la variable de entorno `Q` (sin pasar por el intérprete de órdenes) o como
argumento. Imprime la respuesta por apartados con sus evidencias, los avisos y un resumen de la traza.
Códigos: 0 si hay respuesta (también `insuficiente` o `fuera_de_alcance`), 1 si falta configuración
y 2 si la respuesta tiene estado `error`.
"""

from __future__ import annotations

import os
import sys

from analyst_backend.agent.models import AgentResponse, Claim
from analyst_backend.agent.service import CONFIGURATION_ERROR, answer_question

SECTIONS = (("facts", "Hechos"), ("hypotheses", "Hipótesis"), ("contradictions", "Contradicciones"))


def _claim(claim: Claim) -> str:
    return f"  - {claim.statement} [{', '.join(claim.evidence)}]"


def render(response: AgentResponse) -> str:
    lines = [f"Estado: {response.status}" + (f" ({response.error_code})" if response.error_code else "")]
    if response.message:
        lines.append(response.message)
    for field, title in SECTIONS:
        claims = getattr(response, field)
        if claims:
            lines += ["", f"{title}:", *(_claim(claim) for claim in claims)]
    if response.insufficient:
        lines += ["", "Información insuficiente:", *(f"  - {text}" for text in response.insufficient)]
    if response.warnings:
        lines += ["", "Avisos:", *(f"  - {text}" for text in response.warnings)]
    trace = response.trace
    queries = ", ".join(
        f"{run.tool} ({run.status}{', ' + run.evidence_id if run.evidence_id else ''})" for run in trace.tool_runs
    )
    lines += [
        "",
        f"Traza: modelo {trace.model or '-'}, {trace.llm_calls} llamadas al LLM ({trace.llm_attempts} intentos), "
        f"{trace.repairs} correcciones, {trace.synthesis_retries} reintentos de síntesis, {trace.duration_ms} ms",
        f"Consultas: {queries or 'ninguna'}",
    ]
    if trace.verification_problems:
        lines += ["Problemas de verificación:", *(f"  - {problem}" for problem in trace.verification_problems)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    question = " ".join(args) if args else os.environ.get("Q", "")
    if not question.strip():
        print('Indica la pregunta: make ask Q="<pregunta>"', file=sys.stderr)
        return 1
    response = answer_question(question)
    if response.error_code == CONFIGURATION_ERROR:
        print(f"Error de configuración del agente: {response.message}", file=sys.stderr)
        return 1
    print(render(response))
    return 2 if response.status == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
