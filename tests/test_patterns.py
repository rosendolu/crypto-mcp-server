"""Unit tests for candlestick pattern detection (pure pandas, no network)."""

from __future__ import annotations

import pytest

from patterns import SUPPORTED_PATTERNS, detect, normalize_pattern, pattern_catalog


def candles(*rows: tuple[float, float, float, float]) -> list[list[float]]:
    """Build OHLCV rows from (open, high, low, close) tuples."""
    return [
        [index * 3_600_000, open_price, high, low, close, 1000.0]
        for index, (open_price, high, low, close) in enumerate(rows)
    ]


def fired(data: list[list[float]], pattern: str) -> dict[str, object]:
    return detect(data, [pattern])[pattern]


def test_normalize_pattern_accepts_separators() -> None:
    assert normalize_pattern("Bullish Engulfing") == "bullish_engulfing"
    assert normalize_pattern("shooting-star") == "shooting_star"


def test_unknown_pattern_lists_the_supported_names() -> None:
    with pytest.raises(ValueError, match="Unknown pattern"):
        normalize_pattern("batman")


def test_bullish_engulfing_on_the_last_candle() -> None:
    result = fired(
        candles((100.0, 101.0, 97.5, 98.0), (97.5, 100.6, 97.4, 100.5)),
        "bullish_engulfing",
    )
    assert result["detected"] is True
    assert result["bars_ago"] == 0
    assert result["direction"] == "bullish"


def test_bearish_engulfing_on_the_last_candle() -> None:
    result = fired(
        candles((98.0, 100.5, 97.9, 100.0), (100.5, 100.6, 97.0, 97.2)),
        "bearish_engulfing",
    )
    assert result["detected"] is True
    assert result["direction"] == "bearish"


def test_hammer_and_shooting_star() -> None:
    hammer = fired(candles((100.0, 100.1, 97.0, 100.05)), "hammer")
    assert hammer["detected"] is True
    star = fired(candles((100.0, 103.1, 99.96, 99.98)), "shooting_star")
    assert star["detected"] is True


def test_doji_and_soldiers_and_crows() -> None:
    assert fired(candles((100.0, 101.0, 99.0, 100.05)), "doji")["detected"] is True
    soldiers = candles(
        (100.0, 101.0, 99.5, 100.8),
        (100.8, 102.0, 100.5, 101.9),
        (101.9, 103.0, 101.5, 102.8),
    )
    assert fired(soldiers, "three_white_soldiers")["detected"] is True
    crows = candles(
        (102.0, 102.5, 100.5, 100.8),
        (100.8, 101.0, 99.5, 99.9),
        (99.9, 100.0, 98.5, 98.8),
    )
    assert fired(crows, "three_black_crows")["detected"] is True


def test_morning_and_evening_star() -> None:
    morning = candles(
        (102.0, 102.4, 98.6, 99.0),
        (98.9, 99.4, 98.7, 99.2),
        (99.5, 101.8, 99.4, 101.5),
    )
    assert fired(morning, "morning_star")["detected"] is True
    evening = candles(
        (99.0, 102.4, 98.9, 102.0),
        (102.1, 102.4, 101.8, 101.9),
        (101.8, 101.9, 99.6, 99.8),
    )
    assert fired(evening, "evening_star")["detected"] is True


def test_older_occurrence_reports_bars_ago() -> None:
    data = candles(
        (100.0, 101.0, 97.5, 98.0),
        (97.5, 100.6, 97.4, 100.5),
        (100.5, 101.0, 99.8, 99.9),
    )
    result = fired(data, "bullish_engulfing")
    assert result["detected"] is False
    assert result["bars_ago"] == 1


def test_pattern_catalog_covers_every_supported_pattern() -> None:
    catalog = pattern_catalog()
    assert {row["name"] for row in catalog} == set(SUPPORTED_PATTERNS)
    assert all(row["direction"] in {"bullish", "bearish", "neutral"} for row in catalog)
    assert all(row["description"] for row in catalog)


def test_empty_candles_raise() -> None:
    with pytest.raises(ValueError, match="No candlestick data"):
        detect([], ["doji"])
