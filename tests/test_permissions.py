"""Permission ladder tests."""

from __future__ import annotations

import pytest

from permissions import PermissionLevel, permission_level, tools_for


def test_default_level_is_analysis() -> None:
    assert permission_level() is PermissionLevel.ANALYSIS


def test_enable_trading_overrides_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "market")
    monkeypatch.setenv("ENABLE_TRADING", "true")
    assert permission_level() is PermissionLevel.TRADING


def test_enable_portfolio_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PERMISSION_LEVEL", raising=False)
    monkeypatch.setenv("ENABLE_PORTFOLIO", "true")
    assert permission_level() is PermissionLevel.PORTFOLIO


def test_unknown_level_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_LEVEL", "admin")
    with pytest.raises(ValueError, match="Unknown PERMISSION_LEVEL"):
        permission_level()


def test_trading_includes_every_lower_tool() -> None:
    names = tools_for(PermissionLevel.TRADING)
    assert "get_ticker" in names
    assert "analyze_indicators" in names
    assert "scan_market" in names
    assert "get_portfolio" in names
    assert "place_order" in names


def test_market_excludes_analysis() -> None:
    names = tools_for(PermissionLevel.MARKET)
    assert "get_ticker" in names
    assert "get_basis" in names
    assert "analyze_indicators" not in names
    assert "scan_market" not in names
    assert "place_order" not in names
