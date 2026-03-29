# Proposal: fix-indicator-description

## Change Name
fix-indicator-description

## Problem Statement
The `calculateIndicators` MCP tool has two related bugs:
1. **String-matching bug**: The default indicators list contains `'bollinger bands'` (with a space). The dispatcher in `indicatorService.ts` calls `type.toLowerCase()` and switches on the result — but only has `case 'bollingerbands':` (no space). So any call that passes `'bollinger bands'` (the documented default!) silently returns `null` instead of actual Bollinger Band values.
2. **Stale/incomplete describe string**: The `indicators` parameter describe text says `supported: ["macd", "rsi", "bollinger bands", "kdj", "ema", "atr"]` — missing `obv`, `mfi`, `adx`, `stochastic`, `cmf`, `volumespike`, `sma`, `dmi`, `ema7`, `ema30`, `ema120`. Agents and users relying on tool descriptions get wrong information.

## Target Users
- AI agents calling `calculateIndicators` with the default or documented indicators list
- Developers reading tool descriptions

## Proposed Solution
Fix the dispatcher in `indicatorService.ts` to normalize whitespace before the switch (strip spaces) so `'bollinger bands'` matches `'bollingerbands'`. Update the `indicators` parameter describe string in `src/api/tools/index.ts` to list all supported indicator keys. Also update the default array to use canonical keys consistent with the dispatcher.

## Scope

### In-scope
- `src/indicators/indicatorService.ts`: normalize input in `calculateIndicator()` with `.replace(/\s+/g, '')`
- `src/api/tools/index.ts`: update `indicators` describe string to list all supported types; keep default array as-is (or fix 'bollinger bands' → 'bollingerbands' for consistency)
- `docs/tool-prompts.md`: update calculateIndicators prompt to list all supported indicators

### Out-of-scope
- Adding new indicators
- Changing indicator calculation logic
- Altering other tools

## Risks & Mitigations
1. **Risk**: Normalizing whitespace could mask future case additions that rely on multi-word names. **Mitigation**: The normalization is scoped to whitespace only; the rest of the switch logic is unchanged.
2. **Risk**: Changing the default array could break existing integrations using `'bollinger bands'`. **Mitigation**: Fix both the dispatcher (so `'bollinger bands'` still works) AND update the default to `'bollingerbands'` for canonicality.

## Dependencies
- No external dependencies
- Touches: `src/indicators/indicatorService.ts`, `src/api/tools/index.ts`, `docs/tool-prompts.md`

## Success Metrics
- `calculateIndicators` with `indicators: ['bollinger bands']` returns actual BB values, not null
- TypeScript compiles with 0 errors
- All existing tests pass

## Rough Effort
- 0.1 person-weeks (small). Surgical fix to one function and one string.
