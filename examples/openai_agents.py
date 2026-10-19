"""OpenAI Agents SDK stdio MCP example (read-only analysis)."""

from agents.mcp import MCPServerStdio

crypto_mcp = MCPServerStdio(
    name="crypto-mcp-server",
    params={
        "command": "uv",
        "args": [
            "run",
            "--directory",
            "/absolute/path/to/crypto-mcp-server",
            "crypto-mcp-server",
        ],
        "env": {
            "DEFAULT_EXCHANGE": "binance",
            "PERMISSION_LEVEL": "analysis",
            "ENABLE_TRADING": "false",
        },
    },
)
