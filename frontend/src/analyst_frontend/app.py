"""Página de preguntas al agente.

El historial es solo visual: cada petición a la API lleva únicamente la pregunta nueva. Con una
pregunta pendiente el campo se desactiva; la respuesta se guarda en `st.session_state` en cuanto
llega, antes de pintar nada, para que no se pierda si Streamlit vuelve a ejecutar la página.
"""

from __future__ import annotations

import streamlit as st

from analyst_frontend import client, render
from analyst_frontend.config import load_settings

INDEPENDENCE_NOTICE = (
    "Cada pregunta se responde de forma independiente: el asistente no recuerda las preguntas anteriores."
)
PENDING_TEXT = "Consultando al agente…"

settings = load_settings()

st.set_page_config(page_title=settings.app_title)
st.title(settings.app_title)
st.info(INDEPENDENCE_NOTICE)
if settings.timeout_warning:
    st.warning(settings.timeout_warning)

history: list[dict[str, object]] = st.session_state.setdefault("history", [])
for entry in history:
    with st.chat_message("user"):
        st.text(str(entry["question"]))
    with st.chat_message("assistant"):
        outcome = entry["outcome"]
        if outcome is None:
            st.text(PENDING_TEXT)
        else:
            render.render_outcome(outcome, settings)  # type: ignore[arg-type]

pending = bool(history) and history[-1]["outcome"] is None
question = st.chat_input("Escribe tu pregunta", disabled=pending)

st.caption(f"API: {settings.backend_url}")

if pending:
    entry = history[-1]
    with st.spinner(PENDING_TEXT):
        entry["outcome"] = client.ask_backend(settings.backend_url, str(entry["question"]), settings.backend_timeout_s)
    st.rerun()
elif question:
    history.append({"question": question, "outcome": None})
    st.rerun()
