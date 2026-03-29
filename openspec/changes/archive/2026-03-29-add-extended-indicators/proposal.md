# add-extended-indicators — Proposal

## What & Why

### Problem Statement

The `calculateIndicators` MCP tool supports 18 indicator types via `indicatorService.ts`, but the
`technicalindicators` library (already installed at v3.1.0) exposes 14 additional analysis primitives
that are commonly requested by AI trading agents — **WilliamsR, PSAR, CCI, VWAP, ROC, TRIX, ADL,
ForceIndex, AwesomeOscillator, StochasticRSI, IchimokuCloud, KeltnerChannels, ChandelierExit, KST**.
All 14 are fully implemented in the library with a `calculate()` static method. None requires
additional npm packages.

When an AI agent requests any of these by name, the dispatcher currently throws
`"Unknown indicator type: <name>"`, making them completely unavailable despite being
pre-installed.

### Target Users

- AI agents calling `calculateIndicators` with trending indicators (WilliamsR, PSAR, KST)
- AI agents doing volatility/channel analysis (KeltnerChannels, ChandelierExit, VWAP)
- AI agents doing volume/momentum analysis (ADL, ForceIndex, AwesomeOscillator, CCI, StochasticRSI)
- AI agents doing multi-component Japanese analysis (IchimokuCloud)
- AI agents doing rate-of-change / oscillator analysis (ROC, TRIX)

### Proposed Solution

Add 14 new indicator implementations to `src/indicators/indicatorService.ts`, register each in the
`calculateIndicator` dispatcher switch with canonical lowercase aliases, and extend the Zod describe
string in `src/api/tools/index.ts` to document the new indicator keys. Also add them to the
`IndicatorInput` types if any new fields are required (none are: all accept existing fields
`high`, `low`, `close`, `values`, `volume`, `period`, `fastPeriod`, `slowPeriod`, `signalPeriod`).

### Scope

**In-scope:**
- 14 new calculate functions in `indicatorService.ts`
- Dispatcher `switch` cases for all 14
- Updated `indicators` parameter describe string in `src/api/tools/index.ts`
- Updated `docs/tool-prompts.md` to document the new indicators
- Vitest test cases for all 14 new indicators in `indicatorService.test.ts`

**Out-of-scope:**
- Any new MCP tools (not needed; uses existing `calculateIndicators`)
- Changes to `IndicatorInput` types (all inputs fit existing fields)
- Changes to `ccxt/index.ts` (no exchange data changes)
- Pattern indicators (candle patterns: HeikinAshi, BullishHammer, etc.) — lower-priority

### Risks & Mitigations

1. **KeltnerChannels uses `maPeriod`/`atrPeriod` instead of unified `period`** — Mitigation: default
   both to `input.period || 20` with an internal alias so callers only need `period`.
2. **IchimokuCloud/KST need more candle history than shorter-period indicators** — Mitigation:
   document minimum candle count in the describe string; agents will surface this to users.

### Dependencies

- `technicalindicators` v3.1.0 — already in `package.json`; no new packages required
- `src/types/indicators.types.ts` — no new fields needed

### Success Metrics

- All 14 new indicator types return non-null results from `calculateIndicator` when given valid input
- `pnpm test` passes with new test cases covering all 14
- `tsc --noEmit` passes with 0 errors
- The describe string in `src/api/tools/index.ts` lists all new indicator keys

### Rough Effort

Small: 0.5–1 person-day (14 functions, dispatcher additions, tests, describe update).
