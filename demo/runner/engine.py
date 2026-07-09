"""执行引擎：读 JSON 剧本 → 搭建 workspace → 启动 MCP → 逐步执行。"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

from .display import divider, title
from .mcp_client import McpClient
from .tools import tool_say, tool_edit, tool_gbc, tool_show


def _copy_tree_content(src: Path, dst: Path) -> None:
    """递归复制目录内容，只复制文件内容不碰元数据/permission。"""
    os.makedirs(str(dst), exist_ok=True)
    for item in os.listdir(src):
        s = src / item
        d = dst / item
        if os.path.isdir(s):
            _copy_tree_content(s, d)
        else:
            shutil.copyfile(str(s), str(d))


class ScenarioRunner:
    """读取并执行一个演示剧本。通过 MCP server 与 GBC 通信。"""

    def __init__(self, demo_root: Path, gbc_root: Path):
        self.demo_root = demo_root
        self.gbc_root = gbc_root
        self.workspace = demo_root / "workspace"
        self._mcp: McpClient | None = None

    # ==================================================================
    # 公共入口
    # ==================================================================

    def run(self, scenario_name: str) -> dict:
        """运行指定 scenario。"""
        scenario_dir = self.demo_root / "scenarios" / scenario_name
        if not scenario_dir.is_dir():
            raise FileNotFoundError(f"Scenario 不存在: {scenario_dir}")

        scenario = self._load_scenario(scenario_dir / "scenario.json")
        scenario["_name"] = scenario_name

        title(scenario["name"])

        # 1. 搭建 workspace
        self._setup_workspace(scenario)

        # 2. 启动 MCP server
        self._start_mcp()

        try:
            # 3. 注册 executor（幂等）
            self._register_demo_executor()

            # 4. 逐步执行
            return self._run_steps(scenario)
        finally:
            self._stop_mcp()

    # ==================================================================
    # MCP 生命周期
    # ==================================================================

    def _start_mcp(self) -> None:
        """启动 GBC MCP server，通过 stdio 通信。"""
        serve_py = str(self.gbc_root / "serve.py")
        self._mcp = McpClient([sys.executable, serve_py, str(self.workspace)])

    def _stop_mcp(self) -> None:
        if self._mcp:
            self._mcp.close()
            self._mcp = None

    # ==================================================================
    # Workspace
    # ==================================================================

    def _setup_workspace(self, scenario: dict) -> None:
        """清空并重建 workspace。"""
        project_name = scenario["project"]
        scenario_name = scenario["_name"]

        project_dir = self.demo_root / "projects" / project_name
        scenario_dir = self.demo_root / "scenarios" / scenario_name

        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)

        # 源码
        for item in project_dir.iterdir():
            dst = self.workspace / item.name
            if item.is_dir():
                _copy_tree_content(item, dst)
            else:
                shutil.copyfile(str(item), str(dst))

        # tests
        scenario_tests = scenario_dir / "tests"
        if scenario_tests.is_dir():
            dst_tests = self.workspace / "tests"
            if dst_tests.exists():
                shutil.rmtree(dst_tests)
            _copy_tree_content(scenario_tests, dst_tests)

        # .gbc（若有预置）
        scenario_gbc = scenario_dir / ".gbc"
        if scenario_gbc.is_dir():
            dst_gbc = self.workspace / ".gbc"
            if dst_gbc.exists():
                shutil.rmtree(dst_gbc)
            _copy_tree_content(scenario_gbc, dst_gbc)

    # ==================================================================
    # 步骤执行
    # ==================================================================

    def _run_steps(self, scenario: dict) -> dict:
        delay = float(scenario.get("delay", 1.5))
        results: list[dict] = []
        for i, step in enumerate(scenario["steps"]):
            if i > 0:
                time.sleep(delay)
            divider()
            results.append(self._execute_step(step))

        return {
            "name": scenario["name"],
            "project": scenario["project"],
            "steps": len(results),
            "gbc_verifies": [
                r
                for r in results
                if r.get("type") == "gbc"
                and r.get("tool") == "verify_provider"
            ],
        }

    def _execute_step(self, step: dict) -> dict:
        typ = step["type"]

        if typ == "say":
            tool_say(step["text"])
            return {"type": "say", "ok": True}

        elif typ == "show":
            tool_show(
                self.workspace,
                step["file"],
                step.get("desc", ""),
                highlight=step.get("highlight"),
            )
            return {"type": "show", "ok": True}

        elif typ == "edit":
            tool_edit(
                self.workspace,
                step["file"],
                step["edits"],
                step.get("desc", "编辑文件"),
            )
            return {"type": "edit", "ok": True}

        elif typ == "gbc":
            assert self._mcp is not None
            tool_name = step.get("tool", step.get("cmd", [""])[0] if step.get("cmd") else "")
            tool_args = step.get("args", {})
            info = tool_gbc(
                self._mcp,
                tool_name,
                tool_args,
                step.get("desc", ""),
            )
            return {
                "type": "gbc",
                "tool": tool_name,
                "returncode": info["returncode"],
                "stdout": info["stdout"],
            }

        else:
            raise ValueError(f"未知 step 类型: {typ}")

    # ==================================================================
    # Executor 注册（通过 MCP）
    # ==================================================================

    def _register_demo_executor(self) -> None:
        """通过 MCP 注册 demo-pytest executor（幂等）。"""
        assert self._mcp is not None
        self._mcp.call_tool("upsert_executor", {
            "config_name": "demo-pytest",
            "config_data": {
                "command": [
                    sys.executable,
                    "-m", "pytest",
                    "{file}", "-x", "-q",
                ],
                "cwd": str(self.workspace),
                "timeout": 30,
                "env_ops": [
                    {"key": "PYTHONPATH", "action": "prepend", "value": str(self.workspace)},
                ],
            },
        })

    # ==================================================================
    # 工具
    # ==================================================================

    def _load_scenario(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
