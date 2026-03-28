# fix-bollinger-bands-alias — Tasks

## Implementation Tasks

- [x] 1. Add `case 'bollinger bands':` alias in `calculateIndicator` dispatcher in `src/indicators/indicatorService.ts`
- [x] 2. Update `indicators` parameter `describe()` string in `src/api/tools/index.ts` to document all accepted Bollinger Bands aliases
- [x] 3. Add test case for `'bollinger bands'` alias in `src/indicators/indicatorService.test.ts`
- [x] 4. Run `node_modules/.bin/tsc --noEmit` — must pass with 0 errors
- [x] 5. Run `pnpm test` — all tests must pass
