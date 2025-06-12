// Indicator types for technical indicators

export interface IndicatorInput {
    values: number[];
    period?: number;
    fastPeriod?: number;
    slowPeriod?: number;
    signalPeriod?: number;
    stdDev?: number;
    high?: number[];
    low?: number[];
    close?: number[];
    volume?: number[];
    open?: number[];
}

export interface IndicatorResult {
    [key: string]: any;
}
