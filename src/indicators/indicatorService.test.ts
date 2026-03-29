import { IndicatorInput } from '@/types/indicators.types';
import { describe, expect, it } from 'vitest';
import {
    calculateADL,
    calculateADX,
    calculateATR,
    calculateAwesomeOscillator,
    calculateBollingerBands,
    calculateCCI,
    calculateChandelierExit,
    calculateCMF,
    calculateEMA,
    calculateForceIndex,
    calculateIchimokuCloud,
    calculateIndicator,
    calculateKDJ,
    calculateKeltnerChannels,
    calculateKST,
    calculateMA,
    calculateMACD,
    calculateMFI,
    calculateOBV,
    calculatePSAR,
    calculateROC,
    calculateRSI,
    calculateStochastic,
    calculateStochasticRSI,
    calculateTRIX,
    calculateVWAP,
    calculateWilliamsR,
    detectVolumeSpike,
    getOnChainLargeTransferPlaceholder,
} from './indicatorService';

describe('Indicator Calculation', () => {
    const close = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const input: IndicatorInput = { values: close, period: 3 };

    it('calculates MA (SMA)', () => {
        const result = calculateMA(input);
        expect(result).toEqual([2, 3, 4, 5, 6, 7, 8, 9]);
    });

    it('calculates EMA', () => {
        const result = calculateEMA(input);
        expect(result.length).toBe(close.length - 2); // period = 3
        expect(result[result.length - 1]).toBeTypeOf('number');
    });

    it('calculates MACD', () => {
        const close = Array.from({ length: 40 }, (_, i) => i + 1); // 1..40
        const macd = calculateMACD({ values: close });
        expect(Array.isArray(macd)).toBe(true);
        expect(macd.length).toBeGreaterThan(0);
        expect(macd[0]).toHaveProperty('MACD');
        expect(macd[0]).toHaveProperty('signal');
        expect(macd[0]).toHaveProperty('histogram');
    });

    it('calculates RSI', () => {
        const rsi = calculateRSI(input);
        expect(Array.isArray(rsi)).toBe(true);
        expect(rsi.length).toBeGreaterThan(0);
        expect(typeof rsi[0]).toBe('number');
    });
});

