"""End-to-end stdio smoke test: spawn the real server and speak JSON-RPC.

This is the only test that exercises the real entrypoint, transport and
shutdown path. It deliberately calls a tool that needs no network.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
READ_TIMEOUT_SECONDS = 60.0


def _request(message_id: int, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def test_stdio_handshake_lists_tools_and_calls_one() -> None:
    messages: list[dict[str, Any]] = [
        _request(
            1,
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1"},
            },
        ),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        _request(2, "tools/list"),
        _request(3, "tools/call", {"name": "get_server_info", "arguments": {}}),
    ]

    env = {
        **os.environ,
        "PYTHONPATH": str(SRC),
        "PERMISSION_LEVEL": "analysis",
        "LOG_LEVEL": "CRITICAL",
        "EXCHANGE_RETRY_ATTEMPTS": "1",
        "EXCHANGE_MIN_INTERVAL_MS": "0",
    }
    env.pop("ENABLE_TRADING", None)
    env.pop("ENABLE_PORTFOLIO", None)

    process = subprocess.Popen(
        [sys.executable, "-m", "main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=ROOT,
        env=env,
    )
    assert process.stdin is not None and process.stdout is not None

    lines: queue.Queue[str] = queue.Queue()
    threading.Thread(
        target=lambda: [lines.put(line) for line in process.stdout],
        daemon=True,
    ).start()

    try:
        for message in messages:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        responses: dict[int, dict[str, Any]] = {}
        deadline = time.monotonic() + READ_TIMEOUT_SECONDS
        while len(responses) < 3 and time.monotonic() < deadline:
            try:
                line = lines.get(timeout=1.0)
            except queue.Empty:
                continue
            if not line.strip():
                continue
            payload = json.loads(line)
            if "id" in payload:
                responses[payload["id"]] = payload
    finally:
        process.stdin.close()
        process.wait(timeout=READ_TIMEOUT_SECONDS)

    assert sorted(responses) == [1, 2, 3], f"missing responses: {sorted(responses)}"

    initialized = responses[1]["result"]
    assert initialized["serverInfo"]["name"] == "Crypto MCP Server"
    assert "tools" in initialized["capabilities"]

    tool_names = {tool["name"] for tool in responses[2]["result"]["tools"]}
    assert {"get_ticker", "get_candles", "compare_markets"} <= tool_names
    assert {"place_order", "cancel_order"}.isdisjoint(tool_names)

    result = responses[3]["result"]
    assert result["isError"] is False
    info = json.loads(result["content"][0]["text"])
    assert info["transport"] == "stdio"
    assert info["version"] == "3.0.0"
