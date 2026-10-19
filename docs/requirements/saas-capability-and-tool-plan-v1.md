# Crypto MCP Server — SaaS 化能力与 Tool 规划 v1

## Status

draft-for-review — 需用户确认「待确认决策」章节后方可进入开发。

## Metadata

| | |
| --- | --- |
| Date | 2026-10-15 |
| Branch | `refactor/python-uv-fastmcp` |
| Product goal | 把 stdio MCP server 演进为可收费的 MCP 产品（近期 stdio，后续托管可选） |
| Owner | Product / Maintainer |

## 1. 目标与非目标

**目标（本季度）**：把"能跑的行情 MCP"变成"有人愿意付费的加密研究 MCP"。先把能力边界与 tool 目录定稿并冻结，再谈托管与计费。

**非目标（本季度）**：不做链上数据、不做新闻情绪、不做回测引擎、不做投资建议/信号服务、不代管用户交易所 API Key。

## 2. 现状盘点

### 2.1 形态与技术栈

- Python 3.12 + uv + FastMCP 4.1.0 + CCXT 4.5.85 + pandas 3.0.6，stdio 单传输，日志全部走 stderr。
- 10 个 tool，4 级权限阶梯（`market` → `analysis` → `portfolio` → `trading`），默认 `analysis`，交易必须显式开启。
- 指标引擎 28+（MACD/RSI/BB/KDJ/ADX/Ichimoku/Keltner/Chandelier/PSAR/StochRSI/…），带别名归一化。
- 13 个稳定错误码；重试、退避、per-exchange 限频、公共数据 fallback；Docker + GitHub Actions CI。

### 2.2 现状 tool 清单（10）

| Tool | 层级 | 能力 |
| --- | --- | --- |
| `get_market_data` | market | ticker / order_book / trades / ohlcv / funding_rate（多形态混合） |
| `compare_exchanges` | market | 跨所 ticker / funding 对比 + 价差 |
| `list_exchanges` | market | 支持的交易所与凭据状态 |
| `list_capabilities` | market | 权限阶梯与已注册 tool |
| `analyze_indicators` | analysis | 单周期指标最新值 |
| `get_balance` | portfolio | 单所余额 |
| `get_orders` | portfolio | 挂单 / 历史 / 单笔 / 成交 |
| `get_portfolio` | portfolio | 多所资产汇总 |
| `place_order` | trading | 下单 |
| `cancel_order` | trading | 撤单 |

### 2.3 工程质量实测（2026-10-15）

| 检查 | 结果 |
| --- | --- |
| `.venv/bin/python -m pytest` | 52 passed（录制 fixture，不连真实交易所） |
| `.venv/bin/python -m ruff check .` | **31 errors**：24×E501 行超长、`src/exchanges.py:20` F401 未使用 import、`formatting/indicators` UP035、`retry_call/with_public_fallback/map_exchanges` UP047、`tests/test_tools.py` I001 |
| 工作树 | 未提交改动很大（TS→Python 重构 + 权限阶梯 + README/文档重写均未提交） |
| 远端 | `origin` 仍指向上游 `rosendolu/crypto-mcp-server` |

### 2.4 距离 SaaS 的差距

| # | 差距 | 说明 |
| --- | --- | --- |
| G1 | 无认证与租户 | 无 API Key / OAuth、无 tenant 概念 |
| G2 | 无计量与计费 | 无法统计调用量、无法执行配额、无法开票 |
| G3 | 无托管传输 | 只有 stdio，无法服务"不想本地安装"的用户 |
| G4 | 无缓存层 | 每次 agent 调用都打交易所，成本、延迟、限频风险随用户数线性放大 |
| G5 | 无持久化 | 无告警、无自选表、无历史分析记录 |
| G6 | 输出非结构化 | 全部返回 `str`（Markdown 表格混 JSON），下游难以稳定组合 |
| G7 | 无 MCP prompts/resources | 28 个指标靠 agent 自己猜名字，浪费 token 且易错 |
| G8 | 合规与品牌 | Apache-2.0 需保留声明；上游品牌/包名不可直接商用 |

