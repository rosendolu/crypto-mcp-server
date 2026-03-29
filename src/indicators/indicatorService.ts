import { IndicatorInput, IndicatorResult } from '@/types/indicators.types';
import {
    ADX, ATR, BollingerBands, EMA, MACD, MFI, OBV, RSI, SMA, Stochastic,
    WilliamsR, PSAR, CCI, VWAP, ROC, TRIX, ADL, ForceIndex, AwesomeOscillator,
    StochasticRSI, IchimokuCloud, KeltnerChannels, ChandelierExit, KST,
} from 'technicalindicators';

// PSAR default parameters
const PSAR_STEP = 0.02;
const PSAR_MAX = 0.2;
// MACD default fast period (also used for AwesomeOscillator fast period)
const MACD_FAST_DEFAULT = 5;
// AwesomeOscillator default slow period
const AO_SLOW_DEFAULT = 34;
// KeltnerChannels default multiplier
const KC_MULTIPLIER_DEFAULT = 2;
// ChandelierExit default multiplier
const CHANDELIER_MULTIPLIER_DEFAULT = 3;
// IchimokuCloud standard periods
const ICHIMOKU_CONVERSION_PERIOD = 9;
const ICHIMOKU_BASE_PERIOD = 26;
const ICHIMOKU_SPAN_PERIOD = 52;
const ICHIMOKU_DISPLACEMENT = 26;
// KST standard ROC periods
const KST_ROC1 = 10;
const KST_ROC2 = 13;
const KST_ROC3 = 14;
const KST_ROC4 = 15;
// KST standard SMA periods
const KST_SMA1 = 10;
const KST_SMA2 = 13;
const KST_SMA3 = 14;
const KST_SMA4 = 9;
// KST default signal period
const KST_SIGNAL_DEFAULT = 9;
// StochasticRSI default smoothing period
const STOCHRSI_SMOOTH_DEFAULT = 3;

/**
 * Calculate Simple Moving Average (SMA)
 */
export function calculateMA(input: IndicatorInput): number[] {
    return SMA.calculate({ period: input.period!, values: input.values });
}

/**
 * Calculate Exponential Moving Average (EMA)
 */
export function calculateEMA(input: IndicatorInput): number[] {
    return EMA.calculate({ period: input.period!, values: input.values });
}

/**
 * Calculate MACD
 */
export function calculateMACD(input: IndicatorInput): IndicatorResult[] {
    return MACD.calculate({
        values: input.values,
        fastPeriod: input.fastPeriod || 12,
        slowPeriod: input.slowPeriod || 26,
        signalPeriod: input.signalPeriod || 9,
        SimpleMAOscillator: false,
        SimpleMASignal: false,
    });
}

/**
 * Calculate RSI
 */
export function calculateRSI(input: IndicatorInput): number[] {
    return RSI.calculate({ period: input.period!, values: input.values });
}

/**
 * Calculate Bollinger Bands
 */
export function calculateBollingerBands(input: IndicatorInput): IndicatorResult[] {
    return BollingerBands.calculate({
        period: input.period!,
        values: input.values,
        stdDev: input.stdDev || 2,
    });
}

/**
 * Calculate ADX (DMI)
 */
export function calculateADX(input: IndicatorInput): IndicatorResult[] {
    return ADX.calculate({
        period: input.period!,
        close: input.close!,
        high: input.high!,
        low: input.low!,
    });
}

/**
 * Calculate Stochastic Oscillator
 */
export function calculateStochastic(input: IndicatorInput): IndicatorResult[] {
    return Stochastic.calculate({
        period: input.period!,
        high: input.high!,
        low: input.low!,
        close: input.close!,
        signalPeriod: input.signalPeriod || 3,
    });
}

/**
 * Calculate On-Balance Volume (OBV)
 */
export function calculateOBV(input: IndicatorInput): number[] {
    return OBV.calculate({ close: input.close!, volume: input.volume! });
}

