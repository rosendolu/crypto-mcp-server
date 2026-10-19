"""Shared pytest fixtures. Tests never call live exchange APIs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def recorded_ohlcv_btc_4h() -> list[list[float]]:
    payload = json.loads((FIXTURES / "ohlcv_btc_usdt_4h.json").read_text())
    return payload["candles"]


@pytest.fixture
def recorded_tickers() -> dict[str, dict]:
    return json.loads((FIXTURES / "tickers_btc_usdt.json").read_text())


@pytest.fixture
def recorded_balances() -> dict[str, dict]:
    return json.loads((FIXTURES / "balances.json").read_text())


@pytest.fixture(autouse=True)
def default_read_only_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_TRADING", raising=False)
    monkeypatch.delenv("ENABLE_PORTFOLIO", raising=False)
    monkeypatch.setenv("PERMISSION_LEVEL", "analysis")
    monkeypatch.setenv("EXCHANGE_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("EXCHANGE_MIN_INTERVAL_MS", "0")
    monkeypatch.setenv("EXCHANGE_FALLBACKS", "okx")
