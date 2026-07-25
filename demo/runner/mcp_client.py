"""Minimal MCP JSON-RPC stdio client.

Talks to the GBC MCP server (serve.py) over stdin/stdout.
Protocol: one JSON message per line, JSON-RPC 2.0.
"""

import json
import subprocess
import sys
from typing import Any


class McpClient:
    """MCP stdio client — spawn a server process, call tools via JSON-RPC."""

    def __init__(self, server_cmd: list[str]):
        self._id = 0
        self.proc = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._initialize()

    # ---- public ----

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool; return its result text."""
        resp = self._request("tools/call", {"name": name, "arguments": arguments})
        # MCP result shape: result.content[0].text
        content = resp.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return json.dumps(resp.get("result", {}))

    def close(self) -> None:
        """Shut down the server subprocess."""
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()

    # ---- internal ----

    def _initialize(self) -> None:
        """MCP handshake: initialize → initialized notification."""
        self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "gbc-demo-runner", "version": "0.1.0"},
        })
        self._notify("notifications/initialized")

    def _request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and read the response."""
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        self._send(msg)
        return self._recv()

    def _notify(self, method: str, params: dict | None = None) -> None:
        """Send a JSON-RPC notification (no id, no response)."""
        msg: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def _send(self, msg: dict) -> None:
        """Write one JSON line to the server's stdin."""
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        """Read one JSON line from the server's stdout."""
        line = self.proc.stdout.readline()
        if not line:
            raise ConnectionError("MCP server closed stdout unexpectedly")
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # may be server noise mixed into stdout; try again
            return self._recv()
