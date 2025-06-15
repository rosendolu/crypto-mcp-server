# 📚 Tool Prompt Templates

This document provides prompt templates for all available tools in the Crypto MCP Server. Each tool includes an English and Chinese prompt example for easy reference.

---

## Market Data

### 1. prices

-   **Function:** Get the latest price for a trading pair on a specific exchange.
-   **Parameters:**
    -   `symbol` (optional): Trading pair symbol, e.g., ETH/USDT, BTC/USDT
    -   `exchange` (optional): Exchange id, e.g., binance, okx, gate, etc.
-   **Prompt (EN):**
    > Get the latest price for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的最新价格。

### 2. bookTickers

-   **Function:** Get the best bid/ask for a trading pair on a specific exchange.
-   **Parameters:**
    -   `symbol` (optional): Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show the best bid and ask for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的买一卖一。

### 3. depth

-   **Function:** Get the order book depth for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show the order book depth for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的盘口深度。

### 4. prevDay

-   **Function:** Get previous day statistics for a trading pair or all pairs.
-   **Parameters:**
    -   `symbol` (optional): Trading pair symbol or false for all
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show previous day stats for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的昨日统计。

---

## Account Information

### 5. balance

-   **Function:** Get account balance for an exchange.
-   **Parameters:**
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show my account balance on [exchange].
-   **Prompt (CN):**
    > 查询我在 [exchange] 的账户余额。

### 6. dustLog

-   **Function:** Get dust conversion log for an exchange.
-   **Parameters:**
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show my dust conversion log on [exchange].
-   **Prompt (CN):**
    > 查询我在 [exchange] 的零钱兑换记录。

---

## Order Operations

### 7. buy

-   **Function:** Place a buy order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `quantity`: Order quantity
    -   `price`: Order price
    -   `options` (optional): Order options
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Place a buy order for [quantity] [symbol] at [price] on [exchange].
-   **Prompt (CN):**
    > 在 [exchange] 以 [price] 买入 [quantity] [symbol]。

### 8. sell

-   **Function:** Place a sell order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `quantity`: Order quantity
    -   `price`: Order price
    -   `options` (optional): Order options
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Place a sell order for [quantity] [symbol] at [price] on [exchange].
-   **Prompt (CN):**
    > 在 [exchange] 以 [price] 卖出 [quantity] [symbol]。

### 9. marketBuy

-   **Function:** Place a market buy order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `quantity`: Order quantity
    -   `options` (optional): Order options
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Place a market buy order for [quantity] [symbol] on [exchange].
-   **Prompt (CN):**
    > 在 [exchange] 以市价买入 [quantity] [symbol]。

### 10. marketSell

-   **Function:** Place a market sell order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `quantity`: Order quantity
    -   `options` (optional): Order options
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Place a market sell order for [quantity] [symbol] on [exchange].
-   **Prompt (CN):**
    > 在 [exchange] 以市价卖出 [quantity] [symbol]。

### 11. orderStatus

-   **Function:** Get the status of an order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `orderId`: Order ID
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Check the status of order [orderId] for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的订单 [orderId] 状态。

### 12. allOrders

-   **Function:** Get all orders for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show all orders for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的所有订单。

### 13. openOrders

-   **Function:** Get all open orders for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show all open orders for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的所有挂单。

### 14. cancel

-   **Function:** Cancel an order.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `orderId`: Order ID
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Cancel order [orderId] for [symbol] on [exchange].
-   **Prompt (CN):**
    > 取消 [exchange] 上 [symbol] 的订单 [orderId]。

### 15. cancelAll

-   **Function:** Cancel all orders for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Cancel all orders for [symbol] on [exchange].
-   **Prompt (CN):**
    > 取消 [exchange] 上 [symbol] 的所有订单。

### 16. trades

-   **Function:** Get trade history for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show trade history for [symbol] on [exchange].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的成交历史。

---

## System & Analysis

### 17. checkExchangeConfigs

-   **Function:** List all supported exchanges and their API key/secret status.
-   **Prompt (EN):**
    > List all supported exchanges and their API key/secret status.
-   **Prompt (CN):**
    > 列出所有支持的交易所及其 API 配置状态。

### 18. analyzeLogs

-   **Function:** Analyze log files for a specific date.
-   **Parameters:**
    -   `date`: Log date: YYYY-MM-DD, "today", or "yesterday"
-   **Prompt (EN):**
    > Analyze logs for [date].
-   **Prompt (CN):**
    > 分析 [date] 的日志文件。

### 19. candlesticks

-   **Function:** Get candlestick (OHLCV) data for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `interval`: Candlestick interval, e.g., 1m, 5m, 1h, 1d
    -   `options` (optional): Additional options
    -   `exchange` (optional): Exchange id
-   **Prompt (EN):**
    > Show candlestick data for [symbol] on [exchange] with interval [interval].
-   **Prompt (CN):**
    > 查询 [exchange] 上 [symbol] 的 [interval] K 线数据。

### 20. calculateIndicators

-   **Function:** Calculate technical indicators for a trading pair.
-   **Parameters:**
    -   `symbol`: Trading pair symbol
    -   `interval`: Candlestick interval
    -   `options` (optional): Additional options
    -   `exchange` (optional): Exchange id
    -   `indicators`: Indicators to calculate
    -   `period`, `fastPeriod`, `slowPeriod`, `signalPeriod`, `stdDev` (optional): Indicator parameters
-   **Prompt (EN):**
    > Calculate [indicators] for [symbol] on [exchange] with interval [interval].
-   **Prompt (CN):**
    > 计算 [exchange] 上 [symbol] 的 [interval] K 线的 [indicators] 指标。

---
