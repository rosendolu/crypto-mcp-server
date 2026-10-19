"""Unified error codes for MCP tool responses."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Stable machine-readable codes returned to MCP clients."""

    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    UNKNOWN_EXCHANGE = "UNKNOWN_EXCHANGE"
    UNKNOWN_INDICATOR = "UNKNOWN_INDICATOR"
    UNKNOWN_PATTERN = "UNKNOWN_PATTERN"
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    EXCHANGE_UNAVAILABLE = "EXCHANGE_UNAVAILABLE"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    FALLBACK_EXHAUSTED = "FALLBACK_EXHAUSTED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CryptoMCPError(Exception):
    """Application error with a stable ``code`` for agents and logs."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.as_text())

    def as_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": str(self.code), "message": self.message}
        if self.details:
            payload["details"] = self.details
        return {"error": payload}

    def as_text(self) -> str:
        return json.dumps(self.as_payload(), ensure_ascii=False)


def map_ccxt_error(exc: BaseException) -> CryptoMCPError:
    """Translate a CCXT exception into a ``CryptoMCPError``."""
    import ccxt

    message = str(exc) or exc.__class__.__name__
    if isinstance(exc, ccxt.RequestTimeout):
        return CryptoMCPError(ErrorCode.TIMEOUT, message)
    if isinstance(exc, ccxt.RateLimitExceeded | ccxt.DDoSProtection):
        return CryptoMCPError(ErrorCode.RATE_LIMITED, message)
    if isinstance(exc, ccxt.AuthenticationError | ccxt.PermissionDenied):
        return CryptoMCPError(ErrorCode.AUTHENTICATION_FAILED, message)
    if isinstance(exc, ccxt.NetworkError | ccxt.ExchangeNotAvailable):
        return CryptoMCPError(ErrorCode.NETWORK_ERROR, message)
    if isinstance(exc, ccxt.NotSupported):
        return CryptoMCPError(
            ErrorCode.NOT_SUPPORTED,
            f"{message} — this exchange does not expose that capability.",
        )
    if isinstance(exc, ccxt.BadSymbol | ccxt.BadRequest):
        return CryptoMCPError(ErrorCode.INVALID_ARGUMENT, message)
    return CryptoMCPError(ErrorCode.EXCHANGE_UNAVAILABLE, message)
