# add-extended-indicators — Design

## Overview

Add 14 new technical indicator calculation functions to `src/indicators/indicatorService.ts`,
wire them into the `calculateIndicator` dispatcher, update the tool's Zod describe string, and
add test coverage for all 14 new indicators.

All 14 indicators are already available via the `technicalindicators` library (already a
project dependency). No new npm packages are needed.

## Affected Files

| File | Change Type | Description |
|------|-------------|-------------|
| `src/indicators/indicatorService.ts` | Code | Add 14 calculate functions + dispatcher cases |
| `src/api/tools/index.ts` | Documentation | Extend `indicators` describe string |
| `docs/tool-prompts.md` | Documentation | Update indicator list in tool #20 |
| `src/indicators/indicatorService.test.ts` | Test | Add 14 new test cases |

## Implementation Details

### 1. New Indicator Functions in `src/indicators/indicatorService.ts`

#### Import additions
```typescript
import {
  ADX, ATR, BollingerBands, EMA, MACD, MFI, OBV, RSI, SMA, Stochastic,
  WilliamsR, PSAR, CCI, VWAP, ROC, TRIX, ADL, ForceIndex, AwesomeOscillator,
  StochasticRSI, IchimokuCloud, KeltnerChannels, ChandelierExit, KST
} from 'technicalindicators';
```

#### New calculate functions (all use existing `IndicatorInput` fields)

**WilliamsR** (`number[]`) — requires high, low, close, period
```typescript
export function calculateWilliamsR(input: IndicatorInput): number[] {
    return WilliamsR.calculate({ high: input.high!, low: input.low!, close: input.close!, period: input.period! });
}
```

**PSAR** (`number[]`) — requires high, low; uses step=0.02, max=0.2 constants
```typescript
export function calculatePSAR(input: IndicatorInput): number[] {
    return PSAR.calculate({ high: input.high!, low: input.low!, step: PSAR_STEP, max: PSAR_MAX });
}
```

**CCI** (`number[]`) — requires high, low, close, period
```typescript
export function calculateCCI(input: IndicatorInput): number[] {
    return CCI.calculate({ high: input.high!, low: input.low!, close: input.close!, period: input.period! });
}
```

**VWAP** (`number[]`) — requires high, low, close, volume
```typescript
export function calculateVWAP(input: IndicatorInput): number[] {
    return VWAP.calculate({ high: input.high!, low: input.low!, close: input.close!, volume: input.volume! });
}
```

**ROC** (`number[]`) — requires values, period
```typescript
export function calculateROC(input: IndicatorInput): number[] {
    return ROC.calculate({ values: input.values, period: input.period! });
}
```

**TRIX** (`number[]`) — requires values, period
```typescript
export function calculateTRIX(input: IndicatorInput): number[] {
    return TRIX.calculate({ values: input.values, period: input.period! });
}
```

**ADL** (`number[]`) — requires high, low, close, volume
```typescript
export function calculateADL(input: IndicatorInput): number[] {
    return ADL.calculate({ high: input.high!, low: input.low!, close: input.close!, volume: input.volume! });
}
```

**ForceIndex** (`number[]`) — requires close, volume, period
```typescript
export function calculateForceIndex(input: IndicatorInput): number[] {
    return ForceIndex.calculate({ close: input.close!, volume: input.volume!, period: input.period! });
}
```

**AwesomeOscillator** (`number[]`) — requires high, low, fastPeriod, slowPeriod
```typescript
export function calculateAwesomeOscillator(input: IndicatorInput): number[] {
    return AwesomeOscillator.calculate({ high: input.high!, low: input.low!, fastPeriod: input.fastPeriod || MACD_FAST_DEFAULT, slowPeriod: input.slowPeriod || AO_SLOW_DEFAULT });
}
```

**StochasticRSI** (`IndicatorResult[]`) — requires values, rsiPeriod=period, stochasticPeriod, kPeriod=signalPeriod, dPeriod=signalPeriod
```typescript
export function calculateStochasticRSI(input: IndicatorInput): IndicatorResult[] {
    return StochasticRSI.calculate({ values: input.values, rsiPeriod: input.period!, stochasticPeriod: input.period!, kPeriod: input.signalPeriod || 3, dPeriod: input.signalPeriod || 3 });
}
```

