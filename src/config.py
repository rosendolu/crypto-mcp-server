"""Environment loading, exchange credentials and logging configuration."""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_EXCHANGE_FALLBACK = "binance"
DEFAULT_EXCHANGE_TIMEOUT_MS = 30_000
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_MS = 250
DEFAULT_MIN_INTERVAL_MS = 50
DEFAULT_FALLBACKS = ("okx", "bybit")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Keep in sync with pyproject.toml.
VERSION = "3.0.0"
# Process start time, used by get_server_info.
STARTED_AT = time.time()


def load_env() -> None:
    """Load ``.env.local`` then ``.env`` from the current working directory.

    Existing process environment variables always win.
    """
    for name in (".env.local", ".env"):
        path = Path.cwd() / name
        if path.is_file():
            load_dotenv(path, override=False)


@dataclass(frozen=True)
class ExchangeCredentials:
    """API credentials for a single exchange."""

    api_key: str
    secret: str
    password: str | None = None


def credentials_for(exchange_id: str) -> ExchangeCredentials | None:
    """Return credentials for ``exchange_id`` if both key and secret are set."""
    prefix = exchange_id.upper()
    api_key = os.environ.get(f"{prefix}_API_KEY")
    secret = os.environ.get(f"{prefix}_SECRET")
    if not api_key or not secret:
        return None
    return ExchangeCredentials(api_key, secret, os.environ.get(f"{prefix}_PASSWORD"))


def configured_exchanges() -> list[str]:
    """Exchange ids that have usable credentials in the environment."""
    import ccxt

    return [exchange_id for exchange_id in ccxt.exchanges if credentials_for(exchange_id)]


def default_exchange() -> str | None:
    """Return the explicitly configured default exchange, if any."""
    value = os.environ.get("DEFAULT_EXCHANGE")
    return value.strip().lower() if value and value.strip() else None


def trading_enabled() -> bool:
    """Return whether order placement and cancellation are explicitly enabled."""
    from permissions import PermissionLevel, permission_level

    return permission_level() is PermissionLevel.TRADING


def exchange_timeout_ms() -> int:
    """Return the exchange request timeout, clamped to a safe positive value."""
    return _positive_int("EXCHANGE_TIMEOUT_MS", DEFAULT_EXCHANGE_TIMEOUT_MS, minimum=1_000)


def retry_attempts() -> int:
    """How many times to try a transient exchange call."""
    return _positive_int("EXCHANGE_RETRY_ATTEMPTS", DEFAULT_RETRY_ATTEMPTS, minimum=1)


def retry_backoff_ms() -> int:
    """Base delay between retries in milliseconds."""
    return _positive_int("EXCHANGE_RETRY_BACKOFF_MS", DEFAULT_RETRY_BACKOFF_MS, minimum=50)


def exchange_min_interval_ms() -> int:
    """Minimum spacing between calls to the same exchange."""
    return _positive_int("EXCHANGE_MIN_INTERVAL_MS", DEFAULT_MIN_INTERVAL_MS, minimum=0)


def fallback_exchanges() -> tuple[str, ...]:
    """Public-data fallback ids, excluding the empty token."""
    raw = os.environ.get("EXCHANGE_FALLBACKS", ",".join(DEFAULT_FALLBACKS))
    return tuple(part.strip().lower() for part in raw.split(",") if part.strip())


def _positive_int(name: str, default: int, *, minimum: int) -> int:
    raw_value = os.environ.get(name, str(default))
    try:
        return max(minimum, int(raw_value))
    except ValueError:
        return default


def configure_logging() -> None:
    """Configure stdio-safe logging.

    MCP servers speak JSON-RPC over stdout, so all logs must go to stderr.
    """
    level = log_level()
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stderr, force=True)


def log_level() -> str:
    """Return the configured log level name."""
    return os.environ.get("LOG_LEVEL", "INFO").upper()
