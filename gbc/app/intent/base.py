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

from gbc.app.utils import gbc_md as gf
from gbc.app.models.errors import IntentDocError

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
