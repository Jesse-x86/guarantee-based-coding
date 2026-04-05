# app/interface/cli.py

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
)
from app.models.verify import VerifyModel

# ======== App & Console ========

app = typer.Typer(help="GBC - Guarantee-Based Coding 命令行工具")
guarantee_app = typer.Typer(help="管理保证（Guarantee）的增删改查")
verify_app = typer.Typer(help="运行验证")
executor_app = typer.Typer(help="管理执行器配置")

app.add_typer(guarantee_app, name="guarantee")
app.add_typer(verify_app, name="verify")
app.add_typer(executor_app, name="executor")

console = Console()


# ======== Error Handling ========

def handle_error(e: Exception) -> typer.Exit:
    """统一异常处理，返回 typer.Exit 供 raise 使用"""
    if isinstance(e, IllegalOperationError):
        console.print(f"[bold red]Illegal operation:[/bold red] {e}")
    elif isinstance(e, GuaranteeTestFailedError):
        # 这个比较特殊，有 failure_info，单独格式化
        console.print(f"[bold red]Test failed:[/bold red] {e.guarantee_path} for {e.target_file}")
        if e.failure_info:
            console.print(f"[dim]{e.failure_info}[/dim]")
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

@guarantee_app.command("init")
def guarantee_init(
    provider: str = typer.Argument(..., help="源文件路径"),
    config: str = typer.Argument(..., help="执行器配置名称"),
):
    """为一个源文件初始化保证元数据"""
    try:
        base.initialize_guarantee(provider, config)
        console.print(f"[green]✔[/green] Initialized guarantee meta for [bold]{provider}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("register")
def guarantee_register(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="依赖该文件的目标文件"),
    path: str = typer.Argument(..., help="测试文件路径（插入执行器命令的关键字符串）"),
    spec: str = typer.Argument(..., help="保证的描述"),
):
    """注册一个新的保证。注册时会运行测试，测试不通过则拒绝注册。"""
    try:
        base.register_guarantee(provider, target, path, spec)
        console.print(f"[green]✔[/green] Registered [bold]{path}[/bold] for target [bold]{target}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("unregister")
def guarantee_unregister(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="目标文件"),
    path: str = typer.Argument(..., help="要注销的保证路径"),
):
    """注销一个指定的保证"""
    try:
        base.unregister_guarantee(provider, target, path)
        console.print(f"[yellow]✔[/yellow] Unregistered [bold]{path}[/bold] from target [bold]{target}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("erase")
def guarantee_erase(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="要清除所有保证的目标文件"),
):
    """清除某个 target 下的全部保证"""
    try:
        base.erase_all_guarantees(provider, target)
        console.print(f"[red]✘[/red] Erased all guarantees for target [bold]{target}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("list")
def guarantee_list(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: Optional[str] = typer.Argument(None, help="目标文件（不传则列出所有 target）"),
):
    """查看保证列表。指定 target 则只看该 target，不指定则看全部。"""
    try:
        if target:
            items = base.list_guarantees_of_one(provider, target)
            _print_guarantee_table(target, items)
        else:
            data = base.list_guarantees_of_all(provider)
            if not data:
                console.print("[dim]No guarantees found.[/dim]")
                return
            for t, items in data.items():
                _print_guarantee_table(t, items)
                console.print()  # 空行分隔
    except Exception as e:
        raise handle_error(e)


def _print_guarantee_table(target: str, items):
    """格式化打印一个 target 的保证列表"""
    table = Table(title=f"Guarantees → {target}")
    table.add_column("Path", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    for item in items:
        table.add_row(item.guarantee_path, item.guarantee_desc)
    console.print(table)


@guarantee_app.command("update")
def guarantee_update(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="目标文件"),
    path: str = typer.Argument(..., help="保证路径"),
    spec: str = typer.Argument(..., help="新的保证描述"),
):
    """更新一个保证的描述。更新时会运行测试，测试不通过则拒绝更新。"""
    try:
        base.update_guarantees(provider, target, path, spec)
        console.print(f"[green]✔[/green] Updated [bold]{path}[/bold]")
    except Exception as e:
        raise handle_error(e)


# ======== Verify Commands ========

@verify_app.command("all")
def verify_all(
    provider: str = typer.Argument(..., help="源文件路径"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时秒数，-1 使用默认值"),
    simple: bool = typer.Option(False, "--simple", "-s", help="只输出每个 target 的 pass/fail"),
):
    """验证该 provider 下所有 target 的所有保证"""
    try:
        if simple:
            results = base.verify_all_guarantees(provider, timeout=timeout, single_output=True)
            # results: dict[str, bool]
            _print_simple_results(results)
        else:
            results = base.verify_all_guarantees(provider, timeout=timeout, return_model=True)
            # results: dict[str, list[VerifyModel]]
            _print_full_results(results)
    except Exception as e:
        raise handle_error(e)


@verify_app.command("target")
def verify_target(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="目标文件"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时秒数"),
    simple: bool = typer.Option(False, "--simple", "-s", help="只输出 pass/fail"),
):
    """验证某个 target 的所有保证"""
    try:
        if simple:
            result = base.verify_all_guarantees_of_one_target(
                provider, target, timeout=timeout, single_output=True
            )
            # result: bool
            _print_pass_fail(target, result)
        else:
            results = base.verify_all_guarantees_of_one_target(
                provider, target, timeout=timeout, return_model=True
            )
            # results: list[VerifyModel]
            _print_verify_model_table(target, results)
    except Exception as e:
        raise handle_error(e)


@verify_app.command("single")
def verify_single(
    provider: str = typer.Argument(..., help="源文件路径"),
    target: str = typer.Argument(..., help="目标文件"),
    path: str = typer.Argument(..., help="保证路径"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="超时秒数"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示完整 stdout/stderr"),
):
    """验证单个保证"""
    try:
        result = base.verify_single_guarantee(provider, target, path, timeout=timeout, return_model=True)
        # result: VerifyModel
        passed = result.return_code == 0
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        console.print(f"{status}  {path}  (exit code: {result.return_code})")
        if verbose or not passed:
            if result.stdout:
                console.print(f"[dim]── stdout ──[/dim]\n{result.stdout.rstrip()}")
            if result.stderr:
                console.print(f"[dim]── stderr ──[/dim]\n{result.stderr.rstrip()}")
    except Exception as e:
        raise handle_error(e)


def _print_simple_results(results: dict[str, bool]):
    """打印 simple 模式的 verify all 结果"""
    for target, passed in results.items():
        _print_pass_fail(target, passed)


def _print_pass_fail(target: str, passed: bool):
    status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
    console.print(f"{status}  {target}")


def _print_full_results(results: dict[str, list[VerifyModel]]):
    """打印完整模式的 verify all 结果"""
    for target, models in results.items():
        _print_verify_model_table(target, models)
        console.print()


def _print_verify_model_table(target: str, models: list[VerifyModel]):
    """打印一个 target 的 VerifyModel 列表为 table"""
    table = Table(title=f"Verify → {target}")
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Exit Code", justify="center")
    table.add_column("stderr (truncated)", style="dim", max_width=80)

    for m in models:
        passed = m.return_code == 0
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        stderr_preview = (m.stderr or "")[:200].replace("\n", " ")
        table.add_row(status, str(m.return_code), stderr_preview)

    console.print(table)


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