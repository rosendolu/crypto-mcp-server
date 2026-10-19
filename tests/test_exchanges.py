"""Exchange resolution tests (require ccxt, no network)."""

from __future__ import annotations

import pytest

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
