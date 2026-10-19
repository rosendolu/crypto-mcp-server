# MCP tool reference

Permission ladder (default **analysis**):

| Level | Enable with | Adds |
| --- | --- | --- |
| market | `PERMISSION_LEVEL=market` | quotes, candles, order book, fills, funding, funding history, open interest, basis and positioning, venue comparison, discovery |
| analysis | `PERMISSION_LEVEL=analysis` (default) | market + indicators, multi-timeframe analysis, candlestick patterns, market regime, screener |
| portfolio | `PERMISSION_LEVEL=portfolio` or `ENABLE_PORTFOLIO=true` | analysis + `get_balance`, `get_orders`, `get_portfolio`, `get_positions` |
| trading | `PERMISSION_LEVEL=trading` or `ENABLE_TRADING=true` | portfolio + `place_order`, `cancel_order` |

## Tool index

`tests/test_contracts.py` asserts this table and the registered tool set stay
identical, so add a row whenever you add a tool.

| Tool | Level | Purpose |
| --- | --- | --- |
| `list_exchanges` | market | Venues with data capabilities and credential state |
| `get_capabilities` | market | Active level, tool ladder, size limits, resources |
| `get_server_info` | market | Version, transport, dependency versions |
| `get_ticker` | market | Latest quote for one pair |
| `get_candles` | market | OHLCV candles for one pair |
| `get_order_book` | market | Order-book levels for one pair |
| `get_recent_trades` | market | Most recent public fills |
| `get_funding_rate` | market | Funding rate for one perpetual contract |
| `get_funding_history` | market | Funding-rate history with carry summary |
| `get_open_interest` | market | Open interest: current snapshot or history |
| `get_basis` | market | Spot versus perpetual basis and funding carry |
| `get_long_short_ratio` | market | Long/short account ratio history |
| `compare_markets` | market | One field across venues, with the spread |
| `analyze_indicators` | analysis | Indicators computed from fresh candles |
| `get_multi_timeframe_analysis` | analysis | The same indicators across timeframes, with agreement |
| `detect_patterns` | analysis | Candlestick pattern detection |
| `get_market_regime` | analysis | Trending/ranging and volatility classification |
| `scan_market` | analysis | Filter, rank and slice a venue's markets |
| `get_balance` | portfolio | Non-zero balances on one venue |
| `get_orders` | portfolio | Open orders, history, one order, or fills |
| `get_portfolio` | portfolio | Per-venue and combined balances |
| `get_positions` | portfolio | Open derivative positions with unrealized PnL |
| `place_order` | trading | Place a limit or market order |
| `cancel_order` | trading | Cancel one order or all orders for a symbol |

Market and analysis tools return JSON. `get_balance` and `get_orders` return
Markdown tables; `get_portfolio` and `get_positions` return JSON. Errors use the
envelope below.

## Size caps

Oversized requests are clamped, never rejected, and the response says so:

```json
{
  "truncated": true,
  "limits": { "limit": { "requested": 10000, "applied": 1000, "cap": 1000 } }
}
```

| Argument | Cap |
| --- | --- |
| `get_candles.limit`, `analyze_indicators.limit`, `detect_patterns.limit`, `get_market_regime.limit`, `get_multi_timeframe_analysis.limit` | 1000 candles |
| `get_order_book.depth` | 50 levels per side |
| `get_recent_trades.limit` | 200 fills |
| `get_funding_history.limit`, `get_open_interest.limit`, `get_long_short_ratio.limit` | 200 points |
| `scan_market.limit` | 100 rows |
| `get_orders.limit` | 500 rows |
| `analyze_indicators.tail` | 50 values per series |
| `get_multi_timeframe_analysis.timeframes` | 4 intervals |

A limit below 1 is rejected with `INVALID_ARGUMENT`, as is an interval outside
the supported list.

## Market tools

### `get_ticker`

`symbol`, `exchange?` → last, bid, ask, 24h volume and change.

### `get_candles`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `symbol` | string | yes | |
| `interval` | string | no | `1h` |
| `limit` | int | no | 100 |
| `exchange` | string | no | configured default |

