"""MCP resources and prompt templates.

Resources hand an agent the catalogue it would otherwise have to guess at
(indicator names, candle patterns, venue capabilities, build version). Prompts
hand over our analysis templates, so a user gets a repeatable workflow instead
of ad-hoc questioning. Only the portfolio prompt depends on the permission
ladder, because it describes private tools.
"""

from __future__ import annotations

from fastmcp import FastMCP

from exchanges import MAJOR_EXCHANGES
from formatting import json_text
from indicators import INDICATOR_LIBRARY, indicator_catalog
from patterns import PATTERN_LIBRARY, pattern_catalog

from .meta import exchanges_payload, server_info_payload

INDICATORS_URI = "crypto://indicators"
PATTERNS_URI = "crypto://patterns"
EXCHANGES_URI = "crypto://exchanges"
SERVER_INFO_URI = "crypto://server-info"


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        INDICATORS_URI,
        name="indicators",
        description="Every indicator this server computes, with parameters and aliases.",
        mime_type="application/json",
    )
    def indicators_resource() -> str:
        return json_text(
            {
                "count": len(INDICATOR_LIBRARY),
                "categories": ["trend", "momentum", "volatility", "volume"],
                "indicators": indicator_catalog(),
                "usage": (
                    "Pass a name or alias in analyze_indicators.indicators; "
                    "tail returns the most recent N values per series."
                ),
            }
        )

    @mcp.resource(
        PATTERNS_URI,
        name="patterns",
        description="Candlestick patterns this server detects, with direction.",
        mime_type="application/json",
    )
    def patterns_resource() -> str:
        return json_text(
            {
                "count": len(PATTERN_LIBRARY),
                "patterns": pattern_catalog(),
                "usage": (
                    "Pass a name in detect_patterns.patterns; detected means the "
                    "pattern fired on the most recent candle, bars_ago locates "
                    "the most recent occurrence otherwise."
                ),
            }
        )

    @mcp.resource(
        EXCHANGES_URI,
        name="exchanges",
        description="Feature exchanges with data capabilities and credential state.",
        mime_type="application/json",
    )
    def exchanges_resource() -> str:
        return json_text(exchanges_payload(list(MAJOR_EXCHANGES)))

    @mcp.resource(
        SERVER_INFO_URI,
        name="server-info",
        description="Build version, transport and dependency versions.",
        mime_type="application/json",
    )
    def server_info_resource() -> str:
        return json_text(server_info_payload())

    @mcp.prompt
    def analyze_trend(symbol: str = "BTC/USDT", interval: str = "4h") -> str:
        """Repeatable workflow for a multi-timeframe trend read on one pair."""
        return (
            f"Analyse the trend for {symbol} on the {interval} timeframe.\n\n"
            "1. Read crypto://indicators and choose one trend, one momentum and one "
            "volatility indicator.\n"
            f"2. Call get_market_regime for {symbol} on {interval} to learn whether the "
            "market is trending or ranging and how volatility compares with its own history.\n"
            f"3. Call get_multi_timeframe_analysis for {symbol} to check whether the "
            f"{interval} read is confirmed on the surrounding timeframes.\n"
            f"4. Call analyze_indicators for {symbol} on {interval} with the indicators "
            "you picked.\n"
            f"5. Call detect_patterns for {symbol} on {interval} to see whether the last "
            "candles carry a reversal or continuation signal.\n"
            "6. Report the trend, the level that would invalidate it, and how much the "
            "evidence agrees. Describe the data; do not give investment advice."
        )

    @mcp.prompt
    def funding_arbitrage_check(symbol: str = "BTC/USDT") -> str:
        """Checklist for a funding-rate and basis read on one contract."""
        return (
            f"Check the funding and basis situation for {symbol}.\n\n"
            "1. Call get_basis to compare spot with the perpetual and see the "
            "annualized funding carry on your main venue.\n"
            "2. Call get_funding_history to judge whether the current rate is normal "
            "for this contract.\n"
            "3. Call compare_markets with field='funding_rate' across at least three "
            "venues to see the dispersion.\n"
            "4. Call get_open_interest to see whether positioning is building or unwinding.\n"
            "5. Explain who pays whom at the next funding time, how large the cross-venue "
            "spread is, and which costs (fees, slippage, carry) the spread must cover to "
            "be interesting. Describe the data; do not give investment advice."
        )

    @mcp.prompt
    def market_overview(quote: str = "USDT", exchange: str = "binance") -> str:
        """Screening workflow for a quick read on a venue."""
        return (
            f"Give me an overview of the {quote} markets on {exchange}.\n\n"
            f"1. Call scan_market with exchange={exchange}, quote={quote} and "
            "sort_by='quote_volume' to see where liquidity sits.\n"
            f"2. Call scan_market again with the same filters but sort_by='change_percent' "
            "to separate the movers from the laggards.\n"
            "3. Call scan_market with sort_by='abs_funding_rate' to find the most crowded "
            "perpetual positioning.\n"
            "4. Pick the two or three names that stand out and call get_market_regime on "
            "them on 4h to check whether the move has structure behind it.\n"
            "5. Summarise the state of the market and what you could not verify. Describe "
            "the data; do not give investment advice."
        )


def register_portfolio(mcp: FastMCP) -> None:
    """Prompts that reference private portfolio tools."""

    @mcp.prompt
    def portfolio_review(min_total: float = 100.0) -> str:
        """Review asset distribution, positions and open orders across venues."""
        return (
            "Review my portfolio.\n\n"
            f"1. Call get_portfolio with min_total={min_total} to see per-venue and "
            "combined totals.\n"
            "2. Call get_positions to see derivative exposure, leverage and unrealized PnL.\n"
            "3. Call get_orders with kind='open' for the pairs I hold to find resting "
            "orders.\n"
            "4. Summarise concentration risk, leverage, idle balance and open-order "
            "exposure, then list what you could not verify. Describe the data; do not "
            "give investment advice."
        )
