# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""模拟 LLM 工具：say / edit（带 diff） / gbc（通过 MCP）。"""

import json
from pathlib import Path
from typing import Any

from .display import (
    say_bubble,
    render_diff,
    render_gbc_start,
    render_gbc_result,
    render_file,
)
from .mcp_client import McpClient


def tool_say(text: str) -> None:
    """模拟 LLM 说话。"""
    say_bubble(text)


def tool_show(workspace: Path, file: str, desc: str, *, highlight: str | None = None) -> None:
    """展示一个文件的内容（带语法高亮）。

    highlight: 可选的高亮行号或关键词（在面板标题中标注，不实际高亮代码）。
    """
    path = workspace / file
    if not path.exists():
        from rich.console import Console
        Console().print(f"[dim]（{file} 不存在）[/dim]")
        return
    content = path.read_text(encoding="utf-8")
    lang = _guess_language(file)
    render_file(file, content, lang, desc, highlight=highlight)


def tool_edit(workspace: Path, file: str, edits: list[dict], desc: str) -> None:
    """模拟 LLM 的精确编辑工具（oldText → newText 替换 + unified diff）。"""
    path = workspace / file
    if not path.exists():
        raise FileNotFoundError(f"编辑目标不存在: {path}")

    original = path.read_text(encoding="utf-8")
    current = original

    for e in edits:
        old_text = e["oldText"]
        new_text = e["newText"]
        if old_text not in current:
            raise ValueError(
                f"oldText 未在 {file} 中找到。"
            )
        current = current.replace(old_text, new_text, 1)

    render_diff(
        file,
        original.splitlines(keepends=True),
        current.splitlines(keepends=True),
        desc,
    )
    path.write_text(current, encoding="utf-8")


def tool_gbc(
    mcp: McpClient,
    tool: str,
    args: dict[str, Any],
    desc: str,
) -> dict[str, Any]:
    """通过 MCP 调用 GBC 工具。

    Args:
        mcp: McpClient 实例
        tool: MCP 工具名（如 "create_guarantee", "verify_provider"）
        args: 工具的关键字参数
        desc: 人类可读的描述

    Returns:
        {"returncode": int, "stdout": str, "stderr": str}
    """
    render_gbc_start([tool], desc)

    try:
        result_text = mcp.call_tool(tool, args)
        # 解析结果——MCP 工具返回的文本可能是 JSON error
        try:
            parsed = json.loads(result_text)
            if isinstance(parsed, dict) and "error" in parsed:
                render_gbc_result(1, "", parsed["error"])
                return {"returncode": 1, "stdout": "", "stderr": str(parsed["error"])}
        except (json.JSONDecodeError, TypeError):
            pass

        # verify_provider 的返回是 JSON 对象，提取 green 状态和摘要
        stdout = result_text
        if tool == "verify_provider":
            try:
                vdata = json.loads(result_text)
                passed = len(vdata.get("passed", []))
                failed = len(vdata.get("failed", []))
                skipped = len(vdata.get("skipped", []))
                green = vdata.get("green", failed == 0)
                stdout = (
                    f"{'GREEN' if green else 'RED'}  "
                    f"passed={passed} failed={failed} skipped={skipped}"
                )
                if failed:
                    stdout += f"\nfailed: {', '.join(vdata['failed'])}"
                    # 展示失败的测试原始输出
                    results = vdata.get("results", {})
                    for gid in vdata["failed"]:
                        r = results.get(gid, {})
                        detail = (r.get("stderr", "") + "\n" + r.get("stdout", "")).strip()
                        if detail:
                            # 截断过长的输出，保留关键部分
                            lines = detail.splitlines()
                            if len(lines) > 15:
                                detail = "\n".join(lines[-12:])
                                detail = f"...(省略前 {len(lines) - 12} 行)\n{detail}"
                            stdout += f"\n\n── {gid} ──\n{detail}"
            except (json.JSONDecodeError, TypeError):
                pass

        returncode = 0
        # 检查 stdout 中是否有 RED，或有 failed
        if tool == "verify_provider" and "RED" in stdout:
            returncode = 1

        render_gbc_result(returncode, stdout, "")
        return {"returncode": returncode, "stdout": stdout, "stderr": ""}
    except Exception as e:
        render_gbc_result(1, "", str(e))
        return {"returncode": 1, "stdout": "", "stderr": str(e)}


def _guess_language(filename: str) -> str:
    """从扩展名猜语言，给 Rich Syntax 用。"""
    ext = Path(filename).suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sh": "bash",
        ".sql": "sql",
    }.get(ext, "text")