## 3. 目标能力地图

六个能力域，按"agent 原生做不到 → 必须靠服务端算力与多所聚合"排序价值：

| 域 | 用户问题 | Tool |
| --- | --- | --- |
| D1 现货行情 | 现在多少钱、盘口、成交、K 线 | `get_ticker` `get_candles` `get_order_book` `get_recent_trades` `compare_markets` `list_exchanges` |
| D2 技术分析 | 趋势/超买超卖/形态/多周期共振 | `analyze_indicators` `detect_patterns` `get_market_regime` `get_multi_timeframe_analysis` |
| D3 衍生品情报 | 资金费率、持仓量、基差、多空比、清算 | `get_funding_rate` `get_funding_history` `get_open_interest` `get_basis` `get_long_short_ratio` |
| D4 批量扫描 | 谁在异动、谁费率极端、按条件筛标的 | `scan_market` |
| D5 组合与账户 | 我的资产、持仓、盈亏、订单 | `get_balance` `get_positions` `get_orders` `get_portfolio` `get_pnl` |
| D6 监控与执行 | 到价提醒、下单撤单 | `create_alert` `list_alerts` `delete_alert` `place_order` `cancel_order` |
| D0 元信息 | 有哪些能力、还剩多少额度 | `get_capabilities` `get_server_info` `get_usage` |

## 4. 目标 Tool 目录（v3）

### 4.1 设计准则

1. 命名 `verb_noun`，单 tool 单职责（不靠 `data_type` 开关切形态）。
2. 必填参数优先；枚举约束取值范围；周期/数量有硬上限。
3. 输出结构化 JSON + MCP `outputSchema`，人读友好交给 agent。
4. 每个权限层可见 tool ≤ 15，避免 agent 选择准确率下降。
5. 能力探测：交易所不支持的能力返回 `NOT_SUPPORTED`，不返回空表。

### 4.2 v3 Tool 目录

分层：**Free**（本地 stdio，无需账号）· **Pro**（订阅解锁）· **Enterprise**（自带 Key / 合同）

| # | Tool | 层 | 替代/新增 | 关键参数 | 返回 |
| --- | --- | --- | --- | --- | --- |
| 1 | `get_capabilities` | Free | 升级 `list_capabilities` | — | 层级、套餐、限额、已配置交易所、版本 |
| 2 | `get_server_info` | Free | 新增 | — | 版本、传输模式、数据源状态 |
| 3 | `list_exchanges` | Free | 保留 | — | 交易所 + 是否支持现货/合约/OI/funding |
| 4 | `get_ticker` | Free | 拆自 `get_market_data` | `symbol` `exchange?` | 最新价、买卖价、24h 量、涨跌幅 |
| 5 | `get_candles` | Free | 拆自 `get_market_data` | `symbol` `interval` `limit` | OHLCV 数组（上限 1000） |
| 6 | `get_order_book` | Free | 拆自 `get_market_data` | `symbol` `depth?` | bids/asks（上限 50 档） |
| 7 | `get_recent_trades` | Free | 拆自 `get_market_data` | `symbol` `limit?` | 最近成交（上限 200） |
| 8 | `compare_markets` | Free | 升级 `compare_exchanges` | `symbol` `exchanges[]` `field?` | 多所报价 + 价差 + 最优 venue |
| 9 | `analyze_indicators` | Free / Pro | 保留 | 同现状 | 指标值；Free 限 5 指标/300 根/单周期 |
| 10 | `get_multi_timeframe_analysis` | Pro | 新增 | `symbol` `timeframes[]` `indicators[]` | 多周期共振矩阵 |
| 11 | `detect_patterns` | Pro | 新增 | `symbol` `interval` `patterns?` | 吞没/锤子/十字星/三兵等 |
| 12 | `get_market_regime` | Pro | 新增 | `symbol` `interval` | 趋势/震荡/波动率状态 + 依据 |
| 13 | `get_funding_rate` | Pro | 新增（承接旧 funding_rate 形态） | `symbol` `exchange?` | 当前费率、下次结算、预测费率 |
| 14 | `get_funding_history` | Pro | 新增 | `symbol` `exchange?` `limit` | 历史费率序列 |
| 15 | `get_open_interest` | Pro | 新增 | `symbol` `exchange?` `interval?` | OI 现值 / 历史 |
| 16 | `get_basis` | Pro | 新增 | `symbol` `exchanges[]` | 现货-合约基差 + 年化 |
| 17 | `get_long_short_ratio` | Pro | 新增 | `symbol` `exchange?` | 多空持仓比（支持则返回） |
| 18 | `scan_market` | Pro | 新增 | `exchange?` `criteria` `limit` | 涨跌幅/量能/funding 极值筛选结果 |
| 19 | `get_balance` | Pro | 保留 | `exchange?` `min_total?` | 非零余额 |
| 20 | `get_positions` | Pro | 新增 | `exchange?` `symbol?` | 合约持仓（含未实现盈亏） |
| 21 | `get_orders` | Pro | 保留 | `kind` `symbol?` `order_id?` | 订单 / 成交 |
| 22 | `get_portfolio` | Pro | 保留 | `exchanges[]?` `min_total?` | 多所汇总 |
| 23 | `get_pnl` | Pro | 新增 | `exchange?` `since?` | 已实现/未实现盈亏（支持则返回） |
| 24 | `get_usage` | Pro | 新增 | — | 本期调用量、剩余额度、命中率 |
| 25 | `create_alert` / `list_alerts` / `delete_alert` | Pro（托管后） | 新增 | 条件 + 阈值 + 通知方式 | 服务端常驻监控 |
| 26 | `place_order` / `cancel_order` | Enterprise | 保留 | 同现状 | 订单结果，默认不注册 |

