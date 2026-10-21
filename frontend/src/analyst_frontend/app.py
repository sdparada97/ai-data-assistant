"""Página mínima de Streamlit."""

from __future__ import annotations

import streamlit as st

from analyst_frontend.config import load_settings

settings = load_settings()

st.set_page_config(page_title=settings.app_title)
st.title(settings.app_title)
st.caption(f"API: {settings.backend_url}")
