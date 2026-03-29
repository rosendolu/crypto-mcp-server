# fix-bollinger-bands-alias — Proposal

## What & Why

### Problem Statement

The `calculateIndicators` MCP tool exposes a default indicator list of
`['macd', 'rsi', 'bollinger bands', 'kdj', 'ema', 'atr', 'cmf']`
(see `src/api/tools/index.ts` line 626).

When a user calls `calculateIndicators` without overriding the `indicators` parameter,
the tool iterates this default list and dispatches each indicator name to
`calculateIndicator(type, input)` in `src/indicators/indicatorService.ts`.

The dispatcher's switch-case handles `'bollingerbands'` and `'bb'` but **has no case for
`'bollinger bands'` (with a space)**. The dispatch falls through to the `default` case,
which throws `Error('Unknown indicator type: bollinger bands')`.

This means:
- Every out-of-the-box call to `calculateIndicators` logs a Bollinger Bands error.
- The returned result object sets `bollingerBands: null` silently (the per-indicator
  try/catch in the tool handler swallows the thrown error and assigns `null`).
- Users are silently denied Bollinger Bands data unless they know to pass `'bollingerbands'`
  or `'bb'` explicitly.
- The tool description text also advertises `"bollinger bands"` as a supported name,
  creating a trust/correctness gap.

### Target Users

All users of the `calculateIndicators` MCP tool who rely on the default `indicators` parameter
or follow the documented supported name `"bollinger bands"`.

### Proposed Solution

Add `case 'bollinger bands':` as an additional alias in the `calculateIndicator`
dispatcher switch statement in `src/indicators/indicatorService.ts`, mapping to
`calculateBollingerBands(input)`.

Also update the `calculateIndicators` tool description in `src/api/tools/index.ts` to
clarify all accepted aliases so the documentation matches implementation.

### Scope

**In scope:**
- Add `case 'bollinger bands':` alias in `indicatorService.ts` dispatcher.
- Update the tool description in `index.ts` to list accepted Bollinger Bands aliases.
- Add a test case for the `'bollinger bands'` alias in `indicatorService.test.ts`.

**Out of scope:**
- Fixing any other indicator alias mismatches beyond Bollinger Bands.
- Changing how `calculateIndicators` tool handles errors (null suppression stays).
- Changing any default indicator list values.

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Other indicator names may have similar alias mismatches | Audit the full dispatcher vs. default list as part of this PR (no-code fix required beyond confirming) |
| Renaming or removing existing aliases could break clients | Only **adding** a new alias — existing `'bollingerbands'`/`'bb'` cases are untouched |

### Dependencies

- `src/indicators/indicatorService.ts` — single file change
- `src/api/tools/index.ts` — description string update
- `src/indicators/indicatorService.test.ts` — new test case

### Success Metrics

- `calculateIndicators` with default `indicators` parameter returns a non-null
  `'bollinger bands'` key in the result object.
- `pnpm test` passes with the new alias test.
- `tsc --noEmit` passes with 0 errors.

### Rough Effort

Small: 0.1–0.25 person-days (single-line code change + test + description update).
