# 🚧 Crypto MCP CLI（积极开发中！）

[![Discord](https://img.shields.io/badge/Discord-Join%20Us-5865F2?logo=discord&logoColor=white)](https://discord.gg/mJ8cdaJ5rg) [![Telegram](https://img.shields.io/badge/Telegram-加入我们-229ED9?logo=telegram&logoColor=white)](https://t.me/crypto_mcp)

> ⚠️ **本项目正在积极开发中！功能、API 和文档都在快速迭代，欢迎反馈和贡献。**

一个强大的 MCP 工具，支持加密货币市场数据、跨平台交易、套利、K 线（蜡烛图）分析、投资组合分析等。**支持多交易所、多账户和多策略分析（MACD、布林带、KDJ、EMA 等）**。基于 [CCXT](https://github.com/ccxt/ccxt?tab=readme-ov-file) 实现强大的交易所集成。

## ✨ 功能亮点

-   🏦 **多交易所支持：** 可在所有主流认证交易所进行交易和分析（基于 [CCXT](https://github.com/ccxt/ccxt?tab=readme-ov-file)）
-   🔄 **套利：** 跨交易所套利与分析
-   📈 **K 线/蜡烛图分析：** 高级 OHLCV 与技术指标分析（MACD、布林带、KDJ、EMA 等）
-   📊 **投资组合与持仓分析：** 多交易所统一投资组合视图
-   🤖 **自动化交易与技术分析：** 策略驱动，支持多账户、多币种

## 🛠️ 工具

CLI 提供以下工具（全部基于 [CCXT](https://github.com/ccxt/ccxt?tab=readme-ov-file)，支持多交易所）：

-   `prices` — 获取某个币对或全部币对的当前价格
    -   参数: `symbol?`, `exchange?`
-   `bookTickers` — 获取某个币对或全部币对的最佳买卖价
    -   参数: `symbol?`, `exchange?`
-   `prevDay` — 获取某个币对或全部币对的 24 小时行情统计
    -   参数: `symbol?`, `exchange?`
-   `candlesticks` — 获取 K 线/蜡烛图数据
    -   参数: `symbol`, `interval`, `options?`, `exchange?`
-   `balance` — 获取账户余额
    -   参数: `exchange?`
-   `dustLog` — 获取币安小额资产兑换记录（仅限 Binance）
    -   参数: `exchange?`
-   `buy` — 限价买入
    -   参数: `symbol`, `quantity`, `price`, `options?`, `exchange?`
-   `sell` — 限价卖出
    -   参数: `symbol`, `quantity`, `price`, `options?`, `exchange?`
-   `marketBuy` — 市价买入
    -   参数: `symbol`, `quantity`, `options?`, `exchange?`
-   `marketSell` — 市价卖出
    -   参数: `symbol`, `quantity`, `options?`, `exchange?`
-   `orderStatus` — 查询订单状态
    -   参数: `symbol`, `orderId`, `exchange?`
-   `allOrders` — 查询某币对所有订单
    -   参数: `symbol`, `exchange?`
-   `openOrders` — 查询某币对所有未完成订单
    -   参数: `symbol`, `exchange?`
-   `cancel` — 撤销订单
    -   参数: `symbol`, `orderId`, `exchange?`
-   `cancelAll` — 撤销某币对所有未完成订单
    -   参数: `symbol`, `exchange?`
-   `trades` — 获取某币对近期成交
    -   参数: `symbol`, `exchange?`
-   `checkExchangeConfigs` — 检查所有支持交易所的 API 密钥配置
    -   无参数
-   `analyzeLogs` — 分析系统日志
    -   参数: `date?`, `search?`, `limit?`

## 🚀 快速开始

**如果你觉得本项目有用，请[给我们 GitHub 点个 ⭐️](https://github.com/rosendolu/crypto-mcp-server)！你的支持是我们持续改进的动力。**

### 使用方法

CLI 可直接与 MCP 兼容客户端（如 **Cursor**、**Claude** 等，支持 stdio 传输）配合使用：

<a href="https://cursor.com/install-mcp?name=Crypto%20MCP&config=eyJjb21tYW5kIjoibnB4IC15IGNyeXB0by1tY3AiLCJlbnYiOnsiTE9HX0xFVkVMIjoiZGVidWciLCJCSU5BTkNFX0FQSV9LRVkiOiIiLCJCSU5BTkNFX1NFQ1JFVCI6IiIsIkdBVEVfQVBJX0tFWSI6IiIsIkdBVEVfU0VDUkVUIjoiIn19"><img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Add Crypto MCP MCP server to Cursor" height="32" /></a>

```
{
  "Crypto MCP": {
    "command": "npx",
    "args": ["-y", "crypto-mcp"],
    "env": {
      "LOG_LEVEL": "debug",
      "BINANCE_API_KEY": "",
      "BINANCE_SECRET": "",
      "GATE_API_KEY": "",
      "GATE_SECRET": ""
    }
  }
}
```

### 环境变量

```
# Binance 示例
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret

# OKX 示例
OKX_API_KEY=your_okx_api_key
OKX_SECRET=your_okx_secret

# Gate 示例
GATE_API_KEY=your_gate_api_key
GATE_SECRET=your_gate_secret

# ...为下方所有支持的交易所重复配置
```

#### 支持的交易所（[CCXT](https://github.com/ccxt/ccxt?tab=readme-ov-file) 认证）

-   binance
-   binancecoinm
-   binanceusdm
-   bingx
-   bitget
-   bitmart
-   bitmex
-   bybit
-   coinex
-   cryptocom
-   gate
-   hashkey
-   htx
-   hyperliquid
-   kucoin
-   kucoinfutures
-   mexc
-   modetrade
-   okx
-   woo
-   woofipro

上述每个交易所都需在 `.env` 文件中设置 `${EXCHANGE_ID}_API_KEY` 和 `${EXCHANGE_ID}_SECRET`。可同时配置多个交易所，系统会优先使用你在运行时指定或第一个有效配置。

#### 日志配置（可选）

```
LOG_LEVEL=info # 可选值：emerg, alert, crit, error, warning, notice, info, debug
```

#### 多交易所与多策略支持

-   系统支持所有 [CCXT](https://github.com/ccxt/ccxt?tab=readme-ov-file) 认证交易所的公私接口。
-   至少需配置一个交易所的 API Key/Secret，系统才能启动。
-   可通过配置或参数切换当前活跃交易所。
-   若所有支持交易所均未配置有效 API 密钥，系统将报错并记录日志。
-   **支持多种技术指标与策略：** MACD、布林带、KDJ、EMA 等。

## 许可证

本项目采用 Apache License 2.0 许可。
Copyright (c) 2025 Rosendo.
