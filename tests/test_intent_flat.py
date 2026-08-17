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

"""保证:意图编辑器 flat 语义模型 + 冲突感知选择性保存(base 层)。

覆盖 nested<->flat 纯函数往返、非法路径/节点拒绝、选择性保存只写涉及文档、
非冲突外部改动保留、同路径冲突/force、folder 父投影、file/folder 删除边界。
"""
import json

import pytest

from gbc.app.intent import base
from gbc.app.models.errors import IntentConflictError, IntentDocError


EMPTY = {"": {"kind": "folder", "intent": "", "constraints": ""}}


def _gbc_root(tmp_path):
    gbc_root, _ = base.resolve_gbc(str(tmp_path / "proj"))
    return gbc_root


def _sample_tree():
    """一个含 root + mod/(core/) + 文件的 nested 树。"""
    return {
        "name": "proj", "path": "", "intent": "root intent", "constraints": "root c",
        "entries": [
            {"name": "mod/", "child": {
                "name": "mod", "path": "mod", "intent": "mod intent", "constraints": "mod c",
                "entries": [
                    {"name": "core/", "child": {
                        "name": "core", "path": "mod/core", "intent": "core intent",
                        "constraints": "", "entries": [{"name": "x.py", "desc": "x desc"}]}},
                    {"name": "a.py", "desc": "a desc"},
                ]}},
            {"name": "top.py", "desc": "top desc"},
        ],
    }


# ---------------------------------------------------------------------------
# flat 纯函数往返
# ---------------------------------------------------------------------------

def test_nested_to_flat_shape():
    """承诺:nested_to_flat 产出 root ""、folder 以 / 结尾、file 不带 / 的 flat map。"""
    flat = base.nested_to_flat(_sample_tree())
    assert flat[""] == {"kind": "folder", "intent": "root intent", "constraints": "root c"}
    assert flat["mod/"] == {"kind": "folder", "intent": "mod intent", "constraints": "mod c"}
    assert flat["mod/core/"] == {"kind": "folder", "intent": "core intent", "constraints": ""}
    assert flat["mod/a.py"] == {"kind": "file", "desc": "a desc"}
    assert flat["mod/core/x.py"] == {"kind": "file", "desc": "x desc"}
    assert flat["top.py"] == {"kind": "file", "desc": "top desc"}


def test_flat_roundtrip_pure():
    """承诺:flat -> nested -> flat 精确不变(nested_to_flat(flat_to_nested(flat)) == flat)。"""
    flat = base.nested_to_flat(_sample_tree())
    back = base.nested_to_flat(base.flat_to_nested(flat, name="proj"))
    assert back == flat


def test_nested_roundtrip_semantic():
    """承诺:nested -> flat -> nested 保留语义(意图/约束/desc/结构/名字)。"""
    tree = _sample_tree()
    back = base.flat_to_nested(base.nested_to_flat(tree), name="proj")
    assert back["name"] == "proj" and back["path"] == ""
    assert back["intent"] == "root intent" and back["constraints"] == "root c"
    mod = [e for e in back["entries"] if e["name"] == "mod/"][0]["child"]
    assert mod["name"] == "mod" and mod["path"] == "mod"
    assert mod["intent"] == "mod intent" and mod["constraints"] == "mod c"
    names = [e["name"] for e in mod["entries"]]
    assert set(names) == {"core/", "a.py"}


# ---------------------------------------------------------------------------
# 非法路径 / 节点
# ---------------------------------------------------------------------------

def test_validate_path_rejects_illegal():
    """承诺:绝对路径、..、空段、首尾空白、反斜杠一律拒绝;root "" 合法。"""
    bad = ["/abs", "a//b", "a/../b", "a/./b", " a ", "a ", "a\\b", "C:/win", "/", "a//"]
    for p in bad:
        with pytest.raises(IntentDocError):
            base._validate_path(p)
    base._validate_path("")          # root 合法
    base._validate_path("app/")      # folder 合法
    base._validate_path("app/x.py")  # file 合法


def test_validate_flat_rejects_missing_root_and_ancestor():
    """承诺:缺 root、缺祖先文件夹、kind 与路径不符 -> IntentDocError(400 域)。"""
    with pytest.raises(IntentDocError):
        base._validate_flat({})  # 缺 root
    # 缺祖先:app/x.py 无 app/ 文件夹
    with pytest.raises(IntentDocError):
        base._validate_flat({"": {"kind": "folder", "intent": "", "constraints": ""},
                             "app/x.py": {"kind": "file", "desc": "d"}})
    # kind 与路径不符:file 路径却标 folder
    with pytest.raises(IntentDocError):
        base._validate_flat({"": {"kind": "folder", "intent": "", "constraints": ""},
                             "app/x.py": {"kind": "folder", "intent": "", "constraints": ""}})


# ---------------------------------------------------------------------------
# 选择性保存
# ---------------------------------------------------------------------------

