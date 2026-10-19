"""End-to-end tool tests using recorded fixtures and an in-memory FastMCP client."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import ccxt
import pytest
from fastmcp import Client

from recorded_exchange import RecordedExchange, install_recorded_exchange
from server import create_server


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async def run() -> Any:
        async with Client(create_server()) as client:
            result = await client.call_tool(name, arguments)
            return result.data

    return asyncio.run(run())


def call_tool_json(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return json.loads(call_tool(name, arguments))


def list_tool_names() -> set[str]:
    async def run() -> set[str]:
        async with Client(create_server()) as client:
            return {tool.name for tool in await client.list_tools()}

    return asyncio.run(run())


def enable_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "portfolio")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")


# --- Market data -------------------------------------------------------------
def test_get_ticker_normalizes_symbol(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_ticker", {"symbol": "btc_usdt"})
    assert payload["symbol"] == "BTC/USDT"
    assert payload["last"] == 67850.1
    assert payload["exchange"] == "binance"


def test_get_candles_returns_requested_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "get_candles",
        {"symbol": "BTC/USDT", "interval": "4H", "limit": 48},
    )
    assert payload["interval"] == "4h"
    assert len(payload["candles"]) == 48
    assert payload["columns"][0] == "timestamp"
    assert "truncated" not in payload


def test_get_order_book_respects_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_order_book", {"symbol": "BTC/USDT", "depth": 2})
    assert payload["levels"] == 2
    assert len(payload["bids"]) == 2
    assert len(payload["asks"]) == 2


def test_get_recent_trades(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_recent_trades", {"symbol": "BTC/USDT", "limit": 1})
    assert payload["count"] == 1
    assert payload["trades"][0]["price"] == 67850.1


def test_compare_markets_spread(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "compare_markets",
        {"symbol": "BTC/USDT", "exchanges": ["binance", "okx", "bybit"]},
    )
    assert payload["field"] == "last"
    assert payload["spread"]["highest"]["exchange"] == "okx"
    assert payload["spread"]["lowest"]["exchange"] == "bybit"
    assert payload["spread"]["absolute"] == pytest.approx(17.4)


def test_compare_markets_funding_field(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "compare_markets",
        {"symbol": "BTC/USDT", "exchanges": ["binance", "okx"], "field": "funding_rate"},
    )
    assert payload["venues"]["binance"]["fundingRate"] == 0.0001
    assert payload["spread"]["absolute"] == pytest.approx(0.00003)


def test_compare_markets_requires_two_venues(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="at least two exchange ids"):
        call_tool("compare_markets", {"symbol": "BTC/USDT", "exchanges": ["binance"]})


# --- Derivatives -------------------------------------------------------------
def test_get_funding_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_funding_rate", {"symbol": "BTC/USDT"})
    assert payload["fundingRate"] == 0.0001
    assert payload["nextFundingTimestamp"] == 1710014400000


def test_get_funding_history_summarises_carry(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_funding_history", {"symbol": "BTC/USDT"})
    assert payload["count"] == 6
    assert payload["summary"]["average_rate"] == pytest.approx(0.0001)
    assert payload["summary"]["min_rate"] == 0.00008
    assert payload["summary"]["max_rate"] == 0.00012
    assert payload["summary"]["funding_interval_hours"] == pytest.approx(8.0)
    assert payload["summary"]["average_annualized_percent"] == pytest.approx(10.95)


def test_get_open_interest_current(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_open_interest", {"symbol": "BTC/USDT"})
    assert payload["mode"] == "current"
    assert payload["openInterest"]["openInterestAmount"] == 81234.5
    assert payload["openInterest"]["openInterestValue"] == 5512345678.0


def test_get_open_interest_history(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "get_open_interest",
        {"symbol": "BTC/USDT", "interval": "4h", "limit": 2},
    )
    assert payload["mode"] == "history"
    assert payload["count"] == 2
    assert payload["history"][-1]["openInterestAmount"] == 81234.5


def test_get_open_interest_reports_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    async def unsupported(self: RecordedExchange, symbol: str) -> dict[str, Any]:
        raise ccxt.NotSupported("open interest is not published")

    install_recorded_exchange(monkeypatch)
    monkeypatch.setattr(RecordedExchange, "fetch_open_interest", unsupported)
    with pytest.raises(Exception, match="NOT_SUPPORTED"):
        call_tool("get_open_interest", {"symbol": "BTC/USDT"})


def test_get_basis(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_basis", {"symbol": "BTC/USDT"})
    assert payload["spot"]["price"] == 67850.1
    assert payload["perpetual"]["price"] == 67881.9
    assert payload["basis"] == pytest.approx(31.8)
    assert payload["basis_percent"] == pytest.approx(0.0469, rel=1e-3)
    assert payload["funding_rate"] == 0.0001
    assert payload["funding_interval_hours"] == pytest.approx(8.0)
    assert payload["funding_annualized_percent"] == pytest.approx(10.95)


def test_get_basis_explains_a_missing_perpetual(monkeypatch: pytest.MonkeyPatch) -> None:
    original = RecordedExchange.fetch_ticker

    async def spot_only(self: RecordedExchange, symbol: str) -> dict[str, Any]:
        if ":" in symbol:
            raise ccxt.BadSymbol(symbol)
        return await original(self, symbol)

    install_recorded_exchange(monkeypatch)
    monkeypatch.setattr(RecordedExchange, "fetch_ticker", spot_only)
    with pytest.raises(Exception, match="No perpetual contract"):
        call_tool("get_basis", {"symbol": "BTC/USDT"})


def test_get_long_short_ratio(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "get_long_short_ratio",
        {"symbol": "BTC/USDT", "timeframe": "1h"},
    )
    assert payload["timeframe"] == "1h"
    assert payload["count"] == 4
    assert payload["latest"] == 1.31
    assert payload["average"] == pytest.approx(1.2)


# --- Screener ----------------------------------------------------------------
def test_scan_market_defaults_to_liquid_usdt_markets(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {})
    symbols = [row["symbol"] for row in payload["rows"]]
    assert payload["quote"] == "USDT"
    assert payload["markets_matched"] == 4
    assert symbols[0] == "BTC/USDT"
    assert "ETH/BTC" not in symbols


def test_scan_market_sorts_by_change(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"sort_by": "change_percent", "limit": 2})
    assert [row["symbol"] for row in payload["rows"]] == ["DOGE/USDT", "ETH/USDT"]


def test_scan_market_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"min_quote_volume": 1_000_000_000})
    assert payload["markets_matched"] == 2
    assert {row["symbol"] for row in payload["rows"]} == {"BTC/USDT", "ETH/USDT"}

    positive = call_tool_json("scan_market", {"min_change_percent": 0})
    assert "SOL/USDT" not in {row["symbol"] for row in positive["rows"]}
    assert positive["markets_matched"] == 3


def test_scan_market_sorts_spreads_ascending(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"sort_by": "spread_percent"})
    assert payload["order"] == "ascending"
    assert payload["rows"][0]["symbol"] == "BTC/USDT"


def test_scan_market_merges_funding(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"sort_by": "abs_funding_rate", "limit": 2})
    assert [row["symbol"] for row in payload["rows"]] == ["SOL/USDT", "ETH/USDT"]
    assert payload["rows"][0]["funding_rate"] == -0.0005


def test_scan_market_quote_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"quote": "BTC"})
    assert [row["symbol"] for row in payload["rows"]] == ["ETH/BTC"]


# --- Analysis ----------------------------------------------------------------
def test_analyze_indicators_from_recorded_candles(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "analyze_indicators",
        {
            "symbol": "BTC/USDT",
            "interval": "4h",
            "limit": 48,
            "indicators": ["rsi", "macd", "bb", "ema"],
        },
    )
    assert set(payload["indicators"]) == {"rsi", "macd", "bb", "ema"}
    assert 0.0 <= payload["indicators"]["rsi"] <= 100.0
    assert payload["candles_used"] == 48


def test_analyze_indicators_rejects_unknown_indicator(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="UNKNOWN_INDICATOR"):
        call_tool("analyze_indicators", {"symbol": "BTC/USDT", "indicators": ["nope"]})


def test_multi_timeframe_analysis_reports_consensus(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "get_multi_timeframe_analysis",
        {
            "symbol": "BTC/USDT",
            "timeframes": ["1h", "4h"],
            "indicators": ["ema", "rsi", "adx"],
        },
    )
    assert payload["timeframes"] == ["1h", "4h"]
    assert set(payload["by_timeframe"]) == {"1h", "4h"}
    assert payload["consensus"]["bias"] in {"bullish", "bearish", "mixed", "unknown"}
    for frame in payload["by_timeframe"].values():
        assert frame["bias"] in {"bullish", "bearish"}
        assert set(frame["indicators"]) == {"ema", "rsi", "adx"}


def test_detect_patterns_covers_every_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("detect_patterns", {"symbol": "BTC/USDT", "interval": "4h"})
    assert payload["candles_used"] == 48
    assert len(payload["patterns"]) == 9
    assert all("detected" in entry for entry in payload["patterns"].values())


def test_detect_patterns_rejects_unknown_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="UNKNOWN_PATTERN"):
        call_tool("detect_patterns", {"symbol": "BTC/USDT", "patterns": ["batman"]})


def test_get_market_regime_reports_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_market_regime", {"symbol": "BTC/USDT", "interval": "4h"})
    assert payload["trend"] in {
        "trending_up",
        "trending_down",
        "ranging",
        "transitioning",
        "unknown",
    }
    assert payload["volatility"] in {"expanding", "compressed", "normal", "unknown"}
    assert payload["evidence"]["last_close"] == pytest.approx(43266.8)
    assert "trend" in payload["rules"]


# --- Discovery ---------------------------------------------------------------
def test_list_exchanges_reports_capabilities() -> None:
    payload = call_tool_json("list_exchanges", {})
    assert payload["active_default"] == "binance"
    assert payload["supported_count"] > 50
    featured = {row["exchange"]: row for row in payload["featured"]}
    assert featured["binance"]["fetchOHLCV"] is True
    assert featured["binance"]["fetchOpenInterest"] is True


def test_get_capabilities_lists_levels_limits_and_resources() -> None:
    payload = call_tool_json("get_capabilities", {})
    assert payload["active"] == "analysis"
    enabled = {row["level"]: row["enabled"] for row in payload["ladder"]}
    assert enabled == {
        "market": True,
        "analysis": True,
        "portfolio": False,
        "trading": False,
    }
    assert payload["limits"]["candles"] == 1000
    assert payload["limits"]["scan_rows"] == 100
    assert "crypto://indicators" in payload["resources"]
    assert "crypto://patterns" in payload["resources"]
    assert "market_overview" in payload["prompts"]


def test_get_server_info() -> None:
    payload = call_tool_json("get_server_info", {})
    assert payload["name"] == "Crypto MCP Server"
    assert payload["version"] == "3.0.0"
    assert payload["transport"] == "stdio"
    assert payload["uptime_seconds"] >= 0


# --- Portfolio ---------------------------------------------------------------
def test_portfolio_tools_require_portfolio_level(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    names = list_tool_names()
    assert {"get_balance", "get_positions"}.isdisjoint(names)
    assert "analyze_indicators" in names


def test_get_balance_and_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    enable_portfolio(monkeypatch)
    monkeypatch.setenv("OKX_API_KEY", "k")
    monkeypatch.setenv("OKX_SECRET", "s")
    install_recorded_exchange(monkeypatch)
    balance = call_tool("get_balance", {"exchange": "binance"})
    assert "BTC" in balance and "DOGE" not in balance
    portfolio = call_tool_json("get_portfolio", {})
    assert portfolio["combined_totals"]["BTC"] == pytest.approx(0.75)
    assert "binance" in portfolio["venues"]
    assert "okx" in portfolio["venues"]


def test_get_orders_open_and_trades(monkeypatch: pytest.MonkeyPatch) -> None:
    enable_portfolio(monkeypatch)
    install_recorded_exchange(monkeypatch)
    open_orders = call_tool("get_orders", {"kind": "open", "symbol": "BTC/USDT"})
    assert "open" in open_orders
    fills = call_tool("get_orders", {"kind": "my_trades", "symbol": "BTC/USDT"})
    assert "cost" in fills


def test_get_positions_filters_closed_legs(monkeypatch: pytest.MonkeyPatch) -> None:
    enable_portfolio(monkeypatch)
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_positions", {})
    assert payload["count"] == 2
    assert payload["totals"]["unrealized_pnl"] == pytest.approx(1125.05)
    assert payload["totals"]["notional"] == pytest.approx(40325.05)
    assert {row["symbol"] for row in payload["positions"]} == {
        "BTC/USDT:USDT",
        "ETH/USDT:USDT",
    }


def test_get_positions_accepts_a_pair_symbol(monkeypatch: pytest.MonkeyPatch) -> None:
    enable_portfolio(monkeypatch)
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_positions", {"symbol": "ETH/USDT"})
    assert [row["symbol"] for row in payload["positions"]] == ["ETH/USDT:USDT"]
    assert payload["positions"][0]["side"] == "short"


# --- Trading -----------------------------------------------------------------
def test_place_and_cancel_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_TRADING", "true")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")
    install_recorded_exchange(monkeypatch)
    placed = call_tool(
        "place_order",
        {
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "amount": 1.0,
            "price": 100.0,
        },
    )
    assert '"42"' in placed
    canceled = call_tool("cancel_order", {"symbol": "BTC/USDT", "order_id": "42"})
    assert "canceled" in canceled


def test_place_order_requires_price_for_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_TRADING", "true")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="price"):
        call_tool(
            "place_order",
            {"symbol": "BTC/USDT", "side": "buy", "order_type": "limit", "amount": 1.0},
        )


def test_trading_tools_can_be_enabled_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_TRADING", "true")
    assert {"place_order", "cancel_order"}.issubset(list_tool_names())