### 4.3 与现状的迁移策略

| 现状 tool | v3 处置 | 兼容策略 |
| --- | --- | --- |
| `get_market_data` | 拆成 `get_ticker` / `get_candles` / `get_order_book` / `get_recent_trades` | v3.0 保留为 deprecated 别名，v3.1 移除 |
| `compare_exchanges` | 升级为 `compare_markets` | 保留旧名一个版本 |
| `list_capabilities` | 升级为 `get_capabilities`（旧名保留） | 旧名保留 |
| 其余 6 个 | 保留原名 | 无破坏 |

> **v3.0 实现说明（2026-10-15）**：v3.0 是彻底重构，不留兼容层。Free/Pro/Enterprise
> 列仅作为后续收费边界的设计输入；当前仍由权限阶梯
> （market/analysis/portfolio/trading）控制可见工具，Plan B 的能力已实现，
> Plan C（告警/托管/计量/缓存）尚未开始。详见第 10 节交付状态。

## 10. v3.0 交付状态（2026-10-15）

| 项目 | 状态 |
| --- | --- |
| Plan A（工程基线：lint/CI/上限/契约测试/stdio e2e） | 已交付 |
| Plan B（衍生品情报 + 扫描 + 分析深度） | 已交付 |
| Plan C（托管/认证/计量/缓存/告警） | 未开始（按用户要求暂不实现） |

已交付的 tool（24 个，无任何兼容别名）：

- market（13）：`list_exchanges` `get_capabilities` `get_server_info` `get_ticker` `get_candles` `get_order_book` `get_recent_trades` `get_funding_rate` `get_funding_history` `get_open_interest` `get_basis` `get_long_short_ratio` `compare_markets`
- analysis（+5）：`analyze_indicators` `get_multi_timeframe_analysis` `detect_patterns` `get_market_regime` `scan_market`
- portfolio（+4）：`get_balance` `get_orders` `get_portfolio` `get_positions`
- trading（+2）：`place_order` `cancel_order`

资源 4 个（`crypto://indicators`、`crypto://patterns`、`crypto://exchanges`、`crypto://server-info`），
提示词 4 个（`analyze_trend`、`funding_arbitrage_check`、`market_overview`、`portfolio_review`）。

