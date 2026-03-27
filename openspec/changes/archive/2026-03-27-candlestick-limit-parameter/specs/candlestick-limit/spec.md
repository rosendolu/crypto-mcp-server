## ADDED Requirements

### Requirement: Candlestick fetch with explicit limit
The `candlesticks` provider function and MCP tool SHALL accept an optional `limit` parameter of type `number` that controls the number of OHLCV bars returned by the exchange. When `limit` is omitted, the exchange default SHALL be used.

#### Scenario: Limit specified in provider call
- **WHEN** `candlesticks(symbol, interval, options, exchangeId, 50)` is called with `limit = 50`
- **THEN** `exchange.fetchOHLCV` is called with `limit = 50` as the fourth positional argument
- **THEN** the returned array contains at most 50 candlestick entries (subject to exchange minimum)

#### Scenario: Limit omitted in provider call
- **WHEN** `candlesticks(symbol, interval, options, exchangeId)` is called without a `limit`
- **THEN** `exchange.fetchOHLCV` is called with `limit = undefined`
- **THEN** the returned array size matches the exchange default behavior (no change from prior behavior)

### Requirement: Candlestick MCP tool exposes limit parameter
The `candlesticks` MCP tool schema SHALL include an optional `limit` field of type `z.number().optional()` with a description indicating the number of candles to return.

#### Scenario: AI agent specifies limit in MCP tool call
- **WHEN** the `candlesticks` tool is called with `{ symbol: "BTC/USDT", interval: "1h", limit: 100, exchange: "binance" }`
- **THEN** the tool returns a JSON array of exactly 100 candlestick objects (or fewer if the exchange caps it)

#### Scenario: AI agent omits limit in MCP tool call
- **WHEN** the `candlesticks` tool is called without a `limit` field
- **THEN** the tool behaves identically to the pre-change behavior

### Requirement: calculateIndicators MCP tool exposes limit parameter
The `calculateIndicators` MCP tool schema SHALL include an optional `limit` field of type `z.number().optional()` that is forwarded to the underlying `candlesticks` provider call.

#### Scenario: Indicator calculation with explicit candle limit
- **WHEN** the `calculateIndicators` tool is called with `{ symbol: "ETH/USDT", interval: "1d", limit: 200, indicators: ["sma"] }`
- **THEN** indicators are computed over at most 200 candles fetched from the exchange
