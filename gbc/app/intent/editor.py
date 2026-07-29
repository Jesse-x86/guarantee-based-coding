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

"""意图编辑器的 web 表面 —— 薄。

只做 HTTP 收发 + 静态资源;所有 gbc.md 的解析/读写/整树读写都调 intent.base,
本模块不自己解析路径、不自己拼 gbc.md。`gbc editor up` 调 run_editor()。
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from gbc.app.intent import base

FRONTEND_DIR = Path(__file__).resolve().parent / "editor_static"

# 前端预填 + 自动加载的默认项目路径(经 --root 设定)。
DEFAULT_ROOT = ""


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
            gbc_root, proj_name = base.resolve_gbc((qs.get("root") or [""])[0])
            if gbc_root.exists() and not gbc_root.is_dir():
                return self._json(404, {"error": f"not a directory: {gbc_root}"})
            # 路径不存在也 OK:回一棵空树从头开始
            tree = base.read_tree(gbc_root) if gbc_root.exists() else base.empty_tree(gbc_root)
            tree["name"] = proj_name           # 展示项目,而非 .gbc 层
            return self._json(200, tree)
        # 静态资源:根路径给 index.html,或 frontend 下任意文件
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
            gbc_root, _ = base.resolve_gbc(req["root"])
            if gbc_root.exists() and not gbc_root.is_dir():
                return self._json(404, {"error": f"not a directory: {gbc_root}"})
            gbc_root.mkdir(parents=True, exist_ok=True)  # 首次保存时建 <project>/.gbc
            written = base.write_tree(gbc_root, req["tree"])
            return self._json(200, {"written": written, "count": len(written)})
        except Exception as exc:  # noqa: BLE001 - 报回客户端
            return self._json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):  # 静默控制台
        return


def run_editor(host: str = "127.0.0.1", port: int = 8765, root: str = "") -> None:
    """启动意图编辑器 web 服务(常驻,Ctrl-C 退出)。root 为可选默认项目路径。"""
    global DEFAULT_ROOT
    if root:
        DEFAULT_ROOT = str(Path(root).expanduser())
    srv = ThreadingHTTPServer((host, port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
