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

"""`gbc` 的唯一入口 —— 纯分发器。

不实现任何业务:只把两个子系统的表面**组合**成一棵命令树,再挂上跨子系统的
服务/初始化命令。各表面自己是薄的、只调各自的 base。

  gbc guarantee|dep|verify|doctor|executor|refactor|tree   → 保证引擎(interface.cli)
  gbc doc <...>                                            → 意图文档(intent.cli)
  gbc mcp up [root]                                        → 保证引擎的 MCP 表面(interface.mcp)
  gbc editor up                                            → 意图文档的 web 表面(intent.editor)
  gbc rules / setup                                        → 跨子系统的辅助命令

[project.scripts] 的 `gbc` 指向本模块的 app。
"""
from typing import Optional

import typer

from gbc.app.interface.cli import app as guarantee_cli
from gbc.app.intent.cli import doc_app

# 顶层命令树 = 保证引擎的 cli(含 guarantee/dep/verify/doctor/executor/refactor/tree
# 与全局 --lang callback),再往上挂 doc 子树与服务/辅助命令。
app = guarantee_cli
app.add_typer(doc_app, name="doc")

mcp_app = typer.Typer(help="MCP 服务（给 agent 的常驻通道）")
editor_app = typer.Typer(help="意图编辑器（给人的 web 常驻服务）")
app.add_typer(mcp_app, name="mcp")
app.add_typer(editor_app, name="editor")


@mcp_app.command("up")
def mcp_up(
    project_root: Optional[str] = typer.Argument(None, help="目标项目根的绝对路径；省略则用当前项目判定"),
):
    """启动 GBC 的 stdio MCP server（常驻）。由 MCP 表面自己的启动器承载。"""
    from gbc.app.interface.mcp import run_server
    run_server(project_root)


@editor_app.command("up")
def editor_up(
    root: Optional[str] = typer.Option(None, "--root", "-r", help="默认项目路径，前端预填并自动加载"),
    host: str = typer.Option("127.0.0.1", "--host", help="监听地址"),
    port: int = typer.Option(8765, "--port", "-p", help="监听端口"),
    lang: Optional[str] = typer.Option(None, "--lang", help="界面语言 zh/en"),
):
    """启动意图编辑器 web 服务（常驻）。"""
    from gbc.app.i18n import set_lang, resolve_lang, t
    from gbc.app.intent.editor import run_editor
    set_lang(resolve_lang(lang))
    typer.echo(t("editor.starting", host=host, port=port))
    run_editor(host=host, port=port, root=root or "")


@app.command("rules")
def rules_cmd(
    lang: Optional[str] = typer.Option(None, "--lang", help="输出语言 zh/en"),
):
    """打印作者推荐的围栏规则集到 stdout（推荐默认，非强制沙箱）。"""
    from gbc.app.i18n import set_lang, resolve_lang, load_text
    set_lang(resolve_lang(lang))
    # 纯文本发射器：用 print 而非 rich，便于管道/复制。
    print(load_text("rules"))


@app.command("setup")
def setup_cmd(
    lang: Optional[str] = typer.Option(None, "--lang", help="输出语言 zh/en"),
):
    """打印本地化的接线指南到 stdout：怎么把 MCP / skills 接入你的 agent。"""
    from gbc.app.i18n import set_lang, resolve_lang, load_text
    from gbc.app.assets import SKILLS_DIR
    set_lang(resolve_lang(lang))
    # 与 rules 同构：纯文本发射器。只给坐标(skills 目录/MCP 入口)，
    # 具体怎么接入取决于用户 agent——{skills_dir} 填入随包 skills 的真实路径。
    print(load_text("setup").format(skills_dir=str(SKILLS_DIR)))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
