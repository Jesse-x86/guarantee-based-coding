# app/interface/cli.py
"""GBC 命令行：human/agent 都能用的命令面，镜像 base 层能力（与 mcp 工具一一对应）。"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.interface import base
from app.models.errors import (
    GBCError,
    IllegalOperationError,
    ConfigError,
    ExecutorError,
    GuaranteeError,
    GuaranteeTestFailedError,
    GuaranteeHasDependentsError,
)

# ======== App & Console ========

app = typer.Typer(help="GBC - Guarantee-Based Coding 命令行工具")
guarantee_app = typer.Typer(help="保证（Guarantee）增删改查")
dep_app = typer.Typer(help="依赖边（Dependency）登记与反查")
verify_app = typer.Typer(help="运行验证")
doctor_app = typer.Typer(help="一致性体检")
executor_app = typer.Typer(help="管理执行器配置")

app.add_typer(guarantee_app, name="guarantee")
app.add_typer(dep_app, name="dep")
app.add_typer(verify_app, name="verify")
app.add_typer(doctor_app, name="doctor")
app.add_typer(executor_app, name="executor")

console = Console()


# ======== Error Handling ========

def handle_error(e: Exception) -> typer.Exit:
    """统一异常处理，返回 typer.Exit 供 raise 使用。"""
    if isinstance(e, IllegalOperationError):
        console.print(f"[bold red]Illegal operation:[/bold red] {e}")
    elif isinstance(e, GuaranteeTestFailedError):
        console.print(f"[bold red]Test failed:[/bold red] {e.guarantee_path} on {e.target_file}")
        if e.failure_info:
            console.print(f"[dim]{e.failure_info}[/dim]")
    elif isinstance(e, GuaranteeHasDependentsError):
        console.print(f"[bold red]Retire blocked:[/bold red] {e}")
    elif isinstance(e, GuaranteeError):
        console.print(f"[bold yellow]Guarantee error:[/bold yellow] {e}")
    elif isinstance(e, ConfigError):
        console.print(f"[bold red]Config error:[/bold red] {e}")
    elif isinstance(e, ExecutorError):
        console.print(f"[bold red]Executor error:[/bold red] {e}")
    elif isinstance(e, GBCError):
        console.print(f"[bold red]Error:[/bold red] {e}")
    else:
        console.print(f"[bold red]Unexpected error:[/bold red] {type(e).__name__}: {e}")
    return typer.Exit(code=1)


# ======== Guarantee Commands ========

@guarantee_app.command("create")
def guarantee_create(
    provider: str = typer.Argument(..., help="提供保证的源文件"),
    id: str = typer.Argument(..., help="具名保证 id，如 config.llm.get_model.returns_loaded"),
    test: str = typer.Argument(..., help="测试选择器（交给 executor 的 {file}）"),
    executor: str = typer.Argument(..., help="执行器配置名"),
    desc: str = typer.Argument(..., help="保证描述"),
    heavy: int = typer.Option(0, "--heavy", "-H", help="成本秩；>=1 批量跳过"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时覆写，-1 用默认"),
):
    """新建一条保证。出生即绿：当场跑测试，不过则拒绝。"""
    try:
        base.create_guarantee(provider, id, desc, test, executor, heavy, timeout)
        console.print(f"[green]✔[/green] Created [bold]{id}[/bold] on [bold]{provider}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("update")
def guarantee_update(
    provider: str = typer.Argument(..., help="源文件"),
    id: str = typer.Argument(..., help="保证 id"),
    desc: Optional[str] = typer.Option(None, "--desc", help="新描述"),
    test: Optional[str] = typer.Option(None, "--test", help="新测试选择器"),
    executor: Optional[str] = typer.Option(None, "--executor", help="新执行器"),
    heavy: Optional[int] = typer.Option(None, "--heavy", "-H", help="新成本秩"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="新超时覆写"),
):
    """更新保证字段。改了测试/执行方式会重新跑门禁。"""
    try:
        base.update_guarantee(
            provider, id, desc=desc, test=test, executor_name=executor,
            heavy=heavy, timeout_override=timeout,
        )
        console.print(f"[green]✔[/green] Updated [bold]{id}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("retire")
def guarantee_retire(
    provider: str = typer.Argument(..., help="源文件"),
    id: str = typer.Argument(..., help="要退休的保证 id"),
):
    """退休一条保证。仍有 dependents 则拒绝（退休保护）。"""
    try:
        base.retire_guarantee(provider, id)
        console.print(f"[yellow]✔[/yellow] Retired [bold]{id}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("list")
def guarantee_list(
    provider: str = typer.Argument(..., help="源文件"),
):
    """列出 provider 提供的所有保证及其 dependents。"""
    try:
        data = base.list_provides(provider)
        if not data:
            console.print("[dim]No guarantees.[/dim]")
            return
        table = Table(title=f"Provides → {provider}")
        table.add_column("id", style="cyan", no_wrap=True)
        table.add_column("heavy", justify="center")
        table.add_column("dependents", justify="center")
        table.add_column("desc", style="white")
        for gid, g in data.items():
            table.add_row(gid, str(g.heavy), str(len(g.dependents)), g.desc)
        console.print(table)
    except Exception as e:
        raise handle_error(e)


# ======== Dependency Commands ========

@dep_app.command("add")
def dep_add(
    consumer: str = typer.Argument(..., help="依赖方文件"),
    provider: str = typer.Argument(..., help="被依赖的源文件"),
    symbol: str = typer.Argument(..., help="provider 上的符号名"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="挂的保证 id；不给=免费 symbol 依赖"),
):
    """登记 consumer 对 provider 的依赖（行为级会双向写）。"""
    try:
        base.add_dependency(consumer, provider, symbol, guarantee)
        console.print(f"[green]✔[/green] {consumer} → {provider}:{symbol}" + (f" [{guarantee}]" if guarantee else " (free)"))
    except Exception as e:
        raise handle_error(e)


@dep_app.command("remove")
def dep_remove(
    consumer: str = typer.Argument(..., help="依赖方文件"),
    provider: str = typer.Argument(..., help="被依赖的源文件"),
    symbol: str = typer.Argument(..., help="provider 上的符号名"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="只摘这个保证；不给=撤整条 symbol 边"),
):
    """撤销依赖边（维护双向一致）。"""
    try:
        base.remove_dependency(consumer, provider, symbol, guarantee)
        console.print(f"[yellow]✔[/yellow] removed {consumer} → {provider}:{symbol}")
    except Exception as e:
        raise handle_error(e)


@dep_app.command("of")
def dep_of(
    consumer: str = typer.Argument(..., help="依赖方文件"),
):
    """列出某文件声明的全部依赖边。"""
    try:
        deps = base.list_depends_on(consumer)
        if not deps:
            console.print("[dim]No dependencies.[/dim]")
            return
        table = Table(title=f"Depends on ← {consumer}")
        table.add_column("symbol", style="cyan")
        table.add_column("guarantees", style="white")
        for d in deps:
            table.add_row(d.symbol, ", ".join(d.guarantees) if d.guarantees else "[dim](free)[/dim]")
        console.print(table)
    except Exception as e:
        raise handle_error(e)


@dep_app.command("who")
def dep_who(
    provider: str = typer.Argument(..., help="被依赖的源文件"),
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="收窄到某个符号"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="某保证 id（走 O(1) 反向边）"),
):
    """反查谁依赖 provider（取代手工 grep）。"""
    try:
        result = base.who_depends_on(provider, symbol=symbol, guarantee_id=guarantee)
        console.print_json(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        raise handle_error(e)


# ======== Verify Commands ========

@verify_app.command("provider")
def verify_provider(
    provider: str = typer.Argument(..., help="源文件"),
    max_heavy: int = typer.Option(0, "--max-heavy", "-H", help="批量只跑 heavy <= 该值"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时覆写"),
):
    """验证 provider 的所有保证，按 heavy 阈值跳过并三桶汇总。"""
    try:
        s = base.verify_provider(provider, auto_run_max_heavy=max_heavy, timeout=timeout)
        light = "[green]GREEN[/green]" if s.green else "[red]RED[/red]"
        console.print(f"{light}  passed={len(s.passed)} failed={len(s.failed)} skipped={len(s.skipped)}")
        if s.failed:
            console.print(f"[red]failed:[/red] {', '.join(s.failed)}")
        if s.skipped:
            tags = ", ".join(f"{sk.id}(heavy={sk.heavy})" for sk in s.skipped)
            console.print(f"[yellow]{len(s.skipped)} heavy skipped:[/yellow] {tags}")
    except Exception as e:
        raise handle_error(e)


@verify_app.command("single")
def verify_single(
    provider: str = typer.Argument(..., help="源文件"),
    id: str = typer.Argument(..., help="保证 id"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时覆写"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示完整 stdout/stderr"),
):
    """点名验证单条保证——无视 heavy，永远跑。"""
    try:
        result = base.verify_guarantee(provider, id, timeout=timeout)
        passed = result.return_code == 0
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        console.print(f"{status}  {id}  (exit {result.return_code})")
        if verbose or not passed:
            if result.stdout:
                console.print(f"[dim]── stdout ──[/dim]\n{result.stdout.rstrip()}")
            if result.stderr:
                console.print(f"[dim]── stderr ──[/dim]\n{result.stderr.rstrip()}")
    except Exception as e:
        raise handle_error(e)


# ======== Tree ========

@app.command("tree")
def tree_cmd(
    detail: bool = typer.Option(False, "--detail", "-d", help="展开保证 desc/test/heavy + 每个 .gbc 目录的其它产物(.pyi)"),
    gaps: bool = typer.Option(False, "--gaps", "-g", help="末尾附图反推的登记缺口(有 json/被依赖却未登记)"),
):
    """把整棵 .gbc 渲染成一份 AI 可读的依赖树（gbc.md 意图为骨 + json 依赖边）。"""
    try:
        # 用 print 而非 console.print：树里有 [意图]/[保证] 等方括号，避免被 rich 当样式标记解析。
        print(base.render_tree(detail=detail, gaps=gaps))
    except Exception as e:
        raise handle_error(e)


# ======== Doctor ========

@doctor_app.command("check")
def doctor_check():
    """全局一致性体检：悬空引用 + 双向边漂移。"""
    try:
        violations = base.check_consistency()
        if not violations:
            console.print("[green]✔ consistent[/green]")
            return
        console.print(f"[red]✘ {len(violations)} violation(s):[/red]")
        console.print_json(json.dumps(violations, ensure_ascii=False))
    except Exception as e:
        raise handle_error(e)


# ======== Executor Commands ========

@executor_app.command("upsert")
def executor_upsert(
    config_name: str = typer.Argument(..., help="执行器配置名称"),
    config_json: Optional[str] = typer.Option(None, "--json", "-j", help="JSON 字符串"),
    config_file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON 文件路径"),
):
    """更新或插入一个执行器配置。通过 --json 或 --file 提供配置数据。"""
    data = _parse_executor_input(config_json, config_file)
    try:
        base.upsert_executor(config_name, data)
        console.print(f"[green]✔[/green] Executor [bold]{config_name}[/bold] configured.")
    except Exception as e:
        raise handle_error(e)


def _parse_executor_input(config_json: Optional[str], config_file: Optional[Path]) -> dict:
    """解析执行器配置输入，返回 dict。失败则直接退出。"""
    if config_file:
        if not config_file.exists():
            console.print(f"[red]Error: file not found: {config_file}[/red]")
            raise typer.Exit(code=1)
        try:
            return json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            console.print(f"[red]Error: invalid JSON in file: {config_file}[/red]")
            raise typer.Exit(code=1)

    if config_json:
        try:
            return json.loads(config_json)
        except json.JSONDecodeError:
            console.print("[red]Error: invalid JSON string[/red]")
            raise typer.Exit(code=1)

    console.print("[yellow]Please provide --json or --file[/yellow]")
    raise typer.Exit(code=1)


# ======== Entry Point ========

if __name__ == "__main__":
    app()
