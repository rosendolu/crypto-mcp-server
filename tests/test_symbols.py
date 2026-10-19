"""Symbol normalization tests (pure, no third-party deps)."""

from __future__ import annotations

import pytest

from symbols import normalize_symbol


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("BTC/USDT", "BTC/USDT"),
        ("btc/usdt", "BTC/USDT"),
        ("BTC_USDT", "BTC/USDT"),
        ("btc-usdt", "BTC/USDT"),
        ("ethusdt", "ETHUSDT"),
        ("  btc / usdt ", "BTC/USDT"),
    ],
)
def test_normalize_symbol(raw: str, expected: str) -> None:
    assert normalize_symbol(raw) == expected
