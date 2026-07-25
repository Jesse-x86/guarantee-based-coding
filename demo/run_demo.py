#!/usr/bin/env python3
"""GBC Demo Runner — interactive menu / CLI dual mode.

Usage:
  python demo/run_demo.py                             # no args → menu
  python demo/run_demo.py run config-service-strong   # run a named scenario
  python demo/run_demo.py list                        # list scenarios

Deps: pip install -r demo/requirements.txt
"""

import json
import sys
from pathlib import Path

# repo root
_gbc_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_gbc_root))


def _find_scenarios() -> list[dict]:
    """Scan demo/scenarios/ for valid scenario dirs."""
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
    """Rich table menu; user picks a number to run."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    console = Console()
    scenarios = _find_scenarios()

    console.print()
    console.print(Panel(
        Text("GBC Demo Runner — pick a scenario\n"
             "direct: [bold]python demo/run_demo.py run <name>[/bold]",
             style="white"),
        title="🛡️  Guarantee-Based Coding",
        title_align="left",
        border_style="cyan",
    ))

    if not scenarios:
        console.print("[yellow]No scenarios found.[/yellow]")
        return

    table = Table(title="Available scenarios")
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("Name", style="cyan bold")
    table.add_column("Project", style="white")
    table.add_column("Description", style="dim")

    for i, s in enumerate(scenarios, 1):
        table.add_row(str(i), s["name"], s["project"], s["desc"])

    console.print(table)
    console.print()

    n = len(scenarios)
    while True:
        try:
            choice = console.input(
                f"[bold cyan]Number to run[/bold cyan] [dim](1-{n})[/dim] [bold cyan]or q to quit:[/bold cyan] "
            ).strip()
            if choice.lower() in ("q", "quit", "exit", ""):
                console.print("[dim]Bye.[/dim]")
                return
            idx = int(choice) - 1
            if 0 <= idx < n:
                break
            console.print(f"[red]Enter a number between 1 and {n}.[/red]")
        except ValueError:
            console.print("[red]Enter a number.[/red]")
        except (KeyboardInterrupt, EOFError):
            console.print()
            return

    console.print()
    _run(scenarios[idx]["name"])


def _run(name: str) -> None:
    """Run one scenario by name."""
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
    """End-of-run summary line."""
    from rich.console import Console
    console = Console()
    console.print()
    gbc_v = result.get("gbc_verifies", [])
    if gbc_v:
        last = gbc_v[-1]
        stdout = last.get("stdout", "")
        if "GREEN" in stdout:
            console.print("[bold yellow]⚠️  Final verify green — test did not catch the regression.[/bold yellow]")
        elif "RED" in stdout:
            console.print("[bold green]🛡️  Final verify red — gate caught the regression.[/bold green]")
        else:
            console.print("[bold yellow]⚠️  Could not judge verify result.[/bold yellow]")
    console.print()


# ================================================================
# entry
# ================================================================

if __name__ == "__main__":
    if len(sys.argv) == 1:
        _interactive_menu()
    elif sys.argv[1] == "list":
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title="Available scenarios")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="dim")
        for s in _find_scenarios():
            table.add_row(s["name"], s["desc"])
        console.print(table)
    elif sys.argv[1] == "run" and len(sys.argv) >= 3:
        _run(sys.argv[2])
    else:
        print("Usage: python demo/run_demo.py                  # interactive menu")
        print("       python demo/run_demo.py list              # list scenarios")
        print("       python demo/run_demo.py run <scenario>    # run one")
        sys.exit(1)
