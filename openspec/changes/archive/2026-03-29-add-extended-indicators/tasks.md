# add-extended-indicators — Tasks

## 1. Indicator Service

- [x] 1.1 Add imports for WilliamsR, PSAR, CCI, VWAP, ROC, TRIX, ADL, ForceIndex, AwesomeOscillator, StochasticRSI, IchimokuCloud, KeltnerChannels, ChandelierExit, KST from 'technicalindicators' in `src/indicators/indicatorService.ts`
- [x] 1.2 Add named constants for PSAR_STEP, PSAR_MAX, AO_SLOW_DEFAULT, KC_MULTIPLIER_DEFAULT, CHANDELIER_MULTIPLIER_DEFAULT, ICHIMOKU_CONVERSION_PERIOD, ICHIMOKU_BASE_PERIOD, ICHIMOKU_SPAN_PERIOD, ICHIMOKU_DISPLACEMENT, KST_ROC1-4, KST_SMA1-4, KST_SIGNAL_DEFAULT, MACD_FAST_DEFAULT in `src/indicators/indicatorService.ts`
- [x] 1.3 Add `calculateWilliamsR(input: IndicatorInput): number[]` function
- [x] 1.4 Add `calculatePSAR(input: IndicatorInput): number[]` function
- [x] 1.5 Add `calculateCCI(input: IndicatorInput): number[]` function
- [x] 1.6 Add `calculateVWAP(input: IndicatorInput): number[]` function
- [x] 1.7 Add `calculateROC(input: IndicatorInput): number[]` function
- [x] 1.8 Add `calculateTRIX(input: IndicatorInput): number[]` function
- [x] 1.9 Add `calculateADL(input: IndicatorInput): number[]` function
- [x] 1.10 Add `calculateForceIndex(input: IndicatorInput): number[]` function
- [x] 1.11 Add `calculateAwesomeOscillator(input: IndicatorInput): number[]` function
- [x] 1.12 Add `calculateStochasticRSI(input: IndicatorInput): IndicatorResult[]` function
- [x] 1.13 Add `calculateIchimokuCloud(input: IndicatorInput): IndicatorResult[]` function
- [x] 1.14 Add `calculateKeltnerChannels(input: IndicatorInput): IndicatorResult[]` function
- [x] 1.15 Add `calculateChandelierExit(input: IndicatorInput): IndicatorResult[]` function
- [x] 1.16 Add `calculateKST(input: IndicatorInput): IndicatorResult[]` function
- [x] 1.17 Add dispatcher `case` entries for all 14 new indicators (with aliases) in the `calculateIndicator` switch

## 2. MCP Tool Layer

- [x] 2.1 Extend the `indicators` parameter `.describe()` string in `calculateIndicators` tool in `src/api/tools/index.ts` to list all 14 new indicator keys with aliases

## 3. Documentation

- [x] 3.1 Update `docs/tool-prompts.md` tool #20 indicator list to include the 14 new indicator keys

## 4. Tests

- [x] 4.1 Add 14 new test cases in `src/indicators/indicatorService.test.ts` — one per new indicator — confirming the dispatcher returns a non-empty array for each

## 5. Validation

- [x] 5.1 Run `node_modules/.bin/tsc --noEmit` — must pass with 0 errors
- [x] 5.2 Run `pnpm test` — all tests must pass
