"""Public market-data tools.

Every tool here answers one question: a single symbol's quote, its candles,
the order book, recent fills, funding, or the same field compared across
venues. Responses are JSON so an agent can compose them directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from fastmcp import FastMCP

from errors import CryptoMCPError, ErrorCode
from exchanges import call_exchange, map_exchanges, resolve_exchange_id
from formatting import json_text, summarize_ticker
from validation import (
    MAX_CANDLES,
    MAX_ORDER_BOOK_LEVELS,
    MAX_TRADES,
    Limit,
    bounded,
    note_limits,
    require_symbol,
    validate_interval,
)

logger = logging.getLogger("crypto_mcp.tools.market")

DEFAULT_INTERVAL = "1h"
DEFAULT_CANDLES = 100
DEFAULT_DEPTH = 20
DEFAULT_TRADES = 50
DEFAULT_COMPARE_EXCHANGES = ("binance", "okx")

CompareField = Literal["last", "bid", "ask", "funding_rate"]


@dataclass(frozen=True)
class CandleSeries:
    """Candles plus the request details an analysis tool needs to report."""

    symbol: str
    interval: str
    exchange: str
    candles: list[list[float]]
    limit: Limit


# --- Payload builders --------------------------------------------------------
async def ticker_payload(symbol: str, exchange: str | None) -> dict[str, Any]:
    """Latest quote for one pair on one venue."""
    normalized = require_symbol(symbol)
    ticker, used = await call_exchange(
        "fetch_ticker",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
    )
    payload = summarize_ticker(ticker)
    payload["symbol"] = normalized
    payload["exchange"] = used
    return payload


async def fetch_candles(
    symbol: str,
    interval: str,
    limit: int,
    exchange: str | None,
) -> CandleSeries:
    """Fetch capped OHLCV candles, oldest first."""
    normalized = require_symbol(symbol)
    timeframe = validate_interval(interval)
    capped = bounded("limit", limit, MAX_CANDLES)
    candles, used = await call_exchange(
        "fetch_ohlcv",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
        timeframe=timeframe,
        limit=capped.applied,
    )
    return CandleSeries(
        symbol=normalized,
        interval=timeframe,
        exchange=used,
        candles=candles,
        limit=capped,
    )


async def candles_payload(
    symbol: str,
    interval: str,
    limit: int,
    exchange: str | None,
) -> dict[str, Any]:
    """OHLCV candles for one pair, oldest first."""
    series = await fetch_candles(symbol, interval, limit, exchange)
    payload = {
        "symbol": series.symbol,
        "exchange": series.exchange,
        "interval": series.interval,
        "count": len(series.candles),
        "columns": ["timestamp", "open", "high", "low", "close", "volume"],
        "candles": series.candles,
    }
    return note_limits(payload, series.limit)


async def order_book_payload(
    symbol: str,
    depth: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Order-book levels for one pair."""
    normalized = require_symbol(symbol)
    capped = bounded("depth", depth, MAX_ORDER_BOOK_LEVELS)
    book, used = await call_exchange(
        "fetch_order_book",
        normalized,
        capped.applied,
        exchange_id=exchange,
        allow_fallback=True,
    )
    payload = {
        "symbol": normalized,
        "exchange": used,
        "levels": capped.applied,
        "bids": book.get("bids", [])[: capped.applied],
        "asks": book.get("asks", [])[: capped.applied],
    }
    return note_limits(payload, capped)


async def trades_payload(symbol: str, limit: int, exchange: str | None) -> dict[str, Any]:
    """Most recent public fills for one pair."""
    normalized = require_symbol(symbol)
    capped = bounded("limit", limit, MAX_TRADES)
    trades, used = await call_exchange(
        "fetch_trades",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
        limit=capped.applied,
    )
    rows = [
        {
            "timestamp": trade.get("timestamp"),
            "datetime": trade.get("datetime"),
            "side": trade.get("side"),
            "price": trade.get("price"),
            "amount": trade.get("amount"),
            "cost": trade.get("cost"),
        }
        for trade in trades[: capped.applied]
    ]
    payload = {"symbol": normalized, "exchange": used, "count": len(rows), "trades": rows}
    return note_limits(payload, capped)


def _funding_row(rate: dict[str, Any], exchange: str) -> dict[str, Any]:
    next_funding = rate.get("nextFundingTimestamp") or rate.get("nextFundingTime")
    return {
        "symbol": rate.get("symbol"),
        "exchange": exchange,
        "fundingRate": rate.get("fundingRate"),
        "nextFundingTimestamp": next_funding,
        "predictedFundingRate": rate.get("predictedFundingRate"),
    }


