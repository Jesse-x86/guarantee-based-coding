"""最小 MCP JSON-RPC stdio 客户端。

与 GBC MCP server（serve.py）通过 stdin/stdout 通信。
协议：每行一个 JSON 消息，JSON-RPC 2.0。
"""

import json
import subprocess
import sys
from typing import Any


class McpClient:
    """MCP stdio 客户端 —— 启动 server 子进程，通过 JSON-RPC 调工具。"""

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
        """调用 MCP 工具，返回结果文本。"""
        resp = self._request("tools/call", {"name": name, "arguments": arguments})
        # MCP 返回格式: result.content[0].text
        content = resp.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return json.dumps(resp.get("result", {}))

    def close(self) -> None:
        """关闭 server 子进程。"""
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
        """MCP 握手：initialize → initialized notification。"""
        self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "gbc-demo-runner", "version": "0.1.0"},
        })
        self._notify("notifications/initialized")

    def _request(self, method: str, params: dict) -> dict:
        """发 JSON-RPC 请求，收响应。"""
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        self._send(msg)
        return self._recv()

    def _notify(self, method: str, params: dict | None = None) -> None:
        """发 JSON-RPC 通知（无 id，无响应）。"""
        msg: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def _send(self, msg: dict) -> None:
        """写一行 JSON 到 server 的 stdin。"""
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        """从 server 的 stdout 读一行 JSON 响应。"""
        line = self.proc.stdout.readline()
        if not line:
            raise ConnectionError("MCP server closed stdout unexpectedly")
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # 可能是 server 的 stderr 混进来了，尝试继续读
            return self._recv()
