"""In-memory CCXT stand-in backed by recorded fixtures (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


def swap(symbol: str) -> str:
    """BTC/USDT -> BTC/USDT:USDT, leaving contract symbols untouched."""
    if ":" in symbol:
        return symbol
    base, _, quote = symbol.partition("/")
    return f"{base}/{quote}:{quote}" if base and quote else symbol


class RecordedExchange:
    """Replay recorded tickers, candles, funding, positioning and balances."""

    def __init__(self, exchange_id: str = "binance") -> None:
        self.id = exchange_id
        self.tickers = _load("tickers_btc_usdt.json")
        self.funding = _load("funding_btc_usdt.json")
        self.funding_history = _load("funding_history_btc_usdt.json")
        self.open_interest = _load("open_interest_btc_usdt.json")
        self.open_interest_history = _load("open_interest_history_btc_usdt.json")
        self.long_short_ratio = _load("long_short_ratio_btc_usdt.json")
        self.positions = _load("positions_btc_usdt.json")
        self.balances = _load("balances.json")
        self.ohlcv = _load("ohlcv_btc_usdt_4h.json")["candles"]
        self.book = _load("order_book_btc_usdt.json")
        self.trades = _load("trades_btc_usdt.json")

    def _venue(self, recorded: dict[str, Any]) -> Any:
        return recorded.get(self.id, recorded.get("binance"))

    def _ticker(self, symbol: str) -> dict[str, Any]:
        venue = self._venue(self.tickers)
        payload = venue.get(symbol) or next(iter(venue.values()))
        return {**payload, "symbol": symbol}

    def _funding_for(self, symbol: str) -> dict[str, Any]:
        venue = self._venue(self.funding)
        payload = venue.get(symbol) or venue.get(swap(symbol)) or next(iter(venue.values()))
        return {**payload, "symbol": swap(symbol)}

    def _history(self, recorded: dict[str, Any], symbol: str) -> list[dict[str, Any]]:
        return [{**row, "symbol": swap(symbol)} for row in recorded.get(self.id, [])]

    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return self._ticker(symbol)

    async def fetch_tickers(self) -> dict[str, dict[str, Any]]:
        return {
            symbol: {**payload, "symbol": symbol}
            for symbol, payload in self._venue(self.tickers).items()
        }

    async def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, Any]:
        book = dict(self.book)
        if limit:
            book["bids"] = book["bids"][:limit]
            book["asks"] = book["asks"][:limit]
        return book

    async def fetch_trades(self, symbol: str, limit: int | None = None) -> list[dict[str, Any]]:
        rows = list(self.trades)
        return rows[:limit] if limit else rows

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str | None = None,
        limit: int | None = None,
    ) -> list[list[float]]:
        rows = list(self.ohlcv)
        return rows[-limit:] if limit else rows

    async def fetch_funding_rate(self, symbol: str) -> dict[str, Any]:
        return self._funding_for(symbol)

    async def fetch_funding_rates(self) -> dict[str, dict[str, Any]]:
        return {
            symbol: {**payload, "symbol": symbol}
            for symbol, payload in self._venue(self.funding).items()
        }

    async def fetch_funding_rate_history(
        self,
        symbol: str,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._history(self.funding_history, symbol)
        return rows[-limit:] if limit else rows

    async def fetch_open_interest(self, symbol: str) -> dict[str, Any]:
        payload = self._venue(self.open_interest)
        return {**payload, "symbol": swap(symbol)}

    async def fetch_open_interest_history(
        self,
        symbol: str,
        timeframe: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._history(self.open_interest_history, symbol)
        return rows[-limit:] if limit else rows

    async def fetch_long_short_ratio_history(
        self,
        symbol: str,
        timeframe: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._history(self.long_short_ratio, symbol)
        return rows[-limit:] if limit else rows

    async def fetch_balance(self) -> dict[str, Any]:
        return dict(self._venue(self.balances))

    async def fetch_positions(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        rows = [dict(row) for row in self.positions.get(self.id, [])]
        if symbols:
            wanted = set(symbols)
            rows = [row for row in rows if row.get("symbol") in wanted]
        return rows

    async def fetch_open_orders(
        self,
        symbol: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "1",
                "datetime": "2024-01-09T00:00:00Z",
                "symbol": symbol,
                "type": "limit",
                "side": "buy",
                "price": 66000.0,
                "amount": 0.1,
                "filled": 0.0,
                "status": "open",
            }
        ]

    async def fetch_orders(self, symbol: str, limit: int | None = None) -> list[dict[str, Any]]:
        return await self.fetch_open_orders(symbol)

    async def fetch_my_trades(
        self,
        symbol: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "t1",
                "datetime": "2024-01-08T12:00:00Z",
                "symbol": symbol,
                "side": "buy",
                "price": 65000.0,
                "amount": 0.1,
                "cost": 6500.0,
            }
        ]

    async def fetch_order(self, order_id: str, symbol: str) -> dict[str, Any]:
        return {
            "id": order_id,
            "symbol": symbol,
            "status": "closed",
            "type": "limit",
            "side": "buy",
            "price": 65000.0,
            "amount": 0.1,
            "filled": 0.1,
            "remaining": 0.0,
            "timestamp": 1,
        }

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": "42",
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "price": price,
            "status": "open",
        }

    async def cancel_order(self, order_id: str, symbol: str) -> dict[str, Any]:
        return {"id": order_id, "symbol": symbol, "status": "canceled"}

    async def cancel_all_orders(self, symbol: str) -> list[dict[str, Any]]:
        return [{"id": "1", "symbol": symbol, "status": "canceled"}]


def install_recorded_exchange(
    monkeypatch: Any,
    module_path: str = "exchanges.get_exchange",
) -> None:
    """Point ``get_exchange`` at recorded venues keyed by exchange id."""

    async def fake_get_exchange(
        exchange_id: str | None = None,
        *,
        require_credentials: bool = False,
    ) -> RecordedExchange:
        from exchanges import resolve_exchange_id

        return RecordedExchange(resolve_exchange_id(exchange_id))

    monkeypatch.setattr(module_path, fake_get_exchange)
