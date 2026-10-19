"""Capability ladder for registered MCP tools.

Default is public read-only analysis. Trading is never implied by credentials
alone; it must be selected explicitly.
"""

from __future__ import annotations

import os
from enum import IntEnum


class PermissionLevel(IntEnum):
    """Increasing access from public market data to order execution."""

    MARKET = 1
    ANALYSIS = 2
    PORTFOLIO = 3
    TRADING = 4


LEVEL_NAMES = {
    "market": PermissionLevel.MARKET,
    "analysis": PermissionLevel.ANALYSIS,
    "portfolio": PermissionLevel.PORTFOLIO,
    "trading": PermissionLevel.TRADING,
}

TOOLS_BY_LEVEL: dict[PermissionLevel, tuple[str, ...]] = {
    PermissionLevel.MARKET: (
        "list_exchanges",
        "get_capabilities",
        "get_server_info",
        "get_ticker",
        "get_candles",
        "get_order_book",
        "get_recent_trades",
        "get_funding_rate",
        "get_funding_history",
        "get_open_interest",
        "get_basis",
        "get_long_short_ratio",
        "compare_markets",
    ),
    PermissionLevel.ANALYSIS: (
        "analyze_indicators",
        "get_multi_timeframe_analysis",
        "detect_patterns",
        "get_market_regime",
        "scan_market",
    ),
    PermissionLevel.PORTFOLIO: (
        "get_balance",
        "get_orders",
        "get_portfolio",
        "get_positions",
    ),
    PermissionLevel.TRADING: ("place_order", "cancel_order"),
}


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def permission_level() -> PermissionLevel:
    """Resolve the active capability ladder.

    Order of precedence:
    1. ``ENABLE_TRADING=true`` always selects trading.
    2. Explicit ``PERMISSION_LEVEL``.
    3. ``ENABLE_PORTFOLIO=true`` upgrades the default to portfolio.
    4. Default ``analysis`` (public market data + indicators).
    """
    if _truthy("ENABLE_TRADING"):
        return PermissionLevel.TRADING

    raw = os.environ.get("PERMISSION_LEVEL", "").strip().lower()
    if raw:
        if raw not in LEVEL_NAMES:
            valid = ", ".join(LEVEL_NAMES)
            raise ValueError(f"Unknown PERMISSION_LEVEL '{raw}'. Expected one of: {valid}.")
        return LEVEL_NAMES[raw]

    if _truthy("ENABLE_PORTFOLIO"):
        return PermissionLevel.PORTFOLIO
    return PermissionLevel.ANALYSIS


def tools_for(level: PermissionLevel) -> tuple[str, ...]:
    """Return every tool name available at ``level`` and below."""
    names: list[str] = []
    for candidate in PermissionLevel:
        if candidate <= level:
            names.extend(TOOLS_BY_LEVEL[candidate])
    return tuple(names)


def describe_levels() -> dict[str, object]:
    """Human-readable capability map for ``get_capabilities``."""
    active = permission_level()
    return {
        "active": active.name.lower(),
        "ladder": [
            {
                "level": item.name.lower(),
                "enabled": item <= active,
                "tools": list(TOOLS_BY_LEVEL[item]),
            }
            for item in PermissionLevel
        ],
        "notes": {
            "default": "analysis (public market data and indicators)",
            "portfolio": "set PERMISSION_LEVEL=portfolio or ENABLE_PORTFOLIO=true",
            "trading": "set PERMISSION_LEVEL=trading or ENABLE_TRADING=true",
            "risk": "This software is for research and automation tooling, not investment advice.",
        },
    }
