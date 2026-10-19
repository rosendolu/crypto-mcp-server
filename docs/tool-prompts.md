# Tool prompts

Ready-made prompts. Replace symbols as needed. Default permission is `analysis`
(no orders). The server also ships these workflows as MCP prompts
(`analyze_trend`, `funding_arbitrage_check`, `market_overview`,
`portfolio_review`).

## Market

- `Get the latest price for ETH/USDT on binance.`
- `Show the order book for BTC/USDT on okx.`
- `Give me the last 48 4h candles for BTC/USDT.`
- `What is the current funding rate for BTC/USDT on bybit?`
- `Compare the BTC/USDT last price, and the funding-rate spread, across Binance, OKX and Bybit.`
- `Which exchanges are configured, and what permission level is active?`
- `Which exchanges support open interest or long/short ratio?`

## Derivatives

- `Is BTC/USDT trading above or below spot on binance, and what is the annualized carry?`
- `Has funding for BTC/USDT been unusually high this week?`
- `Is open interest on BTC/USDT building or unwinding?`
- `What is the long/short account ratio for BTC/USDT on binance?`

## Analysis

- `Analyze BTC/USDT on the 4h timeframe with EMA, MACD, RSI, and ADX.`
- `Is ETH/USDT overbought on the 1h chart? Use RSI.`
- `Do the 15m, 1h and 4h timeframes agree on SOL/USDT?`
- `Is BTC/USDT trending or ranging on 4h, and is volatility expanding?`
- `Did the last daily candle form a reversal pattern?`
- `Read crypto://indicators and pick a trend, momentum and volatility set for BTC/USDT.`

## Screener

- `Which USDT markets on binance have the highest volume?`
- `Show me the biggest movers on binance in the last 24h.`
- `Which pairs have the tightest spreads on okx?`
- `Find USDT markets with funding above 0.05% and volume above 100M.`
- `Give me an overview of the USDT market on binance.`

## Portfolio (`PERMISSION_LEVEL=portfolio`)

- `Show my balances on binance.`
- `Show my asset distribution across Binance and OKX.`
- `List my open orders for ETH/USDT.`
- `What positions am I holding, and what is the unrealized PnL?`
- `Show my recent fills for BTC/USDT.`

## Trading (`ENABLE_TRADING=true` only)

- `Buy 0.01 BTC at 60000 USDT on binance (limit).`
- `Cancel order 12345678 for BTC/USDT on binance.`

## Limits

Ask for more than the cap and the response says so instead of failing: candles
1000, order-book levels 50, fills 200, funding/open-interest/positioning points
200, screener rows 100, orders 500, indicator tail 50, timeframes 4.
