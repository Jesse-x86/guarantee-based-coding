"""执行引擎：读 JSON 剧本 → 搭建 workspace → 逐步执行。"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

from .display import divider, title
from .tools import tool_say, tool_edit, tool_gbc


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
    """读取并执行一个演示剧本。"""

    def __init__(self, demo_root: Path, gbc_root: Path):
        self.demo_root = demo_root
        self.gbc_root = gbc_root
        self.workspace = demo_root / "workspace"

    # ==================================================================
    # 公共入口
    # ==================================================================

    def run(self, scenario_name: str) -> dict:
        """运行指定 scenario，返回执行结果摘要。

        自动注册 demo-pytest executor（幂等，不删除——留在 GBC 仓 executors.json 里）。
        """
        scenario_dir = self.demo_root / "scenarios" / scenario_name
        if not scenario_dir.is_dir():
            raise FileNotFoundError(f"Scenario 不存在: {scenario_dir}")

        scenario = self._load_scenario(scenario_dir / "scenario.json")
        scenario["_name"] = scenario_name

        title(scenario["name"])

        # 1. 搭建 workspace
        self._setup_workspace(scenario)

        # 2. 注册临时 executor（幂等，不删除）
        self._register_demo_executor()

        # 3. 逐步执行
        return self._run_steps(scenario)

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

        # tests（覆盖同名）
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
                if r.get("type") == "gbc" and "verify" in str(r.get("cmd", []))
            ],
        }

    def _execute_step(self, step: dict) -> dict:
        typ = step["type"]

        if typ == "say":
            tool_say(step["text"])
            return {"type": "say", "ok": True}

        elif typ == "edit":
            tool_edit(
                self.workspace,
                step["file"],
                step["edits"],
                step.get("desc", "编辑文件"),
            )
            return {"type": "edit", "ok": True}

        elif typ == "gbc":
            info = tool_gbc(
                self.gbc_root,
                self.workspace,
                step["cmd"],
                step.get("desc", ""),
            )
            return {
                "type": "gbc",
                "cmd": step["cmd"],
                "returncode": info["returncode"],
                "stdout": info["stdout"],
            }

        else:
            raise ValueError(f"未知 step 类型: {typ}")

    # ==================================================================
    # Executor 注册（幂等，不删除）
    # ==================================================================

    def _register_demo_executor(self) -> None:
        """通过 GBC CLI 注册 demo-pytest executor（幂等，重复调用无副作用）。

        sys.executable 自动适配当前 Python（跨平台）；cwd 指向 workspace。
        """
        import subprocess

        config_json = json.dumps({
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
        })

        # 直接调 subprocess（走 GBC 的 CLI，不引入 import 依赖）
        env = os.environ.copy()
        app_dir = str(self.gbc_root / "app")
        env["PYTHONPATH"] = app_dir + (
            ":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else ""
        )
        subprocess.run(
            [sys.executable, "-m", "app.interface.cli",
             "executor", "upsert", "demo-pytest",
             "--json", config_json],
            cwd=str(self.gbc_root),
            env=env,
            capture_output=True,
            stdin=subprocess.DEVNULL,
        )

    # ==================================================================
    # 工具
    # ==================================================================

    def _load_scenario(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
