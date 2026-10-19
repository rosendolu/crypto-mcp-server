"""Candlestick pattern detection over OHLCV candles.

Each pattern is a shape rule, plus a short trend context where the pattern is
only meaningful in one direction (engulfing, morning/evening star). Everything
is computed with pandas so the server keeps a single analytics dependency.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd

PatternFunction = Callable[[pd.DataFrame], pd.Series]

# Candles whose shadow is exactly the body length are common; compare with a
# tolerance so floating-point noise does not decide the outcome.
GEOMETRY_EPSILON = 1e-9


def _body(frame: pd.DataFrame) -> pd.Series:
    return (frame["close"] - frame["open"]).abs()


def _range(frame: pd.DataFrame) -> pd.Series:
    return (frame["high"] - frame["low"]).replace(0.0, float("nan"))


def _upper_shadow(frame: pd.DataFrame) -> pd.Series:
    return frame["high"] - frame[["open", "close"]].max(axis=1)


def _lower_shadow(frame: pd.DataFrame) -> pd.Series:
    return frame[["open", "close"]].min(axis=1) - frame["low"]


def _is_bullish(frame: pd.DataFrame) -> pd.Series:
    return frame["close"] > frame["open"]


def _is_bearish(frame: pd.DataFrame) -> pd.Series:
    return frame["close"] < frame["open"]


def _midpoint(frame: pd.DataFrame) -> pd.Series:
    return (frame["open"] + frame["close"]) / 2.0


def doji(frame: pd.DataFrame) -> pd.Series:
    """Open and close are within 10% of the candle range."""
    return _body(frame) <= 0.1 * _range(frame)


def hammer(frame: pd.DataFrame) -> pd.Series:
    """Long lower shadow, small body, little upper shadow."""
    body = _body(frame)
    return (
        (_lower_shadow(frame) >= 2.0 * body - GEOMETRY_EPSILON)
        & (_upper_shadow(frame) <= body + GEOMETRY_EPSILON)
        & (body > 0)
    )


def shooting_star(frame: pd.DataFrame) -> pd.Series:
    """Long upper shadow, small body, little lower shadow."""
    body = _body(frame)
    return (
        (_upper_shadow(frame) >= 2.0 * body - GEOMETRY_EPSILON)
        & (_lower_shadow(frame) <= body + GEOMETRY_EPSILON)
        & (body > 0)
    )


def bullish_engulfing(frame: pd.DataFrame) -> pd.Series:
    """Bullish candle whose body engulfs the previous bearish candle."""
    return (
        _is_bullish(frame)
        & _is_bearish(frame).shift(1)
        & (frame["close"] >= frame["open"].shift(1))
        & (frame["open"] <= frame["close"].shift(1))
    )


def bearish_engulfing(frame: pd.DataFrame) -> pd.Series:
    """Bearish candle whose body engulfs the previous bullish candle."""
    return (
        _is_bearish(frame)
        & _is_bullish(frame).shift(1)
        & (frame["close"] <= frame["open"].shift(1))
        & (frame["open"] >= frame["close"].shift(1))
    )


def three_white_soldiers(frame: pd.DataFrame) -> pd.Series:
    """Three rising bullish candles with higher closes."""
    bullish = _is_bullish(frame)
    return (
        bullish
        & bullish.shift(1)
        & bullish.shift(2)
        & (frame["close"] > frame["close"].shift(1))
        & (frame["close"].shift(1) > frame["close"].shift(2))
    )


def three_black_crows(frame: pd.DataFrame) -> pd.Series:
    """Three falling bearish candles with lower closes."""
    bearish = _is_bearish(frame)
    return (
        bearish
        & bearish.shift(1)
        & bearish.shift(2)
        & (frame["close"] < frame["close"].shift(1))
        & (frame["close"].shift(1) < frame["close"].shift(2))
    )


def morning_star(frame: pd.DataFrame) -> pd.Series:
    """Bearish candle, small-bodied pause, then a bullish recovery candle."""
    first = _is_bearish(frame).shift(2)
    middle_small = _body(frame).shift(1) <= 0.5 * _body(frame).shift(2)
    third = _is_bullish(frame) & (frame["close"] > _midpoint(frame).shift(2))
    return first & middle_small & third


def evening_star(frame: pd.DataFrame) -> pd.Series:
    """Bullish candle, small-bodied pause, then a bearish reversal candle."""
    first = _is_bullish(frame).shift(2)
    middle_small = _body(frame).shift(1) <= 0.5 * _body(frame).shift(2)
    third = _is_bearish(frame) & (frame["close"] < _midpoint(frame).shift(2))
    return first & middle_small & third


PATTERN_FUNCTIONS: dict[str, PatternFunction] = {
    "doji": doji,
    "hammer": hammer,
    "shooting_star": shooting_star,
    "bullish_engulfing": bullish_engulfing,
    "bearish_engulfing": bearish_engulfing,
    "three_white_soldiers": three_white_soldiers,
    "three_black_crows": three_black_crows,
    "morning_star": morning_star,
    "evening_star": evening_star,
}

# name -> (direction, one-line meaning)
PATTERN_LIBRARY: dict[str, tuple[str, str]] = {
    "doji": ("neutral", "Indecision: open and close almost equal across the range"),
    "hammer": ("bullish", "Long lower shadow: sellers rejected at the low"),
    "shooting_star": ("bearish", "Long upper shadow: buyers rejected at the high"),
    "bullish_engulfing": ("bullish", "Bullish body swallows the previous bearish candle"),
    "bearish_engulfing": ("bearish", "Bearish body swallows the previous bullish candle"),
    "three_white_soldiers": ("bullish", "Three consecutive rising bullish candles"),
    "three_black_crows": ("bearish", "Three consecutive falling bearish candles"),
    "morning_star": ("bullish", "Bearish push, pause, then a bullish recovery"),
    "evening_star": ("bearish", "Bullish push, pause, then a bearish reversal"),
}

SUPPORTED_PATTERNS = sorted(PATTERN_FUNCTIONS)


def pattern_catalog() -> list[dict[str, Any]]:
    """Describe every supported candle pattern."""
    return [
        {"name": name, "direction": direction, "description": description}
        for name, (direction, description) in sorted(PATTERN_LIBRARY.items())
    ]


def normalize_pattern(name: str) -> str:
    """Resolve a user-provided pattern name to its canonical key."""
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in PATTERN_FUNCTIONS:
        raise ValueError(
            f"Unknown pattern '{name}'. Supported patterns: {', '.join(SUPPORTED_PATTERNS)}."
        )
    return key


def detect(candles: list[list[float]], patterns: list[str]) -> dict[str, Any]:
    """Report the latest occurrence of ``patterns`` in ``candles``.

    ``detected`` means the pattern fired on the most recent candle; ``bars_ago``
    locates the most recent occurrence otherwise.
    """
    if not candles:
        raise ValueError("No candlestick data available to detect patterns.")
    rows = [row[:6] for row in candles]
    frame = pd.DataFrame(
        rows,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    ).astype(float)
    timestamps = frame["timestamp"].to_numpy()

    results: dict[str, Any] = {}
    for requested in patterns:
        canonical = normalize_pattern(requested)
        direction, description = PATTERN_LIBRARY[canonical]
        fired = PATTERN_FUNCTIONS[canonical](frame).fillna(False).to_numpy()
        positions = [index for index, value in enumerate(fired) if bool(value)]
        bars_ago: int | None = None
        timestamp: int | None = None
        if positions:
            last = positions[-1]
            bars_ago = len(fired) - 1 - last
            timestamp = int(timestamps[last])
        results[requested] = {
            "pattern": canonical,
            "direction": direction,
            "description": description,
            "detected": bars_ago == 0,
            "bars_ago": bars_ago,
            "timestamp": timestamp,
            "occurrences": len(positions),
        }
    return results
