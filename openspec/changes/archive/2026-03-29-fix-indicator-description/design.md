# Design: fix-indicator-description

## Architecture

No new modules, no new dependencies. Two surgical edits + one doc update.

### 1. `src/indicators/indicatorService.ts` — `calculateIndicator()`

Current code:
```ts
switch (type.toLowerCase()) {
    case 'bollingerbands':
    ...
}
```

Change: normalize whitespace before the switch so `'bollinger bands'` → `'bollingerbands'`:
```ts
const normalized = type.toLowerCase().replace(/\s+/g, '');
switch (normalized) {
    case 'bollingerbands':
    ...
}
```

This is backward-compatible: all existing canonical keys (no spaces) are unaffected. The user-facing key `'bollinger bands'` now correctly routes to `calculateBollingerBands`.

Also add `'bollingerbands'` as alias for `'bollinger bands'` in the `bb` alias group (it is already present as `case 'bollingerbands':` — no change needed there). Only the input normalization is added.

### 2. `src/api/tools/index.ts` — `calculateIndicators` tool schema

- Update the `.describe()` string for the `indicators` parameter to list **all** supported types.
- Update the `.default([...])` array to use canonical (no-space) keys: `'bollingerbands'` instead of `'bollinger bands'`.

### 3. `docs/tool-prompts.md`

Update the `calculateIndicators` entry to list all supported indicator names.

## Data Flow
No change to data flow. The normalization is a pure pre-processing step with no side effects.

## Rollback
Revert the three file edits. No migrations or external state involved.
