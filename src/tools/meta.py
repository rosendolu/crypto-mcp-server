"""Server, exchange and capability introspection tools."""

from __future__ import annotations

import platform
import time
from typing import Any

import ccxt
import fastmcp
import pandas
from fastmcp import FastMCP

from config import (
    STARTED_AT,
    VERSION,
    configured_exchanges,
    log_level,
)
from exchanges import MAJOR_EXCHANGES, capability_matrix, resolve_exchange_id
from formatting import json_text
from permissions import describe_levels, permission_level
from validation import (
    MAX_CANDLES,
    MAX_FUNDING_HISTORY,
    MAX_INDICATOR_TAIL,
    MAX_OPEN_INTEREST_POINTS,
    MAX_ORDER_BOOK_LEVELS,
    MAX_ORDERS,
    MAX_POSITIONING_POINTS,
    MAX_SCAN_ROWS,
    MAX_TIMEFRAMES,
    MAX_TRADES,
    SUPPORTED_INTERVALS,
)


def server_info_payload() -> dict[str, Any]:
    """Identity, transport and dependency versions for this running server."""
    return {
        "name": "Crypto MCP Server",
        "version": VERSION,
        "transport": "stdio",
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "python": platform.python_version(),
        "fastmcp": fastmcp.__version__,
        "ccxt": ccxt.__version__,
        "pandas": pandas.__version__,
        "permission_level": permission_level().name.lower(),
        "default_exchange": resolve_exchange_id(None),
        "log_level": log_level(),
    }


def capabilities_payload() -> dict[str, Any]:
    """Permission ladder, size limits and registered resources."""
    payload = describe_levels()
    payload["default_exchange"] = resolve_exchange_id(None)
    payload["configured_exchanges"] = configured_exchanges()
    payload["limits"] = {
        "candles": MAX_CANDLES,
        "order_book_levels": MAX_ORDER_BOOK_LEVELS,
        "trades": MAX_TRADES,
        "orders": MAX_ORDERS,
        "indicator_tail": MAX_INDICATOR_TAIL,
        "timeframes_per_call": MAX_TIMEFRAMES,
        "funding_history_points": MAX_FUNDING_HISTORY,
        "open_interest_points": MAX_OPEN_INTEREST_POINTS,
        "positioning_points": MAX_POSITIONING_POINTS,
        "scan_rows": MAX_SCAN_ROWS,
    }
    payload["intervals"] = list(SUPPORTED_INTERVALS)
    payload["resources"] = [
        "crypto://indicators",
        "crypto://patterns",
        "crypto://exchanges",
        "crypto://server-info",
    ]
    payload["prompts"] = [
        "analyze_trend",
        "funding_arbitrage_check",
        "market_overview",
        "portfolio_review",
    ]
    return payload


def exchanges_payload(exchange_ids: list[str] | None = None) -> dict[str, Any]:
    """Supported venues with their capability matrix and credential state."""
    feature_set = exchange_ids or list(MAJOR_EXCHANGES)
    return {
        "active_default": resolve_exchange_id(None),
        "permission_level": permission_level().name.lower(),
        "configured": configured_exchanges(),
        "supported_count": len(ccxt.exchanges),
        "featured": capability_matrix(feature_set),
        "note": "Any id in ccxt.exchanges is accepted as the `exchange` argument.",
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_exchanges() -> str:
        """List supported exchanges, their data capabilities and credential state.

        Use this to discover valid `exchange` values and to check which venues
        support funding rates, open interest or order books before calling.
        """
        return json_text(exchanges_payload())

    @mcp.tool
    async def get_capabilities() -> str:
        """Show the active permission level, tool ladder, limits and resources.

        Levels: market (quotes) -> analysis (indicators) -> portfolio
        (balances/orders) -> trading (place/cancel, explicit opt-in).
        """
        return json_text(capabilities_payload())

    @mcp.tool
    async def get_server_info() -> str:
        """Report the running server version, transport and dependency versions.

        Useful when filing a bug report or checking whether a client is
        connected to a current build.
        """
        return json_text(server_info_payload())