与规划的两处偏差：原 catalog 的 `get_tickers` / `get_funding_rates` 未实现，其能力由
`scan_market`（`sort_by=quote_volume` / `abs_funding_rate`）覆盖；原 catalog 的
`get_pnl` 未实现，已实现盈亏因各交易所口径不一（部分仅在 `info` 中返回），
`get_positions` 提供未实现盈亏与保证金信息，真实盈亏需要 Plan C 的持久化与对账。

### 4.4 非 tool 的 MCP 能力（当前完全缺失）

**Prompts**（把我们的分析框架交到用户手上）：

- `analyze_trend` — 多周期趋势分析流程
- `funding_arbitrage_check` — 资金费率套利检查清单
- `portfolio_review` — 组合复盘流程

**Resources**（减少 agent 猜测、节省 token）：

- `crypto://indicators` — 28+ 指标目录、参数窗口、别名映射
- `crypto://exchanges` — 各交易所支持能力矩阵（现货/合约/OI/funding/清算）
- `crypto://server-info` — 版本、套餐、限额

## 5. 需求方案

### Plan A — Defect fix：可靠性与工程质量加固

**Problem statement**：现在是"能跑"而不是"可收款"。实测 ruff 31 个错误、CI 只跑 pytest 不阻断 lint、`limit` 无硬上限（K 线可拉爆上下文）、跨所调用串行、交易所不支持合约时的报错不可读、且没有一条真正的 stdio 端到端测试。

**Target users**：现有开源用户；以及"付费后不能容忍数据错/超时/上下文爆炸"的未来付费用户。

**Proposed solution**：用 1–2 周把工程基线拉到"有契约、有边界、有端到端验证"，为后续每次收费能力扩展提供安全网。

**Scope**

- In：ruff 清零并让 CI 阻断；`get_candles`/`analyze_indicators` 的 limit 上限与响应截断提示；`map_exchanges` 并发化（保留 per-exchange 限频）；补 `NOT_SUPPORTED` 错误码与可读提示；10/10 tool 的参数校验 + 错误信封契约测试；stdio 端到端冒烟（spawn → initialize → tools/list → tools/call）；覆盖率门槛；`docs/tools.md` 与真实签名一致性校验。
- Out：任何新能力、托管传输、认证、计费、持久化。

**Risks & mitigations**

- 上限/截断改变现有用户输出 → 默认值保持不变，仅新增上限并在响应中标注 `truncated: true`。
- 并发化提高限频触发率 → 保留 per-exchange 信号量与 `EXCHANGE_MIN_INTERVAL_MS`，并发上限可配置。

**Dependencies**：无外部依赖；需先确认 `get_market_data` 兼容别名策略（见 D3）。

**Success metrics**：`ruff check .` = 0；CI 对 lint/pytest 双阻断；契约测试覆盖 10/10 tool；stdio e2e 冒烟 ≥1 条且稳定；单 tool p95 延迟不劣化（跨所对比类 ≤ 单所 × 1.5）。

**Rough effort**：1.5 人周（小 1 / 可能 1.5 / 大 2）

### Plan B — New feature：衍生品情报与批量扫描

**Problem statement**：当前能力≈"搬运行情 + 算指标"。现货价格用户自己问 ChatGPT 也能拿到，付费理由不足。资金费率历史、持仓量、基差、多空比、清算、跨标的批量扫描，才是 agent 自己做不到、需要服务端算力与多所聚合的部分。

**Target users**：做永续合约的主动交易者、加密研究员、以及把 agent 接入交易工作流的小型量化团队。

**Proposed solution**：新增衍生品数据域与扫描器，用统一 schema 抹平交易所差异，并把口径（公式、窗口、符号规则）写进 resource，让 agent 的输出可复现。

**Scope**

- In：`get_funding_rate` `get_funding_history` `get_open_interest` `get_basis` `scan_market`（+ 可选 `get_long_short_ratio`）；`crypto://indicators`、`crypto://exchanges` 两个 resource；2 个 prompt；CCXT 合约字段差异适配层；能力探测与 `NOT_SUPPORTED` 路径；全部录制 fixture 测试。
- Out：链上数据、新闻/情绪、回测引擎、告警持久化、托管部署。

