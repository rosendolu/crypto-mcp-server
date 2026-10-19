"""Exchange resolution tests (require ccxt, no network)."""

from __future__ import annotations

import pytest

from config import proxy_url
from errors import CryptoMCPError, ErrorCode
from exchanges import _build_client, resolve_exchange_id


def test_resolve_exchange_id_explicit() -> None:
    assert resolve_exchange_id("Binance") == "binance"
    assert resolve_exchange_id(" okx ") == "okx"


def test_resolve_exchange_id_defaults_to_a_supported_exchange() -> None:
    import ccxt

    assert resolve_exchange_id(None) in ccxt.exchanges


def test_unknown_exchange_uses_error_code() -> None:
    with pytest.raises(CryptoMCPError) as exc_info:
        _build_client("not-an-exchange", with_credentials=False)
    assert exc_info.value.code is ErrorCode.UNKNOWN_EXCHANGE


def test_proxy_is_applied_to_the_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRYPTO_MCP_PROXY", "http://127.0.0.1:7890")
    client = _build_client("binance", with_credentials=False)
    assert client.aiohttp_proxy == "http://127.0.0.1:7890"


def test_no_proxy_leaves_the_client_direct(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("CRYPTO_MCP_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        monkeypatch.delenv(name, raising=False)
    assert proxy_url() is None
    assert _build_client("binance", with_credentials=False).aiohttp_proxy is None


def test_crypto_mcp_proxy_wins_over_standard_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CRYPTO_MCP_PROXY", "http://127.0.0.1:7890")
    monkeypatch.setenv("HTTPS_PROXY", "http://corp-proxy:3128")
    assert proxy_url() == "http://127.0.0.1:7890"


def test_standard_proxy_variable_is_used_as_a_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CRYPTO_MCP_PROXY", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://corp-proxy:3128")
    assert proxy_url() == "http://corp-proxy:3128"
