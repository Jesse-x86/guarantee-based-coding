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

"""意图文档子系统的编排/IO 总线 —— 唯一碰 gbc.md 磁盘的地方。

对称于 interface.base(保证引擎的总线):
- 路径解析(.gbc 镜像层)、单文档读写、父子意图单源投影都收在这里;
- 单文档操作(set_intent/set_constraints/set_file/rm_entry/show);
- 整树读写(read_tree/write_tree)供 web 编辑器用;
- 全树一致性(check/sync/migrate)。

上层表面(cli / editor)只调本模块,绝不自己碰磁盘或解析路径。
gbc.md 解析单源复用 gbc.app.utils.gbc_md。
"""
from pathlib import Path
import re
import threading

from gbc.app.utils import gbc_md as gf
from gbc.app.models.errors import IntentDocError, IntentConflictError
from gbc.app.models.meta import FileMeta
from gbc.app.utils.json_model_operator import load_model_from_json
from gbc.app.utils.safe_file_writer import SafeFileWriter

GBC_FILE = "gbc.md"


# ---- 路径解析(.gbc 镜像层) --------------------------------------------------

def resolve_gbc(root_str: str) -> tuple[Path, str]:
    """把用户给的路径映射成 (gbc_root, project_name)。

    `.gbc` 镜像层对树是隐藏的:展示的根是**项目**目录,内容始终落在 <project>/.gbc/ 下。
      - 路径以 `.gbc` 结尾 -> gbc_root = 该路径,        project = 其父目录名
      - 否则               -> gbc_root = 路径/.gbc,     project = 该路径名
    因此加载 `…/proj` 与 `…/proj/.gbc` 行为一致。
    """
    p = Path(root_str).expanduser().resolve()
    if p.name == ".gbc":
        return p, p.parent.name
    return p / ".gbc", p.name


def _norm(rel: str) -> str:
    """规范化文件夹相对路径:去首尾斜杠;'.' 与 '' 都表示根。"""
    rel = (rel or "").strip().strip("/")
    return "" if rel in ("", ".") else rel


def _doc_path(gbc_root: Path, rel: str) -> Path:
    return (gbc_root / rel / GBC_FILE) if rel else (gbc_root / GBC_FILE)


def _parent_name(rel: str) -> tuple[str | None, str | None]:
    """(父文件夹 rel, 本文件夹名)。根 -> (None, None)。"""
    rel = _norm(rel)
    if not rel:
        return None, None
    parts = rel.split("/")
    return "/".join(parts[:-1]), parts[-1]


def _find_entry(doc: gf.ParsedDoc, name: str) -> gf.Entry | None:
    key = name.rstrip("/")
    for e in doc.entries:
        if e.name.rstrip("/") == key:
            return e
    return None


# ---- 单文档读写(唯一 IO 点) ------------------------------------------------

def read_doc(gbc_root: Path, rel: str) -> gf.ParsedDoc:
    p = _doc_path(gbc_root, rel)
    return gf.parse(p.read_text(encoding="utf-8")) if p.exists() else gf.ParsedDoc()


