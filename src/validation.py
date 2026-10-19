"""Argument validation and response caps shared by every MCP tool.

Caps bound both the upstream request and the text handed back to the agent:
one tool call must never blow up a context window. Callers may ask for more
rows than the cap allows; the value is clamped and the response says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from errors import CryptoMCPError, ErrorCode
from symbols import normalize_symbol

MAX_CANDLES = 1_000
MAX_ORDER_BOOK_LEVELS = 50
MAX_TRADES = 200
MAX_ORDERS = 500
MAX_INDICATOR_TAIL = 50
MAX_FUNDING_HISTORY = 200
MAX_OPEN_INTEREST_POINTS = 200
MAX_POSITIONING_POINTS = 200
MAX_SCAN_ROWS = 100
MAX_TIMEFRAMES = 4

SUPPORTED_INTERVALS = (
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
)

# ``1m`` is excluded so a case-insensitive match can never turn ``1M``
# (one month) into a one-minute request.
_CASE_FOLDED_INTERVALS = {
    value.lower(): value for value in SUPPORTED_INTERVALS if value != "1m"
}


@dataclass(frozen=True)
class Limit:
    """Outcome of clamping one caller-supplied row cap."""

    argument: str
    requested: int
    applied: int
    cap: int

    @property
    def truncated(self) -> bool:
        """True when the caller asked for more rows than the cap allows."""
        return self.applied < self.requested

    def as_dict(self) -> dict[str, int]:
        return {"requested": self.requested, "applied": self.applied, "cap": self.cap}


def bounded(argument: str, value: int, cap: int) -> Limit:
    """Clamp ``value`` into ``1..cap`` and describe what happened."""
    try:
        requested = int(value)
    except (TypeError, ValueError) as error:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"`{argument}` must be an integer, got {value!r}.",
        ) from error
    if requested < 1:
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"`{argument}` must be at least 1, got {requested}.",
        )
    return Limit(argument=argument, requested=requested, applied=min(requested, cap), cap=cap)


def note_limits(payload: dict[str, Any], *limits: Limit) -> dict[str, Any]:
    """Flag a payload when any size cap was hit."""
    capped = {limit.argument: limit.as_dict() for limit in limits if limit.truncated}
    if capped:
        payload["truncated"] = True
        payload["limits"] = capped
    return payload


def limit_note(*limits: Limit) -> str:
    """One-line note for Markdown responses when a size cap was applied."""
    capped = [
        f"`{limit.argument}` capped at {limit.cap} (requested {limit.requested})"
        for limit in limits
        if limit.truncated
    ]
    return f"Note: {'; '.join(capped)}." if capped else ""


def require_symbol(symbol: str | None, *, argument: str = "symbol") -> str:
    """Normalize a required trading pair, or fail with a stable error code."""
    if not symbol or not symbol.strip():
        raise CryptoMCPError(
            ErrorCode.INVALID_ARGUMENT,
            f"`{argument}` is required and must be a trading pair such as BTC/USDT.",
        )
    return normalize_symbol(symbol)


def validate_interval(interval: str) -> str:
    """Return a supported candle interval, or fail with the accepted list."""
    text = (interval or "").strip()
    if text in SUPPORTED_INTERVALS:
        return text
    case_folded = _CASE_FOLDED_INTERVALS.get(text.lower())
    if case_folded is not None:
        return case_folded
    raise CryptoMCPError(
        ErrorCode.INVALID_ARGUMENT,
        f"Unsupported interval '{interval}'. Use one of: {', '.join(SUPPORTED_INTERVALS)}.",
        details={"interval": interval},
    )
