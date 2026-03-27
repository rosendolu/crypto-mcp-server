# Funding Rate Tool

## Title
Funding Rate Live Data Tool — Expose Real-Time Funding Rates via MCP

## Status
ready-for-dev

## Summary
The repo currently contains a stub `getFundingRatePlaceholder()` in `src/indicators/indicatorService.ts` that always returns `null`. CCXT exposes `fetchFundingRate(symbol)` and `fetchFundingRates()` methods on futures-capable exchanges. This requirement replaces the placeholder with a real provider function in `src/data-providers/ccxt/index.ts` and adds a new MCP tool `fundingRate` to `src/api/tools/index.ts` so that AI agents can query live funding rate data for perpetual futures pairs. The tool returns the current funding rate, the next funding time, and the predicted funding rate where available. This is an incremental V1 that targets the most common futures exchanges.

## Motivation
Funding rates are a core signal for crypto perpetuals traders. A positive funding rate means longs pay shorts (market leaning bullish), and a negative rate means shorts pay longs. Knowing the funding rate helps agents assess carry costs, arbitrage opportunities, and market sentiment without requiring separate API integrations. The existing `calculateIndicators` tool cannot expose this because it is derived from kline data, not exchange funding-rate endpoints.

## User Story
As a crypto trading assistant user, I want to ask "What is the current BTC/USDT funding rate on Binance?" and receive a structured answer with the current rate, next funding timestamp, and predicted rate, so I can factor carry costs into my trading decisions.

## Scope

### In scope
- Add `fundingRate(symbol, exchangeId?)` function to `src/data-providers/ccxt/index.ts` using `exchange.fetchFundingRate(symbol)`.
- Add `fundingRates(symbols?, exchangeId?)` function to `src/data-providers/ccxt/index.ts` using `exchange.fetchFundingRates(symbols?)`.
- Register two MCP tools in `src/api/tools/index.ts`:
  - `fundingRate` — single symbol funding rate
  - `fundingRates` — multiple symbols or all symbols (if exchange supports it)
- Add `FundingRate` TypeScript interface to `src/types/ccxt.types.ts`.
- Remove/replace the `getFundingRatePlaceholder` placeholder in `src/indicators/indicatorService.ts` with a note pointing to the new tool.
- Update `docs/tool-prompts.md` with prompt templates for the two new tools.
- Exchange-dependent capability handled gracefully: if exchange does not support `fetchFundingRate`, return a helpful error message (not a hard crash).

### Out of scope
- Historical funding rate series (V2+)
- Funding rate charting or trend indicators (V2+)
- Writing funding rate to log files (V2+)
- On-chain funding rate oracles (out of scope entirely)

### Assumptions
- V1 targets only exchanges that support perpetual futures funding rates. If the configured exchange does not support `fetchFundingRate`, the tool returns a clear error message.
- The `FundingRate` type will be placed in the existing `src/types/ccxt.types.ts` type file (no new file needed for a single type group).
- Symbol format follows the repo convention: `ETH/USDT` in tool descriptions and user-facing output; CCXT symbol adaptation uses the existing `adaptSymbolForExchange` utility.

## CCXT Capability Mapping

### Requested feature
Fetch live funding rate (current + next timestamp + predicted) for a perpetual futures pair on a specified exchange.

### Needed ccxt methods/endpoints (by name)
- `exchange.fetchFundingRate(symbol: string)` → single symbol funding rate
- `exchange.fetchFundingRates(symbols?: string[])` → batch funding rates (optional, not available on all exchanges)

### Exchange dependency notes
- `fetchFundingRate` is available on: `binance`, `bybit`, `okx`, `gate`, `bitget`, `mexc`
- `fetchFundingRates` (batch) is less universally supported; treat as optional and fall back to single-symbol fetch if unavailable
- Spot exchanges (no futures) will throw a `BadSymbol` or `NotSupported` error — must be caught and returned as a clear error message
- Gate uses `BTC_USDT` symbol format; `adaptSymbolForExchange` already handles this

### V1 test exchanges
- `binance` (primary — broadest support)
- `gate` (secondary — tests symbol-format adaptation)

## Repo Integration Plan

