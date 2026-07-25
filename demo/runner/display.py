"""Rich rendering: chat bubbles, diffs, command output."""

import difflib
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

console = Console()


def say_bubble(text: str, *, avatar: str = "🤖", color: str = "cyan") -> None:
    """Render a chat bubble as if an LLM were speaking."""
    console.print()
    body = Panel(
        Text(text, style="white"),
        title=f"{avatar} LLM",
        title_align="left",
        border_style=color,
        padding=(0, 1),
    )
    console.print(body)


def render_diff(
    file: str, old_lines: List[str], new_lines: List[str], desc: str
) -> None:
    """Render a unified-diff panel, mimicking an LLM edit tool."""
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file}",
            tofile=f"b/{file}",
            lineterm="",
        )
    )
    if not diff_lines:
        console.print(f"[dim]({file}: no change)[/dim]")
        return

    styled = []
    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            styled.append(f"[bold white]{line}[/bold white]")
        elif line.startswith("@@"):
            styled.append(f"[bold cyan]{line}[/bold cyan]")
        elif line.startswith("+"):
            styled.append(f"[green]{line}[/green]")
        elif line.startswith("-"):
            styled.append(f"[red]{line}[/red]")
        else:
            styled.append(f"[dim]{line}[/dim]")

    console.print()
    body = Panel(
        "\n".join(styled),
        title=f"✏️  Edit: {desc}",
        title_align="left",
        border_style="yellow",
        padding=(0, 1),
    )
    console.print(body)


def render_gbc_start(cmd: List[str], desc: str) -> None:
    """Render the start of a GBC command."""
    console.print()
    console.print(f"[bold blue]▸ gbc {' '.join(cmd)}[/bold blue]")
    console.print(f"[dim]  {desc}[/dim]")


def render_gbc_result(returncode: int, stdout: str, stderr: str) -> None:
    """Render a GBC command result."""
    color = "green" if returncode == 0 else "red"
    status = "PASS" if returncode == 0 else "FAIL"
    console.print(f"[bold {color}]  ── {status} (exit {returncode}) ──[/bold {color}]")
    if stdout:
        console.print(Text(stdout.rstrip(), style="dim"))
    if stderr:
        console.print(Text(stderr.rstrip(), style="red"))


def render_file(file: str, content: str, language: str, desc: str, *, highlight: str | None = None) -> None:
    """Render a source file with syntax highlighting."""
    console.print()
    title_text = f"📄 {file}"
    if highlight:
        title_text += f"  —  {highlight}"
    body = Panel(
        Syntax(content, language, theme="monokai", line_numbers=True),
        title=title_text,
        title_align="left",
        border_style="blue",
        padding=(0, 1),
    )
    console.print(body)
    if desc:
        console.print(f"[dim italic]  {desc}[/dim italic]")


def divider() -> None:
    """Step divider."""
    console.print()
    console.print("─" * 60, style="dim")


def title(text: str) -> None:
    """Section title."""
    console.print()
    console.print(f"[bold magenta]{'=' * 60}[/bold magenta]")
    console.print(f"[bold magenta]  {text}[/bold magenta]")
    console.print(f"[bold magenta]{'=' * 60}[/bold magenta]")
    console.print()


def summary(weak_passed: bool, strong_passed: bool) -> None:
    """End-of-run summary (legacy dual-scenario helper)."""
    console.print()
    console.print("═" * 60, style="bold white")
    if weak_passed and not strong_passed:
        console.print("[bold green]  Weak test passed[/bold green]  [dim]|[/dim]  [bold red]Strong test caught it[/bold red]")
        console.print()
        console.print("[italic dim]Takeaway: only edges your tests cover can the gate hold.[/italic dim]")
    elif not weak_passed:
        console.print("[bold yellow]  Weak test also failed (test may be broken)[/bold yellow]")
    else:
        console.print("[bold yellow]  Both scenarios passed (tests may not cover the edit path)[/bold yellow]")
    console.print("═" * 60, style="bold white")
    console.print()
