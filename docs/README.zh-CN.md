# Crypto MCP Server

**stdio MCP 服务**：加密货币现货与衍生品数据、服务端选币筛选、技术分析、组合与
持仓查询，以及可选的下单执行。技术栈为 Python 3.12、`uv`、FastMCP、CCXT、
pandas。

完整说明、架构图与客户端配置见 [英文 README](../README.md)；工具参数表见
[tools.md](tools.md)。

> **风险声明。** 本项目用于研究与自动化工具开发，**不构成投资建议**，不保证
> 交易结果。API 密钥、下单与市场风险由使用者自行承担。

## 权限层级（默认只读分析）

| 层级 | 启用方式 | 新增能力 |
| --- | --- | --- |
| `market` | `PERMISSION_LEVEL=market` | 行情、K 线、盘口、成交、资金费率及其历史、持仓量、基差、多空比、跨所比价 |
| `analysis` | **默认** | 上述 + 指标、多周期分析、K 线形态、市场状态、选币筛选 |
| `portfolio` | `PERMISSION_LEVEL=portfolio` 或 `ENABLE_PORTFOLIO=true` | 上述 + 余额、订单、组合、持仓 |
| `trading` | `PERMISSION_LEVEL=trading` 或 `ENABLE_TRADING=true` | 上述 + 下单、撤单 |

## 工具一览（24 个）

**行情**

| 工具 | 说明 |
| --- | --- |
| `get_ticker` / `get_candles` / `get_order_book` / `get_recent_trades` | 报价、K 线、盘口、最近成交 |
| `compare_markets` | 跨所比较 `last` / `bid` / `ask` / `funding_rate` 并给出价差 |

**衍生品情报**

| 工具 | 说明 |
| --- | --- |
| `get_funding_rate` | 当前资金费率、下次结算时间、预测费率 |
| `get_funding_history` | 费率历史 + 均值/极值 + 年化持有成本 |
| `get_open_interest` | 持仓量（当前快照或历史序列） |
| `get_basis` | 现货与永续基差 + 资金费率年化（同一交易所内计算） |
| `get_long_short_ratio` | 多空账户比历史 |

**分析**

| 工具 | 说明 |
| --- | --- |
| `analyze_indicators` | 27 个指标，支持别名与 `tail` 历史值 |
| `get_multi_timeframe_analysis` | 多周期同一组指标 + 方向共识 |
| `detect_patterns` | 9 种 K 线形态，含 `bars_ago` 定位最近一次出现 |
| `get_market_regime` | 趋势/震荡与波动率状态，并给出判定依据与规则 |
| `scan_market` | 服务端筛选排序：成交额、涨跌幅、极端费率、最窄点差 |

**组合与执行**

| 工具 | 说明 |
| --- | --- |
| `get_balance` / `get_orders` / `get_portfolio` | 余额、订单、多所汇总 |
| `get_positions` | 持仓：杠杆、强平价、未实现盈亏 |
| `place_order` / `cancel_order` | 下单/撤单（需显式开启） |

**元信息**：`list_exchanges`、`get_capabilities`、`get_server_info`。

## 资源与提示词

| 资源 URI | 内容 |
| --- | --- |
| `crypto://indicators` | 指标目录：分类、参数、别名 |
| `crypto://patterns` | K 线形态及方向 |
| `crypto://exchanges` | 主要交易所能力矩阵与凭据状态 |
| `crypto://server-info` | 版本与依赖信息 |

提示词：`analyze_trend`、`funding_arbitrage_check`、`market_overview`、
`portfolio_review`（portfolio 层级）。

## 响应上限

超限请求会被收敛并在响应中标注 `truncated` / `limits`：K 线 1000、盘口 50 档、
成交 200、费率/持仓量/多空比 200 点、筛选 100 行、订单 500、指标 tail 50、
多周期最多 4 个。小于 1 的 limit 或非法周期直接返回 `INVALID_ARGUMENT`。

## 快速开始

```bash
uv sync
cp .env.example .env
uv run crypto-mcp-server
```

公开行情无需凭据；portfolio 层级需要 `<EXCHANGE_ID>_API_KEY` 与
`<EXCHANGE_ID>_SECRET`。合约符号使用 CCXT 记法（如 `BTC/USDT:USDT`），衍生品工具
会自行从交易对推导。

## Demo 提示词

- 分析 BTC 最近 4 小时趋势
- 比较 Binance 与 OKX 价差
- 哪些永续合约资金费率最极端
- BTC/USDT 现在相对现货是升水还是贴水
- 查看我的多交易所资产分布

详见 [demos.md](demos.md) 与 [tools.md](tools.md)。