describe('All Indicator Calculations', () => {
    // Minimal mock data for OHLCV
    const close = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const high = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    const low = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const open = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const volume = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
    const input: IndicatorInput = { values: close, period: 3, high, low, close, open, volume };

    it('calculates Bollinger Bands', () => {
        const result = calculateBollingerBands(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('lower');
        expect(result[0]).toHaveProperty('middle');
        expect(result[0]).toHaveProperty('upper');
    });

    it('calculates ADX', () => {
        const result = calculateADX(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('adx');
    });

    it('calculates Stochastic', () => {
        const result = calculateStochastic(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('k');
        expect(result[0]).toHaveProperty('d');
    });

    it('calculates OBV', () => {
        const result = calculateOBV(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculates ATR', () => {
        const result = calculateATR(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculates MFI', () => {
        const result = calculateMFI(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculates KDJ', () => {
        const result = calculateKDJ(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('k');
        expect(result[0]).toHaveProperty('d');
        expect(result[0]).toHaveProperty('j');
    });

    it('calculates CMF', () => {
        const result = calculateCMF(input);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('detects Volume Spike', () => {
        const result = detectVolumeSpike(volume, 3);
        expect(typeof result).toBe('boolean');
    });

    it('returns On-chain Large Transfer placeholder', () => {
        const result = getOnChainLargeTransferPlaceholder();
        expect(typeof result).toBe('boolean');
    });

    it('calculates Bollinger Bands via "bollinger bands" alias (space-separated)', () => {
        const result = calculateIndicator('bollinger bands', input);
        expect(Array.isArray(result)).toBe(true);
        expect((result as any[]).length).toBeGreaterThan(0);
        expect((result as any[])[0]).toHaveProperty('lower');
        expect((result as any[])[0]).toHaveProperty('middle');
        expect((result as any[])[0]).toHaveProperty('upper');
    });
});

describe('calculateIndicator dispatcher', () => {
    const close = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const high = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    const low = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const open = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const volume = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
    const input: IndicatorInput = { values: close, period: 3, high, low, close, open, volume };

    it('dispatches "bollinger bands" (with space) correctly — regression for whitespace bug', () => {
        const result = calculateIndicator('bollinger bands', input);
        expect(Array.isArray(result)).toBe(true);
        expect((result as any[]).length).toBeGreaterThan(0);
        expect((result as any[])[0]).toHaveProperty('lower');
        expect((result as any[])[0]).toHaveProperty('upper');
    });

    it('dispatches "bollingerbands" (no space) correctly', () => {
        const result = calculateIndicator('bollingerbands', input);
        expect(Array.isArray(result)).toBe(true);
        expect((result as any[]).length).toBeGreaterThan(0);
    });

    it('dispatches "bb" alias correctly', () => {
        const result = calculateIndicator('bb', input);
        expect(Array.isArray(result)).toBe(true);
        expect((result as any[]).length).toBeGreaterThan(0);
    });

    it('throws for unknown indicator type', () => {
        expect(() => calculateIndicator('unknownindicator', input)).toThrow('Unknown indicator type');
    });
});

describe('Extended indicators (add-extended-indicators)', () => {
    // Realistic-enough test data: 50 candles with slight trend and noise
    const n = 50;
    const close = Array.from({ length: n }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 2);
    const high = close.map(v => v + 1.5);
    const low = close.map(v => v - 1.5);
    const volume = close.map(() => 1_000_000);
    const baseInput: IndicatorInput = { values: close, period: 14, high, low, close, volume };

    it('calculateWilliamsR returns number[]', () => {
        const result = calculateWilliamsR(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculatePSAR returns number[]', () => {
        const result = calculatePSAR(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateCCI returns number[]', () => {
        const result = calculateCCI(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateVWAP returns number[]', () => {
        const result = calculateVWAP(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateROC returns number[]', () => {
        const result = calculateROC(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateTRIX returns number[]', () => {
        const result = calculateTRIX(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateADL returns number[]', () => {
        // Use asymmetric close so ADL is non-zero
        const asymClose = close.map((v, i) => (i % 3 === 0 ? v + 1 : v - 0.5));
        const result = calculateADL({ ...baseInput, close: asymClose });
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateForceIndex returns number[]', () => {
        const result = calculateForceIndex(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateAwesomeOscillator returns number[]', () => {
        const result = calculateAwesomeOscillator(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(typeof result[0]).toBe('number');
    });

    it('calculateStochasticRSI returns IndicatorResult[]', () => {
        const result = calculateStochasticRSI(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('stochRSI');
        expect(result[0]).toHaveProperty('k');
        expect(result[0]).toHaveProperty('d');
    });

    it('calculateIchimokuCloud returns IndicatorResult[] with 200 candles', () => {
        const bigClose = Array.from({ length: 200 }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 5);
        const bigHigh = bigClose.map(v => v + 2);
        const bigLow = bigClose.map(v => v - 2);
        const bigInput: IndicatorInput = { values: bigClose, period: 26, high: bigHigh, low: bigLow, close: bigClose };
        const result = calculateIchimokuCloud(bigInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('conversion');
        expect(result[0]).toHaveProperty('base');
        expect(result[0]).toHaveProperty('spanA');
        expect(result[0]).toHaveProperty('spanB');
    });

    it('calculateKeltnerChannels returns IndicatorResult[]', () => {
        const result = calculateKeltnerChannels(baseInput);
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('middle');
        expect(result[0]).toHaveProperty('upper');
        expect(result[0]).toHaveProperty('lower');
    });

    it('calculateChandelierExit returns IndicatorResult[]', () => {
        const result = calculateChandelierExit({ ...baseInput, period: 22 });
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('exitLong');
        expect(result[0]).toHaveProperty('exitShort');
    });

    it('calculateKST returns IndicatorResult[]', () => {
        const kstClose = Array.from({ length: 60 }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 5);
        const result = calculateKST({ values: kstClose, period: 9 });
        expect(Array.isArray(result)).toBe(true);
        expect(result.length).toBeGreaterThan(0);
        expect(result[0]).toHaveProperty('kst');
    });

    // Dispatcher integration tests for new indicators
    it('dispatcher: williamsr alias works', () => {
        const r = calculateIndicator('williamsr', baseInput);
        expect(Array.isArray(r)).toBe(true);
        expect((r as number[]).length).toBeGreaterThan(0);
    });

    it('dispatcher: willr alias works', () => {
        const r = calculateIndicator('willr', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: psar alias works', () => {
        const r = calculateIndicator('psar', baseInput);
        expect(Array.isArray(r)).toBe(true);
        expect((r as number[]).length).toBeGreaterThan(0);
    });

    it('dispatcher: cci works', () => {
        const r = calculateIndicator('cci', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: vwap works', () => {
        const r = calculateIndicator('vwap', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: roc works', () => {
        const r = calculateIndicator('roc', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: trix works', () => {
        const r = calculateIndicator('trix', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: adl works', () => {
        const r = calculateIndicator('adl', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: forceindex works', () => {
        const r = calculateIndicator('forceindex', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: fi alias works', () => {
        const r = calculateIndicator('fi', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: awesomeoscillator works', () => {
        const r = calculateIndicator('awesomeoscillator', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: ao alias works', () => {
        const r = calculateIndicator('ao', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: stochasticrsi works', () => {
        const r = calculateIndicator('stochasticrsi', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: stochrsi alias works', () => {
        const r = calculateIndicator('stochrsi', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: ichimokucloud works (200 candles)', () => {
        const bigClose = Array.from({ length: 200 }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 5);
        const bigHigh = bigClose.map(v => v + 2);
        const bigLow = bigClose.map(v => v - 2);
        const bigInput: IndicatorInput = { values: bigClose, period: 26, high: bigHigh, low: bigLow, close: bigClose };
        const r = calculateIndicator('ichimokucloud', bigInput);
        expect(Array.isArray(r)).toBe(true);
        expect((r as unknown[]).length).toBeGreaterThan(0);
    });

    it('dispatcher: ichimoku alias works', () => {
        const bigClose = Array.from({ length: 200 }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 5);
        const bigHigh = bigClose.map(v => v + 2);
        const bigLow = bigClose.map(v => v - 2);
        const bigInput: IndicatorInput = { values: bigClose, period: 26, high: bigHigh, low: bigLow, close: bigClose };
        const r = calculateIndicator('ichimoku', bigInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: keltnerchannels works', () => {
        const r = calculateIndicator('keltnerchannels', baseInput);
        expect(Array.isArray(r)).toBe(true);
        expect((r as unknown[]).length).toBeGreaterThan(0);
    });

    it('dispatcher: kc alias works', () => {
        const r = calculateIndicator('kc', baseInput);
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: chandelierexit works', () => {
        const r = calculateIndicator('chandelierexit', { ...baseInput, period: 22 });
        expect(Array.isArray(r)).toBe(true);
        expect((r as unknown[]).length).toBeGreaterThan(0);
    });

    it('dispatcher: chandelier alias works', () => {
        const r = calculateIndicator('chandelier', { ...baseInput, period: 22 });
        expect(Array.isArray(r)).toBe(true);
    });

    it('dispatcher: kst works', () => {
        const kstClose = Array.from({ length: 60 }, (_, i) => 44 + i * 0.3 + Math.sin(i) * 5);
        const r = calculateIndicator('kst', { values: kstClose, period: 9 });
        expect(Array.isArray(r)).toBe(true);
        expect((r as unknown[]).length).toBeGreaterThan(0);
    });
});
