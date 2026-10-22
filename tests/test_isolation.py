"""Requisito: Aislamiento de la suite por defecto."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


# Dirección numérica de documentación (TEST-NET-3): no pasa por DNS.
INTERNET_ADDRESS = ("203.0.113.1", 80)


def test_network_connect_fails_with_explicit_error() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        tcp.settimeout(1)  # sin bloqueo, falla rápido en vez de colgarse
        with pytest.raises(RuntimeError, match="Red deshabilitada"):
            tcp.connect(INTERNET_ADDRESS)


def test_network_connect_ex_fails_with_explicit_error() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        tcp.settimeout(1)  # sin bloqueo, falla rápido en vez de colgarse
        with pytest.raises(RuntimeError, match="Red deshabilitada"):
            tcp.connect_ex(INTERNET_ADDRESS)


def test_env_example_variables_are_hidden(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Reproduce la suite en un directorio aislado con el conftest real.
    pytester.makeconftest((ROOT / "conftest.py").read_text(encoding="utf-8"))
    (pytester.path / ".env.example").write_text(
        (ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8"
    )
    pytester.makepyfile(
        """
        import os
        from conftest import env_example_variables

        def test_probe():
            names = env_example_variables()
            assert "GEMINI_API_KEY" in names
            assert [n for n in names if n in os.environ] == []
        """
    )
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

    result = pytester.runpytest_subprocess("-p", "no:cacheprovider")

    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    "resolve",
    [
        lambda: socket.getaddrinfo("example.com", 443),
        lambda: socket.gethostbyname("example.com"),
        lambda: socket.gethostbyname_ex("example.com"),
    ],
    ids=["getaddrinfo", "gethostbyname", "gethostbyname_ex"],
)
def test_dns_resolution_fails_with_explicit_error(resolve: Any) -> None:
    with pytest.raises(RuntimeError, match="Red deshabilitada"):
        resolve()


def test_udp_send_fails_with_explicit_error() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.settimeout(1)
        with pytest.raises(RuntimeError, match="Red deshabilitada"):
            udp.sendto(b"ping", ("203.0.113.1", 53))
        with pytest.raises(RuntimeError, match="Red deshabilitada"):
            udp.sendmsg([b"ping"], [], 0, ("203.0.113.1", 53))


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="AF_UNIX no disponible en este sistema")
def test_local_unix_sockets_keep_native_behaviour(tmp_path: Path) -> None:
    # connect_ex sobre un socket local inexistente devuelve un código, no lanza.
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as local:
        assert local.connect_ex(str(tmp_path / "missing.sock")) != 0


def test_embeddings_tests_keep_only_models_cache_dir(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Escenario "Caché de modelos en pruebas embeddings".
    pytester.makeconftest((ROOT / "conftest.py").read_text(encoding="utf-8"))
    pytester.makeini("[pytest]\nmarkers =\n    embeddings: prueba con el modelo real\n")
    (pytester.path / ".env.example").write_text(
        (ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8"
    )
    pytester.makepyfile(
        """
        import os
        import socket
        import pytest

        @pytest.mark.embeddings
        def test_probe():
            assert os.environ["MODELS_CACHE_DIR"] == "/tmp/modelos-de-prueba"
            assert "GEMINI_API_KEY" not in os.environ
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
                tcp.settimeout(1)
                with pytest.raises(RuntimeError, match="Red deshabilitada"):
                    tcp.connect(("203.0.113.1", 80))
        """
    )
    monkeypatch.setenv("MODELS_CACHE_DIR", "/tmp/modelos-de-prueba")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

    result = pytester.runpytest_subprocess("-p", "no:cacheprovider")

    result.assert_outcomes(passed=1)
