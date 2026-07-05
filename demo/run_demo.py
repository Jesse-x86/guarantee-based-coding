#!/usr/bin/env python3
"""GBC Demo Runner — 交互式菜单 / 命令行双模式。

用法：
  python demo/run_demo.py                          # 无参数 → 弹出菜单选择
  python demo/run_demo.py run config-service-strong  # 直接跑指定剧本
  python demo/run_demo.py list                        # 仅列出所有剧本

依赖：pip install -r requirements.txt
"""

import json
import sys
from pathlib import Path

# 确保 GBC 的 app/ 在 path 中
_gbc_root = Path(__file__).resolve().parent.parent
_app_dir = str(_gbc_root / "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
sys.path.insert(0, str(_gbc_root))


def _find_scenarios() -> list[dict]:
    """扫描 demo/scenarios/ 下所有有效剧本，返回 [{name, project, desc, steps}]。"""
    scenarios_dir = _gbc_root / "demo" / "scenarios"
    found: list[dict] = []
    if not scenarios_dir.is_dir():
        return found
    for d in sorted(scenarios_dir.iterdir()):
        if not d.is_dir():
            continue
        sj = d / "scenario.json"
        if not sj.exists():
            continue
        with open(sj, "r", encoding="utf-8") as f:
            data = json.load(f)
        found.append({
            "name": d.name,
            "project": data.get("project", "?"),
            "desc": data.get("name", ""),
            "steps": len(data.get("steps", [])),
        })
    return found


def _interactive_menu() -> None:
    """弹出一个 Rich 表格菜单，用户选号执行。"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    console = Console()
    scenarios = _find_scenarios()

    console.print()
    console.print(Panel(
        Text("GBC Demo Runner — 选择要运行的演示剧本\n"
             "直接执行: [bold]python demo/run_demo.py run <name>[/bold]",
             style="white"),
        title="🛡️  Guarantee-Based Coding",
        title_align="left",
        border_style="cyan",
    ))

    if not scenarios:
        console.print("[yellow]没有找到可用剧本。[/yellow]")
        return

    table = Table(title="可用演示剧本")
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("名称", style="cyan bold")
    table.add_column("项目", style="white")
    table.add_column("描述", style="dim")

    for i, s in enumerate(scenarios, 1):
        table.add_row(str(i), s["name"], s["project"], s["desc"])

    console.print(table)
    console.print()

    # 选号
    while True:
        try:
            choice = console.input(
                "[bold cyan]输入序号运行[/bold cyan] [dim](1-{})[/dim] [bold cyan]或 q 退出:[/bold cyan] ".format(
                    len(scenarios)
                )
            ).strip()
            if choice.lower() in ("q", "quit", "exit", ""):
                console.print("[dim]退出。[/dim]")
                return
            idx = int(choice) - 1
            if 0 <= idx < len(scenarios):
                break
            console.print(f"[red]请输入 1 到 {len(scenarios)} 之间的数字。[/red]")
        except ValueError:
            console.print("[red]请输入数字。[/red]")
        except (KeyboardInterrupt, EOFError):
            console.print()
            return

    console.print()
    _run(scenarios[idx]["name"])


def _run(name: str) -> None:
    """直接跑一个剧本。"""
    from demo.runner.engine import ScenarioRunner

    runner = ScenarioRunner(
        demo_root=_gbc_root / "demo",
        gbc_root=_gbc_root,
    )
    try:
        result = runner.run(name)
        _print_summary(result)
    except FileNotFoundError as e:
        from rich.console import Console
        Console().print(f"[red]{e}[/red]")
        sys.exit(1)


def _print_summary(result: dict) -> None:
    """终场总结。"""
    from rich.console import Console
    console = Console()
    console.print()
    gbc_v = result.get("gbc_verifies", [])
    if gbc_v:
        last = gbc_v[-1]
        stdout = last.get("stdout", "")
        if "GREEN" in stdout:
            console.print("[bold yellow]⚠️  最终验证通过 — 测试未能拦截回归。[/bold yellow]")
        elif "RED" in stdout:
            console.print("[bold green]🛡️  最终验证失败 — 门禁成功拦截了回归！[/bold green]")
        else:
            console.print(f"[bold yellow]⚠️  无法判定验证结果。[/bold yellow]")
    console.print()


# ================================================================
# 入口
# ================================================================

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 无参数 → 交互菜单
        _interactive_menu()
    elif sys.argv[1] == "list":
        # 纯列表
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title="可用演示剧本")
        table.add_column("名称", style="cyan")
        table.add_column("描述", style="dim")
        for s in _find_scenarios():
            table.add_row(s["name"], s["desc"])
        console.print(table)
    elif sys.argv[1] == "run" and len(sys.argv) >= 3:
        # run <name>
        _run(sys.argv[2])
    else:
        print("用法: python demo/run_demo.py                  # 交互菜单")
        print("      python demo/run_demo.py list              # 列出剧本")
        print("      python demo/run_demo.py run <scenario>    # 直接跑")
        sys.exit(1)
