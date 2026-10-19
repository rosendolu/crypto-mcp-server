"""Console entrypoint for the stdio MCP server."""

from __future__ import annotations

from server import create_server


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run()


if __name__ == "__main__":
    main()
