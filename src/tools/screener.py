"""Server-side market screening over public tickers and funding rates."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from errors import CryptoMCPError, ErrorCode
from exchanges import call_exchange
from formatting import json_text
from validation import MAX_SCAN_ROWS, bounded, note_limits

logger = logging.getLogger("crypto_mcp.tools.screener")

SortKey = Literal[
    "quote_volume",
    "change_percent",
    "funding_rate",
    "abs_funding_rate",
    "spread_percent",
]
MarketType = Literal["spot", "swap", "all"]

DEFAULT_QUOTE = "USDT"
DEFAULT_LIMIT = 20
FUNDING_SORTS = ("funding_rate", "abs_funding_rate")


def _matches_quote(symbol: str, quote: str) -> bool:
    base, _, rest = symbol.partition("/")
    if not base or not rest:
        return False
    return rest.split(":")[0].upper() == quote


def _matches_market_type(symbol: str, market_type: MarketType) -> bool:
    is_contract = ":" in symbol
    if market_type == "spot":
        return not is_contract
    if market_type == "swap":
        return is_contract
    return True


def _row(ticker: dict[str, Any]) -> dict[str, Any]:
    last = ticker.get("last")
    bid = ticker.get("bid")
    ask = ticker.get("ask")
    spread_percent = None
    if isinstance(bid, int | float) and isinstance(ask, int | float) and last:
        spread_percent = (ask - bid) / last * 100.0
    return {
        "symbol": ticker.get("symbol"),
        "last": last,
        "bid": bid,
        "ask": ask,
        "spread_percent": spread_percent,
        "change_percent": ticker.get("percentage"),
        "quote_volume": ticker.get("quoteVolume"),
        "base_volume": ticker.get("baseVolume"),
        "high": ticker.get("high"),
        "low": ticker.get("low"),
        "funding_rate": None,
    }


def _sort_value(row: dict[str, Any], sort_by: SortKey) -> float | None:
    value = row.get("funding_rate") if sort_by in FUNDING_SORTS else row.get(sort_by)
    if sort_by == "abs_funding_rate" and isinstance(value, int | float):
        return abs(value)
    return value if isinstance(value, int | float) else None


def _passes_filters(
    row: dict[str, Any],
    min_quote_volume: float | None,
    min_change_percent: float | None,
    max_change_percent: float | None,
) -> bool:
    volume = row.get("quote_volume")
    change = row.get("change_percent")
    if min_quote_volume is not None and (
        not isinstance(volume, int | float) or volume < min_quote_volume
    ):
        return False
    if min_change_percent is not None and (
        not isinstance(change, int | float) or change < min_change_percent
    ):
        return False
    return not (
        max_change_percent is not None
        and isinstance(change, int | float)
        and change > max_change_percent
    )


async def scan_payload(
    exchange: str | None,
    quote: str,
    market_type: MarketType,
    sort_by: SortKey,
    limit: int,
    min_quote_volume: float | None,
    min_change_percent: float | None,
    max_change_percent: float | None,
    include_funding: bool,
) -> dict[str, Any]:
    """Filter, rank and slice a venue's markets in one round trip."""
    quote_currency = (quote or DEFAULT_QUOTE).strip().upper()
    if not quote_currency:
        raise CryptoMCPError(ErrorCode.INVALID_ARGUMENT, "`quote` must not be empty.")
    capped = bounded("limit", limit, MAX_SCAN_ROWS)

    tickers, used = await call_exchange(
        "fetch_tickers",
        exchange_id=exchange,
        allow_fallback=True,
    )
    rows = [
        _row(ticker)
        for ticker in tickers.values()
        if isinstance(ticker.get("symbol"), str)
        and _matches_quote(ticker["symbol"], quote_currency)
        and _matches_market_type(ticker["symbol"], market_type)
    ]

    notes: list[str] = []
    if include_funding or sort_by in FUNDING_SORTS:
        try:
            rates, _ = await call_exchange(
                "fetch_funding_rates",
                exchange_id=used,
                allow_fallback=False,
            )
            for row in rows:
                row["funding_rate"] = (rates.get(f"{row['symbol']}:{quote_currency}") or {}).get(
                    "fundingRate"
                )
        except CryptoMCPError as error:
            notes.append(
                f"funding rates unavailable on {used} ({error.code}); "
                "funding_rate is null in every row"
            )

    filtered = [
        row
        for row in rows
        if _passes_filters(row, min_quote_volume, min_change_percent, max_change_percent)
    ]
    ranked = [
        (row, _sort_value(row, sort_by))
        for row in filtered
    ]
    rankable = [(row, value) for row, value in ranked if value is not None]
    missing = len(ranked) - len(rankable)
    ascending = sort_by == "spread_percent"
    rankable.sort(key=lambda item: item[1], reverse=not ascending)
    selected = [row for row, _ in rankable[: capped.applied]]

    payload = {
        "exchange": used,
        "quote": quote_currency,
        "market_type": market_type,
        "sorted_by": sort_by,
        "order": "ascending" if ascending else "descending",
        "filters": {
            "min_quote_volume": min_quote_volume,
            "min_change_percent": min_change_percent,
            "max_change_percent": max_change_percent,
        },
        "markets_matched": len(filtered),
        "skipped_missing_sort_field": missing,
        "returned": len(selected),
        "rows": selected,
    }
    if notes:
        payload["notes"] = notes
    return note_limits(payload, capped)


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def scan_market(
        exchange: str | None = None,
        quote: str = DEFAULT_QUOTE,
        market_type: MarketType = "spot",
        sort_by: SortKey = "quote_volume",
        limit: int = DEFAULT_LIMIT,
        min_quote_volume: float | None = None,
        min_change_percent: float | None = None,
        max_change_percent: float | None = None,
        include_funding: bool = False,
    ) -> str:
        """Screen a venue's markets in one call: filter, rank and slice.

        Use this for questions like "most liquid USDT pairs", "biggest movers",
        "extreme funding" or "tightest spreads". Market data comes from the
        venue's ticker snapshot; funding is merged when requested or when
        sorting by a funding field.

        Args:
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            quote: Quote currency to screen, e.g. USDT.
            market_type: spot (default), swap, or all to include both.
            sort_by: quote_volume, change_percent, funding_rate,
                abs_funding_rate or spread_percent (spread sorts ascending).
            limit: Rows to return, capped at 100.
            min_quote_volume: Drop markets below this 24h quote volume.
            min_change_percent: Drop markets below this 24h change.
            max_change_percent: Drop markets above this 24h change.
            include_funding: Merge funding rates into every row.
        """
        return json_text(
            await scan_payload(
                exchange,
                quote,
                market_type,
                sort_by,
                limit,
                min_quote_volume,
                min_change_percent,
                max_change_percent,
                include_funding,
            )
        )
