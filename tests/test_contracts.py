"""Contract tests for the tool surface, its documentation and its size caps.

These guard the promises a client depends on: which tools exist at each
permission level, that every tool is documented, that every argument carries a
description, and that oversized requests are clamped instead of blowing up an
agent's context window.
"""

from __future__ import annotations

import asyncio
import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client

from config import VERSION
from permissions import TOOLS_BY_LEVEL, PermissionLevel, tools_for
from recorded_exchange import install_recorded_exchange
from server import create_server
from test_tools import call_tool, call_tool_json, list_tool_names

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DOC = ROOT / "docs" / "tools.md"
TOOL_ROW = re.compile(
    r"^\|\s*`(?P<name>[a-z_]+)`\s*\|\s*(?P<level>market|analysis|portfolio|trading)\s*\|",
    re.MULTILINE,
)

# Names from the previous generation that must not come back.
RETIRED_TOOLS = ("get_market_data", "compare_exchanges", "list_capabilities", "get_tickers")


def tool_index_rows() -> set[tuple[str, str]]:
    """Tool/level pairs from the documented index table only."""
    section = TOOLS_DOC.read_text().split("## Tool index", 1)[1].split("\n## ", 1)[0]
    return {
        (match.group("name"), match.group("level"))
        for match in TOOL_ROW.finditer(section)
    }


async def _list_tools() -> list[Any]:
    async with Client(create_server()) as client:
        return list(await client.list_tools())


# --- Tool surface ------------------------------------------------------------
def test_tool_index_matches_the_registry() -> None:
    documented = tool_index_rows()
    registry = {
        (name, level.name.lower())
        for level, names in TOOLS_BY_LEVEL.items()
        for name in names
    }
    assert documented, "docs/tools.md tool index is empty or unparsable"
    assert not registry - documented, f"undocumented: {sorted(registry - documented)}"
    unregistered = sorted(documented - registry)
    assert not unregistered, f"documented but unregistered: {unregistered}"


@pytest.mark.parametrize("level", list(PermissionLevel))
def test_registered_tools_match_the_permission_ladder(
    level: PermissionLevel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    monkeypatch.delenv("ENABLE_PORTFOLIO", raising=False)
    monkeypatch.setenv("PERMISSION_LEVEL", level.name.lower())
    assert list_tool_names() == set(tools_for(level))


def test_every_tool_argument_is_described(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "trading")
    for tool in asyncio.run(_list_tools()):
        assert (tool.description or "").strip(), f"{tool.name} has no description"
        for name, spec in tool.input_schema.get("properties", {}).items():
            assert spec.get("description"), f"{tool.name}.{name} has no argument description"


def test_no_retired_tool_names_are_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "trading")
    registered = list_tool_names()
    assert set(RETIRED_TOOLS).isdisjoint(registered), sorted(set(RETIRED_TOOLS) & registered)


def test_version_matches_pyproject() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert project["project"]["version"] == VERSION


def test_tool_count_per_level_stays_reasonable() -> None:
    """Agents pick tools less accurately as the list grows."""
    for level, names in TOOLS_BY_LEVEL.items():
        assert len(tools_for(level)) <= 24, f"{level.name.lower()} exposes {len(tools_for(level))}"
        assert len(names) >= 2, level


def test_every_tool_is_exercised_by_a_test() -> None:
    sources = "\n".join(path.read_text() for path in Path(__file__).parent.glob("test_*.py"))
    registered = sorted({name for names in TOOLS_BY_LEVEL.values() for name in names})
    missing = [name for name in registered if f'"{name}"' not in sources]
    assert not missing, f"registered tools with no test call: {missing}"


def test_trading_is_never_registered_by_default() -> None:
    assert {"place_order", "cancel_order"}.isdisjoint(list_tool_names())


# --- Size caps ---------------------------------------------------------------
def test_candle_limit_is_clamped_and_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_candles", {"symbol": "BTC/USDT", "limit": 10_000})
    assert payload["truncated"] is True
    assert payload["limits"]["limit"] == {"requested": 10_000, "applied": 1000, "cap": 1000}


def test_order_book_depth_is_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("get_order_book", {"symbol": "BTC/USDT", "depth": 5_000})
    assert payload["limits"]["depth"] == {"requested": 5_000, "applied": 50, "cap": 50}


def test_indicator_tail_is_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "analyze_indicators",
        {"symbol": "BTC/USDT", "limit": 48, "tail": 500, "indicators": ["rsi"]},
    )
    assert payload["limits"]["tail"] == {"requested": 500, "applied": 50, "cap": 50}
    assert len(payload["indicators"]["rsi"]) <= 50


def test_funding_history_and_positioning_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    history = call_tool_json("get_funding_history", {"symbol": "BTC/USDT", "limit": 9_999})
    assert history["limits"]["limit"]["cap"] == 200
    ratio = call_tool_json("get_long_short_ratio", {"symbol": "BTC/USDT", "limit": 9_999})
    assert ratio["limits"]["limit"]["cap"] == 200


def test_open_interest_history_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json(
        "get_open_interest",
        {"symbol": "BTC/USDT", "interval": "4h", "limit": 9_999},
    )
    assert payload["limits"]["limit"]["cap"] == 200
    assert payload["mode"] == "history"


def test_scan_rows_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    payload = call_tool_json("scan_market", {"limit": 9_999})
    assert payload["limits"]["limit"]["cap"] == 100


def test_timeframe_count_is_rejected_above_the_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="At most 4 timeframes"):
        call_tool(
            "get_multi_timeframe_analysis",
            {"symbol": "BTC/USDT", "timeframes": ["5m", "15m", "1h", "4h", "1d"]},
        )


def test_orders_limit_is_clamped_on_markdown_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "portfolio")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")
    install_recorded_exchange(monkeypatch)
    output = call_tool("get_orders", {"kind": "open", "symbol": "BTC/USDT", "limit": 100_000})
    assert "capped at 500" in output


def test_zero_limit_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="INVALID_ARGUMENT"):
        call_tool("get_candles", {"symbol": "BTC/USDT", "limit": 0})


def test_bad_interval_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    with pytest.raises(Exception, match="Unsupported interval") as exc_info:
        call_tool("get_candles", {"symbol": "BTC/USDT", "interval": "7h"})
    assert "INVALID_ARGUMENT" in str(exc_info.value)


def test_default_requests_are_not_flagged_as_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    install_recorded_exchange(monkeypatch)
    for name, arguments in (
        ("get_candles", {"symbol": "BTC/USDT"}),
        ("get_order_book", {"symbol": "BTC/USDT"}),
        ("get_recent_trades", {"symbol": "BTC/USDT"}),
        ("get_funding_history", {"symbol": "BTC/USDT"}),
        ("scan_market", {}),
    ):
        assert "truncated" not in call_tool_json(name, arguments), name