def write_doc(gbc_root: Path, rel: str, doc: gf.ParsedDoc) -> Path:
    p = _doc_path(gbc_root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(gf.serialize(doc.intent, doc.constraints, doc.entries), encoding="utf-8")
    return p


# ---- 单文档操作 -------------------------------------------------------------

def set_intent(gbc_root: Path, rel: str, text: str) -> list[Path]:
    """设文件夹意图,并单源投影到父文档对应的 `## <name>/` 条目。"""
    rel = _norm(rel)
    doc = read_doc(gbc_root, rel)
    doc.intent = text
    written = [write_doc(gbc_root, rel, doc)]

    parent_rel, name = _parent_name(rel)
    if name is not None:  # 非根:把意图投影到父条目(单一事实源)
        pdoc = read_doc(gbc_root, parent_rel)
        entry = _find_entry(pdoc, name)
        if entry is None:
            pdoc.entries.append(gf.Entry(name=f"{name}/", is_dir=True, desc=text))
        else:
            entry.name = f"{name}/"
            entry.is_dir = True
            entry.desc = text
        written.append(write_doc(gbc_root, parent_rel, pdoc))
    return written


def set_constraints(gbc_root: Path, rel: str, text: str) -> list[Path]:
    rel = _norm(rel)
    doc = read_doc(gbc_root, rel)
    doc.constraints = text
    return [write_doc(gbc_root, rel, doc)]


def set_file(gbc_root: Path, rel: str, name: str, desc: str) -> list[Path]:
    """新增/更新一个文件条目(name 不带斜杠)。"""
    if name.rstrip().endswith("/"):
        raise IntentDocError("exc.doc_filename_slash", name=name)
    rel = _norm(rel)
    doc = read_doc(gbc_root, rel)
    entry = _find_entry(doc, name)
    if entry is not None and entry.is_dir:
        raise IntentDocError("exc.doc_name_is_folder", name=name)
    if entry is None:
        doc.entries.append(gf.Entry(name=name, is_dir=False, desc=desc))
    else:
        entry.desc = desc
    return [write_doc(gbc_root, rel, doc)]


def rm_entry(gbc_root: Path, rel: str, name: str) -> list[Path]:
    """从文件夹文档里删掉一个条目(只改文档,不删盘上文件/子目录,留给 git 复核)。"""
    rel = _norm(rel)
    doc = read_doc(gbc_root, rel)
    before = len(doc.entries)
    key = name.rstrip("/")
    doc.entries = [e for e in doc.entries if e.name.rstrip("/") != key]
    if len(doc.entries) == before:
        raise IntentDocError("exc.doc_entry_not_found", name=name)
    return [write_doc(gbc_root, rel, doc)]


def show(gbc_root: Path, rel: str) -> str:
    rel = _norm(rel)
    p = _doc_path(gbc_root, rel)
    if not p.exists():
        return f"(无 gbc.md) {p}"
    doc = read_doc(gbc_root, rel)
    lines = [f"# 文件夹: {rel or '(根)'}  -> {p}", "", "[意图]", doc.intent or "(空)"]
    if doc.constraints:
        lines += ["", "[内部约束]", doc.constraints]
    lines += ["", "[文件]"]
    lines += [f"  {'📁' if e.is_dir else '📄'} {e.name}: {e.desc}" for e in doc.entries] or ["  (无)"]
    return "\n".join(lines)


# ---- 文件条目 → .gbc json 只读视图 -------------------------------------------

def file_meta_view(gbc_root: Path, path: str) -> dict | None:
    """返回一个文件条目对应的 .gbc json(FileMeta)只读可读视图;json 缺失/损坏返回 None。

    path 是完整语义文件路径(如 "app/main.py";根层文件即 "main.py")。在 base 内做完整校验:
    复用 _validate_path(拒绝对路径/.. /空段/首尾空白/反斜杠),且 root("")、folder 尾斜杠、
    空 name 均非法——只接受指向 file 的路径。非法抛 IntentDocError,由上层表面转 400。

    定位规则与 file_utils.to_gbc_json_path 一致:源码 ``<rel>/<name>`` 的元数据落在
    .gbc 镜像下 ``<gbc_root>/<rel>/gbc.<name>.json``(gbc_root 即 .gbc 镜像层,对应项目根)。
    只读视图——绝不写盘、绝不创建缺失的 json、解析失败静默返回 None。
    """
    _validate_path(path)
    if path == "" or path.endswith("/"):
        raise IntentDocError("exc.doc_flat_bad_path", path=path)
    rel, _, name = path.rpartition("/")
    json_path = (gbc_root / rel / f"gbc.{name}.json") if rel else (gbc_root / f"gbc.{name}.json")
    if not json_path.is_file():
        return None
    try:
        meta = load_model_from_json(json_path, FileMeta)
    except (OSError, ValueError):  # 缺失/损坏/不符合模型 → 只读视图不抛错
        return None
    return {
        "provides": [
            {"id": gid, "desc": g.desc, "disabled": g.disabled,
             "dependents": list(g.dependents)}
            for gid, g in meta.provides.items()
        ],
        "depends_on": [
            {"symbol": d.symbol, "provider": d.symbol.split(":", 1)[0],
             "guarantees": list(d.guarantees)}
            for d in meta.depends_on
        ],
    }


# ---- 整树读写(供 web 编辑器) -----------------------------------------------

def empty_tree(gbc_root: Path) -> dict:
    return {"name": gbc_root.name, "path": "", "intent": "", "constraints": "", "entries": []}


def read_tree(abs_dir: Path, rel: str = "") -> dict:
    """把一个 .gbc 目录读成嵌套 dict 树(供前端编辑)。条目类型由名字尾部 '/' 推导。"""
    md = abs_dir / GBC_FILE
    doc = gf.parse(md.read_text(encoding="utf-8")) if md.exists() else gf.ParsedDoc()

    entries: list[dict] = []
    seen_dirs: set[str] = set()
    for e in doc.entries:
        if not e.is_dir:
            entries.append({"name": e.name, "desc": e.desc})
            continue
        child_name = e.name.rstrip("/")
        seen_dirs.add(child_name)
        child_abs = abs_dir / child_name
        child_rel = f"{rel}/{child_name}".lstrip("/") if rel else child_name
        if (child_abs / GBC_FILE).exists():
            child = read_tree(child_abs, child_rel)  # 子自己的 gbc.md 是权威
        else:
            child = {"name": child_name, "path": child_rel,
                     "intent": e.desc, "constraints": "", "entries": []}
        entries.append({"name": e.name, "child": child})

    # 有 gbc.md 但父条目没引用的子文件夹,也一并浮现
    for sub in sorted(p for p in abs_dir.iterdir() if p.is_dir() and (p / GBC_FILE).exists()):
        if sub.name in seen_dirs:
            continue
        child_rel = f"{rel}/{sub.name}".lstrip("/") if rel else sub.name
        entries.append({"name": f"{sub.name}/", "child": read_tree(sub, child_rel)})

    return {"name": abs_dir.name, "path": rel,
            "intent": doc.intent, "constraints": doc.constraints, "entries": entries}


def _is_dir_name(name: str) -> bool:
    return name.rstrip().endswith("/")


def write_tree(node_dir: Path, node: dict, written: list[str] | None = None) -> list[str]:
    """把嵌套 dict 树写回文件系统。目标目录由树结构(父目录 + 条目名)推导,
    改名即写到新位置——绝不信任存储的 path。"""
    if written is None:
        written = []
    node_dir.mkdir(parents=True, exist_ok=True)

    gf_entries: list[gf.Entry] = []
    for e in node["entries"]:
        if not e["name"].strip():
            continue  # 跳过空白幽灵行
        if _is_dir_name(e["name"]):
            child = e.get("child") or {}
            # 单一事实源:父条目文本就是子的意图
            gf_entries.append(gf.Entry(name=e["name"], is_dir=True, desc=child.get("intent", "")))
        else:
            gf_entries.append(gf.Entry(name=e["name"], is_dir=False, desc=e.get("desc", "")))

    text = gf.serialize(node["intent"], node.get("constraints", ""), gf_entries)
    (node_dir / GBC_FILE).write_text(text, encoding="utf-8")
    written.append(str(node_dir / GBC_FILE))

    for e in node["entries"]:
        if e["name"].strip() and _is_dir_name(e["name"]) and e.get("child"):
            child_dir = node_dir / e["name"].rstrip().rstrip("/")
            write_tree(child_dir, e["child"], written)
    return written


# ---- 全树一致性 -------------------------------------------------------------

def check(gbc_root: Path) -> tuple[list[str], list[str]]:
    """全树一致性体检。返回 (errors, notes):

    errors = DRIFT(子有 gbc.md 且其意图与父条目描述不一致) / ORPHAN(子有 gbc.md 但父未登记);
    notes  = STUB(父登记了子文件夹条目但子无 gbc.md)——叶子文件夹的正常状态,仅提示。
    """
    errors: list[str] = []
    notes: list[str] = []
    if not gbc_root.exists():
        return [f"(.gbc 不存在: {gbc_root})"], []

    for md in sorted(gbc_root.rglob(GBC_FILE)):
        rel = md.parent.relative_to(gbc_root).as_posix()
        rel = "" if rel == "." else rel
        doc = gf.parse(md.read_text(encoding="utf-8"))
        for e in doc.entries:
            if not e.is_dir:
                continue
            child_rel = f"{rel}/{e.name.rstrip('/')}".lstrip("/")
            child_md = gbc_root / child_rel / GBC_FILE
            if not child_md.exists():
                notes.append(f"[STUB] {rel or '(根)'} 的条目 '{e.name}' 没有对应 gbc.md(叶子文件夹?)")
                continue
            child_intent = gf.parse(child_md.read_text(encoding="utf-8")).intent.strip()
            if child_intent != (e.desc or "").strip():
                errors.append(f"[DRIFT] '{child_rel}' 的意图 与 父文档条目描述 不一致")

        parent_rel, name = _parent_name(rel)
        if name is not None:
            pmd = gbc_root / (parent_rel or "") / GBC_FILE
            if not pmd.exists():
                errors.append(f"[ORPHAN] '{rel}' 有 gbc.md 但父 '{parent_rel or '(根)'}' 没有 gbc.md")
            elif _find_entry(gf.parse(pmd.read_text(encoding="utf-8")), name) is None:
                errors.append(f"[ORPHAN] '{rel}' 有 gbc.md 但父文档未登记 '{name}/' 条目")
    return errors, notes


def sync(gbc_root: Path) -> list[str]:
    """确定性修复 DRIFT/ORPHAN:把每个有 gbc.md 的子文件夹的意图(唯一事实源)重投影到
    其父文档的 `## <name>/` 条目(缺则补、不一致则覆盖)。只动父条目,不碰子意图。"""
    fixed: list[str] = []
    for md in sorted(gbc_root.rglob(GBC_FILE)):
        rel = md.parent.relative_to(gbc_root).as_posix()
        rel = "" if rel == "." else rel
        parent_rel, name = _parent_name(rel)
        if name is None:
            continue
        child_intent = gf.parse(md.read_text(encoding="utf-8")).intent
        pdoc = read_doc(gbc_root, parent_rel)
        entry = _find_entry(pdoc, name)
        if entry is None:
            pdoc.entries.append(gf.Entry(name=f"{name}/", is_dir=True, desc=child_intent))
            write_doc(gbc_root, parent_rel, pdoc)
            fixed.append(f"+ 补登记 '{rel}' 到父 '{parent_rel or '(根)'}'")
        elif (entry.desc or "").strip() != child_intent.strip():
            entry.name, entry.is_dir, entry.desc = f"{name}/", True, child_intent
            write_doc(gbc_root, parent_rel, pdoc)
            fixed.append(f"~ 重投影 '{rel}' 意图到父 '{parent_rel or '(根)'}'")
    return fixed


def migrate(gbc_root: Path) -> list[str]:
    """把所有 gbc.md parse→serialize 重写一遍,升级到带 `# 文件` 段的新格式。"""
    changed: list[str] = []
    for md in sorted(gbc_root.rglob(GBC_FILE)):
        old = md.read_text(encoding="utf-8")
        doc = gf.parse(old)
        new = gf.serialize(doc.intent, doc.constraints, doc.entries)
        if new != old:
            md.write_text(new, encoding="utf-8")
            changed.append(str(md))
    return changed


# ---- flat 语义模型(供 web 编辑器) -------------------------------------------

# root path 为 "";folder path 以 "/" 结尾;file path 不以 "/" 结尾。
# folder node = {kind:"folder", intent, constraints};file node = {kind:"file", desc}。


def _last_segment(path: str) -> str:
    """"app/" -> "app";"app/main.py" -> "main.py";"" -> ""。"""
    body = path[:-1] if path.endswith("/") else path
    return body.rsplit("/", 1)[-1]


def _parent_flat_key(path: str) -> str:
    """flat 路径的父文件夹 key(""/"a/" 都回 "")。"""
    body = path[:-1] if path.endswith("/") else path
    idx = body.rfind("/")
    return body[:idx] + "/" if idx != -1 else ""


def _children_paths(flat: dict, folder_key: str) -> list[str]:
    return [p for p in flat if p != folder_key and _parent_flat_key(p) == folder_key]


def _node_eq(a, b) -> bool:
    """语义节点相等:kind 参与比较(区分类型),folder 比 intent+constraints,file 比 desc。"""
    if a is None or b is None:
        return a is b
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    if a.get("kind") != b.get("kind"):
        return False
    kind = a.get("kind")
    if kind == "folder":
        return a.get("intent", "") == b.get("intent", "") and a.get("constraints", "") == b.get("constraints", "")
    if kind == "file":
        return a.get("desc", "") == b.get("desc", "")
    return False


def nested_to_flat(node: dict) -> dict:
    """纯函数:nested dict 树(如 read_tree 输出) -> flat {path: node}。"""
    flat: dict[str, dict] = {}

    def walk(n: dict, folder_key: str) -> None:
        flat[folder_key] = {"kind": "folder",
                            "intent": n.get("intent", ""),
                            "constraints": n.get("constraints", "")}
        for e in n.get("entries", []):
            name = e["name"].rstrip("/")
            if _is_dir_name(e["name"]):
                child_key = (f"{folder_key}{name}" if folder_key else name) + "/"
                walk(e.get("child") or {}, child_key)
            else:
                file_key = f"{folder_key}{name}" if folder_key else name
                flat[file_key] = {"kind": "file", "desc": e.get("desc", "")}

    walk(node, "")
    return flat


def flat_to_nested(flat: dict, name: str = "") -> dict:
    """纯函数:flat {path: node} -> nested dict 树(根)。name 为根节点展示名。"""

    def build(folder_key: str) -> dict:
        node = flat.get(folder_key, {"kind": "folder", "intent": "", "constraints": ""})
        nested = {
            "name": _last_segment(folder_key),
            "path": folder_key.rstrip("/"),
            "intent": node.get("intent", ""),
            "constraints": node.get("constraints", ""),
            "entries": [],
        }
        for path in sorted(_children_paths(flat, folder_key)):
            child = flat[path]
            seg = _last_segment(path)
            if child.get("kind") == "folder":
                nested["entries"].append({"name": f"{seg}/", "child": build(path)})
            else:
                nested["entries"].append({"name": seg, "desc": child.get("desc", "")})
        return nested

    root = build("")
    root["name"] = name
    return root


def _validate_path(path: str) -> None:
    """拒绝绝对路径、..、空段、首尾空白、反斜杠;root "" 合法。"""
    if not isinstance(path, str):
        raise IntentDocError("exc.doc_flat_bad_path", path=repr(path))
    if path == "":
        return
    if path != path.strip():
        raise IntentDocError("exc.doc_flat_bad_path", path=path)
    if "\\" in path:
        raise IntentDocError("exc.doc_flat_bad_path", path=path)
    body = path[:-1] if path.endswith("/") else path
    if body.startswith("/") or re.match(r"^[A-Za-z]:", body):
        raise IntentDocError("exc.doc_flat_bad_path", path=path)
    segs = body.split("/")
    if "" in segs or any(s in (".", "..") for s in segs):
        raise IntentDocError("exc.doc_flat_bad_path", path=path)


def _validate_node(path: str, node) -> None:
    if not isinstance(node, dict):
        raise IntentDocError("exc.doc_flat_bad_node", path=path, reason="not an object")
    kind = node.get("kind")
    expected = "folder" if (path == "" or path.endswith("/")) else "file"
    if kind != expected:
        raise IntentDocError("exc.doc_flat_bad_node", path=path,
                             reason=f"kind must be '{expected}'")
    if kind == "folder":
        for key in ("intent", "constraints"):
            if key in node and not isinstance(node[key], str):
                raise IntentDocError("exc.doc_flat_bad_node", path=path, reason=f"{key} must be a string")
    else:
        if "desc" in node and not isinstance(node["desc"], str):
            raise IntentDocError("exc.doc_flat_bad_node", path=path, reason="desc must be a string")


def _validate_flat(flat: dict) -> None:
    if not isinstance(flat, dict):
        raise IntentDocError("exc.doc_flat_bad_node", path="<root>", reason="flat must be an object")
    if "" not in flat:
        raise IntentDocError("exc.doc_flat_bad_node", path="", reason="root node is required")
    for path, node in flat.items():
        _validate_path(path)
        _validate_node(path, node)
    for path in flat:
        if path == "":
            continue
        parent = _parent_flat_key(path)
        if parent not in flat or flat[parent].get("kind") != "folder":
            raise IntentDocError("exc.doc_flat_missing_ancestor", path=path, parent=parent)


def read_flat(gbc_root: Path) -> dict:
    """读磁盘 -> flat map。gbc_root 不存在时回仅根节点的空树。"""
    if not gbc_root.exists():
        return {"": {"kind": "folder", "intent": "", "constraints": ""}}
    return nested_to_flat(read_tree(gbc_root))


# ---- 选择性保存(冲突感知,最小写盘) -------------------------------------------

_save_locks: dict[str, threading.Lock] = {}
_save_locks_guard = threading.Lock()


def _lock_for(root_key: str) -> threading.Lock:
    with _save_locks_guard:
        if root_key not in _save_locks:
            _save_locks[root_key] = threading.Lock()
        return _save_locks[root_key]


def _entries_for_folder(flat: dict, folder_key: str) -> list[gf.Entry]:
    entries: list[gf.Entry] = []
    for path in sorted(_children_paths(flat, folder_key)):
        node = flat[path]
        seg = _last_segment(path)
        if node.get("kind") == "folder":
            entries.append(gf.Entry(name=f"{seg}/", is_dir=True, desc=node.get("intent", "")))
        else:
            entries.append(gf.Entry(name=seg, is_dir=False, desc=node.get("desc", "")))
    return entries


def _reconcile_entries(disk_entries: list[gf.Entry], target_entries: list[gf.Entry]) -> list[gf.Entry]:
    """保留盘上条目顺序(未涉及条目原样),更新已存在条目的 desc,新条目追加到末尾。"""
    target_map = {(e.name.rstrip("/"), e.is_dir): e for e in target_entries}
    result: list[gf.Entry] = []
    seen: set[tuple[str, bool]] = set()
    for e in disk_entries:
        key = (e.name.rstrip("/"), e.is_dir)
        te = target_map.get(key)
        if te is not None:
            result.append(gf.Entry(name=e.name, is_dir=e.is_dir, desc=te.desc))
            seen.add(key)
    for te in target_entries:
        key = (te.name.rstrip("/"), te.is_dir)
        if key not in seen:
            result.append(te)
    return result


def _docs_equal(a: gf.ParsedDoc, b: gf.ParsedDoc) -> bool:
    if a.intent != b.intent or a.constraints != b.constraints:
        return False
    if len(a.entries) != len(b.entries):
        return False
    for ea, eb in zip(a.entries, b.entries):
        if ea.name != eb.name or ea.is_dir != eb.is_dir or ea.desc != eb.desc:
            return False
    return True


def _render_doc(flat: dict, folder_key: str, order_source: gf.ParsedDoc | None) -> gf.ParsedDoc:
    node = flat.get(folder_key, {"kind": "folder", "intent": "", "constraints": ""})
    entries = _entries_for_folder(flat, folder_key)
    if order_source is not None:
        entries = _reconcile_entries(order_source.entries, entries)
    return gf.ParsedDoc(intent=node.get("intent", ""), constraints=node.get("constraints", ""),
                        entries=entries)


def _write_doc_atomic(gbc_root: Path, rel: str, text: str) -> Path:
    p = _doc_path(gbc_root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    with SafeFileWriter(p).open(mode="w", encoding="utf-8") as f:
        f.write(text)
    return p


def _apply_flat(gbc_root: Path, disk_flat: dict, merged_flat: dict) -> tuple[list[str], list[str]]:
    """把 merged 落到磁盘:只重写内容变化的 gbc.md;删除文件夹时 unlink 子树 gbc.md,绝不碰 json。"""
    written: list[str] = []
    deleted: list[str] = []

    merged_folders = {p for p in merged_flat if p == "" or p.endswith("/")}
    disk_folders = {p for p in disk_flat if p == "" or p.endswith("/")}

    # 先删(深路径在前),避免残留孤儿 gbc.md
    for f in sorted(disk_folders - merged_folders, key=len, reverse=True):
        p = _doc_path(gbc_root, f)
        if p.exists():
            p.unlink()
            deleted.append(str(p))

    for f in sorted(merged_folders):
        order_source = None
        if f in disk_folders and _doc_path(gbc_root, f).exists():
            order_source = read_doc(gbc_root, f)
        disk_doc = _render_doc(disk_flat, f, order_source) if f in disk_folders else gf.ParsedDoc()
        target_doc = _render_doc(merged_flat, f, order_source)
        if not _docs_equal(disk_doc, target_doc):
            text = gf.serialize(target_doc.intent, target_doc.constraints, target_doc.entries)
            _write_doc_atomic(gbc_root, f, text)
            written.append(str(_doc_path(gbc_root, f)))

    return written, deleted


_FOLDER_FIELDS = ("intent", "constraints")
_FILE_FIELDS = ("desc",)


def _fields_for_kind(kind: str) -> tuple[str, ...]:
    return _FOLDER_FIELDS if kind == "folder" else _FILE_FIELDS


def _merge_path_fields(path: str, base_node: dict, disk_node: dict, current_node: dict,
                       force: bool, conflicts: list[dict]) -> tuple[dict | None, bool]:
    """三方都存在且 kind 相同的节点:逐字段三方合并。返回 (最终节点, 是否冲突)。

    file 仅 desc;folder 为 intent/constraints。用户字段未改→取 disk;仅用户改→current;
    仅外部改→disk;双方改到相同值→该值;双方改到不同值→冲突字段(force 时取 current)。
    """
    fields = _fields_for_kind(base_node.get("kind"))
    merged = dict(current_node)
    conflict_fields: list[str] = []
    for f in fields:
        b = base_node.get(f, "")
        d = disk_node.get(f, "")
        c = current_node.get(f, "")
        if c == b:
            merged[f] = d          # 用户未改该字段 → 保留外部(disk)值
        elif d == b:
            merged[f] = c          # 仅用户改 → current
        elif c == d:
            merged[f] = c          # 双方改到相同值 → 该值
        else:
            conflict_fields.append(f)
            merged[f] = c if force else d
    if conflict_fields and not force:
        conflicts.append({"path": path, "fields": conflict_fields,
                          "disk": disk_node, "user": current_node})
        return None, True
    return merged, False


def _merge_path(path: str, base_node, disk_node, current_node, force: bool,
                conflicts: list[dict]) -> tuple[dict | None, bool]:
    """单路径三方合并。返回 (最终节点或 None=删除, 是否冲突)。

    节点新增/删除/type change 按整节点冲突;三方都存在且 kind 相同才走字段级合并。
    """
    base_present = base_node is not None
    disk_present = disk_node is not None
    current_present = current_node is not None

    if not base_present:
        # 新增语义
        if not disk_present and not current_present:
            return None, False
        if disk_present and not current_present:
            return disk_node, False
        if current_present and not disk_present:
            return current_node, False
        if _node_eq(disk_node, current_node):
            return current_node, False
        conflicts.append({"path": path, "disk": disk_node, "user": current_node})
        return (current_node if force else disk_node), True

    # base 存在:先处理删除
    if not disk_present and not current_present:
        return None, False                                   # 双方都删 → 删除
    if not disk_present:                                     # 外部删、用户保留
        if not _node_eq(current_node, base_node):
            conflicts.append({"path": path, "disk": disk_node, "user": current_node})
            return (current_node if force else None), True
        return None, False                                   # 用户没改 → 外部删除生效
    if not current_present:                                  # 用户删、外部保留
        if not _node_eq(disk_node, base_node):
            conflicts.append({"path": path, "disk": disk_node, "user": current_node})
            return (None if force else disk_node), True
        return None, False                                   # 外部没改 → 用户删除生效

    # 双方都在:类型变化 → 整节点
    base_kind = base_node.get("kind")
    if disk_node.get("kind") != base_kind or current_node.get("kind") != base_kind:
        if _node_eq(disk_node, current_node):
            return current_node, False
        conflicts.append({"path": path, "disk": disk_node, "user": current_node})
        return (current_node if force else disk_node), True

    return _merge_path_fields(path, base_node, disk_node, current_node, force, conflicts)


def save_flat(gbc_root: Path, base_flat: dict, current_flat: dict, force: bool = False) -> dict:
    """冲突感知的选择性保存(字段级三方合并)。

    重新读盘比较 external=base vs disk、user=base vs current:
    - 节点新增/删除/type change 按整节点冲突;
    - 三方都存在且 kind 相同:逐字段三方合并(file 仅 desc;folder 为 intent/constraints)。
    无冲突:以 disk 为合并基线只应用 user 改动,保留不相关外部变动,只重写内容变化的 gbc.md。
    force 仅覆盖冲突字段/冲突节点。返回 {"written", "deleted", "count"};冲突且 !force 抛
    IntentConflictError。
    """
    _validate_flat(base_flat)
    _validate_flat(current_flat)

    with _lock_for(str(gbc_root)):
        gbc_root.mkdir(parents=True, exist_ok=True)
        disk_flat = read_flat(gbc_root)

        all_paths = set(base_flat) | set(disk_flat) | set(current_flat)
        conflicts: list[dict] = []
        external_changes: list[str] = []
        merged: dict = {}
        for path in all_paths:
            base_node = base_flat.get(path)
            disk_node = disk_flat.get(path)
            current_node = current_flat.get(path)
            if not _node_eq(disk_node, base_node):
                external_changes.append(path)
            final, _ = _merge_path(path, base_node, disk_node, current_node, force, conflicts)
            if final is not None:
                merged[path] = final
        # 根节点永不可删
        merged.setdefault("", {"kind": "folder", "intent": "", "constraints": ""})

        if conflicts and not force:
            raise IntentConflictError(conflicts, external_changes)

        written, deleted = _apply_flat(gbc_root, disk_flat, merged)
    return {"written": written, "deleted": deleted, "count": len(written)}
