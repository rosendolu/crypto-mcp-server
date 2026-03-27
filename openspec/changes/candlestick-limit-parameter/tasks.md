## 1. Provider Layer

- [ ] 1.1 Add optional `limit?: number` parameter to `candlesticks()` function signature in `src/data-providers/ccxt/index.ts`
- [ ] 1.2 Pass `limit` as the fourth positional argument to `exchange.fetchOHLCV(adaptedSymbol, interval, undefined, limit, options)` in `src/data-providers/ccxt/index.ts`
- [ ] 1.3 Update the `logger.debug` call in `candlesticks()` to include `limit` in the logged params object

## 2. MCP Tool Layer

- [ ] 2.1 Add `limit: z.number().int().positive().optional().describe('Number of candles to return (default: exchange default)')` to the `candlesticks` tool schema in `src/api/tools/index.ts`
- [ ] 2.2 Add `limit` to the destructured parameters in the `candlesticks` tool handler and forward it to `ccxtProvider.candlesticks(symbol, interval, options, exchange, limit)`
- [ ] 2.3 Add `limit: z.number().int().positive().optional().describe('Number of candles to fetch for indicator calculation (default: exchange default)')` to the `calculateIndicators` tool schema in `src/api/tools/index.ts`
- [ ] 2.4 Add `limit` to the destructured parameters in the `calculateIndicators` tool handler and forward it to `ccxtProvider.candlesticks(symbol, interval, options, exchange, limit)`

## 3. Documentation

- [ ] 3.1 Update `docs/tool-prompts.md` section for `candlesticks` (tool #19) to document the `limit` parameter with example prompts
- [ ] 3.2 Update `docs/tool-prompts.md` section for `calculateIndicators` (tool #20) to document the `limit` parameter with example prompts

## 4. Validation

- [ ] 4.1 Run `node_modules/.bin/tsc --noEmit` and confirm zero TypeScript errors
- [ ] 4.2 Run `pnpm test` and confirm all tests pass
