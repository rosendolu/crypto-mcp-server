"""Technical-indicator engine.

Everything is computed from OHLCV candles with pandas, so a single dependency
covers all indicators. Each indicator returns the *latest* ``tail`` value(s),
which keeps tool responses small and directly useful to an LLM.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

# --- Indicator defaults ------------------------------------------------------
SMA_PERIOD = 14
EMA_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2.0
ADX_PERIOD = 14
STOCHASTIC_PERIOD = 14
STOCHASTIC_SIGNAL = 3
ATR_PERIOD = 14
MFI_PERIOD = 14
CMF_PERIOD = 20
WILLIAMS_PERIOD = 14
CCI_PERIOD = 20
ROC_PERIOD = 12
TRIX_PERIOD = 15
FORCE_PERIOD = 13
AO_FAST = 5
AO_SLOW = 34
STOCHRSI_PERIOD = 14
STOCHRSI_STOCH = 14
STOCHRSI_SMOOTH = 3
ICHIMOKU_CONVERSION = 9
ICHIMOKU_BASE = 26
ICHIMOKU_SPAN = 52
KELTNER_PERIOD = 20
KELTNER_MULT = 2.0
CHANDELIER_PERIOD = 22
CHANDELIER_MULT = 3.0
KST_ROC_PERIODS = (10, 13, 14, 15)
KST_SMA_PERIODS = (10, 13, 14, 9)
KST_SIGNAL = 9
PSAR_STEP = 0.02
PSAR_MAX = 0.2
VOLUME_SPIKE_FACTOR = 2.0

TICKERS = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class IndicatorParams:
    """Knobs shared by the indicator functions."""

    period: int = SMA_PERIOD
    fast_period: int | None = None
    slow_period: int | None = None
    signal_period: int | None = None
    std_dev: float = BOLLINGER_STD
    tail: int = 1

    def fast(self, default: int) -> int:
        return self.fast_period or default

    def slow(self, default: int) -> int:
        return self.slow_period or default

    def signal(self, default: int) -> int:
        return self.signal_period or default


# --- Building blocks ---------------------------------------------------------
def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False).mean()


def _true_range(frame: pd.DataFrame) -> pd.Series:
    previous_close = frame["close"].shift(1)
    ranges = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    average_gain = _wilder(gain, period)
    average_loss = _wilder(loss, period)
    relative_strength = average_gain / average_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + relative_strength))
    return rsi.where(average_loss != 0, 100.0)


def _money_flow_multiplier(frame: pd.DataFrame) -> pd.Series:
    span = (frame["high"] - frame["low"]).replace(0.0, np.nan)
    multiplier = ((frame["close"] - frame["low"]) - (frame["high"] - frame["close"])) / span
    return multiplier.fillna(0.0)


# --- Indicators --------------------------------------------------------------
def sma(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return frame["close"].rolling(params.period).mean()


def ema(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return _ema(frame["close"], params.period)


def macd(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    fast = _ema(frame["close"], params.fast(MACD_FAST))
    slow = _ema(frame["close"], params.slow(MACD_SLOW))
    macd_line = fast - slow
    signal_line = _ema(macd_line, params.signal(MACD_SIGNAL))
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": macd_line - signal_line}
    )


def rsi(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return _rsi(frame["close"], params.period)


def bollinger_bands(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    middle = frame["close"].rolling(params.period).mean()
    deviation = frame["close"].rolling(params.period).std(ddof=0)
    return pd.DataFrame(
        {
            "middle": middle,
            "upper": middle + params.std_dev * deviation,
            "lower": middle - params.std_dev * deviation,
        }
    )


def adx(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    upward = frame["high"].diff()
    downward = -frame["low"].diff()
    plus_dm = upward.where((upward > downward) & (upward > 0), 0.0)
    minus_dm = downward.where((downward > upward) & (downward > 0), 0.0)
    atr = _wilder(_true_range(frame), params.period)
    plus_di = 100.0 * _wilder(plus_dm, params.period) / atr
    minus_di = 100.0 * _wilder(minus_dm, params.period) / atr
    directional_sum = (plus_di + minus_di).replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / directional_sum
    return pd.DataFrame(
        {"adx": _wilder(dx, params.period), "plus_di": plus_di, "minus_di": minus_di}
    )


def stochastic(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    lowest = frame["low"].rolling(params.period).min()
    highest = frame["high"].rolling(params.period).max()
    percent_k = 100.0 * (frame["close"] - lowest) / (highest - lowest)
    percent_d = percent_k.rolling(params.signal(STOCHASTIC_SIGNAL)).mean()
    return pd.DataFrame({"k": percent_k, "d": percent_d})


def kdj(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    stochastic_frame = stochastic(frame, params)
    percent_k = stochastic_frame["k"]
    percent_d = stochastic_frame["d"]
    return pd.DataFrame({"k": percent_k, "d": percent_d, "j": 3 * percent_k - 2 * percent_d})


def obv(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    direction = np.sign(frame["close"].diff()).fillna(0.0)
    return (direction * frame["volume"]).cumsum()


def atr(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return _wilder(_true_range(frame), params.period)


def mfi(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    typical_price = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    raw_money_flow = typical_price * frame["volume"]
    positive = raw_money_flow.where(typical_price > typical_price.shift(1), 0.0)
    negative = raw_money_flow.where(typical_price < typical_price.shift(1), 0.0)
    ratio = positive.rolling(params.period).sum() / negative.rolling(params.period).sum()
    return 100.0 - (100.0 / (1.0 + ratio))


def cmf(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    money_flow_volume = _money_flow_multiplier(frame) * frame["volume"]
    traded_volume = frame["volume"].rolling(params.period).sum()
    return money_flow_volume.rolling(params.period).sum() / traded_volume


def williams_r(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    highest = frame["high"].rolling(params.period).max()
    lowest = frame["low"].rolling(params.period).min()
    return -100.0 * (highest - frame["close"]) / (highest - lowest)


def psar(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    highs = frame["high"].to_numpy(dtype=float)
    lows = frame["low"].to_numpy(dtype=float)
    values: list[float] = [float("nan")] * len(highs)
    if len(highs) < 2:
        return pd.Series(values, index=frame.index)
    rising = True
    extreme = highs[0]
    sar = lows[0]
    acceleration = PSAR_STEP
    values[0] = sar
    for index in range(1, len(highs)):
        sar = sar + acceleration * (extreme - sar)
        if rising:
            if lows[index] < sar:
                rising, sar, extreme, acceleration = False, extreme, lows[index], PSAR_STEP
            else:
                extreme = max(extreme, highs[index])
                acceleration = min(acceleration + PSAR_STEP, PSAR_MAX)
        else:
            if highs[index] > sar:
                rising, sar, extreme, acceleration = True, extreme, highs[index], PSAR_STEP
            else:
                extreme = min(extreme, lows[index])
                acceleration = min(acceleration + PSAR_STEP, PSAR_MAX)
        values[index] = sar
    return pd.Series(values, index=frame.index)


def cci(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    typical_price = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    moving_average = typical_price.rolling(params.period).mean()
    mean_deviation = typical_price.rolling(params.period).apply(
        lambda window: np.abs(window - window.mean()).mean(), raw=True
    )
    return (typical_price - moving_average) / (0.015 * mean_deviation)


def vwap(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    typical_price = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    return (typical_price * frame["volume"]).cumsum() / frame["volume"].cumsum()


def roc(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return frame["close"].pct_change(params.period) * 100.0


def trix(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    triple = _ema(_ema(_ema(frame["close"], params.period), params.period), params.period)
    return 100.0 * triple.pct_change()


def adl(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return (_money_flow_multiplier(frame) * frame["volume"]).cumsum()


def force_index(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    return _ema(frame["close"].diff() * frame["volume"], params.period)


def awesome_oscillator(frame: pd.DataFrame, params: IndicatorParams) -> pd.Series:
    median_price = (frame["high"] + frame["low"]) / 2.0
    fast = median_price.rolling(params.fast(AO_FAST)).mean()
    slow = median_price.rolling(params.slow(AO_SLOW)).mean()
    return fast - slow


def stochastic_rsi(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    rsi_series = _rsi(frame["close"], params.period)
    lowest = rsi_series.rolling(STOCHRSI_STOCH).min()
    highest = rsi_series.rolling(STOCHRSI_STOCH).max()
    raw = 100.0 * (rsi_series - lowest) / (highest - lowest)
    percent_k = raw.rolling(params.signal(STOCHRSI_SMOOTH)).mean()
    percent_d = percent_k.rolling(params.signal(STOCHRSI_SMOOTH)).mean()
    return pd.DataFrame({"k": percent_k, "d": percent_d})


def ichimoku_cloud(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    def midpoint(period: int) -> pd.Series:
        return (frame["high"].rolling(period).max() + frame["low"].rolling(period).min()) / 2.0

    conversion = midpoint(ICHIMOKU_CONVERSION)
    base = midpoint(ICHIMOKU_BASE)
    return pd.DataFrame(
        {
            "conversion": conversion,
            "base": base,
            "span_a": (conversion + base) / 2.0,
            "span_b": midpoint(ICHIMOKU_SPAN),
        }
    )


def keltner_channels(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    middle = _ema(frame["close"], params.period)
    bands = params.std_dev or KELTNER_MULT
    deviation = _wilder(_true_range(frame), params.period) * bands
    return pd.DataFrame(
        {"middle": middle, "upper": middle + deviation, "lower": middle - deviation}
    )


def chandelier_exit(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    period = params.period or CHANDELIER_PERIOD
    deviation = _wilder(_true_range(frame), period) * CHANDELIER_MULT
    return pd.DataFrame(
        {
            "long": frame["high"].rolling(period).max() - deviation,
            "short": frame["low"].rolling(period).min() + deviation,
        }
    )


def kst(frame: pd.DataFrame, params: IndicatorParams) -> pd.DataFrame:
    smoothed = [
        frame["close"].pct_change(roc_period).rolling(sma_period).mean() * 100.0
        for roc_period, sma_period in zip(KST_ROC_PERIODS, KST_SMA_PERIODS, strict=True)
    ]
    kst_line = sum(smoothed[1:], start=smoothed[0])
    signal_line = kst_line.rolling(params.signal(KST_SIGNAL)).mean()
    return pd.DataFrame({"kst": kst_line, "signal": signal_line})


IndicatorFunction = Callable[[pd.DataFrame, IndicatorParams], pd.Series | pd.DataFrame]

SERIES_INDICATORS: dict[str, IndicatorFunction] = {
    "sma": sma,
    "ema": ema,
    "macd": macd,
    "rsi": rsi,
    "bollinger_bands": bollinger_bands,
    "adx": adx,
    "stochastic": stochastic,
    "kdj": kdj,
    "obv": obv,
    "atr": atr,
    "mfi": mfi,
    "cmf": cmf,
    "williams_r": williams_r,
    "psar": psar,
    "cci": cci,
    "vwap": vwap,
    "roc": roc,
    "trix": trix,
    "adl": adl,
    "force_index": force_index,
    "awesome_oscillator": awesome_oscillator,
    "stochastic_rsi": stochastic_rsi,
    "ichimoku_cloud": ichimoku_cloud,
    "keltner_channels": keltner_channels,
    "chandelier_exit": chandelier_exit,
    "kst": kst,
}

# Every alias maps to a canonical indicator key. Keys are normalized by
# lower-casing and stripping spaces, underscores and dashes.
ALIASES: dict[str, str] = {
    "ma": "sma",
    "bb": "bollinger_bands",
    "bollingerbands": "bollinger_bands",
    "dmi": "adx",
    "willr": "williams_r",
    "williamsr": "williams_r",
    "parabolicsar": "psar",
    "fi": "force_index",
    "ao": "awesome_oscillator",
    "stochrsi": "stochastic_rsi",
    "ichimoku": "ichimoku_cloud",
    "ichimokucloud": "ichimoku_cloud",
    "kc": "keltner_channels",
    "keltnerchannel": "keltner_channels",
    "chandelier": "chandelier_exit",
}
ALIASES.update({name.replace("_", ""): name for name in SERIES_INDICATORS})

SPECIAL_INDICATORS = {"volume_spike"}
ALIASES.update({"volumespike": "volume_spike"})

SUPPORTED_INDICATORS = sorted({*SERIES_INDICATORS, *SPECIAL_INDICATORS})

# name -> (category, tunable parameters, one-line meaning). Kept next to the
# implementations so ``crypto://indicators`` and the tool description cannot
# drift away from what the engine actually computes.
INDICATOR_LIBRARY: dict[str, tuple[str, str, str]] = {
    "sma": ("trend", "period", "Simple moving average of close"),
    "ema": ("trend", "period", "Exponential moving average of close"),
    "macd": ("trend", "fast_period, slow_period, signal_period", "MACD line, signal and histogram"),
    "adx": ("trend", "period", "ADX trend strength with +DI/-DI"),
    "psar": ("trend", "-", "Parabolic SAR stop-and-reverse"),
    "ichimoku_cloud": ("trend", "-", "Ichimoku conversion, base, span A and span B"),
    "rsi": ("momentum", "period", "Relative Strength Index, 0-100"),
    "stochastic": ("momentum", "period, signal_period", "Stochastic %K/%D oscillator"),
    "kdj": ("momentum", "period, signal_period", "KDJ variant of the stochastic oscillator"),
    "stochastic_rsi": ("momentum", "period, signal_period", "Stochastic RSI %K/%D"),
    "williams_r": ("momentum", "period", "Williams %R, -100..0"),
    "cci": ("momentum", "period", "Commodity Channel Index"),
    "roc": ("momentum", "period", "Rate of change in percent"),
    "trix": ("momentum", "period", "Triple-smoothed EMA rate of change"),
    "awesome_oscillator": (
        "momentum",
        "fast_period, slow_period",
        "Bill Williams awesome oscillator",
    ),
    "kst": ("momentum", "signal_period", "Know Sure Thing momentum"),
    "atr": ("volatility", "period", "Average true range"),
    "bollinger_bands": (
        "volatility",
        "period, std_dev",
        "Middle/upper/lower bands around an average",
    ),
    "keltner_channels": ("volatility", "period, std_dev", "EMA channel offset by ATR"),
    "chandelier_exit": ("volatility", "period", "Chandelier exit long/short stop levels"),
    "obv": ("volume", "-", "On-balance volume, cumulative signed volume"),
    "mfi": ("volume", "period", "Money Flow Index, volume-weighted RSI"),
    "cmf": ("volume", "period", "Chaikin Money Flow"),
    "vwap": ("volume", "-", "Volume-weighted average price"),
    "adl": ("volume", "-", "Accumulation/distribution line"),
    "force_index": ("volume", "period", "Elder force index"),
    "volume_spike": (
        "volume",
        "period",
        "True when the latest volume exceeds 2x the prior average",
    ),
}


def indicator_catalog() -> list[dict[str, Any]]:
    """Describe every supported indicator, its parameters, aliases and meaning."""
    aliases: dict[str, list[str]] = {}
    for alias, canonical in ALIASES.items():
        if alias != canonical:
            aliases.setdefault(canonical, []).append(alias)
    return [
        {
            "name": name,
            "category": category,
            "parameters": parameters,
            "description": description,
            "aliases": sorted(aliases.get(name, [])),
        }
        for name, (category, parameters, description) in sorted(INDICATOR_LIBRARY.items())
    ]


def normalize_indicator(name: str) -> str:
    """Resolve a user-provided indicator name (or alias) to its canonical key."""
    key = name.strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    canonical = ALIASES.get(key)
    if canonical is None:
        raise ValueError(
            f"Unknown indicator '{name}'. Supported indicators: {', '.join(SUPPORTED_INDICATORS)}."
        )
    return canonical


def _latest(series: pd.Series, tail: int) -> Any:
    clean = series.dropna()
    if clean.empty:
        return None
    window = clean.tail(tail)
    if tail == 1:
        return float(window.iloc[-1])
    return [float(value) for value in window]


def _format_result(result: pd.Series | pd.DataFrame, tail: int) -> Any:
    if isinstance(result, pd.DataFrame):
        return {column: _latest(result[column], tail) for column in result.columns}
    return _latest(result, tail)


def _volume_spike(frame: pd.DataFrame, params: IndicatorParams) -> bool:
    period = max(params.period, 1)
    if len(frame) <= period:
        return False
    recent = frame["volume"].iloc[-period - 1 : -1]
    return bool(frame["volume"].iloc[-1] > VOLUME_SPIKE_FACTOR * recent.mean())


def compute(
    candles: list[list[float]],
    indicators: list[str],
    params: IndicatorParams,
) -> dict[str, Any]:
    """Compute ``indicators`` from raw OHLCV ``candles`` and return latest values.

    ``candles`` follow CCXT's ``[[timestamp, open, high, low, close, volume], ...]``
    layout. Unknown indicator names raise ``ValueError``.
    """
    if not candles:
        raise ValueError("No candlestick data available to compute indicators.")
    rows = [row[:6] for row in candles]
    frame = pd.DataFrame(rows, columns=["timestamp", *TICKERS]).astype(float)

    results: dict[str, Any] = {}
    for requested in indicators:
        canonical = normalize_indicator(requested)
        if canonical == "volume_spike":
            results[requested] = _volume_spike(frame, params)
        else:
            computed = SERIES_INDICATORS[canonical](frame, params)
            results[requested] = _format_result(computed, params.tail)
    return results
