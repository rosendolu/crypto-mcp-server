## Context

The `candlesticks` provider function calls `exchange.fetchOHLCV(symbol, interval, since, limit, params)`. Currently the `limit` argument is always passed as `undefined`, and extra options are forwarded via an opaque `options` object. This means callers cannot directly control the number of candles returned without knowing the CCXT API internals. The `calculateIndicators` tool also calls `candlesticks` without any limit control, meaning it always fetches whatever the exchange default is (typically 100–500 bars).

## Goals / Non-Goals

**Goals:**
- Expose `limit?: number` as a first-class optional parameter on the `candlesticks` provider function.
- Expose `limit?: number` on both the `candlesticks` and `calculateIndicators` MCP tools.
- Pass the `limit` through to `exchange.fetchOHLCV()` as the fourth positional argument.
- Default to `undefined` (exchange default) when not provided — fully backward-compatible.

**Non-Goals:**
- Pagination across multiple CCXT calls to fetch more than the exchange maximum per request.
- `since` (timestamp-based) parameter exposure (future work).
- Changing the response format or existing behavior when `limit` is omitted.

## Decisions

**Decision 1: Add `limit` as a direct positional argument to `exchange.fetchOHLCV()`**

CCXT's `fetchOHLCV` signature is `(symbol, timeframe, since, limit, params)`. Passing `limit` as the fourth positional argument is the canonical way to control bar count. Putting it in `options/params` also works but is less discoverable and bypasses CCXT validation. We use the positional argument.

**Decision 2: Keep `options` parameter alongside `limit`**

The existing `options` escape-hatch is still needed for exchange-specific parameters (e.g., `endTime`). Both `limit` and `options` are kept as independent parameters.

**Decision 3: Default undefined = exchange default**

Passing `undefined` to CCXT's `limit` position causes CCXT to use the exchange's default. This is the right default — no breaking change.

## Risks / Trade-offs

- [Risk: Exchange minimum/maximum limits] → Some exchanges enforce min/max candle counts per request. Exceeding the maximum may return fewer bars than requested or throw an error. Mitigation: document this in tool description; no clamping is implemented at this layer (exchange-level behavior is expected).
- [Risk: Very large limit values] → Requesting thousands of candles increases response size and latency. Mitigation: no server-side cap is implemented in V1; AI agents should use reasonable values.

## Migration Plan

No migration needed. The parameter is optional and backward-compatible. Existing callers that omit `limit` see no behavioral change.

## Open Questions

None — all decisions are resolved.
