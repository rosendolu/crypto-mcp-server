"""Unit tests for market regime classification (pure pandas, no network)."""

from __future__ import annotations

import pytest

from indicators import IndicatorParams
from regime import classify


def trend_candles(count: int = 120, step: float = 1.0) -> list[list[float]]:
    rows: list[list[float]] = []
    price = 100.0
    for index in range(count):
        open_price = price
        price += step
        rows.append([index * 3_600_000, open_price, price + 0.5, open_price - 0.5, price, 1000.0])
    return rows


def chop_candles(count: int = 120) -> list[list[float]]:
    rows: list[list[float]] = []
    for index in range(count):
        base = 100.0 + (1.0 if index % 2 else -1.0)
        close = base + (0.1 if index % 2 else -0.1)
        rows.append([index * 3_600_000, base, base + 1.2, base - 1.2, close, 1000.0])
    return rows


def test_uptrend_is_classified_as_trending_up() -> None:
    result = classify(trend_candles(), IndicatorParams())
    assert result["trend"] == "trending_up"
    assert result["evidence"]["adx"] is not None
    assert result["evidence"]["plus_di"] > result["evidence"]["minus_di"]
    assert result["evidence"]["ema_spread_percent"] > 0


def test_chop_is_not_classified_as_trending() -> None:
    result = classify(chop_candles(), IndicatorParams())
    assert result["trend"] in {"ranging", "transitioning"}


def test_downtrend_direction() -> None:
    result = classify(trend_candles(step=-1.0), IndicatorParams())
    assert result["trend"] == "trending_down"


def test_volatility_state_and_rules_are_reported() -> None:
    result = classify(trend_candles(), IndicatorParams())
    assert result["volatility"] in {"expanding", "compressed", "normal", "unknown"}
    assert set(result["rules"]) == {"trend", "volatility", "emas"}
    assert result["evidence"]["last_close"] > 0


def test_empty_candles_raise() -> None:
    with pytest.raises(ValueError, match="No candlestick data"):
        classify([], IndicatorParams())
