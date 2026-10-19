"""Derivatives intelligence: funding history, open interest, basis, positioning."""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from errors import CryptoMCPError, ErrorCode
from exchanges import call_exchange, resolve_exchange_id
from formatting import json_text
from validation import (
    MAX_FUNDING_HISTORY,
    MAX_OPEN_INTEREST_POINTS,
    MAX_POSITIONING_POINTS,
    bounded,
    note_limits,
    require_symbol,
    validate_interval,
)

logger = logging.getLogger("crypto_mcp.tools.derivatives")

DEFAULT_HISTORY = 50
DEFAULT_RATIO_TIMEFRAME = "1h"
HOURS_PER_YEAR = 8760.0
DEFAULT_FUNDING_INTERVAL_HOURS = 8.0
FUNDING_INTERVALS: dict[str, float] = {
    "1h": 1.0,
    "2h": 2.0,
    "4h": 4.0,
    "6h": 6.0,
    "8h": 8.0,
    "12h": 12.0,
    "1d": 24.0,
}


def swap_symbol(symbol: str) -> str:
    """Derive the CCXT perpetual symbol for a pair, e.g. BTC/USDT -> BTC/USDT:USDT."""
    normalized = require_symbol(symbol)
    if ":" in normalized:
        return normalized
    base, _, quote = normalized.partition("/")
    if not base or not quote:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"`symbol` must look like BTC/USDT, got '{symbol}'.",
        )
    return f"{base}/{quote}:{quote}"


