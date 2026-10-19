"""Order placement and cancellation tools (explicit trading permission)."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from errors import CryptoMCPError, ErrorCode
from exchanges import call_exchange
from formatting import json_text
from symbols import normalize_symbol

logger = logging.getLogger("crypto_mcp.tools.trading")

OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def place_order(
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
        exchange: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Place a buy or sell order. Requires credentials and PERMISSION_LEVEL=trading.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            side: buy or sell.
            order_type: limit or market.
            amount: Base-currency amount to trade.
            price: Limit price. Required for order_type='limit', ignored for 'market'.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
            params: Optional extra CCXT order parameters (e.g. {"timeInForce": "GTC"}).
        """
        if order_type == "limit" and price is None:
            raise CryptoMCPError(
                ErrorCode.INVALID_ARGUMENT,
                "`price` is required for a limit order.",
            )
        normalized = normalize_symbol(symbol)
        logger.info(
            "place_order %s %s %s amount=%s exchange=%s",
            side,
            order_type,
            normalized,
            amount,
            exchange,
        )
        order, used = await call_exchange(
            "create_order",
            normalized,
            order_type,
            side,
            amount,
            price if order_type == "limit" else None,
            params or {},
            exchange_id=exchange,
            require_credentials=True,
        )
        payload = dict(order)
        payload["exchange"] = used
        return json_text(payload)

    @mcp.tool
    async def cancel_order(
        symbol: str,
        order_id: str | None = None,
        exchange: str | None = None,
    ) -> str:
        """Cancel one order, or every open order on a symbol when `order_id` is omitted.

        Requires API credentials and PERMISSION_LEVEL=trading.

        Args:
            symbol: Trading pair, e.g. BTC/USDT.
            order_id: Order id to cancel. Omit to cancel all open orders for the symbol.
            exchange: Exchange id, e.g. binance, okx, bybit, gate.
        """
        normalized = normalize_symbol(symbol)
        logger.info(
            "cancel_order symbol=%s order_id=%s exchange=%s",
            normalized,
            order_id,
            exchange,
        )
        if order_id:
            result, used = await call_exchange(
                "cancel_order",
                order_id,
                normalized,
                exchange_id=exchange,
                require_credentials=True,
            )
        else:
            result, used = await call_exchange(
                "cancel_all_orders",
                normalized,
                exchange_id=exchange,
                require_credentials=True,
            )
        if isinstance(result, dict):
            payload = {**result, "exchange": used}
        else:
            payload = {"exchange": used, "result": result}
        return json_text(payload)
