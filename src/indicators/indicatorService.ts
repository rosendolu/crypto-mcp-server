import { IndicatorInput, IndicatorResult } from '@/types/indicators.types';
import { ADX, ATR, BollingerBands, EMA, MACD, MFI, OBV, RSI, SMA, Stochastic } from 'technicalindicators';

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
 * Funding Rate (Placeholder)
 * Funding rate is not calculated from kline, needs to be fetched from exchange API
 */
export function getFundingRatePlaceholder(): number | null {
    // Placeholder: Implement via exchange API integration
    return null;
}

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
    switch (type.toLowerCase()) {
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
        case 'volumespike':
            return detectVolumeSpike(input.volume!, input.period || 3);
        case 'fundingrate':
            return getFundingRatePlaceholder();
        case 'onchainlargetransfer':
            return getOnChainLargeTransferPlaceholder();
        default:
            throw new Error(`Unknown indicator type: ${type}`);
    }
}
