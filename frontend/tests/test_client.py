"""Cliente de la API (sin abrir puertos) y lectura de BACKEND_TIMEOUT_S."""

from __future__ import annotations

import json

import httpx
import pytest

from analyst_frontend.client import ask_backend
from analyst_frontend.config import DEFAULT_BACKEND_TIMEOUT_S, load_settings

URL = "http://backend:8000"
AGENT_BODY = {"status": "error", "error_code": "quota_exhausted", "message": "m", "trace": {"question": "q"}}


def _transport(handler: object) -> httpx.MockTransport:
    return httpx.MockTransport(handler)  # type: ignore[arg-type]


def test_agent_response_with_any_status() -> None:
    sent: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(429, json=AGENT_BODY)

    outcome = ask_backend(URL, "¿Qué región cayó más?", 5, _transport(handler))

    assert (outcome.kind, outcome.http_status, outcome.body) == ("answer", 429, AGENT_BODY)
    assert sent == [{"question": "¿Qué región cayó más?"}]


def test_plain_text_500_is_unrecognized() -> None:
    outcome = ask_backend(URL, "q", 5, _transport(lambda request: httpx.Response(500, text="Internal Server Error")))

    assert (outcome.kind, outcome.http_status) == ("unrecognized", 500)


@pytest.mark.parametrize("error", [httpx.ConnectError("sin conexión"), httpx.RemoteProtocolError("cortada")])
def test_connection_failures_are_unreachable(error: Exception) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    assert ask_backend(URL, "q", 5, _transport(handler)).kind == "unreachable"


def test_read_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("sin respuesta")

    assert ask_backend(URL, "q", 5, _transport(handler)).kind == "timeout"


@pytest.mark.parametrize(("raw", "expected", "warned"), [
    (None, DEFAULT_BACKEND_TIMEOUT_S, False),
    ("", DEFAULT_BACKEND_TIMEOUT_S, False),
    ("600", 600.0, False),
    ("abc", DEFAULT_BACKEND_TIMEOUT_S, True),
    ("inf", DEFAULT_BACKEND_TIMEOUT_S, True),
    ("-5", DEFAULT_BACKEND_TIMEOUT_S, True),
])
def test_backend_timeout_setting(monkeypatch: pytest.MonkeyPatch, raw: str | None, expected: float, warned: bool) -> None:
    if raw is None:
        monkeypatch.delenv("BACKEND_TIMEOUT_S", raising=False)
    else:
        monkeypatch.setenv("BACKEND_TIMEOUT_S", raw)

    settings = load_settings()

    assert settings.backend_timeout_s == expected
    assert (settings.timeout_warning is not None) == warned
    if warned:
        assert "BACKEND_TIMEOUT_S" in settings.timeout_warning  # type: ignore[operator]
