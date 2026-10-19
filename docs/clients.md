# MCP client configuration

Copy a file from `examples/` and replace `/absolute/path/to/crypto-mcp-server`. Keep `ENABLE_TRADING=false` unless you intentionally want order tools.

## Cursor

Save as `.cursor/mcp.json` in the project or the user MCP config. See `examples/cursor.mcp.json`.

## Claude Desktop

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

See `examples/claude-desktop.json`. Restart Claude Desktop after editing.

## Claude Code

Project-level `.mcp.json` or `claude mcp add`. See `examples/claude-code.mcp.json`.

```bash
claude mcp add crypto-mcp-server -- uv run --directory /absolute/path/to/crypto-mcp-server crypto-mcp-server
```

## OpenAI Agents SDK

See `examples/openai_agents.py`. Use `MCPServerStdio` with the same `uv run` command.

## Docker

```bash
docker build -t crypto-mcp-server .
```

Point the MCP client at:

```json
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "--env-file", ".env", "crypto-mcp-server"]
}
```