async def funding_rate_payload(symbol: str, exchange: str | None) -> dict[str, Any]:
    """Current funding rate for one perpetual contract."""
    normalized = require_symbol(symbol)
    rate, used = await call_exchange(
        "fetch_funding_rate",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
    )
    return _funding_row(rate, used)


def _spread(results: dict[str, Any], value_key: str) -> dict[str, Any] | None:
    """Highest/lowest venue for one numeric field, or ``None`` if unavailable."""
    pairs = [
        (name, row[value_key])
        for name, row in results.items()
        if isinstance(row, dict)
        and "error" not in row
        and isinstance(row.get(value_key), int | float)
        and not isinstance(row.get(value_key), bool)
    ]
    if len(pairs) < 2:
        return None
    highest = max(pairs, key=lambda item: item[1])
    lowest = min(pairs, key=lambda item: item[1])
    absolute = highest[1] - lowest[1]
    return {
        "highest": {"exchange": highest[0], value_key: highest[1]},
        "lowest": {"exchange": lowest[0], value_key: lowest[1]},
        "absolute": absolute,
        "percent": (absolute / lowest[1]) * 100 if lowest[1] else None,
    }


async def compare_payload(
    symbol: str,
    exchanges: list[str] | None,
    field: CompareField,
) -> dict[str, Any]:
    """Compare one field for a pair across two or more venues."""
    normalized = require_symbol(symbol)
    venues = list(
        dict.fromkeys(
            item.strip().lower()
            for item in (exchanges or list(DEFAULT_COMPARE_EXCHANGES))
            if item.strip()
        )
    )
    if len(venues) < 2:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            "compare_markets needs at least two exchange ids.",
        )

    if field == "funding_rate":
        value_key = "fundingRate"

        async def load(exchange_id: str) -> dict[str, Any]:
            rate, used = await call_exchange(
                "fetch_funding_rate",
                normalized,
                exchange_id=exchange_id,
                allow_fallback=False,
            )
            return _funding_row(rate, used)
    else:
        value_key = field

        async def load(exchange_id: str) -> dict[str, Any]:
            ticker, used = await call_exchange(
                "fetch_ticker",
                normalized,
                exchange_id=exchange_id,
                allow_fallback=False,
            )
            summary = summarize_ticker(ticker)
            summary["symbol"] = normalized
            summary["exchange"] = used
            return summary

    results = await map_exchanges(venues, load)
    return {
        "symbol": normalized,
        "field": field,
        "default_exchange": resolve_exchange_id(None),
        "venues": results,
        "spread": _spread(results, value_key),
    }


# --- Tools -------------------------------------------------------------------
def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_ticker(symbol: str, exchange: str | None = None) -> str:
        """Latest quote for one pair: last, bid, ask, 24h volume and change.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
                Defaults to the configured exchange.
        """
        return json_text(await ticker_payload(symbol, exchange))

    @mcp.tool
    async def get_candles(
        symbol: str,
        interval: str = DEFAULT_INTERVAL,
        limit: int = DEFAULT_CANDLES,
        exchange: str | None = None,
    ) -> str:
        """Fetch OHLCV candles for one pair, oldest first.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            interval: Candle interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M.
            limit: Number of candles to return, capped at 1000.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await candles_payload(symbol, interval, limit, exchange))

    @mcp.tool
    async def get_order_book(
        symbol: str,
        depth: int = DEFAULT_DEPTH,
        exchange: str | None = None,
    ) -> str:
        """Fetch the order book for one pair, with bids and asks.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            depth: Number of levels per side, capped at 50.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await order_book_payload(symbol, depth, exchange))

    @mcp.tool
    async def get_recent_trades(
        symbol: str,
        limit: int = DEFAULT_TRADES,
        exchange: str | None = None,
    ) -> str:
        """Fetch the most recent public fills for one pair.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            limit: Number of fills to return, capped at 200.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await trades_payload(symbol, limit, exchange))

    @mcp.tool
    async def get_funding_rate(symbol: str, exchange: str | None = None) -> str:
        """Current funding rate, next funding time and predicted rate for a perp.

        Perpetual contracts only. Pass the contract symbol when a venue
        distinguishes it from spot, e.g. BTC/USDT:USDT.

        Args:
            symbol: Contract or pair, e.g. BTC/USDT.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await funding_rate_payload(symbol, exchange))

    @mcp.tool
    async def compare_markets(
        symbol: str,
        exchanges: list[str] | None = None,
        field: CompareField = "last",
    ) -> str:
        """Compare one field for a pair across venues and report the spread.

        Use this for cross-venue price or funding-rate spreads, e.g. Binance
        versus OKX. Each venue is queried independently; a single venue failure
        is reported in place without aborting the comparison.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            exchanges: Exchange ids to compare. Defaults to binance and okx.
            field: last, bid, ask or funding_rate.
        """
        return json_text(await compare_payload(symbol, exchanges, field))