### Provider changes (`src/data-providers/ccxt/index.ts`)
- Add `fundingRate(symbol: string, exchangeId?: ExchangeId): Promise<FundingRate | null>`
  - Calls `adaptSymbolForExchange`, then `exchange.fetchFundingRate(symbol)`
  - Maps CCXT response fields: `fundingRate`, `nextFundingTime`, `predictedFundingRate`, `symbol`, `timestamp`
- Add `fundingRates(symbols?: string[], exchangeId?: ExchangeId): Promise<FundingRate[] | null>`
  - Calls `exchange.fetchFundingRates(symbols)` if available, else iterates single calls
  - Handles `NotSupported` gracefully

### Type changes (`src/types/ccxt.types.ts`)
Add interface:
```typescript
export interface FundingRate {
    symbol: string;
    fundingRate: number;
    nextFundingTime: number | null;
    predictedFundingRate: number | null;
    timestamp: number | null;
}
```

### Indicator service (`src/indicators/indicatorService.ts`)
- Replace `getFundingRatePlaceholder()` with a note: "Use the `fundingRate` MCP tool to fetch live funding rates from exchange API."
- Remove the `fundingrate` case from the `calculateIndicator` switch (it returned null, which was useless).

## API / Tool Changes

### Tool: `fundingRate`
**Parameters:**
- `symbol` (required): `z.string()` — e.g., `ETH/USDT`
- `exchange` (optional): `z.string()` — exchange id

**Response:** Markdown table with columns: Symbol, Funding Rate, Next Funding Time, Predicted Rate, Timestamp

### Tool: `fundingRates`
**Parameters:**
- `symbols` (optional): `z.array(z.string())` — list of symbols; if omitted, fetches all available
- `exchange` (optional): `z.string()` — exchange id

**Response:** Markdown table with same columns for each symbol

## Error Handling & Logging Expectations
- All functions use `logger.debug`, `logger.info`, `logger.warn`, `logger.error` via `@/utils/logger` — no `console.log`
- If exchange does not support `fetchFundingRate`: catch error, `logger.warn('Exchange %s does not support fetchFundingRate: %s', exchangeId, error)`, return `null` with a user-friendly message
- If symbol is not found / is spot-only: catch error, `logger.warn`, return `null`
- All parameters logged at `logger.debug` on entry; results logged at `logger.debug` on exit

## Acceptance Criteria
1. Calling the `fundingRate` tool with `{ symbol: "BTC/USDT", exchange: "binance" }` returns a markdown table containing a numeric funding rate value.
2. Calling the `fundingRates` tool with `{ exchange: "binance" }` returns a table with at least one row.
3. Calling either tool with a spot-only exchange (e.g., one without perpetuals) returns an `isError: true` response with a descriptive message (not a server crash).
4. No `console.log` calls in any new/modified file.
5. All new types are in `src/types/ccxt.types.ts` — no inline type definitions.
6. `getFundingRatePlaceholder` is removed from `indicatorService.ts` and the `calculateIndicator` switch no longer has a `fundingrate` case.
7. `docs/tool-prompts.md` includes prompt templates for `fundingRate` and `fundingRates`.
8. TypeScript compiles without errors (`tsc --noEmit`).

## Milestones

### V1 (ship)
- Live `fundingRate` + `fundingRates` MCP tools backed by CCXT
- Exchange-aware error handling
- Updated types and prompt documentation

### V2+
- Historical funding rate series (time range query)
- Funding rate charting / trend analysis via indicators
- Funding rate arbitrage scanner (cross-exchange comparison)

## Test Plan

### Unit tests (if applicable)
- Mock `exchange.fetchFundingRate` to return a fixture response; assert `FundingRate` shape is correctly mapped
- Mock `exchange.fetchFundingRate` to throw `NotSupported`; assert function returns `null` and logs a warning

### Integration / Manual test steps
1. Set `BINANCE_API_KEY` and `BINANCE_SECRET` in `.env`
2. Run `npx ts-node -e "const p = require('./src/data-providers/ccxt'); p.fundingRate('BTC/USDT', 'binance').then(console.log)"`
3. Confirm output contains `fundingRate` as a non-null number
4. Run MCP server and invoke `fundingRate` tool via MCP client; verify markdown table response
5. Invoke with an exchange that doesn't support futures; confirm graceful error message
