"""FastMCP server assembly."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastmcp import FastMCP

import tools
from config import VERSION, configure_logging, load_env
from exchanges import close_exchanges
from permissions import permission_level

INSTRUCTIONS = """\
Crypto MCP Server — market data, derivatives intelligence, technical analysis,
and optional trading over CCXT.

Permission ladder (default: analysis, trading never implied):
- market: quotes, candles, order book, fills, funding, funding history, open
  interest, basis, positioning and venue comparison
- analysis: + indicators, multi-timeframe analysis, candlestick patterns,
  market regime and the market screener
- portfolio: + get_balance, get_orders, get_portfolio, get_positions (needs keys)
- trading: + place_order, cancel_order (PERMISSION_LEVEL=trading or ENABLE_TRADING=true)

Symbols use BASE/QUOTE (e.g. BTC/USDT). Pass `exchange` to target a venue.
Perpetual contracts use BASE/QUOTE:QUOTE (e.g. BTC/USDT:USDT) and derivative
tools derive that symbol from the pair for you.
Read crypto://indicators and crypto://patterns for the catalogues, and
crypto://exchanges for venue capabilities before calling.
Prompts: analyze_trend, funding_arbitrage_check, market_overview, portfolio_review.
Unsupported capabilities return NOT_SUPPORTED instead of an empty result.
Public calls retry on transient errors and may fall back to EXCHANGE_FALLBACKS.
This software is for research and automation tooling. It is not investment advice.
"""


@asynccontextmanager
async def lifespan(_: FastMCP):
    """Close cached CCXT clients when the server shuts down."""
    yield
    await close_exchanges()


def create_server() -> FastMCP:
    """Build the stdio FastMCP server with the configured permission level."""
    load_env()
    configure_logging()
    level = permission_level()
    mcp = FastMCP(
        name="Crypto MCP Server",
        instructions=INSTRUCTIONS,
        version=VERSION,
        lifespan=lifespan,
    )
    tools.register_all(mcp, level=level)
    return mcp
