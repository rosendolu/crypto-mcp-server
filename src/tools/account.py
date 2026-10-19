"""Private account tools: balances, orders and multi-exchange portfolio."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from config import configured_exchanges
from errors import CryptoMCPError, ErrorCode
from exchanges import call_exchange, map_exchanges
from formatting import json_text, to_markdown_table
from symbols import normalize_symbol
from validation import MAX_ORDERS, bounded, limit_note

from .derivatives import swap_symbol

logger = logging.getLogger("crypto_mcp.tools.account")

OrdersKind = Literal["open", "all", "status", "my_trades"]

ORDER_COLUMNS = ["id", "datetime", "symbol", "type", "side", "price", "amount", "filled", "status"]


def _order_row(order: dict[str, Any]) -> list[Any]:
    return [order.get(column) for column in ORDER_COLUMNS]


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_balance(exchange: str | None = None, min_total: float = 0.0) -> str:
        """Return non-zero balances for a single exchange account.

        Requires API credentials and the portfolio permission level.

        Args:
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            min_total: Only include assets whose total balance is at least this value.
        """
        balance, used = await call_exchange(
            "fetch_balance",
            exchange_id=exchange,
            require_credentials=True,
        )
        logger.debug("get_balance exchange=%s", used)
        totals = balance.get("total") or {}
        free = balance.get("free") or {}
        used_amounts = balance.get("used") or {}
        rows = [
            [asset, free.get(asset, 0), used_amounts.get(asset, 0), total]
            for asset, total in totals.items()
            if total and total >= min_total
        ]
        if not rows:
            return f"No non-zero balances found on {used}."
        table = to_markdown_table(["asset", "free", "used", "total"], rows)
        return f"**balances on {used}**\n\n{table}"

    @mcp.tool
    async def get_portfolio(
        exchanges: list[str] | None = None,
        min_total: float = 0.0,
    ) -> str:
        """Aggregate non-zero balances across every exchange with credentials.

        Requires the portfolio permission level. Use this to inspect asset
        distribution across venues.

        Args:
            exchanges: Exchange ids to include. Defaults to every configured venue.
            min_total: Only include assets whose total balance is at least this value.
        """
        venues = exchanges or configured_exchanges()
        if not venues:
            raise CryptoMCPError(
                ErrorCode.MISSING_CREDENTIALS,
                "No exchange credentials are configured. "
                "Set <EXCHANGE>_API_KEY and <EXCHANGE>_SECRET.",
            )

        async def load_balance(exchange_id: str) -> dict[str, Any]:
            balance, used = await call_exchange(
                "fetch_balance",
                exchange_id=exchange_id,
                require_credentials=True,
            )
            totals = balance.get("total") or {}
            assets = {
                asset: {
                    "free": balance.get("free", {}).get(asset, 0),
                    "used": balance.get("used", {}).get(asset, 0),
                    "total": total,
                }
                for asset, total in totals.items()
                if total and total >= min_total
            }
            return {"exchange": used, "assets": assets}

        per_venue = await map_exchanges(venues, load_balance)
        combined: dict[str, float] = {}
        for row in per_venue.values():
            if not isinstance(row, dict) or "assets" not in row:
                continue
            for asset, values in row["assets"].items():
                combined[asset] = combined.get(asset, 0.0) + float(values["total"])
        return json_text({"venues": per_venue, "combined_totals": combined})

    @mcp.tool
    async def get_orders(
        kind: OrdersKind,
        symbol: str | None = None,
        order_id: str | None = None,
        exchange: str | None = None,
        limit: int = 100,
    ) -> str:
        """Look up orders and fills on an exchange account.

        Requires API credentials and the portfolio permission level.

        Args:
            kind: open (open orders), all (order history), status (single order)
                or my_trades (fills).
            symbol: Trading pair, e.g. BTC/USDT. Required for every kind except
                my_trades when omitted.
            order_id: Order id, required when kind='status'.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            limit: Max rows to return.
        """
        normalized = normalize_symbol(symbol) if symbol else None
        capped = bounded("limit", limit, MAX_ORDERS)
        logger.debug("get_orders kind=%s symbol=%s", kind, symbol)

        if kind == "status":
            if not order_id or not normalized:
                raise CryptoMCPError(
                    ErrorCode.INVALID_ARGUMENT,
                    "kind='status' requires both `symbol` and `order_id`.",
                )
            order, used = await call_exchange(
                "fetch_order",
                order_id,
                normalized,
                exchange_id=exchange,
                require_credentials=True,
            )
            payload = dict(order)
            payload["exchange"] = used
            return json_text(payload)

        if kind == "open":
            if not normalized:
                raise CryptoMCPError(ErrorCode.INVALID_ARGUMENT, "kind='open' requires `symbol`.")
            orders, used = await call_exchange(
                "fetch_open_orders",
                normalized,
                exchange_id=exchange,
                require_credentials=True,
                limit=capped.applied,
            )
        elif kind == "all":
            if not normalized:
                raise CryptoMCPError(ErrorCode.INVALID_ARGUMENT, "kind='all' requires `symbol`.")
            orders, used = await call_exchange(
                "fetch_orders",
                normalized,
                exchange_id=exchange,
                require_credentials=True,
                limit=capped.applied,
            )
        elif kind == "my_trades":
            trades, used = await call_exchange(
                "fetch_my_trades",
                normalized,
                exchange_id=exchange,
                require_credentials=True,
                limit=capped.applied,
            )
            rows = [
                [
                    trade.get("id"),
                    trade.get("datetime"),
                    trade.get("symbol"),
                    trade.get("side"),
                    trade.get("price"),
                    trade.get("amount"),
                    trade.get("cost"),
                ]
                for trade in trades
            ]
            table = to_markdown_table(
                ["id", "datetime", "symbol", "side", "price", "amount", "cost"], rows
            )
            note = limit_note(capped)
            return f"**fills on {used}**\n\n{table}" + (f"\n\n{note}" if note else "")
        else:
            raise CryptoMCPError(ErrorCode.INVALID_ARGUMENT, f"Unsupported kind '{kind}'.")

        table = to_markdown_table(ORDER_COLUMNS, [_order_row(order) for order in orders])
        note = limit_note(capped)
        return f"**orders on {used}**\n\n{table}" + (f"\n\n{note}" if note else "")

    @mcp.tool
    async def get_positions(
        exchange: str | None = None,
        symbol: str | None = None,
        min_notional: float = 0.0,
    ) -> str:
        """List open derivative positions with entry, mark, leverage and unrealized PnL.

        Requires API credentials and the portfolio permission level. Venues that
        do not expose positions return NOT_SUPPORTED.

        Args:
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            symbol: Optional pair filter, e.g. BTC/USDT.
            min_notional: Drop positions whose notional is below this value.
        """
        # A pair symbol such as ETH/USDT resolves to its perpetual contract.
        normalized = swap_symbol(symbol) if symbol else None
        positions, used = await call_exchange(
            "fetch_positions",
            [normalized] if normalized else None,
            exchange_id=exchange,
            require_credentials=True,
        )
        rows: list[dict[str, Any]] = []
        unrealized = 0.0
        notional_total = 0.0
        for position in positions or []:
            contracts = position.get("contracts")
            if not contracts:
                continue
            notional = position.get("notional")
            if isinstance(notional, int | float) and abs(notional) < min_notional:
                continue
            pnl = position.get("unrealizedPnl")
            if isinstance(pnl, int | float):
                unrealized += pnl
            if isinstance(notional, int | float):
                notional_total += abs(notional)
            rows.append(
                {
                    "symbol": position.get("symbol"),
                    "side": position.get("side"),
                    "contracts": contracts,
                    "contractSize": position.get("contractSize"),
                    "notional": notional,
                    "leverage": position.get("leverage"),
                    "marginMode": position.get("marginMode"),
                    "entryPrice": position.get("entryPrice"),
                    "markPrice": position.get("markPrice"),
                    "liquidationPrice": position.get("liquidationPrice"),
                    "unrealizedPnl": pnl,
                    "collateral": position.get("collateral"),
                    "timestamp": position.get("timestamp"),
                }
            )
        payload = {
            "exchange": used,
            "count": len(rows),
            "totals": {
                "unrealized_pnl": unrealized,
                "notional": notional_total,
            },
            "positions": rows,
        }
        return json_text(payload)