/**
 * Calculate Average True Range (ATR)
 */
export function calculateATR(input: IndicatorInput): number[] {
    return ATR.calculate({ period: input.period!, high: input.high!, low: input.low!, close: input.close! });
}

/**
 * Calculate Money Flow Index (MFI)
 */
export function calculateMFI(input: IndicatorInput): number[] {
    return MFI.calculate({
        period: input.period!,
        high: input.high!,
        low: input.low!,
        close: input.close!,
        volume: input.volume!,
    });
}

/**
 * Calculate KDJ (Stochastic Oscillator with J value)
 */
export function calculateKDJ(input: IndicatorInput): IndicatorResult[] {
    // KDJ is a variant of Stochastic Oscillator
    // K = %K, D = %D, J = 3*K - 2*D
    const stochastic = Stochastic.calculate({
        period: input.period!,
        high: input.high!,
        low: input.low!,
        close: input.close!,
        signalPeriod: input.signalPeriod || 3,
    });
    return stochastic.map(({ k, d }) => ({
        k,
        d,
        j: 3 * k - 2 * d,
    }));
}

/**
 * Calculate Chaikin Money Flow (CMF)
 * Placeholder: Not available in technicalindicators, implement basic version
 */
export function calculateCMF(input: IndicatorInput): number[] {
    // CMF = SUM(((Close - Low) - (High - Close)) / (High - Low) * Volume, N) / SUM(Volume, N)
    const { high, low, close, volume, period } = input;
    if (!high || !low || !close || !volume || !period) return [];
    const result: number[] = [];
    for (let i = 0; i < close.length; i++) {
        if (i < period - 1) {
            result.push(NaN);
            continue;
        }
        let sumNumerator = 0;
        let sumVolume = 0;
        for (let j = i - period + 1; j <= i; j++) {
            const hl = high[j] - low[j];
            const mfm = hl === 0 ? 0 : (close[j] - low[j] - (high[j] - close[j])) / hl;
            sumNumerator += mfm * volume[j];
            sumVolume += volume[j];
        }
        result.push(sumVolume === 0 ? 0 : sumNumerator / sumVolume);
    }
    return result;
}

/**
 * Calculate Williams %R
 * Requires: high[], low[], close[], period
 */
export function calculateWilliamsR(input: IndicatorInput): number[] {
    return WilliamsR.calculate({ high: input.high!, low: input.low!, close: input.close!, period: input.period! });
}

/**
 * Calculate Parabolic SAR
 * Requires: high[], low[]
 * Uses standard step=0.02, max=0.2
 */
export function calculatePSAR(input: IndicatorInput): number[] {
    return PSAR.calculate({ high: input.high!, low: input.low!, step: PSAR_STEP, max: PSAR_MAX });
}

/**
 * Calculate Commodity Channel Index (CCI)
 * Requires: high[], low[], close[], period
 */
export function calculateCCI(input: IndicatorInput): number[] {
    return CCI.calculate({ high: input.high!, low: input.low!, close: input.close!, period: input.period! });
}

/**
 * Calculate Volume Weighted Average Price (VWAP)
 * Requires: high[], low[], close[], volume[]
 */
export function calculateVWAP(input: IndicatorInput): number[] {
    return VWAP.calculate({ high: input.high!, low: input.low!, close: input.close!, volume: input.volume! });
}

/**
 * Calculate Rate of Change (ROC)
 * Requires: values[], period
 */
export function calculateROC(input: IndicatorInput): number[] {
    return ROC.calculate({ values: input.values, period: input.period! });
}

/**
 * Calculate TRIX (Triple Exponential Average)
 * Requires: values[], period
 */
export function calculateTRIX(input: IndicatorInput): number[] {
    return TRIX.calculate({ values: input.values, period: input.period! });
}

/**
 * Calculate Accumulation/Distribution Line (ADL)
 * Requires: high[], low[], close[], volume[]
 */
