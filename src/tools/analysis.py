"""Technical analysis tools: indicators, multi-timeframe, patterns, regime."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastmcp import FastMCP

from errors import CryptoMCPError, ErrorCode
from formatting import json_text
from indicators import SUPPORTED_INDICATORS, IndicatorParams, compute
from patterns import SUPPORTED_PATTERNS, detect
from regime import classify
from validation import (
    MAX_INDICATOR_TAIL,
    MAX_TIMEFRAMES,
    Limit,
    bounded,
    note_limits,
    validate_interval,
)

from .market import fetch_candles

logger = logging.getLogger("crypto_mcp.tools.analysis")

DEFAULT_INTERVAL = "1h"
ANALYSIS_LIMIT = 300
PATTERN_LIMIT = 200
DEFAULT_TIMEFRAMES = ("15m", "1h", "4h")
DEFAULT_INDICATORS = ("macd", "rsi", "bollinger_bands", "ema", "atr")


def _indicator_params(
    period: int,
    fast_period: int | None,
    slow_period: int | None,
    signal_period: int | None,
    std_dev: float,
    tail: int,
) -> tuple[IndicatorParams, Limit]:
    tail_limit = bounded("tail", max(tail, 1), MAX_INDICATOR_TAIL)
    params = IndicatorParams(
        period=period,
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        std_dev=std_dev,
        tail=tail_limit.applied,
    )
    return params, tail_limit


def _as_indicator_error(error: ValueError) -> CryptoMCPError:
    code = (
        ErrorCode.INSUFFICIENT_DATA
        if "candlestick" in str(error).lower()
        else ErrorCode.UNKNOWN_INDICATOR
    )
    return CryptoMCPError(
        code,
        f"{error} Supported indicators: {', '.join(SUPPORTED_INDICATORS)}.",
    )


def _as_pattern_error(error: ValueError) -> CryptoMCPError:
    code = (
        ErrorCode.INSUFFICIENT_DATA
        if "candlestick" in str(error).lower()
        else ErrorCode.UNKNOWN_PATTERN
    )
    return CryptoMCPError(
        code,
        f"{error} Supported patterns: {', '.join(SUPPORTED_PATTERNS)}.",
    )


def timeframe_bias(results: dict[str, Any], close: float) -> str | None:
    """Derived direction for one timeframe, from the indicators that were asked for.

    Price above its EMA is bullish, below is bearish; without an EMA the MACD
    histogram sign is used, and RSI above 50 is the last fallback.
    """
    ema_value = results.get("ema")
    if isinstance(ema_value, int | float):
        return "bullish" if close > ema_value else "bearish"
    macd_value = results.get("macd")
    if isinstance(macd_value, dict) and isinstance(macd_value.get("histogram"), int | float):
        return "bullish" if macd_value["histogram"] > 0 else "bearish"
    rsi_value = results.get("rsi")
    if isinstance(rsi_value, int | float):
        return "bullish" if rsi_value >= 50 else "bearish"
    return None


async def multi_timeframe_payload(
    symbol: str,
    timeframes: list[str] | None,
    indicators: list[str] | None,
    limit: int,
    period: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Indicators per timeframe plus a confluence summary."""
    requested = [validate_interval(item) for item in (timeframes or list(DEFAULT_TIMEFRAMES))]
    unique = list(dict.fromkeys(requested))
    if len(unique) > MAX_TIMEFRAMES:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"At most {MAX_TIMEFRAMES} timeframes per call, got {len(unique)}.",
            details={"timeframes": unique},
        )
    wanted = list(indicators or DEFAULT_INDICATORS)
    series = await asyncio.gather(
        *(fetch_candles(symbol, timeframe, limit, exchange) for timeframe in unique)
    )
    params = IndicatorParams(period=period, tail=1)

    by_timeframe: dict[str, Any] = {}
    biases: list[str] = []
    for item in series:
        try:
            results = compute(item.candles, wanted, params)
        except ValueError as error:
            raise _as_indicator_error(error) from error
        close = float(item.candles[-1][4])
        bias = timeframe_bias(results, close)
        if bias:
            biases.append(bias)
        by_timeframe[item.interval] = {
            "interval": item.interval,
            "candles_used": len(item.candles),
            "last_close": close,
            "bias": bias,
            "indicators": results,
        }

    bullish = biases.count("bullish")
    bearish = biases.count("bearish")
    if biases and not bearish:
        consensus = "bullish"
    elif biases and not bullish:
        consensus = "bearish"
    elif biases:
        consensus = "mixed"
    else:
        consensus = "unknown"

    return {
        "symbol": series[0].symbol,
        "exchange": series[0].exchange,
        "timeframes": unique,
        "indicators": wanted,
        "consensus": {
            "bias": consensus,
            "bullish_timeframes": bullish,
            "bearish_timeframes": bearish,
            "note": (
                "Each timeframe is bullish when the last close is above its EMA, "
                "otherwise bearish (MACD histogram and RSI are fallbacks)."
            ),
        },
        "by_timeframe": by_timeframe,
        "params": {"period": period, "limit": limit},
    }


