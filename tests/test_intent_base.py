# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:意图文档子系统 base 的核心承诺。

- base 是唯一 IO 点:set_intent 落盘 gbc.md,并单源投影到父条目。
- 整树 read_tree/write_tree 往返保真(round-trip)。
- check 能发现 DRIFT,sync 能修复它。
- 非法操作走 IntentDocError(本地化异常),不裸抛 ValueError。
"""
import pytest

from gbc.app.intent import base
from gbc.app.models.errors import IntentDocError


def test_set_intent_persists_and_projects(tmp_path):
    """承诺:set_intent 落盘子意图,并投影到父文档条目(单一事实源)。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    base.set_intent(gbc_root, "app", "app layer intent")
    base.set_intent(gbc_root, "app/core", "core intent")

    # 子文档存在且含意图
    assert "core intent" in base.show(gbc_root, "app/core")
    # 父文档 app 里有指向 core/ 的条目,描述即子意图(投影)
    parent = base.show(gbc_root, "app")
    assert "core" in parent and "core intent" in parent


def test_tree_round_trip(tmp_path):
    """承诺:整树 write 后再 read,意图结构保真。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    tree = {
        "name": "proj", "path": "", "intent": "root intent", "constraints": "",
        "entries": [
            {"name": "mod/", "child": {
                "name": "mod", "path": "mod", "intent": "mod intent",
                "constraints": "", "entries": [{"name": "a.py", "desc": "file a"}]}},
        ],
    }
    base.write_tree(gbc_root, tree)
    back = base.read_tree(gbc_root)
    assert back["intent"] == "root intent"
    names = [e["name"] for e in back["entries"]]
    assert "mod/" in names


def test_check_detects_and_sync_fixes_drift(tmp_path):
    """承诺:父条目与子意图不一致时 check 报 DRIFT,sync 后消除。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    base.set_intent(gbc_root, "x", "child truth")
    # 手动制造漂移:直接改父条目描述(模拟外部污染)
    pdoc = base.read_doc(gbc_root, "")
    for e in pdoc.entries:
        if e.name.rstrip("/") == "x":
            e.desc = "stale parent text"
    base.write_doc(gbc_root, "", pdoc)

    errors, _ = base.check(gbc_root)
    assert any("DRIFT" in e for e in errors)

    base.sync(gbc_root)
    errors_after, _ = base.check(gbc_root)
    assert not any("DRIFT" in e for e in errors_after)


def test_illegal_ops_raise_intent_doc_error(tmp_path):
    """承诺:非法操作抛 IntentDocError(GBCError 体系),不是裸 ValueError。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    with pytest.raises(IntentDocError):
        base.set_file(gbc_root, "", "bad/", "desc")  # 文件名不应以 / 结尾
    with pytest.raises(IntentDocError):
        base.rm_entry(gbc_root, "", "nonexistent")   # 条目不存在
