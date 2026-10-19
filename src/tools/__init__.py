"""MCP tool registration gated by permission level."""

from __future__ import annotations

from fastmcp import FastMCP

from permissions import PermissionLevel, permission_level

from . import account, analysis, catalog, derivatives, market, meta, screener, trading

_REGISTRARS = {
    PermissionLevel.MARKET: (
        market.register,
        derivatives.register,
        meta.register,
        catalog.register,
    ),
    PermissionLevel.ANALYSIS: (analysis.register, screener.register),
    PermissionLevel.PORTFOLIO: (account.register, catalog.register_portfolio),
    PermissionLevel.TRADING: (trading.register,),
}


def register_all(mcp: FastMCP, *, level: PermissionLevel | None = None) -> None:
    """Attach tools allowed at ``level`` (and every lower public/read-only tier)."""
    active = level if level is not None else permission_level()
    for candidate, registrars in _REGISTRARS.items():
        if candidate <= active:
            for register in registrars:
                register(mcp)
