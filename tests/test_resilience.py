"""Retry, rate-limit and public-fallback tests (no live network)."""

from __future__ import annotations

import asyncio

import ccxt
import pytest

from errors import CryptoMCPError, ErrorCode
from resilience import fallback_chain, retry_call, with_public_fallback


def test_retry_call_eventually_succeeds() -> None:
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ccxt.NetworkError("blip")
        return "ok"

    result = asyncio.run(retry_call(flaky, exchange_id="binance", attempts=3))
    assert result == "ok"
    assert attempts["count"] == 3


def test_retry_call_maps_exhausted_failure() -> None:
    async def always_timeout() -> str:
        raise ccxt.RequestTimeout("late")

    with pytest.raises(CryptoMCPError) as exc_info:
        asyncio.run(retry_call(always_timeout, exchange_id="binance", attempts=2))
    assert exc_info.value.code is ErrorCode.TIMEOUT


def test_public_fallback_uses_second_venue() -> None:
    async def operation(exchange_id: str) -> str:
        if exchange_id == "binance":
            raise CryptoMCPError(ErrorCode.NETWORK_ERROR, "binance down")
        return f"from-{exchange_id}"

    async def run() -> tuple[str, str]:
        return await with_public_fallback("binance", operation, allow_fallback=True)

    result, used = asyncio.run(run())
    assert result == "from-okx"
    assert used == "okx"


def test_invalid_argument_does_not_fallback() -> None:
    async def operation(exchange_id: str) -> str:
        raise CryptoMCPError(ErrorCode.INVALID_ARGUMENT, "bad symbol")

    async def run() -> None:
        await with_public_fallback("binance", operation, allow_fallback=True)

    with pytest.raises(CryptoMCPError) as exc_info:
        asyncio.run(run())
    assert exc_info.value.code is ErrorCode.INVALID_ARGUMENT


def test_fallback_chain_deduplicates_primary() -> None:
    chain = fallback_chain("okx")
    assert chain[0] == "okx"
    assert chain.count("okx") == 1