**Risks & mitigations**

- 各交易所对 OI/清算/多空比支持参差 → 启动前跑一次真实能力探测，产出支持矩阵；不支持的返回 `NOT_SUPPORTED`。
- 符号歧义（现货 `BTC/USDT` vs 永续 `BTC/USDT:USDT`）→ 显式 `market_type: spot|swap` 参数 + 解析规则写进 resource。
- 指标/形态口径争议 → resource 写明公式与窗口，结果回显所用参数。

**Dependencies**：CCXT 合约元数据；需一次性联网录制 fixture；Plan A 的契约测试框架。

**Success metrics**：新增 tool ≥5；合约类 tool 在 binance/okx/bybit 三所全部可用；试用用户中 ≥30% 调用过至少一个衍生品 tool；新增代码 fixture 测试覆盖率 100%。

**Rough effort**：4 人周（小 3 / 可能 4 / 大 6）

### Plan C — Iteration/optimization：SaaS 平台化

**Problem statement**：本地 stdio 模式无法计量、无法防盗版、无法多租户、无法做服务端缓存与常驻告警，因此无法形成可续费收入；同时每次 agent 调用都直连交易所，成本与限频风险随用户数线性放大。

**Target users**：不想本地安装/维护的用户、团队席位、以及需要服务端常驻监控的用户。

**Proposed solution**：在保留 stdio 的同时用 FastMCP `http_app` 暴露 Streamable HTTP 端点，叠加 API Key/OAuth 认证、租户配额与用量计量、共享 TTL 缓存与请求合并，并补齐健康检查、指标与日志脱敏，最后接入收费。

**Scope**

- In：HTTP(streamable) 端点 + 认证中间件 + 租户上下文；每租户配额与用量记录（tenant/tool/latency/upstream/cache-hit），对外暴露 `get_usage`；TTL 缓存（ticker≈5s、candles 按周期、funding≈30s）+ 同参请求合并；`/healthz` `/readyz` `/metrics`；日志与缓存脱敏；容器化部署 + 支付对接（先手动开票亦可）。
- Out：v3.2 前不代管用户交易所 API Key；不做 trading 托管；不做多区域。

**Risks & mitigations**

- 交易所 ToS / 数据再分发风险 → 定位为"实时查询代理 + 分析工具"而非数据转售，保留 attribution，上线前做一次合规审阅。
- 多租户缓存串数据 → 公共市场数据可共享缓存，任何私有账户数据禁止进入共享缓存，缓存键含权限层级。
- 成本失控（上游调用费/限频） → 配额 + 单租户 QPS 限制 + 上游调用计数告警。

**Dependencies**：域名/证书、认证方案、支付渠道、运维值守；Plan A 的契约测试。

**Success metrics**：托管端点 p95 < 1.5s；公共行情缓存命中率 ≥ 60%；超额请求 100% 被拦截；首个付费租户上线。

**Rough effort**：6 人周（小 5 / 可能 6 / 大 8）

## 6. ROI 评估

| Plan | Impact (1-5) | Reach (1-5) | Confidence (1-5) | Effort (1-5) | ROI = (I*R*C)/E |
| ---- | -----------: | ----------: | ---------------: | -----------: | --------------: |
| A | 3 | 5 | 5 | 2 | 37.50 |
| B | 5 | 4 | 3 | 4 | 15.00 |
| C | 5 | 4 | 3 | 5 | 12.00 |

打分依据：

- **A**：Impact 3（不直接产生收入，但决定"能不能收钱不被投诉"）；Reach 5（所有用户）；Confidence 5（31 个 lint 错误、无 e2e、无上限都是当场实测到的硬证据）；Effort 2（1–2 人周）。
- **B**：Impact 5（决定"用户为什么付费"）；Reach 4（付费意愿最强的衍生品用户，非全体）；Confidence 3（付费意愿与 tool 边界仍未验证）；Effort 4（新数据域 + 多所差异 + fixture）。
- **C**：Impact 5（没有它就没有订阅收入）；Reach 4（愿意迁移到托管的用户子集）；Confidence 3（定价、合规、运维成本均未验证）；Effort 5（认证 + 计量 + 缓存 + 运维）。

