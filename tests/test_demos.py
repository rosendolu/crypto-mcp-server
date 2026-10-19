"""Recorded-data walkthroughs for the README demo prompts."""

from __future__ import annotations

import json

import pytest

from indicators import IndicatorParams, compute
from recorded_exchange import RecordedExchange, install_recorded_exchange
from test_tools import call_tool


def test_demo_btc_4h_trend(recorded_ohlcv_btc_4h: list[list[float]]) -> None:
    result = compute(
        recorded_ohlcv_btc_4h,
        ["ema", "macd", "rsi", "adx"],
        IndicatorParams(period=14, tail=1),
    )
    assert 0.0 <= result["rsi"] <= 100.0
    assert set(result["macd"]) == {"macd", "signal", "histogram"}
    assert result["adx"]["adx"] >= 0


def test_demo_binance_okx_spread(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = json.loads(
        call_tool("compare_markets", {"symbol": "BTC/USDT", "exchanges": ["binance", "okx"]})
    )
    assert payload["venues"]["binance"]["last"] == 67850.1
    assert payload["venues"]["okx"]["last"] == 67862.4
    assert payload["spread"]["percent"] > 0


def test_demo_multi_exchange_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "portfolio")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")
    monkeypatch.setenv("OKX_API_KEY", "k")
    monkeypatch.setenv("OKX_SECRET", "s")
    install_recorded_exchange(monkeypatch)
    payload = json.loads(call_tool("get_portfolio", {}))
    assert payload["combined_totals"]["USDT"] == pytest.approx(15500.0)
    assert payload["venues"]["binance"]["assets"]["ETH"]["total"] == 2.0
    assert payload["venues"]["okx"]["assets"]["SOL"]["total"] == 15.0


def test_recorded_exchange_never_hits_network() -> None:
    exchange = RecordedExchange("binance")
    assert exchange.ohlcv[0][0] == 1_704_067_200_000