def _seed(tmp_path):
    """落一个 root + app/ + app/core/ + 两个文件的结构,返回 (gbc_root, base_flat)。"""
    gbc_root = _gbc_root(tmp_path)
    base_flat = {
        "": {"kind": "folder", "intent": "root intent", "constraints": ""},
        "app/": {"kind": "folder", "intent": "app intent", "constraints": ""},
        "app/core/": {"kind": "folder", "intent": "core intent", "constraints": ""},
        "app/main.py": {"kind": "file", "desc": "main desc"},
        "app/core/x.py": {"kind": "file", "desc": "x desc"},
    }
    base.save_flat(gbc_root, EMPTY, base_flat)
    return gbc_root, base_flat


def test_save_no_changes_no_write(tmp_path):
    """承诺:无用户变化 -> 空 written/deleted/count=0,不重写。"""
    gbc_root, base_flat = _seed(tmp_path)
    result = base.save_flat(gbc_root, base_flat, dict(base_flat))
    assert result == {"written": [], "deleted": [], "count": 0}


def test_save_only_writes_involved_docs(tmp_path):
    """承诺:只改 app/main.py desc -> 只重写 app/gbc.md,root 与 app/core 不动。"""
    gbc_root, base_flat = _seed(tmp_path)
    current = {k: dict(v) for k, v in base_flat.items()}
    current["app/main.py"] = {"kind": "file", "desc": "changed desc"}
    result = base.save_flat(gbc_root, base_flat, current)

    app_md = str(gbc_root / "app" / "gbc.md")
    assert result["written"] == [app_md]
    assert result["deleted"] == []
    assert result["count"] == 1


def test_save_preserves_unrelated_external_changes(tmp_path):
    """承诺:外部改了 app/main.py desc(用户未碰) -> 保存后保留外部值;用户改动独立落盘。"""
    gbc_root, base_flat = _seed(tmp_path)
    # 外部直接改 app/main.py desc(不经 base)
    pdoc = base.read_doc(gbc_root, "app")
    for e in pdoc.entries:
        if e.name.rstrip("/") == "main.py":
            e.desc = "external desc"
    base.write_doc(gbc_root, "app", pdoc)

    # 用户只改 app intent
    current = {k: dict(v) for k, v in base_flat.items()}
    current["app/"] = {"kind": "folder", "intent": "NEW app intent", "constraints": ""}
    base.save_flat(gbc_root, base_flat, current)

    disk = base.read_flat(gbc_root)
    assert disk["app/main.py"]["desc"] == "external desc"   # 外部改动保留
    assert disk["app/"]["intent"] == "NEW app intent"       # 用户改动落盘


def test_conflict_raises_and_force_wins(tmp_path):
    """承诺:同路径外部/用户都改且结果不同 -> IntentConflictError;force 后用户值落盘。"""
    gbc_root, base_flat = _seed(tmp_path)
    # 外部改 main.py desc
    pdoc = base.read_doc(gbc_root, "app")
    for e in pdoc.entries:
        if e.name.rstrip("/") == "main.py":
            e.desc = "external desc"
    base.write_doc(gbc_root, "app", pdoc)

    # 用户改同一 main.py desc 到不同值
    current = {k: dict(v) for k, v in base_flat.items()}
    current["app/main.py"] = {"kind": "file", "desc": "user desc"}

    with pytest.raises(IntentConflictError) as ei:
        base.save_flat(gbc_root, base_flat, current)
    exc = ei.value
    assert exc.conflicts[0]["path"] == "app/main.py"
    assert exc.conflicts[0]["disk"]["desc"] == "external desc"
    assert exc.conflicts[0]["user"]["desc"] == "user desc"

    # force:用户值落盘
    base.save_flat(gbc_root, base_flat, current, force=True)
    assert base.read_flat(gbc_root)["app/main.py"]["desc"] == "user desc"


def _folder_seed(tmp_path):
    """root + app/ folder 两节点(app intent=A、constraints=B)。"""
    gbc_root = _gbc_root(tmp_path)
    base_flat = {
        "": {"kind": "folder", "intent": "", "constraints": ""},
        "app/": {"kind": "folder", "intent": "A", "constraints": "B"},
    }
    base.save_flat(gbc_root, EMPTY, base_flat)
    return gbc_root, base_flat


