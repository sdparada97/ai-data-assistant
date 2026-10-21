"""Aislamiento de la suite por defecto.

Toda prueba sin la marca ``llm`` se ejecuta sin red y sin las variables
declaradas en ``.env.example``, aunque existan en el entorno del desarrollador.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

pytest_plugins = ["pytester"]

ENV_EXAMPLE = Path(__file__).parent / ".env.example"
_BLOCKED_FAMILIES = {socket.AF_INET, socket.AF_INET6}


class NetworkDisabledError(RuntimeError):
    """Se lanza cuando una prueba sin marca ``llm`` intenta abrir una conexión."""


def env_example_variables(path: Path = ENV_EXAMPLE) -> list[str]:
    """Devuelve los nombres de variable declarados en ``.env.example``."""
    if not path.exists():
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.append(line.split("=", 1)[0].strip())
    return names


_NETWORK_DISABLED = (
    "Red deshabilitada en la suite por defecto: marca la prueba con "
    "@pytest.mark.llm si necesita servicios externos."
)
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_sendto = socket.socket.sendto
_original_sendmsg = socket.socket.sendmsg


def _guard(family: int) -> None:
    if family in _BLOCKED_FAMILIES:
        raise NetworkDisabledError(_NETWORK_DISABLED)


def _blocked_connect(self: socket.socket, address: Any) -> None:
    _guard(self.family)
    _original_connect(self, address)


def _blocked_connect_ex(self: socket.socket, address: Any) -> int:
    _guard(self.family)
    return _original_connect_ex(self, address)


def _blocked_sendto(self: socket.socket, *args: Any) -> int:
    _guard(self.family)
    return _original_sendto(self, *args)


def _blocked_sendmsg(self: socket.socket, *args: Any) -> int:
    _guard(self.family)
    return _original_sendmsg(self, *args)


def _blocked_resolution(*args: Any, **kwargs: Any) -> Any:
    raise NetworkDisabledError(_NETWORK_DISABLED)


@pytest.fixture(autouse=True)
def _isolate_default_suite(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    if request.node.get_closest_marker("llm") is None:
        for name in env_example_variables():
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
        monkeypatch.setattr(socket.socket, "connect_ex", _blocked_connect_ex)
        monkeypatch.setattr(socket.socket, "sendto", _blocked_sendto)
        monkeypatch.setattr(socket.socket, "sendmsg", _blocked_sendmsg)
        for resolver in ("getaddrinfo", "gethostbyname", "gethostbyname_ex"):
            monkeypatch.setattr(socket, resolver, _blocked_resolution)
    yield