export function calculateADL(input: IndicatorInput): number[] {
    return ADL.calculate({ high: input.high!, low: input.low!, close: input.close!, volume: input.volume! });
}

/**
 * Calculate Force Index
 * Requires: close[], volume[], period
 */
export function calculateForceIndex(input: IndicatorInput): number[] {
    return ForceIndex.calculate({ close: input.close!, volume: input.volume!, period: input.period! });
}

/**
 * Calculate Awesome Oscillator
 * Requires: high[], low[]
 * Uses fastPeriod (default 5) and slowPeriod (default 34)
 */
export function calculateAwesomeOscillator(input: IndicatorInput): number[] {
    return AwesomeOscillator.calculate({
        high: input.high!,
        low: input.low!,
        fastPeriod: input.fastPeriod || MACD_FAST_DEFAULT,
        slowPeriod: input.slowPeriod || AO_SLOW_DEFAULT,
    });
}

/**
 * Calculate Stochastic RSI
 * Requires: values[], period (used as rsiPeriod and stochasticPeriod), signalPeriod (default 3)
 * Returns: Array of {stochRSI, k, d}
 */
export function calculateStochasticRSI(input: IndicatorInput): IndicatorResult[] {
    return StochasticRSI.calculate({
        values: input.values,
        rsiPeriod: input.period!,
        stochasticPeriod: input.period!,
        kPeriod: input.signalPeriod || STOCHRSI_SMOOTH_DEFAULT,
        dPeriod: input.signalPeriod || STOCHRSI_SMOOTH_DEFAULT,
    });
}

/**
 * Calculate Ichimoku Cloud
 * Requires: high[], low[]
 * Uses standard Ichimoku periods: conversion=9, base=26, span=52, displacement=26
 * Returns: Array of {conversion, base, spanA, spanB}
 */
export function calculateIchimokuCloud(input: IndicatorInput): IndicatorResult[] {
    return IchimokuCloud.calculate({
        high: input.high!,
        low: input.low!,
        conversionPeriod: ICHIMOKU_CONVERSION_PERIOD,
        basePeriod: ICHIMOKU_BASE_PERIOD,
        spanPeriod: ICHIMOKU_SPAN_PERIOD,
        displacement: ICHIMOKU_DISPLACEMENT,
    });
}

/**
 * Calculate Keltner Channels
 * Requires: high[], low[], close[], period
 * Uses period for both maPeriod and atrPeriod; multiplier from stdDev (default 2)
 * Returns: Array of {middle, upper, lower}
 */
export function calculateKeltnerChannels(input: IndicatorInput): IndicatorResult[] {
    return KeltnerChannels.calculate({
        high: input.high!,
        low: input.low!,
        close: input.close!,
        maPeriod: input.period!,
        atrPeriod: input.period!,
        multiplier: input.stdDev || KC_MULTIPLIER_DEFAULT,
        useSMA: false,
    });
}

/**
 * Calculate Chandelier Exit
 * Requires: high[], low[], close[], period
 * Uses multiplier from stdDev (default 3)
 * Returns: Array of {exitLong, exitShort}
 */
export function calculateChandelierExit(input: IndicatorInput): IndicatorResult[] {
    // The technicalindicators d.ts declares number[] but the actual return is {exitLong, exitShort}[]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (ChandelierExit.calculate as any)({
        high: input.high!,
        low: input.low!,
        close: input.close!,
        period: input.period!,
        multiplier: input.stdDev || CHANDELIER_MULTIPLIER_DEFAULT,
    }) as IndicatorResult[];
}

/**
 * Calculate KST (Know Sure Thing oscillator)
 * Requires: values[]
 * Uses standard KST parameters; signalPeriod from input (default 9)
 * Returns: Array of {kst, signal?}
 */
