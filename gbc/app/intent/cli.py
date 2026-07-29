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

"""意图文档(gbc.md)的 CLI 表面 —— 薄。

`gbc doc <command>`。只做参数收集 → 调 intent.base → 渲染;不碰磁盘、不解析路径。
"""
from typing import Optional

import typer
from rich.console import Console

from gbc.app.intent import base

doc_app = typer.Typer(help="意图文档（gbc.md）的合规读写入口")
console = Console()


def _gbc_root(project: Optional[str]):
    """确定作用的项目根:显式 project > 当前 GBC 目标项目。"""
    if project:
        gbc_root, _ = base.resolve_gbc(project)
        return gbc_root
    from gbc.app.config.project import get_current_project
    gbc_root, _ = base.resolve_gbc(str(get_current_project()))
    return gbc_root


@doc_app.command("show")
def doc_show(
    folder: str = typer.Argument("", help="项目相对文件夹路径，根用空串"),
    project: Optional[str] = typer.Option(None, "--project", "-C", help="目标项目根；省略则用当前项目"),
):
    """查看文件夹的意图 / 约束 / 条目。"""
    print(base.show(_gbc_root(project), folder))


@doc_app.command("set-intent")
def doc_set_intent(
    folder: str = typer.Argument(...),
    text: str = typer.Argument(...),
    project: Optional[str] = typer.Option(None, "--project", "-C"),
):
    """设文件夹意图（自动单源投影到父文档条目）。"""
    for p in base.set_intent(_gbc_root(project), folder, text):
        console.print(f"[green]written:[/green] {p}")


@doc_app.command("set-constraints")
def doc_set_constraints(
    folder: str = typer.Argument(...),
    text: str = typer.Argument(...),
    project: Optional[str] = typer.Option(None, "--project", "-C"),
):
    """设文件夹的内部约束（只活在本地，不冒泡到父节点）。"""
    for p in base.set_constraints(_gbc_root(project), folder, text):
        console.print(f"[green]written:[/green] {p}")


@doc_app.command("set-file")
def doc_set_file(
    folder: str = typer.Argument(...),
    name: str = typer.Argument(...),
    desc: str = typer.Argument(...),
    project: Optional[str] = typer.Option(None, "--project", "-C"),
):
    """新增/更新一个文件条目（name 不带 /）。"""
    for p in base.set_file(_gbc_root(project), folder, name, desc):
        console.print(f"[green]written:[/green] {p}")


@doc_app.command("rm-entry")
def doc_rm_entry(
    folder: str = typer.Argument(...),
    name: str = typer.Argument(...),
    project: Optional[str] = typer.Option(None, "--project", "-C"),
):
    """删条目（只改文档，不删盘上文件，留给 git 复核）。"""
    for p in base.rm_entry(_gbc_root(project), folder, name):
        console.print(f"[green]written:[/green] {p}")


@doc_app.command("check")
def doc_check(project: Optional[str] = typer.Option(None, "--project", "-C")):
    """全树意图一致性体检（DRIFT/ORPHAN 为错误，STUB 为提示）。"""
    errors, notes = base.check(_gbc_root(project))
    for e in errors:
        console.print(f"[red]{e}[/red]")
    for n in notes:
        console.print(f"[dim]{n}[/dim]")
    if errors:
        raise typer.Exit(code=1)
    console.print("[green]✔ intent tree consistent[/green]")


@doc_app.command("sync")
def doc_sync(project: Optional[str] = typer.Option(None, "--project", "-C")):
    """确定性修复 DRIFT/ORPHAN：把子意图重投影到父条目。"""
    fixed = base.sync(_gbc_root(project))
    for f in fixed:
        console.print(f"[green]{f}[/green]")
    if not fixed:
        console.print("[dim]nothing to sync[/dim]")


@doc_app.command("migrate")
def doc_migrate(project: Optional[str] = typer.Option(None, "--project", "-C")):
    """把所有 gbc.md 升级到最新格式。"""
    changed = base.migrate(_gbc_root(project))
    for c in changed:
        console.print(f"[green]migrated:[/green] {c}")
    if not changed:
        console.print("[dim]all up to date[/dim]")
