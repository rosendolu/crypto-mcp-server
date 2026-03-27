## Why

The `candlesticks` MCP tool fetches OHLCV data via CCXT but does not expose a `limit` parameter, so consumers always receive the exchange's default candle count (typically 100–500 bars). AI agents performing technical analysis often need a precise number of candles (e.g., exactly 200 for a 200-period SMA) or a minimal set (e.g., 50 candles) to reduce token payload size and latency. Without a first-class `limit` parameter, users are forced to use the opaque `options` escape-hatch in an undocumented way.

## What Changes

- Add an optional `limit` parameter to the `candlesticks` MCP tool in `src/api/tools/index.ts`.
- Add an optional `limit` parameter to the `candlesticks` provider function in `src/data-providers/ccxt/index.ts` and pass it to `exchange.fetchOHLCV()`.
- Add an optional `limit` parameter to the `calculateIndicators` MCP tool so it can control how many candles are fetched when computing indicators.
- Update `docs/tool-prompts.md` to document the new `limit` parameter in the `candlesticks` and `calculateIndicators` prompt templates.

## Capabilities

### New Capabilities
- `candlestick-limit`: Expose an explicit `limit` parameter on the candlestick fetch flow, allowing callers to request a specific number of OHLCV bars from the exchange.

### Modified Capabilities
<!-- No existing spec-level requirement files exist under openspec/specs/ — no delta specs required -->

## Impact

- `src/data-providers/ccxt/index.ts` — `candlesticks()` function signature gains an optional `limit?: number` parameter.
- `src/api/tools/index.ts` — `candlesticks` and `calculateIndicators` tool schemas gain an optional `limit` field.
- `docs/tool-prompts.md` — updated prompt examples for `candlesticks` and `calculateIndicators`.
- No breaking changes: the parameter is optional with undefined (exchange-default) as the fallback.
