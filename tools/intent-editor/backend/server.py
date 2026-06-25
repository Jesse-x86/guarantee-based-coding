"""GBC intent-tree editor — thin local backend (stdlib only; shares the main lib's parser).

Run:  python3 server.py [--port 8765]
Then: open http://localhost:8765

Two jobs only:
  GET  /api/tree?root=<project dir, or its .gbc>  -> nested node tree (parsed)
  POST /api/tree   body {root, tree}              -> write the tree back to gbc.md files

`root` may be a project dir (content read/written under `<project>/.gbc/`) or the
`.gbc` dir itself — both behave identically; the `.gbc` layer is hidden (resolve_gbc).

Single source of truth lives in the editor's tree model. A subfolder's intent is
written in two render locations (its own `# 意图` AND the parent's `## sub/` entry);
on save both are generated from the one `child["intent"]`, so they can never drift.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sys

# 让 `from app...` 解析到本仓主库包(而非目标项目的同名 app/):把 GBC 仓根放 sys.path 最前。
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.utils import gbc_md as gf  # noqa: E402  gbc.md 解析器单源(取代旧的本地 gbc_format)

GBC_FILE = "gbc.md"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Optional default directory the frontend prefills + auto-loads (set via --root).
DEFAULT_ROOT = ""


def empty_node(abs_dir: Path) -> dict:
    return {"name": abs_dir.name, "path": "", "intent": "", "constraints": "", "entries": []}


def resolve_gbc(root_str: str) -> tuple[Path, str]:
    """Map a user-supplied path to (gbc_root, project_name).

    The `.gbc` mirror layer is hidden from the tree: the displayed root is the
    *project* directory, while content always lives under `<project>/.gbc/`.
      - path ends in `.gbc`  -> gbc_root = path,        project = path.parent.name
      - otherwise            -> gbc_root = path/.gbc,    project = path.name
    So loading `…/AIGameGen` and `…/AIGameGen/.gbc` behave identically.
    """
    p = Path(root_str).expanduser().resolve()
    if p.name == ".gbc":
        return p, p.parent.name
    return p / ".gbc", p.name


# ---- read: filesystem -> tree (plain dicts) --------------------------------

def build_node(abs_dir: Path, rel: str) -> dict:
    md = abs_dir / GBC_FILE
    doc = gf.parse(md.read_text(encoding="utf-8")) if md.exists() else gf.ParsedDoc()

    # entry kind is derived from the name's trailing "/" (no stored "type" field),
    # so the editor can flip a file <-> folder just by editing the name.
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
            child = build_node(child_abs, child_rel)  # child's own gbc.md is authoritative
        else:
            # listed in parent but no folder/gbc.md yet — keep the text as a stub
            child = {"name": child_name, "path": child_rel,
                     "intent": e.desc, "constraints": "", "entries": []}
        entries.append({"name": e.name, "child": child})

    # documented subfolders not referenced by any `## sub/` entry — surface them too
    for sub in sorted(p for p in abs_dir.iterdir() if p.is_dir() and (p / GBC_FILE).exists()):
        if sub.name in seen_dirs:
            continue
        child_rel = f"{rel}/{sub.name}".lstrip("/") if rel else sub.name
        child = build_node(sub, child_rel)
        entries.append({"name": f"{sub.name}/", "child": child})

    return {"name": abs_dir.name, "path": rel,
            "intent": doc.intent, "constraints": doc.constraints, "entries": entries}


# ---- write: tree -> filesystem ---------------------------------------------

def _is_dir(name: str) -> bool:
    return name.rstrip().endswith("/")


def write_node(node_dir: Path, node: dict, written: list[str]) -> None:
    # Target dir is derived from tree structure (parent dir + entry name), so renaming
    # a folder writes to the new place — we never trust a stored path.
    node_dir.mkdir(parents=True, exist_ok=True)

    gf_entries: list[gf.Entry] = []
    for e in node["entries"]:
        if not e["name"].strip():
            continue  # skip blank "ghost" rows
        if _is_dir(e["name"]):
            child = e.get("child") or {}
            # single source: the parent entry's text IS the child's intent
            gf_entries.append(gf.Entry(name=e["name"], is_dir=True, desc=child.get("intent", "")))
        else:
            gf_entries.append(gf.Entry(name=e["name"], is_dir=False, desc=e.get("desc", "")))

    text = gf.serialize(node["intent"], node.get("constraints", ""), gf_entries)
    (node_dir / GBC_FILE).write_text(text, encoding="utf-8")
    written.append(str(node_dir / GBC_FILE))

    for e in node["entries"]:
        if e["name"].strip() and _is_dir(e["name"]) and e.get("child"):
            child_dir = node_dir / e["name"].rstrip().rstrip("/")
            write_node(child_dir, e["child"], written)


# ---- http handler ----------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            return self._json(200, {"root": DEFAULT_ROOT})
        if parsed.path == "/api/tree":
            qs = parse_qs(parsed.query)
            gbc_root, proj_name = resolve_gbc((qs.get("root") or [""])[0])
            if gbc_root.exists() and not gbc_root.is_dir():
                return self._json(404, {"error": f"not a directory: {gbc_root}"})
            # a missing path is fine: hand back an empty tree to start from scratch
            tree = build_node(gbc_root, "") if gbc_root.exists() else empty_node(gbc_root)
            tree["name"] = proj_name           # show the project, not the .gbc layer
            return self._json(200, tree)
        # static: index.html at "/", or any file under frontend/
        name = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        fpath = (FRONTEND_DIR / name).resolve()
        if FRONTEND_DIR in fpath.parents and fpath.is_file():
            ctype = "text/html; charset=utf-8" if fpath.suffix == ".html" else "text/plain"
            return self._send(200, fpath.read_bytes(), ctype)
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/tree":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
            gbc_root, _ = resolve_gbc(req["root"])
            if gbc_root.exists() and not gbc_root.is_dir():
                return self._json(404, {"error": f"not a directory: {gbc_root}"})
            gbc_root.mkdir(parents=True, exist_ok=True)  # create <project>/.gbc on first save
            written: list[str] = []
            write_node(gbc_root, req["tree"], written)
            return self._json(200, {"written": written, "count": len(written)})
        except Exception as exc:  # noqa: BLE001 - report to client
            return self._json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):  # quieter console
        return


def main() -> None:
    global DEFAULT_ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--root", default="", help="default .gbc dir to prefill + auto-load")
    args = ap.parse_args()
    if args.root:
        DEFAULT_ROOT = str(Path(args.root).expanduser())
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"GBC intent editor → http://{args.host}:{args.port}  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
