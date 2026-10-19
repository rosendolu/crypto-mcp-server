"""Small helpers that turn CCXT payloads into LLM-friendly text."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from typing import Any


def json_text(payload: Any) -> str:
    """Serialize ``payload`` to pretty JSON, tolerating non-JSON scalars."""
    return json.dumps(payload, indent=2, default=str, ensure_ascii=False)


def format_number(value: Any) -> str:
    """Render numbers compactly without float noise."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        return f"{value:.8g}"
    return str(value)


def to_markdown_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Build a GitHub-flavoured Markdown table."""
    header_line = "| " + " | ".join(headers) + " |"
    separator = "|" + "|".join("---" for _ in headers) + "|"
    body = [
        "| " + " | ".join(format_number(cell) for cell in row) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator, *body])


def summarize_ticker(ticker: dict[str, Any]) -> dict[str, Any]:
    """Keep the fields an LLM actually reasons about."""
    return {
        "symbol": ticker.get("symbol"),
        "last": ticker.get("last"),
        "bid": ticker.get("bid"),
        "ask": ticker.get("ask"),
        "high": ticker.get("high"),
        "low": ticker.get("low"),
        "baseVolume": ticker.get("baseVolume"),
        "quoteVolume": ticker.get("quoteVolume"),
        "change": ticker.get("change"),
        "percentage": ticker.get("percentage"),
        "timestamp": ticker.get("timestamp"),
    }
