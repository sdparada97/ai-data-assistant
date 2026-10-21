"""Punto de entrada ``analyst-frontend``: lanza la página con la API pública ``st.App``.

Acepta opciones de servidor con la misma forma que ``streamlit run``
(``--server.port=8501``) y las pasa como ``config`` a ``st.App.run``.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import streamlit as st

APP_PATH = Path(__file__).with_name("app.py")

ConfigValue = bool | int | str


def _coerce(value: str) -> ConfigValue:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if value.isdigit():
        return int(value)
    return value


def parse_config(args: Sequence[str]) -> dict[str, ConfigValue]:
    """Convierte ``--clave=valor`` en ``{"clave": valor}``; rechaza cualquier otra forma."""
    config: dict[str, ConfigValue] = {}
    for arg in args:
        name, separator, value = arg.removeprefix("--").partition("=")
        if not arg.startswith("--") or not separator or not name:
            raise ValueError(f"Opción no válida: {arg!r}. Usa la forma --seccion.opcion=valor.")
        config[name] = _coerce(value)
    return config


def main(argv: Sequence[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    try:
        config = parse_config(args)
    except ValueError as error:
        sys.exit(str(error))
    st.App(APP_PATH).run(config=config or None)