async def patterns_payload(
    symbol: str,
    interval: str,
    limit: int,
    patterns: list[str] | None,
    exchange: str | None,
) -> dict[str, Any]:
    """Latest occurrence of each requested candle pattern."""
    series = await fetch_candles(symbol, interval, limit, exchange)
    wanted = list(patterns or SUPPORTED_PATTERNS)
    try:
        results = detect(series.candles, wanted)
    except ValueError as error:
        raise _as_pattern_error(error) from error
    return {
        "symbol": series.symbol,
        "exchange": series.exchange,
        "interval": series.interval,
        "candles_used": len(series.candles),
        "patterns": results,
    }


async def regime_payload(
    symbol: str,
    interval: str,
    limit: int,
    period: int,
    exchange: str | None,
) -> dict[str, Any]:
    """Trend/range and volatility classification with its evidence."""
    series = await fetch_candles(symbol, interval, limit, exchange)
    result = classify(series.candles, IndicatorParams(period=period))
    return {
        "symbol": series.symbol,
        "exchange": series.exchange,
        "interval": series.interval,
        "candles_used": len(series.candles),
        "summary": f"{result['trend']} market with {result['volatility']} volatility",
        **result,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def analyze_indicators(
        symbol: str,
        indicators: list[str] | None = None,
        exchange: str | None = None,
        interval: str = DEFAULT_INTERVAL,
        limit: int = ANALYSIS_LIMIT,
        period: int = 14,
        fast_period: int | None = None,
        slow_period: int | None = None,
        signal_period: int | None = None,
        std_dev: float = 2.0,
        tail: int = 1,
    ) -> str:
        """Compute technical indicators from fresh candles and return the latest values.

        An indicator can be named with any common alias (e.g. "bb",
        "bollingerbands", "willr", "stochrsi", "ao"). Read crypto://indicators
        for the full catalogue, parameter names and aliases.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            indicators: Indicator names. Defaults to macd, rsi, bollinger_bands, ema, atr.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            interval: Candle interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M.
            limit: Candles to fetch for the calculation, capped at 1000.
            period: Default lookback period for period-based indicators.
            fast_period: Fast period for macd / awesome_oscillator.
            slow_period: Slow period for macd / awesome_oscillator.
            signal_period: Signal period for macd / stochastic / kst.
            std_dev: Standard-deviation multiplier for bollinger_bands / keltner_channels.
            tail: Most-recent values to return per indicator (1 = latest only, capped at 50).
        """
        wanted = list(indicators or DEFAULT_INDICATORS)
        params, tail_limit = _indicator_params(
            period,
            fast_period,
            slow_period,
            signal_period,
            std_dev,
            tail,
        )
        series = await fetch_candles(symbol, interval, limit, exchange)
        try:
            results = compute(series.candles, wanted, params)
        except ValueError as error:
            raise _as_indicator_error(error) from error
        payload = {
            "symbol": series.symbol,
            "exchange": series.exchange,
            "interval": series.interval,
            "candles_used": len(series.candles),
            "indicators": results,
        }
        return json_text(note_limits(payload, series.limit, tail_limit))

    @mcp.tool
    async def get_multi_timeframe_analysis(
        symbol: str,
        timeframes: list[str] | None = None,
        indicators: list[str] | None = None,
        exchange: str | None = None,
        limit: int = ANALYSIS_LIMIT,
        period: int = 14,
    ) -> str:
        """Run the same indicators across several timeframes and report agreement.

        Use this to check whether a move is confirmed on higher timeframes
        instead of reading one chart in isolation.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            timeframes: Intervals to compare, at most 4. Defaults to 15m, 1h, 4h.
            indicators: Indicator names. Defaults to macd, rsi, bollinger_bands, ema, atr.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            limit: Candles per timeframe, capped at 1000.
            period: Lookback period for period-based indicators.
        """
        return json_text(
            await multi_timeframe_payload(symbol, timeframes, indicators, limit, period, exchange)
        )

    @mcp.tool
    async def detect_patterns(
        symbol: str,
        interval: str = DEFAULT_INTERVAL,
        patterns: list[str] | None = None,
        limit: int = PATTERN_LIMIT,
        exchange: str | None = None,
    ) -> str:
        """Detect candlestick patterns and report their latest occurrence.

        `detected` is true when the pattern fired on the most recent candle;
        `bars_ago` locates the most recent occurrence otherwise. Read
        crypto://patterns for the supported names and their direction.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            interval: Candle interval, e.g. 15m, 1h, 4h, 1d.
            patterns: Pattern names to test. Defaults to every supported pattern.
            limit: Candles to scan, capped at 1000.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await patterns_payload(symbol, interval, limit, patterns, exchange))

    @mcp.tool
    async def get_market_regime(
        symbol: str,
        interval: str = DEFAULT_INTERVAL,
        limit: int = ANALYSIS_LIMIT,
        period: int = 14,
        exchange: str | None = None,
    ) -> str:
        """Classify the market as trending or ranging, and volatility as expanding or not.

        The classification is a documented rule set over ADX/DMI, ATR%,
        Bollinger width percentile and EMA spread, and the response includes
        the evidence and the rules that produced it.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            interval: Candle interval, e.g. 1h, 4h, 1d.
            limit: Candles to classify, capped at 1000 (at least 100 recommended).
            period: Lookback period for ADX, ATR and Bollinger calculations.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        return json_text(await regime_payload(symbol, interval, limit, period, exchange))