def test_field_three_way_merge_and_force(tmp_path):
    """承诺:字段级三方合并。

    - 用户改 intent、外部改 constraints(不同字段)→ 普通保存无冲突,两者都落盘(A2,B2)。
    - 双方改同一字段(intent)到不同值 → 冲突(带 fields:[...]);force 后 intent=current,
      constraints 仍保留外部值(只覆盖真正冲突字段)。
    """
    # 场景1:不同字段各自合并,普通保存无冲突
    gbc_root, base_flat = _folder_seed(tmp_path / "p1")
    pdoc = base.read_doc(gbc_root, "app")
    pdoc.constraints = "B2"              # 外部改 constraints
    base.write_doc(gbc_root, "app", pdoc)
    current = {k: dict(v) for k, v in base_flat.items()}
    current["app/"] = {"kind": "folder", "intent": "A2", "constraints": "B"}  # 用户改 intent

    base.save_flat(gbc_root, base_flat, current)   # 不抛冲突
    disk = base.read_flat(gbc_root)
    assert disk["app/"]["intent"] == "A2"          # 用户字段落盘
    assert disk["app/"]["constraints"] == "B2"     # 外部字段保留

    # 场景2:双方改同一字段(intent)到不同值 → 冲突;force 只覆盖冲突字段
    gbc_root2, base_flat2 = _folder_seed(tmp_path / "p2")
    pdoc2 = base.read_doc(gbc_root2, "app")
    pdoc2.intent = "A_ext"                # 外部改 intent
    pdoc2.constraints = "B2_ext"          # 外部同时改 constraints
    base.write_doc(gbc_root2, "app", pdoc2)
    current2 = {k: dict(v) for k, v in base_flat2.items()}
    current2["app/"] = {"kind": "folder", "intent": "A_user", "constraints": "B"}  # 用户只改 intent

    with pytest.raises(IntentConflictError) as ei:
        base.save_flat(gbc_root2, base_flat2, current2)
    exc = ei.value
    assert exc.conflicts[0]["path"] == "app/"
    assert exc.conflicts[0]["fields"] == ["intent"]
    assert exc.conflicts[0]["disk"]["intent"] == "A_ext"
    assert exc.conflicts[0]["user"]["intent"] == "A_user"

    base.save_flat(gbc_root2, base_flat2, current2, force=True)
    disk2 = base.read_flat(gbc_root2)
    assert disk2["app/"]["intent"] == "A_user"      # force:冲突字段取 current
    assert disk2["app/"]["constraints"] == "B2_ext"  # 非冲突外部字段保留


# ---------------------------------------------------------------------------
# 投影 + 删除边界
# ---------------------------------------------------------------------------

def test_folder_intent_projects_to_parent(tmp_path):
    """承诺:改 folder 自身 intent 会同时更新父文档对应 entry desc(投影)。"""
    gbc_root, base_flat = _seed(tmp_path)
    current = {k: dict(v) for k, v in base_flat.items()}
    current["app/core/"] = {"kind": "folder", "intent": "NEW core intent", "constraints": ""}
    base.save_flat(gbc_root, base_flat, current)

    app_doc = base.read_doc(gbc_root, "app")
    core_entry = [e for e in app_doc.entries if e.name.rstrip("/") == "core"][0]
    assert core_entry.is_dir and core_entry.desc == "NEW core intent"
    errors, _ = base.check(gbc_root)
    assert errors == []


def test_file_delete_preserves_source_and_json(tmp_path):
    """承诺:删 file 只删父 gbc.md 条目,不碰源文件也不碰 gbc.<file>.json。"""
    gbc_root, base_flat = _seed(tmp_path)
    proj = gbc_root.parent
    (proj / "app").mkdir(parents=True, exist_ok=True)
    (proj / "app" / "main.py").write_text("code", encoding="utf-8")
    json_path = gbc_root / "app" / "gbc.main.py.json"
    json_path.write_text("{}", encoding="utf-8")

    current = {k: dict(v) for k, v in base_flat.items()}
    del current["app/main.py"]
    base.save_flat(gbc_root, base_flat, current)

    assert (proj / "app" / "main.py").exists()   # 源文件不删
    assert json_path.exists()                    # json 不删
    app_doc = base.read_doc(gbc_root, "app")
    assert all(e.name.rstrip("/") != "main.py" for e in app_doc.entries)


def test_folder_delete_removes_subtree_keeps_json_no_orphan(tmp_path):
    """承诺:删 folder 删父条目 + 该子树 gbc.md,保留 json,无 ORPHAN。"""
    gbc_root, base_flat = _seed(tmp_path)
    proj = gbc_root.parent
    (proj / "app" / "core").mkdir(parents=True, exist_ok=True)
    json_path = gbc_root / "app" / "core" / "gbc.x.py.json"
    json_path.write_text("{}", encoding="utf-8")

    current = {k: dict(v) for k, v in base_flat.items()}
    for key in list(current):
        if key.startswith("app/core"):
            del current[key]
    result = base.save_flat(gbc_root, base_flat, current)

    assert not (gbc_root / "app" / "core" / "gbc.md").exists()  # 子树 gbc.md 删
    assert json_path.exists()                                   # json 保留
    assert str(gbc_root / "app" / "core" / "gbc.md") in result["deleted"]
    errors, _ = base.check(gbc_root)
    assert errors == []                                         # 无 ORPHAN/DRIFT
