"""MCP resources and prompt templates."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from fastmcp import Client

from server import create_server


def read_resource(uri: str) -> dict[str, Any]:
    async def run() -> dict[str, Any]:
        async with Client(create_server()) as client:
            contents = await client.read_resource(uri)
            return json.loads(contents[0].text)

    return asyncio.run(run())


def list_prompt_names() -> set[str]:
    async def run() -> set[str]:
        async with Client(create_server()) as client:
            return {prompt.name for prompt in await client.list_prompts()}

    return asyncio.run(run())


def render_prompt(name: str, arguments: dict[str, Any]) -> str:
    async def run() -> str:
        async with Client(create_server()) as client:
            result = await client.get_prompt(name, arguments)
            return result.messages[0].content.text

    return asyncio.run(run())


def test_indicators_resource_lists_every_indicator() -> None:
    payload = read_resource("crypto://indicators")
    names = {row["name"] for row in payload["indicators"]}
    assert payload["count"] == len(payload["indicators"])
    assert {"macd", "rsi", "ichimoku_cloud", "volume_spike"} <= names
    bollinger = next(row for row in payload["indicators"] if row["name"] == "bollinger_bands")
    assert "bb" in bollinger["aliases"]
    assert bollinger["category"] == "volatility"
    assert all(row["description"] for row in payload["indicators"])


def test_exchanges_resource_reports_capabilities() -> None:
    payload = read_resource("crypto://exchanges")
    assert payload["supported_count"] > 50
    featured = {row["exchange"]: row for row in payload["featured"]}
    assert featured["binance"]["fetchOHLCV"] is True
    assert featured["binance"]["fetchFundingRate"] is True


def test_patterns_resource_lists_every_pattern() -> None:
    payload = read_resource("crypto://patterns")
    names = {row["name"] for row in payload["patterns"]}
    assert payload["count"] == len(payload["patterns"])
    assert {"doji", "bullish_engulfing", "morning_star"} <= names
    assert all(row["direction"] for row in payload["patterns"])


def test_server_info_resource_reports_transport() -> None:
    payload = read_resource("crypto://server-info")
    assert payload["transport"] == "stdio"
    assert payload["version"] == "3.0.0"


def test_default_level_exposes_public_prompts_only() -> None:
    names = list_prompt_names()
    assert {"analyze_trend", "funding_arbitrage_check", "market_overview"} <= names
    assert "portfolio_review" not in names


def test_portfolio_prompt_is_gated_by_permission_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "portfolio")
    assert "portfolio_review" in list_prompt_names()


def test_analyze_trend_prompt_uses_the_requested_symbol() -> None:
    prompt = render_prompt("analyze_trend", {"symbol": "ETH/USDT", "interval": "1h"})
    assert "ETH/USDT" in prompt
    assert "1h" in prompt
    assert "analyze_indicators" in prompt
