# Changelog

All notable changes to this project are documented here. Releases are published
on the [GitHub Releases](https://github.com/rosendolu/crypto-mcp-server/releases) page.

## [3.0.0] - 2026-10-15

A full rebuild of the tool surface. There are no compatibility aliases: the v2
names (`get_market_data`, `compare_exchanges`, `list_capabilities`) and the
intermediate `get_tickers` / `get_funding_rates` rankers are gone, replaced by
24 focused tools.

### Added

- **Derivatives intelligence**: `get_funding_history` (with average, min/max and
  annualized carry), `get_open_interest` (snapshot or history), `get_basis`
  (spot versus perpetual plus funding carry, read from one venue) and
  `get_long_short_ratio`.
- **Screener**: `scan_market` filters by quote, market type, volume and change,
  ranks by volume, change, funding, absolute funding or spread, and reports how
  many markets matched and how many were dropped for a missing sort field.
- **Analysis depth**: `get_multi_timeframe_analysis` (per-timeframe bias plus
  consensus), `detect_patterns` (nine candlestick patterns with `bars_ago`) and
  `get_market_regime` (trend/range and volatility classification with its
  evidence and the rules that produced it).
- **Portfolio**: `get_positions` reports leverage, margin mode, entry/mark/
  liquidation prices and unrealized PnL, filtering closed legs and accepting
  either a pair or a contract symbol.
- **MCP resources**: `crypto://indicators`, `crypto://patterns`,
  `crypto://exchanges`, `crypto://server-info`.
- **MCP prompts**: `analyze_trend`, `funding_arbitrage_check`, `market_overview`
  and `portfolio_review` (portfolio level).
- `UNKNOWN_PATTERN` error code, and `NOT_SUPPORTED` is now surfaced when every
  venue in the fallback chain lacks a capability.
- Contract tests (tool index versus registry, argument descriptions, size caps,
  retired names, version consistency), pattern and regime unit tests, resource
  and prompt tests, and a stdio end-to-end test that spawns the real entrypoint.

### Changed

- `compare_markets` compares `last`, `bid`, `ask` or `funding_rate` and keys the
  spread on the compared field.
- Cross-venue comparison, multi-timeframe analysis and portfolio fan-out run
  concurrently, with per-venue errors reported in place.
- Every list response is capped and reports `truncated` / `limits`; intervals
  are validated against a 15-value list (`4H` is accepted, `1M` is never read as
  one minute).
- Market and analysis tools return JSON consistently, and `get_server_info`
  reports uptime and dependency versions.
- CI runs ruff and pytest as separate blocking jobs.

### Removed

- The v2 compatibility layer and the `on_chain_large_transfer` placeholder that
  always returned `false`.

### Fixed

- Ruff baseline: 31 errors (unused re-export, outdated typing imports, long
  lines) are gone; `ruff check .` is clean.
- Order-book and fill responses no longer return unbounded result sets.
- Candles, funding history, open interest, positioning, positions and screener
  rows all have explicit caps, and schema-level validation rejects invalid
  intervals and limits before any exchange request.

## [2.2.0] - 2026-10-14

### Added

- Permission ladder: `market` → `analysis` → `portfolio` → `trading`.
- Default capability is public analysis. Trading requires `PERMISSION_LEVEL=trading` or `ENABLE_TRADING=true`.
- `compare_exchanges` for venue spreads and `get_portfolio` for multi-exchange balances.
- `list_capabilities` describing the active permission level and registered tools.
- Unified error codes (`TIMEOUT`, `RATE_LIMITED`, `FALLBACK_EXHAUSTED`, …).
- Exchange request retry, per-venue spacing, and public-data fallbacks (`EXCHANGE_FALLBACKS`).
- Recorded market fixtures under `tests/fixtures/` so pytest never calls live exchange APIs.
- Docker image, GitHub Actions CI, and GitHub Release workflow.
- Client configuration examples for Cursor, Claude Code, Claude Desktop, and OpenAI Agents.

### Changed

- Portfolio tools (`get_balance`, `get_orders`) are no longer registered at the default level.
- Public market calls report the venue actually used after a fallback.

## [2.1.0] - 2026-10-01

- Python 3.12 rewrite on FastMCP, uv, CCXT, and pandas.
- Seven focused MCP tools replacing the previous TypeScript surface.
