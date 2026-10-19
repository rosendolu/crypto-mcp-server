"""Market regime classification from OHLCV candles.

Answers what a single indicator does not: is this market trending or ranging,
and is volatility compressed or expanding? The classification is a documented
rule set over ADX/DMI, ATR%, Bollinger width and EMA spread, so a result is
reproducible instead of a black box.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from indicators import IndicatorParams, adx, atr, bollinger_bands

TREND_ADX = 25.0
TRANSITION_ADX = 20.0
WINDOW = 100
FAST_EMA = 20
SLOW_EMA = 50


def _last(series: pd.Series) -> float | None:
    clean = series.dropna()
    return float(clean.iloc[-1]) if not clean.empty else None


def _percentile_rank(series: pd.Series) -> float | None:
    clean = series.dropna().tail(WINDOW)
    if len(clean) < 20:
        return None
    return float((clean <= clean.iloc[-1]).mean() * 100.0)


def _volatility_state(percentile: float | None) -> str:
    if percentile is None:
        return "unknown"
    if percentile >= 70.0:
        return "expanding"
    if percentile <= 30.0:
        return "compressed"
    return "normal"


def _trend_state(
    adx_value: float | None,
    plus_di: float | None,
    minus_di: float | None,
) -> str:
    if adx_value is None:
        return "unknown"
    if adx_value >= TREND_ADX:
        if plus_di is not None and minus_di is not None and minus_di > plus_di:
            return "trending_down"
        return "trending_up"
    if adx_value < TRANSITION_ADX:
        return "ranging"
    return "transitioning"


def classify(candles: list[list[float]], params: IndicatorParams) -> dict[str, Any]:
    """Classify the market regime of the most recent candle."""
    if not candles:
        raise ValueError("No candlestick data available to classify the market regime.")
    rows = [row[:6] for row in candles]
    frame = pd.DataFrame(
        rows,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    ).astype(float)

    directional = adx(frame, params)
    adx_value = _last(directional["adx"])
    plus_di = _last(directional["plus_di"])
    minus_di = _last(directional["minus_di"])

    close = frame["close"]
    atr_value = _last(atr(frame, params))
    atr_percent = (atr_value / float(close.iloc[-1]) * 100.0) if atr_value else None

    bands = bollinger_bands(frame, params)
    width = (bands["upper"] - bands["lower"]) / bands["middle"] * 100.0
    width_percent = _last(width)
    width_percentile = _percentile_rank(width)

    fast = close.ewm(span=params.fast(FAST_EMA), adjust=False).mean()
    slow = close.ewm(span=params.slow(SLOW_EMA), adjust=False).mean()
    spread = (fast - slow) / slow * 100.0

    return {
        "trend": _trend_state(adx_value, plus_di, minus_di),
        "volatility": _volatility_state(width_percentile),
        "evidence": {
            "adx": adx_value,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "atr": atr_value,
            "atr_percent": atr_percent,
            "bollinger_width_percent": width_percent,
            "bollinger_width_percentile": width_percentile,
            "ema_fast": _last(fast),
            "ema_slow": _last(slow),
            "ema_spread_percent": _last(spread),
            "ema_spread_change_percent": _last(spread.diff(10)),
            "last_close": float(close.iloc[-1]),
        },
        "rules": {
            "trend": (
                f"ADX >= {TREND_ADX} is trending, direction from +DI/-DI; "
                f"ADX < {TRANSITION_ADX} is ranging; in between is transitioning"
            ),
            "volatility": (
                f"Bollinger width percentile over the last {WINDOW} bars: "
                f">= 70 expanding, <= 30 compressed, otherwise normal"
            ),
            "emas": f"{FAST_EMA}/{SLOW_EMA} EMA spread and its change over 10 bars",
        },
    }
