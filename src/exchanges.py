"""Async CCXT exchange clients with retry, rate limits and public fallbacks."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import ccxt.async_support as ccxt

from config import (
    DEFAULT_EXCHANGE_FALLBACK,
    credentials_for,
    default_exchange,
    exchange_timeout_ms,
    proxy_url,
)
from errors import CryptoMCPError, ErrorCode
from resilience import retry_call, with_public_fallback

logger = logging.getLogger("crypto_mcp.exchanges")

# Public-data endpoints an agent actually reasons about.
CAPABILITY_KEYS = (
    "fetchTicker",
    "fetchOrderBook",
    "fetchTrades",
    "fetchOHLCV",
    "fetchFundingRate",
    "fetchFundingRateHistory",
    "fetchOpenInterest",
)

# Curated discovery list: the venues worth showing in a round-trip response.
MAJOR_EXCHANGES = (
    "binance",
    "okx",
    "bybit",
    "bitget",
    "gate",
    "kucoin",
    "mexc",
    "kraken",
    "coinbase",
    "htx",
    "cryptocom",
    "bitfinex",
)

_clients: dict[str, ccxt.Exchange] = {}
_lock = asyncio.Lock()
_capabilities: dict[str, dict[str, bool]] = {}


def resolve_exchange_id(exchange_id: str | None) -> str:
    """Resolve which exchange a call should target.

    Order of precedence: explicit argument, ``DEFAULT_EXCHANGE`` env var,
    first configured exchange, then a safe public-data fallback.
    """
    if exchange_id and exchange_id.strip():
        return exchange_id.strip().lower()
    configured_default = default_exchange()
    if configured_default:
        return configured_default
    for candidate in ccxt.exchanges:
        if credentials_for(candidate):
            return candidate
    return DEFAULT_EXCHANGE_FALLBACK


def _build_client(exchange_id: str, with_credentials: bool) -> ccxt.Exchange:
    if exchange_id not in ccxt.exchanges:
        raise CryptoMCPError(
            ErrorCode.UNKNOWN_EXCHANGE,
            f"Unknown exchange '{exchange_id}'. Call list_exchanges to see supported ids.",
            details={"exchange": exchange_id},
        )
    exchange_class = getattr(ccxt, exchange_id)
    config: dict[str, Any] = {"enableRateLimit": True, "timeout": exchange_timeout_ms()}
    if with_credentials:
        credentials = credentials_for(exchange_id)
        if credentials is not None:
            config["apiKey"] = credentials.api_key
            config["secret"] = credentials.secret
            if credentials.password:
                config["password"] = credentials.password
    client = exchange_class(config)
    proxy = proxy_url()
    if proxy:
        # CCXT's async client does not read proxy env vars by itself.
        client.aiohttp_proxy = proxy
    return client


async def get_exchange(
    exchange_id: str | None = None,
    *,
    require_credentials: bool = False,
) -> ccxt.Exchange:
    """Return a cached async CCXT client for ``exchange_id``.

    Public endpoints do not need credentials; private ones do. ``require_credentials``
    surfaces a clear error before hitting the network when they are missing.
    """
    resolved = resolve_exchange_id(exchange_id)
    if require_credentials and credentials_for(resolved) is None:
        prefix = resolved.upper()
        raise CryptoMCPError(
            ErrorCode.MISSING_CREDENTIALS,
            f"Exchange '{resolved}' has no API credentials. "
            f"Set {prefix}_API_KEY and {prefix}_SECRET in your environment.",
            details={"exchange": resolved},
        )
    async with _lock:
        if resolved not in _clients:
            has_credentials = credentials_for(resolved) is not None
            _clients[resolved] = _build_client(resolved, with_credentials=has_credentials)
        return _clients[resolved]


def exchange_capabilities(exchange_id: str) -> dict[str, bool]:
    """Report which public endpoints ``exchange_id`` supports.

    Read from CCXT's offline metadata, so this never hits the network and is
    safe to call while assembling discovery responses.
    """
    resolved = exchange_id.strip().lower()
    cached = _capabilities.get(resolved)
    if cached is not None:
        return cached
    if resolved not in ccxt.exchanges:
        raise CryptoMCPError(
            ErrorCode.UNKNOWN_EXCHANGE,
            f"Unknown exchange '{resolved}'. Call list_exchanges to see supported ids.",
            details={"exchange": resolved},
        )
    metadata = getattr(getattr(ccxt, resolved)(), "has", None) or {}
    capabilities = {key: bool(metadata.get(key)) for key in CAPABILITY_KEYS}
    _capabilities[resolved] = capabilities
    return capabilities


def capability_matrix(exchange_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Capability rows plus credential state for the requested venues."""
    venues = exchange_ids if exchange_ids else list(MAJOR_EXCHANGES)
    rows: list[dict[str, Any]] = []
    for exchange_id in venues:
        rows.append(
            {
                "exchange": exchange_id,
                "configured": credentials_for(exchange_id) is not None,
                **exchange_capabilities(exchange_id),
            }
        )
    return rows


async def call_exchange(
    method: str,
    *args: Any,
    exchange_id: str | None = None,
    require_credentials: bool = False,
    allow_fallback: bool = False,
    **kwargs: Any,
) -> tuple[Any, str]:
    """Invoke a CCXT method with retry, rate limiting and optional public fallback."""
    primary = resolve_exchange_id(exchange_id)

    async def invoke(target: str) -> Any:
        client = await get_exchange(target, require_credentials=require_credentials)

        async def operation() -> Any:
            bound = getattr(client, method)
            return await bound(*args, **kwargs)

        return await retry_call(operation, exchange_id=target)

    if allow_fallback and not require_credentials:
        return await with_public_fallback(primary, invoke, allow_fallback=True)
    return await invoke(primary), primary


async def map_exchanges[T](
    exchange_ids: list[str],
    operation: Callable[[str], Awaitable[T]],
) -> dict[str, T | dict[str, Any]]:
    """Run ``operation`` on several exchanges concurrently.

    Venues are queried in parallel; rate limiting stays per exchange, so a slow
    venue cannot delay the others and a single venue failure is reported in
    place instead of aborting the whole fan-out.
    """

    async def run(exchange_id: str) -> tuple[str, T | dict[str, Any]]:
        try:
            return exchange_id, await operation(exchange_id)
        except CryptoMCPError as exc:
            return exchange_id, exc.as_payload()
        except Exception as exc:  # noqa: BLE001 - one bad venue must not sink the rest
            logger.exception("Unexpected failure on %s", exchange_id)
            return exchange_id, CryptoMCPError(
                ErrorCode.INTERNAL_ERROR,
                str(exc) or exc.__class__.__name__,
                details={"exchange": exchange_id},
            ).as_payload()

    return dict(await asyncio.gather(*(run(exchange_id) for exchange_id in exchange_ids)))


async def close_exchanges() -> None:
    """Close every cached client. Wired into the FastMCP lifespan."""
    clients = list(_clients.values())
    _clients.clear()
    for client in clients:
        try:
            await client.close()
        except Exception:  # noqa: BLE001 - best effort shutdown
            logger.warning("Failed to close CCXT client cleanly", exc_info=True)
