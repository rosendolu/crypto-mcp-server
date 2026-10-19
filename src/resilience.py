"""Timeout, retry, rate-limit and public-data fallback helpers."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Sequence

import ccxt

from config import (
    exchange_min_interval_ms,
    fallback_exchanges,
    retry_attempts,
    retry_backoff_ms,
)
from errors import CryptoMCPError, ErrorCode, map_ccxt_error

logger = logging.getLogger("crypto_mcp.resilience")

RETRYABLE = (
    ccxt.RequestTimeout,
    ccxt.NetworkError,
    ccxt.DDoSProtection,
    ccxt.RateLimitExceeded,
    ccxt.ExchangeNotAvailable,
)

_last_call_at: dict[str, float] = {}
_rate_lock = asyncio.Lock()


async def respect_rate_limit(exchange_id: str) -> None:
    """Serialize calls per exchange with a minimum spacing."""
    minimum = exchange_min_interval_ms() / 1000.0
    async with _rate_lock:
        now = time.monotonic()
        wait_for = _last_call_at.get(exchange_id, 0.0) + minimum - now
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _last_call_at[exchange_id] = time.monotonic()


async def retry_call[T](
    operation: Callable[[], Awaitable[T]],
    *,
    exchange_id: str,
    attempts: int | None = None,
) -> T:
    """Retry transient CCXT failures with exponential backoff."""
    total = attempts if attempts is not None else retry_attempts()
    delay_ms = retry_backoff_ms()
    last_error: BaseException | None = None
    for index in range(max(1, total)):
        await respect_rate_limit(exchange_id)
        try:
            return await operation()
        except RETRYABLE as exc:
            last_error = exc
            logger.warning(
                "Transient %s on %s (attempt %s/%s): %s",
                exc.__class__.__name__,
                exchange_id,
                index + 1,
                total,
                exc,
            )
            if index + 1 >= total:
                break
            await asyncio.sleep((delay_ms / 1000.0) * (2**index))
        except ccxt.BaseError as exc:
            raise map_ccxt_error(exc) from exc
        except CryptoMCPError:
            raise
    assert last_error is not None
    raise map_ccxt_error(last_error)


def fallback_chain(primary: str) -> list[str]:
    """Primary exchange first, then configured public-data fallbacks."""
    ordered = [primary]
    for candidate in fallback_exchanges():
        if candidate not in ordered:
            ordered.append(candidate)
    return ordered


async def with_public_fallback[T](
    primary: str,
    operation: Callable[[str], Awaitable[T]],
    *,
    allow_fallback: bool,
) -> tuple[T, str]:
    """Run ``operation(exchange_id)`` and fail over for public market data."""
    candidates: Sequence[str] = fallback_chain(primary) if allow_fallback else [primary]
    attempts: list[dict[str, str]] = []
    for exchange_id in candidates:
        try:
            result = await operation(exchange_id)
            if attempts:
                logger.info("Fell back to %s after %s", exchange_id, attempts)
            return result, exchange_id
        except CryptoMCPError as exc:
            attempts.append(
                {"exchange": exchange_id, "code": str(exc.code), "message": exc.message}
            )
            if exc.code in {
                ErrorCode.INVALID_ARGUMENT,
                ErrorCode.UNKNOWN_EXCHANGE,
                ErrorCode.MISSING_CREDENTIALS,
                ErrorCode.PERMISSION_DENIED,
                ErrorCode.AUTHENTICATION_FAILED,
            }:
                raise
            logger.warning("Public call failed on %s (%s); trying fallback", exchange_id, exc.code)
    if attempts and all(attempt["code"] == str(ErrorCode.NOT_SUPPORTED) for attempt in attempts):
        raise CryptoMCPError(
            ErrorCode.NOT_SUPPORTED,
            "No exchange in the fallback chain exposes this capability.",
            details={"attempts": attempts},
        )
    raise CryptoMCPError(
        ErrorCode.FALLBACK_EXHAUSTED,
        f"All exchanges failed for public data starting at '{primary}'.",
        details={"attempts": attempts},
    )
