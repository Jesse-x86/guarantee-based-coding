# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:MCP 表面把意图文档(doc)能力也暴露出来——读(show/check)与写(set-*)对称可达。

MCP 与 CLI 对称:doc 不再仅走 cli/editor 两薄表面,agent 经 MCP 同样能读写意图。
写入的人类确认闸门由用户 agent 框架承担,不在此层设阻。这条守着"doc 工具在 MCP 里
存在且真的调到 intent.base"这个承诺。
"""
import json

from gbc.app.config import project
from gbc.app.interface import mcp as M


def _use_project(tmp_path):
    """把当前目标项目指到临时目录,让 doc 工具的 _doc_root 落在那里。"""
    project.set_current_project(str(tmp_path))


def test_doc_tools_registered():
    """承诺:读写两类 doc 工具都注册进了 MCP 表面。"""
    import asyncio
    names = {t.name for t in asyncio.run(M.mcp.list_tools())}
    # 读
    assert "doc_show" in names
    assert "doc_check" in names
    # 写
    assert "doc_set_intent" in names
    assert "doc_sync" in names


def test_doc_set_intent_then_show_roundtrip(tmp_path):
    """承诺:经 MCP 写意图,再经 MCP 读回来,内容确实落地(调到了 intent.base)。"""
    _use_project(tmp_path)
    written = M.doc_set_intent("sub", "intent via mcp")
    assert "error" not in written  # 写成功返回路径列表的 JSON
    out = M.doc_show("sub")
    assert "intent via mcp" in out


def test_doc_check_returns_structured(tmp_path):
    """承诺:doc_check 返回结构化结果(errors/notes),空 errors = 一致。"""
    _use_project(tmp_path)
    M.doc_set_intent("sub", "hi")
    res = json.loads(M.doc_check())
    assert "errors" in res and "notes" in res
