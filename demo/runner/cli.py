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

"""Demo Runner CLI：列出和运行 GBC 演示剧本。"""

from pathlib import Path

import typer

app = typer.Typer(help="GBC Demo Runner — 运行演示剧本")

# 项目路径：demo/ 在 GBC 仓库根下
GBC_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_ROOT = GBC_ROOT / "demo"


@app.command("list")
def list_scenarios():
    """列出所有可用的演示剧本。"""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    scenarios_dir = DEMO_ROOT / "scenarios"
    if not scenarios_dir.is_dir():
        console.print("[yellow]scenarios/ 目录不存在[/yellow]")
        return

    table = Table(title="可用演示剧本")
    table.add_column("名称", style="cyan")
    table.add_column("项目", style="white")

    for d in sorted(scenarios_dir.iterdir()):
        if not d.is_dir():
            continue
        sj = d / "scenario.json"
        if not sj.exists():
            continue
        import json

        with open(sj, "r", encoding="utf-8") as f:
            data = json.load(f)
        table.add_row(d.name, data.get("project", "?"))

    console.print(table)


@app.command("run")
def run_scenario(
    name: str = typer.Argument(..., help="Scenario 名称，如 config-service-weak"),
):
    """运行一个演示剧本。"""
    from .engine import ScenarioRunner

    runner = ScenarioRunner(demo_root=DEMO_ROOT, gbc_root=GBC_ROOT)
    try:
        result = runner.run(name)
        _print_run_summary(result)
    except FileNotFoundError as e:
        from rich.console import Console
        Console().print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)


def _print_run_summary(result: dict) -> None:
    """打印终场总结。"""
    from rich.console import Console
    console = Console()
    console.print()
    gbc_v = result["gbc_verifies"]
    if gbc_v:
        last = gbc_v[-1]
        # verify 的 exit code 始终为 0（CLI 本身没 crash）；
        # 测试是否通过需要看 stdout 里是 GREEN 还是 RED
        stdout = last.get("stdout", "")
        if "GREEN" in stdout:
            console.print(
                "[bold yellow]⚠️ 最终验证通过——测试未能拦截回归。[/bold yellow]"
            )
        elif "RED" in stdout:
            console.print(
                "[bold green]🛡️ 最终验证失败——门禁成功拦截了回归！[/bold green]"
            )
        else:
            console.print(
                f"[bold yellow]⚠️ 无法判定验证结果（exit {last.get('returncode')}）[/bold yellow]"
            )
    console.print()
