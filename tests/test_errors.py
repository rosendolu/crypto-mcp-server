"""Unified error-code tests."""

from __future__ import annotations

import json

import ccxt

from errors import CryptoMCPError, ErrorCode, map_ccxt_error


def test_error_serializes_code_and_message() -> None:
    error = CryptoMCPError(ErrorCode.TIMEOUT, "deadline exceeded", details={"ms": 30_000})
    payload = json.loads(str(error))
    assert payload["error"]["code"] == "TIMEOUT"
    assert payload["error"]["details"]["ms"] == 30_000


def test_map_ccxt_timeout() -> None:
    mapped = map_ccxt_error(ccxt.RequestTimeout("slow"))
    assert mapped.code is ErrorCode.TIMEOUT


def test_map_ccxt_rate_limit() -> None:
    mapped = map_ccxt_error(ccxt.RateLimitExceeded("429"))
    assert mapped.code is ErrorCode.RATE_LIMITED


def test_map_ccxt_auth() -> None:
    mapped = map_ccxt_error(ccxt.AuthenticationError("bad key"))
    assert mapped.code is ErrorCode.AUTHENTICATION_FAILED


def test_map_ccxt_not_supported() -> None:
    mapped = map_ccxt_error(ccxt.NotSupported("binance does not support fetchOpenInterest"))
    assert mapped.code is ErrorCode.NOT_SUPPORTED
    assert "does not expose that capability" in mapped.message


def test_map_ccxt_bad_symbol_is_invalid_argument() -> None:
    mapped = map_ccxt_error(ccxt.BadSymbol("BTC/NOPE"))
    assert mapped.code is ErrorCode.INVALID_ARGUMENT
