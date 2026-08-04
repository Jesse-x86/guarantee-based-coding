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

# app/interface/cli.py
"""GBC 命令行：human/agent 都能用的命令面，镜像 base 层能力（与 mcp 工具一一对应）。"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from gbc.app.config import project as project_config
from gbc.app.interface import base
from gbc.app.models.errors import (
    GBCError,
    IllegalOperationError,
    ConfigError,
    ExecutorError,
    GuaranteeError,
    GuaranteeTestFailedError,
    GuaranteeHasDependentsError,
)

# ======== App & Console ========

app = typer.Typer(help="cli.app.help")
guarantee_app = typer.Typer(help="cli.guarantee.help")
dep_app = typer.Typer(help="cli.dep.help")
verify_app = typer.Typer(help="cli.verify.help")
doctor_app = typer.Typer(help="cli.doctor.help")
executor_app = typer.Typer(help="cli.executor.help")

app.add_typer(guarantee_app, name="guarantee")
app.add_typer(dep_app, name="dep")
app.add_typer(verify_app, name="verify")
app.add_typer(doctor_app, name="doctor")
app.add_typer(executor_app, name="executor")

console = Console()


def _set_project(project: Optional[str]) -> None:
    """显式项目参数覆盖当前目标项目；省略时保留既有配置。"""
    if project is not None:
        project_config.set_current_project(project)


# ======== 全局语言入口 ========

@app.callback()
def _main(
    lang: Optional[str] = typer.Option(None, "--lang", help="cli.option.lang.help"),
):
    """在任何子命令执行前固定语言，使报错与提示都本地化。"""
    from gbc.app.i18n import set_lang, resolve_lang
    set_lang(resolve_lang(lang))


# ======== i18n 帮助文本延迟翻译 ========

import sys as _sys


def _lang_from_argv():
    """从 sys.argv 抓 --lang 值；没有或值非法则返回 None。

    处理 --help 是 eager option 的场景：Click 在 --help 触发时可能尚未解析 --lang
    （eager pass 优先），此时 ctx.params 里没有 lang。只好退而求其次扫 argv。

    支持两种语法：`--lang zh`（分两 token）与 `--lang=zh`（合在一 token）。
    """
    for i, arg in enumerate(_sys.argv):
        if arg == "--lang" and i + 1 < len(_sys.argv):
            val = _sys.argv[i + 1]
            if val and not val.startswith("-"):
                return val
            return None
        if arg.startswith("--lang="):
            val = arg.split("=", 1)[1]
            if val and not val.startswith("-"):
                return val
            return None
    return None


# ======== Help i18n: save / translate / render / restore ========

def _snapshot_tree_helps(node):
    """深度保存 Click 节点树所有 .help 属性，返回可还原的快照 dict。

    覆盖：(a) 节点自身的 .help  (b) 所有 param(Argument/Option) 的 .help
    (c) 所有子命令(递归)。
    """
    snap: dict = {"_help": node.help if hasattr(node, "help") else None}
    if hasattr(node, "params"):
        snap["_params"] = [p.help for p in node.params]
    else:
        snap["_params"] = []
    if hasattr(node, "commands"):
        snap["_subs"] = {name: _snapshot_tree_helps(cmd) for name, cmd in node.commands.items()}
    else:
        snap["_subs"] = {}
    return snap


def _restore_tree_helps(node, snap):
    """从快照恢复 Click 节点树的全部 .help 属性（_snapshot_tree_helps 的逆操作）。"""
    if snap is None:
        return
    if hasattr(node, "help") and snap.get("_help") is not None:
        node.help = snap["_help"]
    if hasattr(node, "params"):
        saved_params = snap.get("_params", [])
        for i, p in enumerate(node.params):
            if i < len(saved_params):
                p.help = saved_params[i]
    if hasattr(node, "commands"):
        saved_subs = snap.get("_subs", {})
        for name, cmd in node.commands.items():
            if name in saved_subs:
                _restore_tree_helps(cmd, saved_subs[name])


def _translate_tree_helps(node):
    """深度遍历 Click 节点树，把 i18n key 翻译成当前语言串（原地改写 .help）。

    覆盖 Group/Command 的 .help 与 Parameter(Argument/Option) 的 .help。
    非 key（如硬编码中文）由 t() 原样返回，不会被误翻。
    """
    from gbc.app.i18n import t

    if hasattr(node, "help") and node.help is not None and isinstance(node.help, str):
        translated = t(node.help)
        if translated != node.help:
            node.help = translated

    if hasattr(node, "params"):
        for param in node.params:
            if param.help is not None and isinstance(param.help, str):
                translated = t(param.help)
                if translated != param.help:
                    param.help = translated

    if hasattr(node, "commands"):
        for cmd in node.commands.values():
            _translate_tree_helps(cmd)


def i18n_wrap_click_tree(root):
    """给 Click 命令树的每个节点注入 get_help 包装：求助时临时翻译 → 渲染 → 恢复。

    不永久改写 Click 的 .help 属性——只在 get_help() 调用期间临时翻译，
    finally 恢复原始 i18n key。这避免了「同一进程内语言被首次请求锁死」的问题。

    解决 Typer/Click help 字符串是模块加载时求值、而语言要到运行时才确定的矛盾。
    """
    from gbc.app.i18n import resolve_lang, set_lang

    def _wrap_node(node):
        orig_get_help = node.get_help

        def translated_get_help(ctx):
            # 语言可能已由 _main callback 设置；若未设置(例如根 --help 绕过了 callback)
            # 则从 argv / env / locale 自判。
            explicit = _lang_from_argv()
            set_lang(resolve_lang(explicit))

            # 保存 → 翻译 → 渲染 → 恢复（保证 finally 恢复，不泄漏）
            snap = _snapshot_tree_helps(node)
            try:
                _translate_tree_helps(node)
                return orig_get_help(ctx)
            finally:
                _restore_tree_helps(node, snap)

        node.get_help = translated_get_help

        if hasattr(node, "commands"):
            for cmd in node.commands.values():
                _wrap_node(cmd)

    _wrap_node(root)


# ======== Error Handling ========

def handle_error(e: Exception) -> typer.Exit:
    """统一异常处理，返回 typer.Exit 供 raise 使用。消息经 i18n 本地化。"""
    from gbc.app.i18n import t
    if isinstance(e, IllegalOperationError):
        console.print(f"[bold red]{t('err.illegal_operation', msg=str(e))}[/bold red]")
    elif isinstance(e, GuaranteeTestFailedError):
        console.print(f"[bold red]{t('err.test_failed', guarantee=e.guarantee_path, target=e.target_file)}[/bold red]")
        if e.failure_info:
            console.print(f"[dim]{e.failure_info}[/dim]")
    elif isinstance(e, GuaranteeHasDependentsError):
        console.print(f"[bold red]{t('err.retire_blocked', msg=str(e))}[/bold red]")
    elif isinstance(e, GuaranteeError):
        console.print(f"[bold yellow]{t('err.guarantee', msg=str(e))}[/bold yellow]")
    elif isinstance(e, ConfigError):
        console.print(f"[bold red]{t('err.config', msg=str(e))}[/bold red]")
    elif isinstance(e, ExecutorError):
        console.print(f"[bold red]{t('err.executor', msg=str(e))}[/bold red]")
    elif isinstance(e, GBCError):
        console.print(f"[bold red]{t('err.generic', msg=str(e))}[/bold red]")
    else:
        console.print(f"[bold red]{t('err.unexpected', kind=type(e).__name__, msg=str(e))}[/bold red]")
    return typer.Exit(code=1)


# ======== Guarantee Commands ========

@guarantee_app.command("create")
def guarantee_create(
    provider: str = typer.Argument(..., help="cli.arg.provider_offering"),
    id: str = typer.Argument(..., help="cli.guarantee.create.arg.id"),
    test: str = typer.Argument(..., help="cli.guarantee.create.arg.test"),
    executor: str = typer.Argument(..., help="cli.guarantee.create.arg.executor"),
    desc: str = typer.Argument(..., help="cli.guarantee.create.arg.desc"),
    heavy: int = typer.Option(0, "--heavy", "-H", help="cli.guarantee.create.opt.heavy"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="cli.option.timeout"),
    disabled: bool = typer.Option(False, "--disabled", help="cli.guarantee.create.opt.disabled"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """新建一条保证。出生即绿：当场跑测试，不过则拒绝。--disabled 则跳过门禁建占位。"""
    try:
        _set_project(project)
        base.create_guarantee(provider, id, desc, test, executor, heavy, timeout, disabled)
        if disabled:
            console.print(f"[yellow]✔[/yellow] Created [bold]{id}[/bold] [DISABLED placeholder] — enable it once the test passes")
        else:
            console.print(f"[green]✔[/green] Created [bold]{id}[/bold] on [bold]{provider}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("update")
def guarantee_update(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    id: str = typer.Argument(..., help="cli.arg.guarantee_id"),
    desc: Optional[str] = typer.Option(None, "--desc", help="cli.guarantee.update.opt.desc"),
    test: Optional[str] = typer.Option(None, "--test", help="cli.guarantee.update.opt.test"),
    executor: Optional[str] = typer.Option(None, "--executor", help="cli.guarantee.update.opt.executor"),
    heavy: Optional[int] = typer.Option(None, "--heavy", "-H", help="cli.guarantee.update.opt.heavy"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="cli.guarantee.update.opt.timeout"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """更新保证字段。改了测试/执行方式会重新跑门禁。"""
    try:
        _set_project(project)
        base.update_guarantee(
            provider, id, desc=desc, test=test, executor_name=executor,
            heavy=heavy, timeout_override=timeout,
        )
        console.print(f"[green]✔[/green] Updated [bold]{id}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("retire")
def guarantee_retire(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    id: str = typer.Argument(..., help="cli.guarantee.retire.arg.id"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """退休一条保证。仍有 dependents 则拒绝（退休保护）。"""
    try:
        _set_project(project)
        base.retire_guarantee(provider, id)
        console.print(f"[yellow]✔[/yellow] Retired [bold]{id}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("disable")
def guarantee_disable(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    id: str = typer.Argument(..., help="cli.guarantee.disable.arg.id"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """停用一条保证：保留 id 与全部边，暂缓门禁/批量 verify。停用 ≠ 退休，不删任何东西。"""
    try:
        _set_project(project)
        base.disable_guarantee(provider, id)
        console.print(f"[yellow]✔[/yellow] Disabled [bold]{id}[/bold] — edges kept; enable to re-prove")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("enable")
def guarantee_enable(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    id: str = typer.Argument(..., help="cli.guarantee.enable.arg.id"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """恢复一条停用保证：当场补跑门禁(born-green)，过了才转正；不过则保持停用。"""
    try:
        _set_project(project)
        base.enable_guarantee(provider, id)
        console.print(f"[green]✔[/green] Enabled [bold]{id}[/bold]")
    except Exception as e:
        raise handle_error(e)


@guarantee_app.command("list")
def guarantee_list(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """列出 provider 提供的所有保证及其 dependents。"""
    try:
        _set_project(project)
        data = base.list_provides(provider)
        if not data:
            console.print("[dim]No guarantees.[/dim]")
            return
        table = Table(title=f"Provides → {provider}")
        table.add_column("id", style="cyan", no_wrap=True)
        table.add_column("state", justify="center")
        table.add_column("heavy", justify="center")
        table.add_column("dependents", justify="center")
        table.add_column("desc", style="white")
        for gid, g in data.items():
            state = "[magenta]DISABLED[/magenta]" if g.disabled else "[green]on[/green]"
            table.add_row(gid, state, str(g.heavy), str(len(g.dependents)), g.desc)
        console.print(table)
    except Exception as e:
        raise handle_error(e)


# ======== Dependency Commands ========

@dep_app.command("add")
def dep_add(
    consumer: str = typer.Argument(..., help="cli.dep.arg.consumer"),
    provider: str = typer.Argument(..., help="cli.dep.arg.provider"),
    symbol: str = typer.Argument(..., help="cli.dep.arg.symbol"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="cli.dep.add.opt.guarantee"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """登记 consumer 对 provider 的依赖（行为级会双向写）。"""
    try:
        _set_project(project)
        base.add_dependency(consumer, provider, symbol, guarantee)
        console.print(f"[green]✔[/green] {consumer} → {provider}:{symbol}" + (f" [{guarantee}]" if guarantee else " (free)"))
    except Exception as e:
        raise handle_error(e)


@dep_app.command("remove")
def dep_remove(
    consumer: str = typer.Argument(..., help="cli.dep.arg.consumer"),
    provider: str = typer.Argument(..., help="cli.dep.arg.provider"),
    symbol: str = typer.Argument(..., help="cli.dep.arg.symbol"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="cli.dep.remove.opt.guarantee"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """撤销依赖边（维护双向一致）。"""
    try:
        _set_project(project)
        base.remove_dependency(consumer, provider, symbol, guarantee)
        console.print(f"[yellow]✔[/yellow] removed {consumer} → {provider}:{symbol}")
    except Exception as e:
        raise handle_error(e)


@dep_app.command("of")
def dep_of(
    consumer: str = typer.Argument(..., help="cli.dep.arg.consumer"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """列出某文件声明的全部依赖边。"""
    try:
        _set_project(project)
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
    provider: str = typer.Argument(..., help="cli.dep.arg.provider"),
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="cli.dep.who.opt.symbol"),
    guarantee: Optional[str] = typer.Option(None, "--guarantee", "-g", help="cli.dep.who.opt.guarantee"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """反查谁依赖 provider（取代手工 grep）。"""
    try:
        _set_project(project)
        result = base.who_depends_on(provider, symbol=symbol, guarantee_id=guarantee)
        console.print_json(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        raise handle_error(e)


# ======== Verify Commands ========

@verify_app.command("provider")
def verify_provider(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    max_heavy: int = typer.Option(0, "--max-heavy", "-H", help="cli.verify.provider.opt.max_heavy"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="cli.option.timeout"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """验证 provider 的所有保证，按 heavy 阈值跳过并三桶汇总。"""
    try:
        _set_project(project)
        s = base.verify_provider(provider, auto_run_max_heavy=max_heavy, timeout=timeout)
        light = "[green]GREEN[/green]" if s.green else "[red]RED[/red]"
        console.print(f"{light}  passed={len(s.passed)} failed={len(s.failed)} skipped={len(s.skipped)}")
        if s.failed:
            console.print(f"[red]failed:[/red] {', '.join(s.failed)}")
        disabled = [sk for sk in s.skipped if sk.reason == "disabled"]
        heavy_sk = [sk for sk in s.skipped if sk.reason != "disabled"]
        if heavy_sk:
            tags = ", ".join(f"{sk.id}(heavy={sk.heavy})" for sk in heavy_sk)
            console.print(f"[yellow]{len(heavy_sk)} heavy skipped:[/yellow] {tags}")
        if disabled:
            tags = ", ".join(sk.id for sk in disabled)
            console.print(f"[magenta]{len(disabled)} DISABLED (born-green suspended):[/magenta] {tags}")
    except Exception as e:
        raise handle_error(e)


@verify_app.command("single")
def verify_single(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    id: str = typer.Argument(..., help="cli.arg.guarantee_id"),
    timeout: int = typer.Option(-1, "--timeout", "-t", help="cli.option.timeout"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="cli.verify.single.opt.verbose"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """点名验证单条保证——无视 heavy，永远跑。"""
    try:
        _set_project(project)
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


# ======== Refactor ========

refactor_app = typer.Typer(help="cli.refactor.help")
app.add_typer(refactor_app, name="refactor")


@refactor_app.command("file")
def refactor_file_cmd(
    old: str = typer.Argument(..., help="cli.refactor.file.arg.old"),
    new: str = typer.Argument(..., help="cli.refactor.file.arg.new"),
    no_disable: bool = typer.Option(False, "--no-disable", help="cli.refactor.file.opt.no_disable"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """移动文件/目录 + 它的 .gbc 产物，全图重写路径引用，并自动停用被移动方的保证。

    id 不动(路径无关)。移动是幂等的：已手动搬走则只收尾图引用。改完逐个 enable。
    """
    try:
        _set_project(project)
        report = base.refactor_file(old, new, disable_guarantees=not no_disable)
        console.print(f"[green]✔[/green] {report['old']} → {report['new']}")
        console.print(
            f"  code={report['code_move']}  gbc={report['gbc_move']}  "
            f"refs_rewritten={report['refs_rewritten']}  md_refs={report['md_refs_rewritten']}  "
            f"disabled={len(report['disabled'])}"
        )
        if report["disabled"]:
            ids = ", ".join(d["guarantee"] for d in report["disabled"])
            console.print(f"[magenta]disabled (enable after fixing tests):[/magenta] {ids}")
        console.print(f"[dim]{report['next_steps']}[/dim]")
    except Exception as e:
        raise handle_error(e)


@refactor_app.command("rename-id")
def refactor_rename_id_cmd(
    provider: str = typer.Argument(..., help="cli.arg.provider_offering"),
    old_id: str = typer.Argument(..., help="cli.refactor.rename_id.arg.old_id"),
    new_id: str = typer.Argument(..., help="cli.refactor.rename_id.arg.new_id"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """保证 id 改名(双向同步消费者)。用于把带路径前缀的旧 id 归一成 <symbol>.<behavior>。"""
    try:
        _set_project(project)
        rep = base.rename_guarantee(provider, old_id, new_id)
        console.print(f"[green]✔[/green] {rep['old_id']} → {rep['new_id']}  (consumers: {len(rep['consumers_updated'])})")
    except Exception as e:
        raise handle_error(e)


@refactor_app.command("func")
def refactor_func_cmd(
    provider: str = typer.Argument(..., help="cli.arg.source_file"),
    old_symbol: str = typer.Argument(..., help="cli.refactor.func.arg.old_symbol"),
    new_symbol: str = typer.Argument(..., help="cli.refactor.func.arg.new_symbol"),
    no_disable: bool = typer.Option(False, "--no-disable", help="cli.refactor.func.opt.no_disable"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """符号改名:改消费者 symbol 字段 + 该符号名下的保证 id，自动停用。源码 def/调用处由 AI 改。"""
    try:
        _set_project(project)
        rep = base.refactor_func(provider, old_symbol, new_symbol, disable_guarantees=not no_disable)
        console.print(f"[green]✔[/green] {provider}:{rep['old_symbol']} → {rep['new_symbol']}")
        console.print(f"  symbol_refs={rep['symbol_refs_rewritten']}  md_refs={rep['md_refs_rewritten']}  ids_renamed={len(rep['ids_renamed'])}  disabled={len(rep['disabled'])}")
        console.print(f"[dim]{rep['next_steps']}[/dim]")
    except Exception as e:
        raise handle_error(e)


# ======== Tree ========

@app.command("tree", help="cli.tree.help")
def tree_cmd(
    detail: bool = typer.Option(False, "--detail", "-d", help="cli.tree.option.detail"),
    gaps: bool = typer.Option(False, "--gaps", "-g", help="cli.tree.option.gaps"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """把整棵 .gbc 渲染成一份 AI 可读的依赖树（gbc.md 意图为骨 + json 依赖边）。"""
    try:
        _set_project(project)
        # 用 print 而非 console.print：树里有 [意图]/[保证] 等方括号，避免被 rich 当样式标记解析。
        print(base.render_tree(detail=detail, gaps=gaps))
    except Exception as e:
        raise handle_error(e)


# ======== Doctor ========

@doctor_app.command("check")
def doctor_check(
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """全局一致性体检：悬空引用 + 双向边漂移 + 停用保证(响亮报出)。"""
    try:
        _set_project(project)
        violations = base.check_consistency()
        if not violations:
            console.print("[green]✔ consistent[/green]")
            return
        disabled_types = {"disabled_guarantee", "depends_on_disabled"}
        errors = [v for v in violations if v["type"] not in disabled_types]
        notices = [v for v in violations if v["type"] in disabled_types]
        if errors:
            console.print(f"[red]✘ {len(errors)} error(s):[/red]")
            console.print_json(json.dumps(errors, ensure_ascii=False))
        if notices:
            console.print(f"[magenta]⊘ {len(notices)} disabled notice(s) (not errors, but loud until enabled):[/magenta]")
            console.print_json(json.dumps(notices, ensure_ascii=False))
    except Exception as e:
        raise handle_error(e)


# ======== Executor Commands ========

@executor_app.command("upsert")
def executor_upsert(
    config_name: str = typer.Argument(..., help="cli.executor.upsert.arg.config_name"),
    config_json: Optional[str] = typer.Option(None, "--json", "-j", help="cli.executor.upsert.opt.json"),
    config_file: Optional[Path] = typer.Option(None, "--file", "-f", help="cli.executor.upsert.opt.file"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="cli.option.project"),
):
    """更新或插入一个执行器配置。通过 --json 或 --file 提供配置数据。"""
    data = _parse_executor_input(config_json, config_file)
    try:
        _set_project(project)
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
