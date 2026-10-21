"""Requisito: Página mínima del frontend."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from analyst_frontend import cli
from analyst_frontend.config import DEFAULT_APP_TITLE, DEFAULT_BACKEND_URL

APP_FILE = str(cli.APP_PATH)


def _render() -> AppTest:
    app = AppTest.from_file(APP_FILE)
    app.run()
    return app


def test_page_shows_configured_title_and_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_TITLE", "Brío Analyst")
    monkeypatch.setenv("BACKEND_URL", "http://backend:8000")

    app = _render()

    assert not app.exception
    assert app.title[0].value == "Brío Analyst"
    assert "http://backend:8000" in app.caption[0].value


def test_page_uses_defaults_without_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_TITLE", raising=False)
    monkeypatch.delenv("BACKEND_URL", raising=False)

    app = _render()

    assert not app.exception
    assert app.title[0].value == DEFAULT_APP_TITLE == "Asistente de análisis"
    assert DEFAULT_BACKEND_URL == "http://localhost:8000"
    assert DEFAULT_BACKEND_URL in app.caption[0].value


class _FakeApp:
    """Sustituye a ``st.App`` para comprobar qué se lanza sin abrir un servidor."""

    calls: list[tuple[str, object]] = []

    def __init__(self, script_path: object) -> None:
        self.script_path = str(script_path)

    def run(self, *, config: object = None) -> None:
        _FakeApp.calls.append((self.script_path, config))


def test_cli_launches_page_with_server_options(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeApp.calls = []
    monkeypatch.setattr(cli.st, "App", _FakeApp)

    cli.main(["--server.port=8501", "--server.headless=true", "--server.address=0.0.0.0"])

    assert _FakeApp.calls == [
        (APP_FILE, {"server.port": 8501, "server.headless": True, "server.address": "0.0.0.0"})
    ]


def test_cli_without_options_uses_default_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeApp.calls = []
    monkeypatch.setattr(cli.st, "App", _FakeApp)

    cli.main([])

    assert _FakeApp.calls == [(APP_FILE, None)]


@pytest.mark.parametrize("bad_arg", ["nope", "--server.port", "--=1", "-server.port=1"])
def test_cli_rejects_malformed_options(monkeypatch: pytest.MonkeyPatch, bad_arg: str) -> None:
    _FakeApp.calls = []
    monkeypatch.setattr(cli.st, "App", _FakeApp)

    with pytest.raises(SystemExit) as exit_info:
        cli.main([bad_arg])

    assert "Opción no válida" in str(exit_info.value.code)
    assert _FakeApp.calls == []
