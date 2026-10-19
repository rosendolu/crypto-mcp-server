"""Pure symbol helpers (no third-party dependencies)."""

from __future__ import annotations

SYMBOL_SEPARATORS = ("/", "_", "-")


def normalize_symbol(symbol: str) -> str:
    """Normalize a trading pair to CCXT's unified ``BASE/QUOTE`` form.

    Accepts ``BTC/USDT``, ``btc_usdt``, ``BTC-USDT`` and ``btcusdt``.
    """
    text = symbol.strip().upper()
    for separator in SYMBOL_SEPARATORS:
        if separator in text:
            base, quote = (part.strip() for part in text.split(separator, 1))
            return f"{base}/{quote}"
    return text
