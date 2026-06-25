"""gbc.md 的领域 API + CLI —— 给 agent 用的、有结构与父子一致性保证的接口。

为什么存在:gbc.md 的结构(# 意图 / # 内部约束 / # 文件）与父子文档一致性是
确定性 + 重复的约束,必须由程序保证,不该由 agent 手编(手编会漂移、破坏结构）。
本模块在 gbc_format(parse/serialize)之上提供文件夹级操作,保存时把子文件夹意图
单源投影到父条目,并提供 check(漂移检测）与 migrate(批量升级格式)。

它和保证 MCP 是两条线、权限不同:意图人类持有,agent 经此「起草」、人类批准。

用法:
    python gbc_doc.py --root <项目目录或其 .gbc> <command> ...
命令:
    show         <folder>
    set-intent   <folder> <text>
    set-constraints <folder> <text>
    set-file     <folder> <name> <desc>
    rm-entry     <folder> <name>
    check
    sync
    migrate
    tree         （把整棵 .gbc 渲染成 AI 可读的依赖树:md 意图为骨、json 依赖边为注解）
其中 <folder> 是项目相对路径,根用 "" 或 "."。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import gbc_format as gf
from app import resolve_gbc, GBC_FILE


# ---- 路径与读写 -------------------------------------------------------------

def _norm(rel: str) -> str:
    """规范化文件夹相对路径:去首尾斜杠;'.' 与 '' 都表示根。"""
    rel = (rel or "").strip().strip("/")
    return "" if rel in ("", ".") else rel


def _doc_path(gbc_root: Path, rel: str) -> Path:
    return (gbc_root / rel / GBC_FILE) if rel else (gbc_root / GBC_FILE)


def read_doc(gbc_root: Path, rel: str) -> gf.ParsedDoc:
    p = _doc_path(gbc_root, rel)
    return gf.parse(p.read_text(encoding="utf-8")) if p.exists() else gf.ParsedDoc()


def write_doc(gbc_root: Path, rel: str, doc: gf.ParsedDoc) -> Path:
    p = _doc_path(gbc_root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(gf.serialize(doc.intent, doc.constraints, doc.entries), encoding="utf-8")
    return p


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


# ---- 操作 -------------------------------------------------------------------

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
        raise ValueError(f"文件名不应以 / 结尾(子文件夹请用 set-intent <folder>/<sub>): {name!r}")
    rel = _norm(rel)
    doc = read_doc(gbc_root, rel)
    entry = _find_entry(doc, name)
    if entry is not None and entry.is_dir:
        raise ValueError(f"{name!r} 已是子文件夹条目,不能当文件改")
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
        raise ValueError(f"未找到条目: {name!r}")
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


def check(gbc_root: Path) -> tuple[list[str], list[str]]:
    """全树一致性体检。返回 (errors, notes):

    errors = DRIFT(子有 gbc.md 且其意图与父条目描述不一致) / ORPHAN(子有 gbc.md 但父未登记);
    notes  = STUB(父登记了子文件夹条目但子无 gbc.md)——叶子文件夹(如 config/workspace)的
             正常状态,仅提示、不算错误。
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


# ---- tree:整棵 .gbc → AI 可读的依赖树 --------------------------------------

_LEGEND = "图例: 📁 文件夹 / 📄 文件 / → 依赖<provider:符号> [保证] / ⊕ 提供<保证> ← 被依赖"


def _block(text: str, indent: str) -> str:
    """把多行文本接到一个标签后:首行原位,后续行按 indent 对齐。"""
    parts = text.strip().splitlines()
    if not parts:
        return ""
    return parts[0] + "".join(f"\n{indent}{p}" for p in parts[1:])


def _load_meta(gbc_root: Path, rel: str, filename: str) -> dict | None:
    """读某文件条目同目录的 `gbc.<filename>.json`(依赖图元数据)。无/坏则 None。

    只 json.load 抽 depends_on/provides 两段,不依赖主库的 FileMeta 模型——工具自包含、语言无关。
    """
    base = (gbc_root / rel) if rel else gbc_root
    p = base / f"gbc.{filename}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _render_file(gbc_root: Path, rel: str, entry: gf.Entry, depth: int, lines: list[str]) -> None:
    pad = "  " * depth
    inner = pad + "   "
    lines.append(f"{pad}📄 {entry.name}")
    if entry.desc:
        lines.append(f"{inner}{_block(entry.desc, inner)}")
    meta = _load_meta(gbc_root, rel, entry.name)
    if not meta:
        return
    for dep in meta.get("depends_on") or []:
        sym = dep.get("symbol", "?")
        gids = dep.get("guarantees") or []
        tag = f"  [{', '.join(gids)}]" if gids else ""
        lines.append(f"{inner}→ {sym}{tag}")
    for gid, g in (meta.get("provides") or {}).items():
        deps = (g or {}).get("dependents") or []
        tail = f"  ← {', '.join(deps)}" if deps else ""
        lines.append(f"{inner}⊕ {gid}{tail}")


