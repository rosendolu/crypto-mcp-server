"""Unit tests for the indicator engine (no network required)."""

from __future__ import annotations

import math

import pytest

from indicators import (
    SUPPORTED_INDICATORS,
    IndicatorParams,
    compute,
    indicator_catalog,
    normalize_indicator,
)


def make_candles(count: int = 120, start: float = 100.0) -> list[list[float]]:
    """Deterministic OHLCV series with a mild uptrend and oscillation."""
    candles: list[list[float]] = []
    price = start
    for index in range(count):
        price += math.sin(index / 5.0) + 0.2
        open_price = price
        close_price = price + math.sin(index / 3.0) * 0.5
        high = max(open_price, close_price) + 1.0
        low = min(open_price, close_price) - 1.0
        volume = 1000 + (index % 7) * 25
        candles.append([index * 60_000, open_price, high, low, close_price, volume])
    return candles


CANDLES = make_candles()


def test_normalize_indicator_aliases() -> None:
    assert normalize_indicator("BB") == "bollinger_bands"
    assert normalize_indicator("bollinger bands") == "bollinger_bands"
    assert normalize_indicator("willr") == "williams_r"
    assert normalize_indicator("stochrsi") == "stochastic_rsi"
    assert normalize_indicator("ao") == "awesome_oscillator"
    assert normalize_indicator("macd") == "macd"


def test_normalize_indicator_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown indicator"):
        normalize_indicator("definitely-not-an-indicator")


def test_sma_matches_manual_average() -> None:
    result = compute(CANDLES, ["sma"], IndicatorParams(period=5))
    expected = sum(row[4] for row in CANDLES[-5:]) / 5
    assert result["sma"] == pytest.approx(expected)


def test_rsi_is_bounded() -> None:
    result = compute(CANDLES, ["rsi"], IndicatorParams(period=14))
    assert 0.0 <= result["rsi"] <= 100.0


def test_macd_shape() -> None:
    result = compute(CANDLES, ["macd"], IndicatorParams())
    assert set(result["macd"]) == {"macd", "signal", "histogram"}


def test_bollinger_alias_and_shape() -> None:
    result = compute(CANDLES, ["bb"], IndicatorParams(period=20))
    assert set(result["bb"]) == {"middle", "upper", "lower"}
    assert result["bb"]["lower"] <= result["bb"]["middle"] <= result["bb"]["upper"]


def test_tail_returns_series_of_requested_length() -> None:
    result = compute(CANDLES, ["ema"], IndicatorParams(period=10, tail=3))
    assert isinstance(result["ema"], list)
    assert len(result["ema"]) == 3


def test_volume_spike_boolean() -> None:
    candles = make_candles(20)
    candles[-1][5] = 100_000.0
    assert compute(candles, ["volume_spike"], IndicatorParams(period=5))["volume_spike"] is True


def test_all_supported_indicators_compute() -> None:
    for name in SUPPORTED_INDICATORS:
        result = compute(CANDLES, [name], IndicatorParams())
        assert name in result


def test_empty_candles_raise() -> None:
    with pytest.raises(ValueError, match="No candlestick data"):
        compute([], ["rsi"], IndicatorParams())


def test_indicator_catalog_covers_every_supported_indicator() -> None:
    catalog = indicator_catalog()
    assert {row["name"] for row in catalog} == set(SUPPORTED_INDICATORS)
    assert all(row["category"] and row["description"] for row in catalog)
    assert all(row["name"] not in row["aliases"] for row in catalog)
