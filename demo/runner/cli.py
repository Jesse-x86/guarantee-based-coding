"""Demo Runner CLI: list and run GBC demo scenarios."""

from pathlib import Path

import typer

app = typer.Typer(help="GBC Demo Runner — run demo scenarios")

# demo/ sits under the GBC repo root
GBC_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_ROOT = GBC_ROOT / "demo"


@app.command("list")
def list_scenarios():
    """List available demo scenarios."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    scenarios_dir = DEMO_ROOT / "scenarios"
    if not scenarios_dir.is_dir():
        console.print("[yellow]scenarios/ directory missing[/yellow]")
        return

    table = Table(title="Available scenarios")
    table.add_column("Name", style="cyan")
    table.add_column("Project", style="white")

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
    name: str = typer.Argument(..., help="Scenario name, e.g. config-service-weak"),
):
    """Run one demo scenario."""
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
    """Print end-of-run summary."""
    from rich.console import Console
    console = Console()
    console.print()
    gbc_v = result["gbc_verifies"]
    if gbc_v:
        last = gbc_v[-1]
        # verify's process exit is always 0 when the CLI itself did not crash;
        # pass/fail is read from GREEN/RED in stdout
        stdout = last.get("stdout", "")
        if "GREEN" in stdout:
            console.print(
                "[bold yellow]⚠️ Final verify green — test did not catch the regression.[/bold yellow]"
            )
        elif "RED" in stdout:
            console.print(
                "[bold green]🛡️ Final verify red — gate caught the regression.[/bold green]"
            )
        else:
            console.print(
                f"[bold yellow]⚠️ Could not judge verify result (exit {last.get('returncode')})[/bold yellow]"
            )
    console.print()
