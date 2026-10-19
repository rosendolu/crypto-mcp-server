# Demos (recorded fixtures)

These prompts are exercised in `tests/test_demos.py` and `tests/test_tools.py`
against `tests/fixtures/`, so CI never hits a live exchange.

## Analyze BTC over the 4h timeframe

Prompt: `Analyze BTC/USDT on the 4h timeframe. Use EMA, MACD, RSI, and ADX.`

Tool: `analyze_indicators`

```json
{
  "symbol": "BTC/USDT",
  "interval": "4h",
  "limit": 48,
  "indicators": ["ema", "macd", "rsi", "adx"]
}
```

## Compare Binance and OKX price

Prompt: `Compare the BTC/USDT last price on Binance and OKX.`

Tool: `compare_markets`

```json
{
  "symbol": "BTC/USDT",
  "exchanges": ["binance", "okx", "bybit"],
  "field": "last"
}
```

The recorded snapshot has Binance last `67850.1`, OKX `67862.4` and Bybit
`67845.0`, so the spread is `17.4` with OKX highest.

## Screen the most crowded funding

Prompt: `Which USDT pairs on binance have the most extreme funding?`

Tool: `scan_market` with funding merged into every row.

```json
{ "exchange": "binance", "quote": "USDT", "sort_by": "abs_funding_rate", "limit": 2 }
```

The recorded snapshot ranks `SOL/USDT` (`-0.0005`) above `ETH/USDT` (`0.0003`).

## Spot versus perpetual basis

Prompt: `Is BTC/USDT trading above spot on binance?`

Tool: `get_basis`

```json
{ "symbol": "BTC/USDT", "exchange": "binance" }
```

The recorded snapshot has spot `67850.1`, perpetual `67881.9`, basis `31.8`
(`+0.0469%`) and an annualized funding carry of `10.95%`.

## Market regime and patterns

Prompt: `Is BTC/USDT trending or ranging on 4h, and did the last candle form a pattern?`

Tools: `get_market_regime`, then `detect_patterns`.

## Multi-exchange asset distribution

Requires `PERMISSION_LEVEL=portfolio` and API keys.

Prompt: `Show my asset distribution across Binance and OKX.`

Tool: `get_portfolio` with default configured venues. The recorded fixture
combines `0.75 BTC` and `15500 USDT`.

## Open positions

Requires `PERMISSION_LEVEL=portfolio` and API keys.

Prompt: `What positions am I holding, and what is the unrealized PnL?`

Tool: `get_positions`. The recorded fixture returns a `0.5 BTC` long and a
`2 ETH` short, filtering out the closed leg.
