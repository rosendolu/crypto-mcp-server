import { IndicatorInput } from '@/types/indicators.types';
import { describe, expect, it } from 'vitest';
import {
    calculateADX,
    calculateATR,
    calculateBollingerBands,
    calculateCMF,
    calculateEMA,
    calculateKDJ,
    calculateMA,
    calculateMACD,
    calculateMFI,
    calculateOBV,
    calculateRSI,
    calculateStochastic,
    detectVolumeSpike,
    getFundingRatePlaceholder,
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

    it('returns Funding Rate placeholder', () => {
        const result = getFundingRatePlaceholder();
        expect(result === null || typeof result === 'number').toBe(true);
    });

    it('returns On-chain Large Transfer placeholder', () => {
        const result = getOnChainLargeTransferPlaceholder();
        expect(typeof result).toBe('boolean');
    });
});
