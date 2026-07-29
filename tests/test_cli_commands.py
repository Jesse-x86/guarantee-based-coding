# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:入口分发器(gbc.entry)整合后的命令树承诺。

- 唯一入口暴露两子系统的表面 + 服务/辅助命令。
- gbc rules 输出双语规则文本,声明"非强制沙箱"。
- gbc doc 经 intent 子系统合规读意图。
- gbc init 透明建立 .gbc/ 骨架。
"""
from typer.testing import CliRunner

from gbc.entry import app

runner = CliRunner()


def test_command_tree_has_all_commands():
    """承诺:保证命令 + doc/mcp/editor/rules/init 都在唯一入口下。"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("guarantee", "verify", "doc", "mcp", "editor", "rules", "init"):
        assert cmd in result.output


def test_rules_outputs_bilingual_and_non_sandbox():
    """承诺:rules 双语可出,且都强调不是强制沙箱。"""
    zh = runner.invoke(app, ["rules", "--lang", "zh"])
    en = runner.invoke(app, ["rules", "--lang", "en"])
    assert zh.exit_code == 0 and en.exit_code == 0
    assert "强制" in zh.output
    assert "sandbox" in en.output.lower()


def test_mcp_up_is_a_command():
    """承诺:mcp up 子命令存在。"""
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "up" in result.output


def test_init_creates_gbc_dir(tmp_path):
    """承诺:init 在目标项目建立 .gbc/ 骨架。"""
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".gbc").is_dir()


def test_doc_show_reads_intent(tmp_path):
    """承诺:doc show 经 intent 子系统读出意图(用 --project 显式指定)。"""
    from gbc.app.intent import base
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    base.set_intent(gbc_root, "sub", "hello intent")

    result = runner.invoke(app, ["doc", "show", "sub", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert "hello intent" in result.output
