# fix-bollinger-bands-alias — Design

## Overview

This is a minimal defect fix. The design is straightforward: one switch-case alias addition
and one documentation string update.

## Affected Files

| File | Change Type | Description |
|------|-------------|-------------|
| `src/indicators/indicatorService.ts` | Code | Add `case 'bollinger bands':` alias in `calculateIndicator` dispatcher |
| `src/api/tools/index.ts` | Documentation | Update indicator description string to list all accepted BB aliases |
| `src/indicators/indicatorService.test.ts` | Test | Add test verifying `calculateIndicator('bollinger bands', input)` works |

## Implementation Details

### 1. `src/indicators/indicatorService.ts` — Dispatcher alias fix

Current:
```typescript
case 'bollingerbands':
case 'bb':
    return calculateBollingerBands(input);
```

After:
```typescript
case 'bollingerbands':
case 'bb':
case 'bollinger bands':
    return calculateBollingerBands(input);
```

### 2. `src/api/tools/index.ts` — Description string update

Update the `describe()` string for `indicators` parameter to list all accepted aliases,
including `'bollinger bands'`, `'bollingerbands'`, and `'bb'`.

### 3. `src/indicators/indicatorService.test.ts` — New test

Add to the existing `'All Indicator Calculations'` describe block:

```typescript
it('calculates Bollinger Bands via "bollinger bands" alias (space-separated)', () => {
    const result = calculateIndicator('bollinger bands', input);
    expect(Array.isArray(result)).toBe(true);
    expect((result as any[]).length).toBeGreaterThan(0);
    expect((result as any[])[0]).toHaveProperty('lower');
    expect((result as any[])[0]).toHaveProperty('middle');
    expect((result as any[])[0]).toHaveProperty('upper');
});
```

## Technical Constraints

- TypeScript only; `@/` path aliases used via tsconfig-paths.
- Use `logger.info/debug/error` — no `console.log`.
- `tsc --noEmit` must pass with 0 errors after change.
- `pnpm test` must pass with all existing + new tests green.