**IchimokuCloud** (`IndicatorResult[]`) — requires high, low; uses constants for periods
```typescript
export function calculateIchimokuCloud(input: IndicatorInput): IndicatorResult[] {
    return IchimokuCloud.calculate({ high: input.high!, low: input.low!, conversionPeriod: ICHIMOKU_CONVERSION_PERIOD, basePeriod: ICHIMOKU_BASE_PERIOD, spanPeriod: ICHIMOKU_SPAN_PERIOD, displacement: ICHIMOKU_DISPLACEMENT });
}
```

**KeltnerChannels** (`IndicatorResult[]`) — requires high, low, close; maps period to maPeriod and atrPeriod
```typescript
export function calculateKeltnerChannels(input: IndicatorInput): IndicatorResult[] {
    return KeltnerChannels.calculate({ high: input.high!, low: input.low!, close: input.close!, maPeriod: input.period!, atrPeriod: input.period!, multiplier: input.stdDev || KC_MULTIPLIER_DEFAULT, useSMA: false });
}
```

**ChandelierExit** (`IndicatorResult[]`) — requires high, low, close, period
```typescript
export function calculateChandelierExit(input: IndicatorInput): IndicatorResult[] {
    return ChandelierExit.calculate({ high: input.high!, low: input.low!, close: input.close!, period: input.period!, multiplier: input.stdDev || CHANDELIER_MULTIPLIER_DEFAULT });
}
```

**KST** (`IndicatorResult[]`) — requires values; uses standard KST constants
```typescript
export function calculateKST(input: IndicatorInput): IndicatorResult[] {
    return KST.calculate({ values: input.values, ROCPer1: KST_ROC1, ROCPer2: KST_ROC2, ROCPer3: KST_ROC3, ROCPer4: KST_ROC4, SMAROCPer1: KST_SMA1, SMAROCPer2: KST_SMA2, SMAROCPer3: KST_SMA3, SMAROCPer4: KST_SMA4, signalPeriod: input.signalPeriod || KST_SIGNAL_DEFAULT });
}
```

### 2. Constants for magic numbers (in `src/indicators/indicatorService.ts`)

```typescript
// PSAR constants
const PSAR_STEP = 0.02;
const PSAR_MAX = 0.2;
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
// KST standard parameters
const KST_ROC1 = 10;
const KST_ROC2 = 13;
const KST_ROC3 = 14;
const KST_ROC4 = 15;
const KST_SMA1 = 10;
const KST_SMA2 = 13;
const KST_SMA3 = 14;
const KST_SMA4 = 9;
const KST_SIGNAL_DEFAULT = 9;
```

Note: MACD_FAST_DEFAULT (12) already exists conceptually from the existing MACD default; use a named constant.

### 3. Dispatcher additions in `calculateIndicator`

Add 14 `case` entries in the `switch (normalized)` block. Aliases are lowercased and whitespace-stripped (the dispatcher already calls `.toLowerCase().replace(/\s+/g, '')`):

| Indicator | Cases |
|-----------|-------|
| WilliamsR | `'williamsr'`, `'willr'` |
| PSAR | `'psar'`, `'parabolicsar'` |
| CCI | `'cci'` |
| VWAP | `'vwap'` |
| ROC | `'roc'` |
| TRIX | `'trix'` |
| ADL | `'adl'` |
| ForceIndex | `'forceindex'`, `'fi'` |
| AwesomeOscillator | `'awesomeoscillator'`, `'ao'` |
| StochasticRSI | `'stochasticrsi'`, `'stochrsi'` |
| IchimokuCloud | `'ichimokucloud'`, `'ichimoku'` |
| KeltnerChannels | `'keltnerchannel'`, `'keltnerchannels'`, `'kc'` |
| ChandelierExit | `'chandelierexit'`, `'chandelier'` |
| KST | `'kst'` |

### 4. Updated describe string in `src/api/tools/index.ts`

Extend the `.describe()` string on the `indicators` field to list all new keys alongside the existing ones.

### 5. Updated `docs/tool-prompts.md`

Update the indicator list in tool #20 (`calculateIndicators`) to include the 14 new indicator keys.

## Type Checklist

- All new functions return `number[]` or `IndicatorResult[]` — consistent with existing signatures
- No new fields added to `IndicatorInput` — uses existing `high`, `low`, `close`, `values`, `volume`, `period`, `fastPeriod`, `slowPeriod`, `signalPeriod`, `stdDev`
- Constants defined in same file (no separate `constant.ts` needed for indicators module — consistent with current pattern)
