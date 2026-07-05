"""Rich 渲染：聊天气泡、diff、命令输出。"""

import difflib
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

console = Console()


def say_bubble(text: str, *, avatar: str = "🤖", color: str = "cyan") -> None:
    """渲染模拟 LLM 说话的聊天气泡。"""
    console.print()
    body = Panel(
        Text(text, style="white"),
        title=f"{avatar} LLM 说",
        title_align="left",
        border_style=color,
        padding=(0, 1),
    )
    console.print(body)


def render_diff(
    file: str, old_lines: List[str], new_lines: List[str], desc: str
) -> None:
    """渲染 unified diff 面板，模拟 LLM 编辑工具的输出。"""
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
        console.print(f"[dim]（{file} 无变化）[/dim]")
        return

    # 给 diff 行加颜色
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
        title=f"✏️  编辑: {desc}",
        title_align="left",
        border_style="yellow",
        padding=(0, 1),
    )
    console.print(body)


def render_gbc_start(cmd: List[str], desc: str) -> None:
    """渲染 GBC 命令开始。"""
    console.print()
    console.print(f"[bold blue]▸ gbc {' '.join(cmd)}[/bold blue]")
    console.print(f"[dim]  {desc}[/dim]")


def render_gbc_result(returncode: int, stdout: str, stderr: str) -> None:
    """渲染 GBC 命令结果。"""
    color = "green" if returncode == 0 else "red"
    status = "PASS" if returncode == 0 else "FAIL"
    console.print(f"[bold {color}]  ── {status} (exit {returncode}) ──[/bold {color}]")
    if stdout:
        console.print(Text(stdout.rstrip(), style="dim"))
    if stderr:
        console.print(Text(stderr.rstrip(), style="red"))


def divider() -> None:
    """步骤分隔线。"""
    console.print()
    console.print("─" * 60, style="dim")


def title(text: str) -> None:
    """大标题。"""
    console.print()
    console.print(f"[bold magenta]{'=' * 60}[/bold magenta]")
    console.print(f"[bold magenta]  {text}[/bold magenta]")
    console.print(f"[bold magenta]{'=' * 60}[/bold magenta]")
    console.print()


def summary(weak_passed: bool, strong_passed: bool) -> None:
    """终场总结。"""
    console.print()
    console.print("═" * 60, style="bold white")
    if weak_passed and not strong_passed:
        console.print("[bold green]  弱测试通过[/bold green]  [dim]|[/dim]  [bold red]强测试拦截[/bold red]")
        console.print()
        console.print("[italic dim]结论：测试覆盖了 edge path，门禁才能守住 edge path。[/italic dim]")
    elif not weak_passed:
        console.print("[bold yellow]  弱测试也未通过（测试可能有问题）[/bold yellow]")
    else:
        console.print("[bold yellow]  两个 scenario 都通过了（测试可能未覆盖改动路径）[/bold yellow]")
    console.print("═" * 60, style="bold white")
    console.print()