Intervals: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`,
`12h`, `1d`, `3d`, `1w`, `1M`. Uppercase forms such as `4H` are accepted.

### `get_order_book`

`symbol`, `depth?` (default 20), `exchange?` → bids and asks.

### `get_recent_trades`

`symbol`, `limit?` (default 50), `exchange?` → timestamp, side, price, amount, cost.

### `get_funding_rate`

`symbol`, `exchange?` → current rate, next funding time, predicted rate.
Perpetual contracts only; venues that distinguish spot from swap may need the
contract symbol such as `BTC/USDT:USDT`.

### `get_funding_history`

`symbol`, `limit?` (default 50), `exchange?` → funding points plus a summary:
`average_rate`, `min_rate`, `max_rate`, `funding_interval_hours` (derived from
the spacing of the recorded points) and `average_annualized_percent`.

### `get_open_interest`

`symbol`, `interval?`, `limit?` (default 50), `exchange?`. Omit `interval` for
the current snapshot (`mode: current`); pass an interval for the series
(`mode: history`).

### `get_basis`

`symbol`, `exchange?` → spot price, perpetual price, `basis`,
`basis_percent`, `funding_rate`, `funding_interval_hours` and
`funding_annualized_percent`. Both legs are read from one venue, so the basis is
never mixed across exchanges.

### `get_long_short_ratio`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `symbol` | string | yes | |
| `timeframe` | string | no | `1h` |
| `limit` | int | no | 50 |
| `exchange` | string | no | configured default |

Returns `latest`, `average` and the series. Coverage varies by venue;
unsupported venues return `NOT_SUPPORTED`.

### `compare_markets`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `symbol` | string | yes | |
| `exchanges` | string[] | no | `["binance","okx"]` |
| `field` | `last` \| `bid` \| `ask` \| `funding_rate` | no | `last` |

Returns per-venue rows plus `spread` (`highest`, `lowest`, `absolute`,
`percent`). A venue that fails is reported in place; the others still return.
At least two exchange ids are required.

## Discovery tools

### `list_exchanges`

Active default venue, venues with credentials, the number of supported
exchanges, and a capability matrix for the featured venues (`fetchTicker`,
`fetchOrderBook`, `fetchTrades`, `fetchOHLCV`, `fetchFundingRate`,
`fetchFundingRateHistory`, `fetchOpenInterest`).

### `get_capabilities`

Active level, the ladder with enabled flags, configured venues, every size cap,
supported intervals, resource URIs and prompt names.

### `get_server_info`

Name, version, transport, uptime, Python/FastMCP/CCXT/pandas versions, the
active permission level and the default exchange. Useful when reporting a bug.

## Analysis tools

### `analyze_indicators`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `symbol` | string | yes | |
| `indicators` | string[] | no | macd, rsi, bollinger_bands, ema, atr |
| `exchange` | string | no | configured default |
| `interval` | string | no | `1h` |
| `limit` | int | no | 300 |
| `period` | int | no | 14 |
| `fast_period` / `slow_period` / `signal_period` | int | no | indicator default |
| `std_dev` | float | no | `2.0` |
| `tail` | int | no | 1 |

Returns `{ symbol, exchange, interval, candles_used, indicators }`. Read
`crypto://indicators` for the full catalogue, parameters and aliases.

### `get_multi_timeframe_analysis`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `symbol` | string | yes | |
| `timeframes` | string[] | no | 15m, 1h, 4h (max 4) |
| `indicators` | string[] | no | macd, rsi, bollinger_bands, ema, atr |
| `exchange` | string | no | configured default |
| `limit` | int | no | 300 |
| `period` | int | no | 14 |

Each timeframe gets a `bias` (price above its EMA is bullish, below is bearish;
MACD histogram and RSI are fallbacks) plus a `consensus` block counting bullish
and bearish timeframes.

### `detect_patterns`

`symbol`, `interval?`, `patterns?`, `limit?` (default 200), `exchange?`. Each
pattern reports `detected` (fired on the most recent candle), `bars_ago`,
`timestamp`, `direction` and `occurrences`. Read `crypto://patterns` for the
supported names.