def _render_folder(gbc_root: Path, rel: str, depth: int, lines: list[str]) -> None:
    pad = "  " * depth
    inner = pad + "   "
    doc = read_doc(gbc_root, rel)
    lines.append(f"{pad}📁 {rel + '/' if rel else '(根)'}")
    if doc.intent:
        lines.append(f"{inner}[意图] {_block(doc.intent, inner)}")
    if doc.constraints:
        lines.append(f"{inner}[约束] {_block(doc.constraints, inner)}")
    # 按 gbc.md `# 文件` 的登记顺序渲染:文件叶子就地展开,子文件夹递归读其自身 gbc.md。
    for e in doc.entries:
        if not e.is_dir:
            _render_file(gbc_root, rel, e, depth + 1, lines)
            continue
        child = f"{rel}/{e.name.rstrip('/')}".lstrip("/")
        if _doc_path(gbc_root, child).exists():
            _render_folder(gbc_root, child, depth + 1, lines)
        else:  # 父登记了子文件夹但其 gbc.md 尚未建(叶子/待建)
            cpad = "  " * (depth + 1)
            lines.append(f"{cpad}📁 {e.name}(未建 gbc.md)")
            if e.desc:
                lines.append(f"{cpad}   {_block(e.desc, cpad + '   ')}")


def tree(gbc_root: Path) -> str:
    """一键把整棵 `.gbc` 渲染成一份 AI 可读的依赖树。

    骨架来自所有 gbc.md(意图 / 内部约束 / `# 文件` 条目,沿登记的包含关系递归);
    每个文件叶子再从同目录 `gbc.<name>.json` 折入依赖边(出边 depends_on)与所提供保证
    (provides + 反向 dependents)。一次调用替代逐个读散落的 gbc.md/json。
    """
    if not gbc_root.exists():
        return f"(.gbc 不存在: {gbc_root})"
    lines: list[str] = [_LEGEND, ""]
    _render_folder(gbc_root, "", 0, lines)
    return "\n".join(lines)


# ---- CLI --------------------------------------------------------------------

def main() -> None:
    try:  # WSL 调 Windows python 时强制 UTF-8 输出，避免中文走本地码页乱码
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="gbc.md 领域 CLI(agent 用,勿手编 gbc.md)")
    ap.add_argument("--root", required=True, help="项目目录或其 .gbc 目录")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def f(name, *args):
        sp = sub.add_parser(name)
        for a in args:
            sp.add_argument(a)
        return sp

    f("show", "folder")
    f("set-intent", "folder", "text")
    f("set-constraints", "folder", "text")
    f("set-file", "folder", "name", "desc")
    f("rm-entry", "folder", "name")
    sub.add_parser("check")
    sub.add_parser("sync")
    sub.add_parser("migrate")
    sub.add_parser("tree")

    args = ap.parse_args()
    gbc_root, _ = resolve_gbc(args.root)

    if args.cmd == "show":
        print(show(gbc_root, args.folder))
    elif args.cmd == "set-intent":
        for p in set_intent(gbc_root, args.folder, args.text):
            print("written:", p)
    elif args.cmd == "set-constraints":
        for p in set_constraints(gbc_root, args.folder, args.text):
            print("written:", p)
    elif args.cmd == "set-file":
        for p in set_file(gbc_root, args.folder, args.name, args.desc):
            print("written:", p)
    elif args.cmd == "rm-entry":
        for p in rm_entry(gbc_root, args.folder, args.name):
            print("written:", p)
    elif args.cmd == "check":
        errors, notes = check(gbc_root)
        for n in notes:
            print("note:", n)
        if not errors:
            print("✔ consistent")
        else:
            print(f"✘ {len(errors)} error(s):")
            for i in errors:
                print(" ", i)
            sys.exit(1)
    elif args.cmd == "sync":
        fixed = sync(gbc_root)
        print(f"synced {len(fixed)} parent entr(ies)")
        for x in fixed:
            print(" ", x)
    elif args.cmd == "migrate":
        changed = migrate(gbc_root)
        print(f"migrated {len(changed)} file(s)")
        for c in changed:
            print(" ", c)
    elif args.cmd == "tree":
        print(tree(gbc_root))


if __name__ == "__main__":
    main()