## 7. 推荐

- **Recommended**：**Plan A**
- **Why**：
  - ROI 最高（37.50），成本最低（1–2 人周），且是 B 与 C 的前置条件——没有契约测试、输入上限与端到端验证，一旦开放托管，问题会直接变成事故与账单。
  - 战略契合：本季度的商业目标是"能收费"，而收费的第一要求是可信与稳定；当前 ruff 31 个错误 + 无端到端测试的组合不适合任何付费产品。
  - 顺序：**A（1–2 周）→ B（3–6 周，收入引擎）→ C（6–10 周，平台化）**；A 期间同步冻结 v3 tool 目录，避免改名成本随用户增长而上升。
- **Week-1 de-risking**：
  1. 评审并冻结本文件的 v3 tool 目录（改名一次性做完）。
  2. ruff 清零 + CI 双阻断，建立"红了就不许合并"的基线。
  3. 落地契约测试框架 + 1 条 stdio 端到端冒烟。
  4. 跑一次真实交易所能力探测脚本，产出 OI/funding/basis/清算 支持矩阵，决定 Plan B 的 tool 边界。
- **MVP slice**：Plan A + v3 目录的 Free 层落地（4 个 `get_*` 拆分 tool + 兼容别名 + `crypto://indicators` resource + 3 个 prompt）。
- **Timeline**：
  - M1（第 1 周）：工程基线（lint/CI/e2e/契约测试/输入上限）。
  - M2（第 2–3 周）：v3 tool 目录落地 + Free 层重构 + resource/prompt。
  - M3（第 4–7 周）：Pro 能力包（funding/OI/basis/扫描）。
  - M4（第 8–12 周）：SaaS 平台层（HTTP + 认证 + 计量 + 缓存）并开始收费。
- **Decision log**：
  - 假设付费用户是"用 AI agent 做加密交易/研究"的个人与小型团队，愿意自带交易所 Key（降低合规风险）。
  - 假设 6 个月内靠"能力密度 + 可靠性"取胜，而不是拼数据源数量或最低价。
  - 会改变决定的信号：试用用户 80% 只用现货行情 → B 优先级下调；多数用户强烈要求"不要本地安装" → C 提前；出现数据准确性问题 → A 范围扩大。

## 8. 待确认决策（需用户回复选项）

| 编号 | 决策 | 选项 | 建议 |
| --- | --- | --- | --- |
| D1 | 近 6 个月商业化形态 | A 本地优先（stdio + License Key 订阅）／B 托管优先（HTTP + API Key + 额度）／C 双轨（先 stdio 分层与配额，抽象服务层后再开托管） | **C** |
| D2 | 免费/付费边界 | A 行情+分析全免费，只卖托管／B 现货行情+基础指标免费，衍生品/扫描/组合/多周期付费／C 全部免费，只卖 Enterprise SLA | **B** |
| D3 | tool 命名迁移 | A 直接改名不加兼容层／B 改名并保留旧名一个版本／C 不改名，只在旧名内部扩展 | **B** |
| D4 | trading 是否留在自托管产品内 | A 保留（默认关闭）／B 移出，仅 Enterprise 合同提供／C 彻底移除 | **A** |

## 9. 已知仓库遗留问题（建议随 Plan A 一并处理）

- `docs/.DS_Store` 等文件处于 staged 删除状态，工作树长期未提交，建议 Plan A 第一周内结清。
- `origin` 指向上游 fork：商业化前需切到自有仓库，并决定是否继续 rebase 上游、改用自有包名与品牌（Apache-2.0 需保留声明与 NOTICE）。
- `pyproject.toml` 中 `crypto-mcp-server` 包名与上游同名，若发布到 PyPI 需改名。