def _interval_hours(values: list[int]) -> float:
    """Most common gap between consecutive timestamps, in hours."""
    gaps = [
        (later - earlier) / 3_600_000.0
        for earlier, later in zip(values, values[1:], strict=False)
        if later > earlier
    ]
    if not gaps:
        return DEFAULT_FUNDING_INTERVAL_HOURS
    return sorted(gaps)[len(gaps) // 2]


def _annualized_percent(rate: float, interval_hours: float) -> float:
    return rate * (HOURS_PER_YEAR / interval_hours) * 100.0


def funding_interval_hours(funding: dict[str, Any] | None) -> float:
    """Funding interval in hours, from the venue hint or the funding timestamps."""
    if not funding:
        return DEFAULT_FUNDING_INTERVAL_HOURS
    raw = funding.get("interval")
    if isinstance(raw, str) and raw in FUNDING_INTERVALS:
        return FUNDING_INTERVALS[raw]
    next_timestamp = funding.get("nextFundingTimestamp")
    timestamp = funding.get("timestamp")
    if (
        isinstance(next_timestamp, int)
        and isinstance(timestamp, int)
        and next_timestamp > timestamp
    ):
        return (next_timestamp - timestamp) / 3_600_000.0
    return DEFAULT_FUNDING_INTERVAL_HOURS


async def funding_history_payload(
    symbol: str,
    limit: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Historical funding rates for one perpetual contract."""
    normalized = require_symbol(symbol)
    capped = bounded("limit", limit, MAX_FUNDING_HISTORY)
    history, used = await call_exchange(
        "fetch_funding_rate_history",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
        limit=capped.applied,
    )
    rows = [
        {
            "symbol": entry.get("symbol"),
            "fundingRate": entry.get("fundingRate"),
            "timestamp": entry.get("timestamp"),
            "datetime": entry.get("datetime"),
        }
        for entry in history[: capped.applied]
    ]
    rates = [row["fundingRate"] for row in rows if isinstance(row["fundingRate"], int | float)]
    timestamps = [row["timestamp"] for row in rows if isinstance(row["timestamp"], int)]
    summary: dict[str, Any] = {"points": len(rates)}
    if rates:
        average = sum(rates) / len(rates)
        interval_hours = _interval_hours(sorted(timestamps))
        summary |= {
            "average_rate": average,
            "min_rate": min(rates),
            "max_rate": max(rates),
            "average_annualized_percent": _annualized_percent(average, interval_hours),
            "funding_interval_hours": interval_hours,
        }
    payload = {
        "symbol": normalized,
        "exchange": used,
        "count": len(rows),
        "summary": summary,
        "history": rows,
    }
    return note_limits(payload, capped)


def _open_interest_row(interest: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": interest.get("symbol"),
        "openInterestAmount": interest.get("openInterestAmount"),
        "openInterestValue": interest.get("openInterestValue"),
        "timestamp": interest.get("timestamp"),
        "datetime": interest.get("datetime"),
    }


async def open_interest_payload(
    symbol: str,
    interval: str | None,
    limit: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Current open interest, or its history when ``interval`` is given."""
    normalized = require_symbol(symbol)
    if interval is None:
        interest, used = await call_exchange(
            "fetch_open_interest",
            normalized,
            exchange_id=exchange,
            allow_fallback=True,
        )
        return {
            "symbol": normalized,
            "exchange": used,
            "mode": "current",
            "openInterest": _open_interest_row(interest),
        }

    timeframe = validate_interval(interval)
    capped = bounded("limit", limit, MAX_OPEN_INTEREST_POINTS)
    history, used = await call_exchange(
        "fetch_open_interest_history",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
        timeframe=timeframe,
        limit=capped.applied,
    )
    rows = [_open_interest_row(entry) for entry in history[: capped.applied]]
    payload = {
        "symbol": normalized,
        "exchange": used,
        "mode": "history",
        "interval": timeframe,
        "count": len(rows),
        "history": rows,
    }
    return note_limits(payload, capped)


async def basis_payload(symbol: str, exchange: str | None) -> dict[str, Any]:
    """Spot versus perpetual basis plus the funding carry on one venue."""
    normalized = require_symbol(symbol)
    contract = swap_symbol(normalized)
    venue = resolve_exchange_id(exchange)

    spot, _ = await call_exchange(
        "fetch_ticker",
        normalized,
        exchange_id=venue,
        allow_fallback=False,
    )
    try:
        perpetual, _ = await call_exchange(
            "fetch_ticker",
            contract,
            exchange_id=venue,
            allow_fallback=False,
        )
    except CryptoMCPError as error:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"No perpetual contract '{contract}' on {venue}. Pass the contract "
            f"symbol explicitly (e.g. {contract}) or pick another exchange.",
            details={"symbol": normalized, "contract": contract, "reason": str(error.code)},
        ) from error

    funding: dict[str, Any] | None
    try:
        funding, _ = await call_exchange(
            "fetch_funding_rate",
            contract,
            exchange_id=venue,
            allow_fallback=False,
        )
    except CryptoMCPError:
        funding = None

    spot_price = spot.get("last")
    perpetual_price = perpetual.get("last")
    basis = None
    basis_percent = None
    if isinstance(spot_price, int | float) and isinstance(perpetual_price, int | float):
        basis = perpetual_price - spot_price
        basis_percent = (basis / spot_price * 100.0) if spot_price else None

    rate = (funding or {}).get("fundingRate")
    has_funding = isinstance(rate, int | float)
    interval_hours = funding_interval_hours(funding)

    return {
        "symbol": normalized,
        "contract": contract,
        "exchange": venue,
        "spot": {
            "symbol": normalized,
            "price": spot_price,
            "bid": spot.get("bid"),
            "ask": spot.get("ask"),
            "timestamp": spot.get("timestamp"),
        },
        "perpetual": {
            "symbol": contract,
            "price": perpetual_price,
            "bid": perpetual.get("bid"),
            "ask": perpetual.get("ask"),
            "timestamp": perpetual.get("timestamp"),
        },
        "basis": basis,
        "basis_percent": basis_percent,
        "funding_rate": rate,
        "funding_interval_hours": interval_hours if has_funding else None,
        "funding_annualized_percent": (
            _annualized_percent(rate, interval_hours) if has_funding else None
        ),
        "notes": [
            "basis = perpetual last - spot last; positive means the contract trades above spot",
            "funding_annualized_percent assumes the current rate repeats every funding interval",
        ],
    }


async def long_short_ratio_payload(
    symbol: str,
    timeframe: str,
    limit: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Long/short account ratio history for one contract."""
    normalized = require_symbol(symbol)
    period = validate_interval(timeframe)
    capped = bounded("limit", limit, MAX_POSITIONING_POINTS)
    history, used = await call_exchange(
        "fetch_long_short_ratio_history",
        normalized,
        exchange_id=exchange,
        allow_fallback=True,
        timeframe=period,
        limit=capped.applied,
    )
    rows = [
        {
            "symbol": entry.get("symbol"),
            "longShortRatio": entry.get("longShortRatio"),
            "timestamp": entry.get("timestamp"),
            "datetime": entry.get("datetime"),
        }
        for entry in history[: capped.applied]
    ]
    ratios = [
        row["longShortRatio"]
        for row in rows
        if isinstance(row["longShortRatio"], int | float)
    ]
    payload = {
        "symbol": normalized,
        "exchange": used,
        "timeframe": period,
        "count": len(rows),
        "latest": ratios[-1] if ratios else None,
        "average": (sum(ratios) / len(ratios)) if ratios else None,
        "history": rows,
    }
    return note_limits(payload, capped)


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_funding_history(
        symbol: str,
        limit: int = DEFAULT_HISTORY,
        exchange: str | None = None,
    ) -> str:
        """Funding-rate history for a perpetual contract, with carry summary.

        Use this to judge whether the current funding rate is normal for this
        contract, and what holding the position has cost over time.

        Args:
            symbol: Contract or pair, e.g. BTC/USDT.
            limit: Number of funding points to return, capped at 200.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await funding_history_payload(symbol, limit, exchange))

    @mcp.tool
    async def get_open_interest(
        symbol: str,
        interval: str | None = None,
        limit: int = DEFAULT_HISTORY,
        exchange: str | None = None,
    ) -> str:
        """Open interest for a contract: the current snapshot, or its history.

        Args:
            symbol: Contract or pair, e.g. BTC/USDT.
            interval: Omit for the current value, or pass a candle interval
                (1h, 4h, 1d, ...) to return the series instead.
            limit: Number of history points, capped at 200.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await open_interest_payload(symbol, interval, limit, exchange))

    @mcp.tool
    async def get_basis(symbol: str, exchange: str | None = None) -> str:
        """Spot versus perpetual basis and funding carry on one venue.

        Use this to see whether a contract trades above or below spot and what
        the funding rate annualizes to. Requires the venue to list both a spot
        market and a perpetual for the pair.

        Args:
            symbol: Pair, e.g. BTC/USDT.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await basis_payload(symbol, exchange))

    @mcp.tool
    async def get_long_short_ratio(
        symbol: str,
        timeframe: str = DEFAULT_RATIO_TIMEFRAME,
        limit: int = DEFAULT_HISTORY,
        exchange: str | None = None,
    ) -> str:
        """Long/short account ratio history for a contract.

        Ratio above 1 means more accounts are long than short. Coverage varies
        by venue; unsupported venues return NOT_SUPPORTED.

        Args:
            symbol: Contract or pair, e.g. BTC/USDT.
            timeframe: Sampling period, e.g. 1h, 4h, 1d.
            limit: Number of points, capped at 200.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await long_short_ratio_payload(symbol, timeframe, limit, exchange))