export function calculateKST(input: IndicatorInput): IndicatorResult[] {
    return KST.calculate({
        values: input.values,
        ROCPer1: KST_ROC1,
        ROCPer2: KST_ROC2,
        ROCPer3: KST_ROC3,
        ROCPer4: KST_ROC4,
        SMAROCPer1: KST_SMA1,
        SMAROCPer2: KST_SMA2,
        SMAROCPer3: KST_SMA3,
        SMAROCPer4: KST_SMA4,
        signalPeriod: input.signalPeriod || KST_SIGNAL_DEFAULT,
    });
}

/**
 * Detect Volume Spike
 * Returns true if the latest volume > 2x average of previous N days
 */
export function detectVolumeSpike(volume: number[], period: number = 3): boolean {
    if (volume.length <= period) return false;
    const recent = volume.slice(-period - 1, -1);
    const avg = recent.reduce((a, b) => a + b, 0) / period;
    const latest = volume[volume.length - 1];
    return latest > 2 * avg;
}

/**
 * Funding Rate
 * Funding rate is not calculable from kline data.
 * Use the `fundingRate` or `fundingRates` MCP tools to fetch live funding rates from the exchange API.
 */
// Funding rate retrieval is handled by the `fundingRate` MCP tool via the CCXT provider.

/**
 * On-chain Large Transfer (Placeholder)
 * Needs on-chain data, not calculable from kline
 */
export function getOnChainLargeTransferPlaceholder(): boolean {
    // Placeholder: Implement via on-chain data provider
    return false;
}

// Extend dispatcher
export function calculateIndicator(
    type: string,
    input: IndicatorInput
): IndicatorResult | IndicatorResult[] | number[] | boolean | number | null {
    const normalized = type.toLowerCase().replace(/\s+/g, '');
    switch (normalized) {
        case 'ma':
        case 'sma':
            return calculateMA(input);
        case 'ema':
            return calculateEMA(input);
        case 'ema7':
            return calculateEMA({ ...input, period: 7 });
        case 'ema30':
            return calculateEMA({ ...input, period: 30 });
        case 'ema120':
            return calculateEMA({ ...input, period: 120 });
        case 'macd':
            return calculateMACD(input);
        case 'rsi':
            return calculateRSI(input);
        case 'bollingerbands':
        case 'bb':
        case 'bollinger bands':
            return calculateBollingerBands(input);
        case 'adx':
        case 'dmi':
            return calculateADX(input);
        case 'stochastic':
            return calculateStochastic(input);
        case 'kdj':
            return calculateKDJ(input);
        case 'cmf':
            return calculateCMF(input);
        case 'obv':
            return calculateOBV(input);
        case 'atr':
            return calculateATR(input);
        case 'mfi':
            return calculateMFI(input);
        case 'williamsr':
        case 'willr':
            return calculateWilliamsR(input);
        case 'psar':
        case 'parabolicsar':
            return calculatePSAR(input);
        case 'cci':
            return calculateCCI(input);
        case 'vwap':
            return calculateVWAP(input);
        case 'roc':
            return calculateROC(input);
        case 'trix':
            return calculateTRIX(input);
        case 'adl':
            return calculateADL(input);
        case 'forceindex':
        case 'fi':
            return calculateForceIndex(input);
        case 'awesomeoscillator':
        case 'ao':
            return calculateAwesomeOscillator(input);
        case 'stochasticrsi':
        case 'stochrsi':
            return calculateStochasticRSI(input);
        case 'ichimokucloud':
        case 'ichimoku':
            return calculateIchimokuCloud(input);
        case 'keltnerchannel':
        case 'keltnerchannels':
        case 'kc':
            return calculateKeltnerChannels(input);
        case 'chandelierexit':
        case 'chandelier':
            return calculateChandelierExit(input);
        case 'kst':
            return calculateKST(input);
        case 'volumespike':
            return detectVolumeSpike(input.volume!, input.period || 3);
        case 'onchainlargetransfer':
            return getOnChainLargeTransferPlaceholder();
        default:
            throw new Error(`Unknown indicator type: ${type}`);
    }
}