### `get_market_regime`

`symbol`, `interval?`, `limit?` (default 300), `period?` (default 14),
`exchange?`. Returns `trend` (`trending_up`, `trending_down`, `ranging`,
`transitioning`), `volatility` (`expanding`, `compressed`, `normal`), the
`evidence` (ADX/DMI, ATR%, Bollinger width and percentile, EMA spread) and the
`rules` that produced the classification.

### `scan_market`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `exchange` | string | no | configured default |
| `quote` | string | no | `USDT` |
| `sort_by` | `quote_volume` \| `change_percent` \| `funding_rate` \| `abs_funding_rate` \| `spread_percent` | no | `quote_volume` |
| `limit` | int | no | 20 |
| `min_quote_volume` | float | no | |
| `min_change_percent` | float | no | |
| `max_change_percent` | float | no | |
| `include_funding` | bool | no | `false` |

Sorts descending except `spread_percent`, which sorts ascending so the tightest
markets come first. Rows carry symbol, last, bid/ask, `spread_percent`,
`change_percent`, `quote_volume` and `funding_rate`. The response reports
`markets_matched`, `returned` and `skipped_missing_sort_field`, so a filter that
dropped everything is visible instead of looking empty.

## Portfolio tools

Require credentials and `PERMISSION_LEVEL=portfolio`.

### `get_balance`

`exchange?`, `min_total?` → Markdown table of non-zero balances.

### `get_orders`

| Parameter | Type | Required |
| --- | --- | --- |
| `kind` | `open` \| `all` \| `status` \| `my_trades` | yes |
| `symbol` | string | yes, except `my_trades` without a symbol |
| `order_id` | string | when `kind=status` |
| `exchange` | string | no |
| `limit` | int | no (100) |

### `get_portfolio`

`exchanges?`, `min_total?` → JSON `{ venues, combined_totals }`.

### `get_positions`

| Parameter | Type | Required | Default |
| --- | --- | --- | --- |
| `exchange` | string | no | configured default |
| `symbol` | string | no | every position |
| `min_notional` | float | no | 0 |

A pair symbol such as `ETH/USDT` is resolved to its perpetual. Zero-sized legs
are dropped, and `totals` reports combined `unrealized_pnl` and `notional`.

## Trading tools

Registered only at **trading**. `place_order` needs `symbol`, `side`,
`order_type`, `amount`, and `price` for limit orders. `cancel_order` cancels one
id or every open order on the symbol.

## Resources and prompts

| URI | Contents |
| --- | --- |
| `crypto://indicators` | Indicator catalogue: name, category, parameters, aliases |
| `crypto://patterns` | Candlestick patterns with their direction |
| `crypto://exchanges` | Featured venues with capability matrix and credentials |
| `crypto://server-info` | Version, transport and dependency versions |

| Prompt | Available at | Purpose |
| --- | --- | --- |
| `analyze_trend` | market | Multi-timeframe trend workflow for one pair |
| `funding_arbitrage_check` | market | Funding, basis and positioning checklist |
| `market_overview` | market | Screening workflow for one venue |
| `portfolio_review` | portfolio | Balances, positions and open-order review |

## Error payload

Failed calls raise a JSON error:

```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "...",
    "details": {}
  }
}
```

Codes: `INVALID_ARGUMENT`, `UNKNOWN_EXCHANGE`, `UNKNOWN_INDICATOR`,
`UNKNOWN_PATTERN`, `MISSING_CREDENTIALS`, `PERMISSION_DENIED`, `TIMEOUT`,
`RATE_LIMITED`, `NETWORK_ERROR`, `EXCHANGE_UNAVAILABLE`, `NOT_SUPPORTED`,
`FALLBACK_EXHAUSTED`, `AUTHENTICATION_FAILED`, `INSUFFICIENT_DATA`,
`INTERNAL_ERROR`.

`NOT_SUPPORTED` means the venue does not publish that capability. When every
venue in the fallback chain says so, the tool reports `NOT_SUPPORTED` instead of
`FALLBACK_EXHAUSTED`, with the per-venue attempts in `details`.
