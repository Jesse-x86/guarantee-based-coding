"""模拟 LLM 工具：say / edit（带 diff） / gbc。"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from .display import (
    say_bubble,
    render_diff,
    render_gbc_start,
    render_gbc_result,
)


def tool_say(text: str) -> None:
    """模拟 LLM 说话。"""
    say_bubble(text)


def tool_edit(workspace: Path, file: str, edits: List[dict], desc: str) -> None:
    """模拟 LLM 的精确编辑工具。

    对每个 edit 做 oldText → newText 替换（只替换第一次出现），
    并渲染彩色 unified diff 让用户看到改了什么。
    """
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
                f"oldText 未在 {file} 中找到。\n"
                f"  查找内容: {old_text[:80]}..."
            )
        current = current.replace(old_text, new_text, 1)

    # 渲染 diff
    render_diff(
        file,
        original.splitlines(keepends=True),
        current.splitlines(keepends=True),
        desc,
    )

    # 写回
    path.write_text(current, encoding="utf-8")


def tool_gbc(gbc_root: Path, workspace: Path, cmd: List[str], desc: str) -> dict:
    """模拟 LLM 调用 GBC CLI。

    gbc_root 是 GBC 工具仓根目录（app/ 所在位置）。
    workspace 是 demo 工作区（GBC_PROJECT_PATH 指向它）。
    cmd 是 typer 子命令参数列表。

    返回 {"returncode": int, "stdout": str, "stderr": str}。
    """
    render_gbc_start(cmd, desc)

    env = os.environ.copy()
    env["GBC_PROJECT_PATH"] = str(workspace)
    env["PYTHONPATH"] = str(gbc_root / "app") + (
        ":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else ""
    )

    full_cmd = [
        sys.executable,
        "-m", "app.interface.cli",
        *cmd,
    ]

    proc = subprocess.run(
        full_cmd,
        cwd=str(gbc_root),
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )

    render_gbc_result(proc.returncode, proc.stdout, proc.stderr)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
