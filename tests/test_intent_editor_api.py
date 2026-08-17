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

"""保证:意图编辑器的「文件条目 → .gbc json 只读视图」后端支持。

覆盖 base.file_meta_view 的只读视图语义(存在/缺失/损坏),以及 editor 的
/api/file-meta、/api/config(含 lang)、静态资源 MIME 三个 web 表面承诺。
"""
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

import pytest

from gbc.app.intent import base
from gbc.app.intent import editor
from gbc.app.i18n.lang import resolve_lang
from gbc.app.models.errors import IntentDocError
from gbc.app.models.meta import FileMeta, Guarantee, Dependency
from gbc.app.utils.json_model_operator import save_model_to_json


def _serve():
    """在随机端口起一个 editor.Handler 服务,返回 (server, port)。"""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), editor.Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    return srv, srv.server_address[1]


def _get(port: int, path: str):
    return urlopen(f"http://127.0.0.1:{port}{path}")


# ---------------------------------------------------------------------------
# base.file_meta_view
# ---------------------------------------------------------------------------

def test_file_meta_view_returns_readonly_shape(tmp_path):
    """承诺:file_meta_view 把 FileMeta 读成 {provides, depends_on} 只读视图。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    meta = FileMeta(
        provides={
            "mk.returns_x": Guarantee(
                desc="returns x", test="tests/test_x.py", executor="pytest-gbc-v2",
                dependents=["app/consumer.py"],
            ),
            "mk.disabled_g": Guarantee(
                desc="disabled one", test="t", executor="pytest-gbc-v2", disabled=True,
            ),
        },
        depends_on=[Dependency(symbol="gbc/app/lib.py:helper", guarantees=["helper.works"])],
    )
    save_model_to_json(meta, gbc_root / "app" / "gbc.main.py.json")

    view = base.file_meta_view(gbc_root, "app/main.py")

    assert view is not None
    provides = {p["id"]: p for p in view["provides"]}
    assert set(provides) == {"mk.returns_x", "mk.disabled_g"}
    assert provides["mk.returns_x"]["desc"] == "returns x"
    assert provides["mk.returns_x"]["disabled"] is False
    assert provides["mk.returns_x"]["dependents"] == ["app/consumer.py"]
    assert provides["mk.disabled_g"]["disabled"] is True

    dep = view["depends_on"][0]
    assert dep["symbol"] == "gbc/app/lib.py:helper"
    assert dep["provider"] == "gbc/app/lib.py"
    assert dep["guarantees"] == ["helper.works"]


def test_file_meta_view_root_level_file(tmp_path):
    """承诺:根层文件条目(rel 为空)也能定位到 .gbc/gbc.<name>.json。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    meta = FileMeta(provides={"top.x": Guarantee(desc="d", test="t", executor="e")})
    save_model_to_json(meta, gbc_root / "gbc.top.py.json")

    view = base.file_meta_view(gbc_root, "top.py")

    assert view is not None
    assert {p["id"] for p in view["provides"]} == {"top.x"}


def test_file_meta_view_none_when_missing_and_readonly(tmp_path):
    """承诺:json 缺失返回 None,且绝不创建缺失 json(只读)。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))

    assert base.file_meta_view(gbc_root, "app/missing.py") is None
    assert not (gbc_root / "app" / "gbc.missing.py.json").exists()


def test_file_meta_view_none_on_corrupt_json(tmp_path):
    """承诺:json 存在但解析失败时返回 None,不抛错。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    p = gbc_root / "app" / "gbc.bad.py.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not json", encoding="utf-8")

    assert base.file_meta_view(gbc_root, "app/bad.py") is None


def test_file_meta_view_rejects_illegal_paths(tmp_path):
    """承诺:file_meta_view 复用 _validate_path 校验完整语义文件路径;
    root / folder 尾斜杠 / 绝对 / .. / 反斜杠 / 空段 / 空 name 均抛 IntentDocError。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    illegal = [
        "",              # root 非法
        "app/",          # folder 尾斜杠非法
        "/abs.py",       # 绝对路径
        "../x.py",       # 父目录逃逸
        "a/../b.py",
        "a\\b.py",       # 反斜杠
        "C:/win.py",     # Windows 盘符
        "a//b.py",       # 空段
        " a.py",         # 首尾空白
        "a.py ",
        "./a.py",
    ]
    for p in illegal:
        with pytest.raises(IntentDocError):
            base.file_meta_view(gbc_root, p)


def test_file_meta_view_accepts_file_paths(tmp_path):
    """承诺:合法 file 路径(含根层文件)不抛,可正常定位(存在/缺失均不炸)。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    assert base.file_meta_view(gbc_root, "app/main.py") is None
    assert base.file_meta_view(gbc_root, "top.py") is None


# ---------------------------------------------------------------------------
# editor /api/file-meta
# ---------------------------------------------------------------------------

def test_api_file_meta_route(tmp_path):
    """承诺:/api/file-meta 经 base 返回文件元数据只读视图。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    meta = FileMeta(provides={"f.x": Guarantee(desc="d", test="t", executor="e")})
    save_model_to_json(meta, gbc_root / "app" / "gbc.main.py.json")

    srv, port = _serve()
    try:
        url = f"http://127.0.0.1:{port}/api/file-meta?" + urlencode(
            {"root": str(tmp_path), "path": "app/main.py"}
        )
        with urlopen(url) as r:
            assert r.status == 200
            body = json.loads(r.read().decode("utf-8"))
        assert body["meta"] is not None
        assert {p["id"] for p in body["meta"]["provides"]} == {"f.x"}
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_file_meta_400_invalid_and_null_when_missing(tmp_path):
    """承诺:path 非法(缺省/folder 尾斜杠/绝对/../反斜杠)返回 400;json 缺失返回 200 且 meta 为 null。"""
    srv, port = _serve()
    try:
        illegal = [
            None,          # path 缺省 → 空串(root)非法
            "app/",        # folder 尾斜杠
            "/abs.py",     # 绝对路径
            "../x.py",     # 父目录逃逸
            "a\\b.py",     # 反斜杠
        ]
        for path in illegal:
            q = {"root": str(tmp_path)}
            if path is not None:
                q["path"] = path
            with pytest.raises(HTTPError) as ei:
                _get(port, "/api/file-meta?" + urlencode(q))
            assert ei.value.code == 400, path

        # json 缺失 → 200 + meta: null
        url = "/api/file-meta?" + urlencode(
            {"root": str(tmp_path), "path": "app/nope.py"}
        )
        with _get(port, url) as r:
            assert r.status == 200
            body = json.loads(r.read().decode("utf-8"))
        assert body["meta"] is None
    finally:
        srv.shutdown()
        srv.server_close()


# ---------------------------------------------------------------------------
# editor /api/config 含 lang
# ---------------------------------------------------------------------------

def test_api_config_has_lang():
    """承诺:/api/config 返回当前语言码(与 resolve_lang() 一致)。"""
    srv, port = _serve()
    try:
        with _get(port, "/api/config") as r:
            assert r.status == 200
            body = json.loads(r.read().decode("utf-8"))
        assert body["root"] == ""
        assert body["lang"] == resolve_lang()
    finally:
        srv.shutdown()
        srv.server_close()


# ---------------------------------------------------------------------------
# 静态资源 MIME
# ---------------------------------------------------------------------------

def test_static_mime_types(tmp_path, monkeypatch):
    """承诺:静态资源按后缀给正确 Content-Type(.js/.css/.json 不再 text/plain)。"""
    front = tmp_path / "front"
    front.mkdir()
    (front / "index.html").write_text("<html></html>", encoding="utf-8")
    (front / "app.js").write_text("console.log(1)", encoding="utf-8")
    (front / "style.css").write_text("body{}", encoding="utf-8")
    (front / "data.json").write_text("{}", encoding="utf-8")
    (front / "note.txt").write_text("hi", encoding="utf-8")
    monkeypatch.setattr(editor, "FRONTEND_DIR", front)

    cases = {
        "/index.html": "text/html; charset=utf-8",
        "/app.js": "application/javascript; charset=utf-8",
        "/style.css": "text/css; charset=utf-8",
        "/data.json": "application/json; charset=utf-8",
        "/note.txt": "text/plain; charset=utf-8",
    }
    srv, port = _serve()
    try:
        for path, expected in cases.items():
            with _get(port, path) as r:
                assert r.status == 200
                assert r.headers["Content-Type"] == expected, path
    finally:
        srv.shutdown()
        srv.server_close()


# ---------------------------------------------------------------------------
# 新前端 API:/api/tree-flat 与 /api/save(冲突感知选择性保存)
# ---------------------------------------------------------------------------

def _post(port: int, path: str, body: dict):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(f"http://127.0.0.1:{port}{path}", data=data,
                  headers={"Content-Type": "application/json"})
    return urlopen(req)


EMPTY_FLAT = {"": {"kind": "folder", "intent": "", "constraints": ""}}


def test_api_tree_flat_returns_flat_map(tmp_path):
    """承诺:GET /api/tree-flat 返回 {root, name, tree} flat map;folder 以 / 结尾。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path / "proj"))
    base.save_flat(gbc_root, EMPTY_FLAT, {
        "": {"kind": "folder", "intent": "", "constraints": ""},
        "app/": {"kind": "folder", "intent": "app intent", "constraints": ""},
        "app/main.py": {"kind": "file", "desc": "main desc"},
    })

    srv, port = _serve()
    try:
        url = "/api/tree-flat?" + urlencode({"root": str(tmp_path / "proj")})
        with _get(port, url) as r:
            assert r.status == 200
            body = json.loads(r.read().decode("utf-8"))
        assert body["name"] == "proj"
        assert body["tree"]["app/"] == {"kind": "folder", "intent": "app intent", "constraints": ""}
        assert body["tree"]["app/main.py"] == {"kind": "file", "desc": "main desc"}
        assert "" in body["tree"]
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_tree_flat_empty_root(tmp_path):
    """承诺:root 不存在 -> 200 仅根节点的空树。"""
    srv, port = _serve()
    try:
        url = "/api/tree-flat?" + urlencode({"root": str(tmp_path / "nope")})
        with _get(port, url) as r:
            assert r.status == 200
            body = json.loads(r.read().decode("utf-8"))
        assert body["tree"] == EMPTY_FLAT
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_save_contract_200(tmp_path):
    """承诺:POST /api/save 成功返回 {written, deleted, count}。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path / "proj"))
    srv, port = _serve()
    try:
        body = {"root": str(tmp_path / "proj"), "base": EMPTY_FLAT, "current": {
            "": {"kind": "folder", "intent": "r", "constraints": ""}}}
        with _post(port, "/api/save", body) as r:
            assert r.status == 200
            resp = json.loads(r.read().decode("utf-8"))
        assert resp["count"] == 1
        assert resp["written"] == [str(gbc_root / "gbc.md")]
        assert resp["deleted"] == []
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_save_conflict_409_and_force_200(tmp_path):
    """承诺:同路径冲突 -> 409 {error:conflict,...};force 后 200 且用户值落盘。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path / "proj"))
    base_flat = {"": {"kind": "folder", "intent": "", "constraints": ""},
                 "main.py": {"kind": "file", "desc": "base desc"}}
    base.save_flat(gbc_root, EMPTY_FLAT, base_flat)

    # 外部改盘上值(直接改根文档的 main.py 条目)
    pdoc = base.read_doc(gbc_root, "")
    for e in pdoc.entries:
        if e.name.rstrip("/") == "main.py":
            e.desc = "external desc"
    base.write_doc(gbc_root, "", pdoc)

    current = {"": {"kind": "folder", "intent": "", "constraints": ""},
               "main.py": {"kind": "file", "desc": "user desc"}}

    srv, port = _serve()
    try:
        # 非 force -> 409
        with pytest.raises(HTTPError) as ei:
            _post(port, "/api/save", {"root": str(tmp_path / "proj"), "base": base_flat,
                                      "current": current, "force": False})
        assert ei.value.code == 409
        err = json.loads(ei.value.read().decode("utf-8"))
        assert err["error"] == "conflict"
        assert err["conflicts"][0]["path"] == "main.py"
        assert err["conflicts"][0]["disk"]["desc"] == "external desc"
        assert err["conflicts"][0]["user"]["desc"] == "user desc"

        # force -> 200 用户值落盘
        with _post(port, "/api/save", {"root": str(tmp_path / "proj"), "base": base_flat,
                                       "current": current, "force": True}) as r:
            assert r.status == 200
        assert base.read_flat(gbc_root)["main.py"]["desc"] == "user desc"
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_save_invalid_body_400(tmp_path):
    """承诺:路径/节点非法 -> 400。"""
    srv, port = _serve()
    try:
        bad_current = {"": {"kind": "folder", "intent": "", "constraints": ""},
                       "/abs.py": {"kind": "file", "desc": "d"}}
        with pytest.raises(HTTPError) as ei:
            _post(port, "/api/save", {"root": str(tmp_path / "proj"), "base": EMPTY_FLAT,
                                      "current": bad_current})
        assert ei.value.code == 400
    finally:
        srv.shutdown()
        srv.server_close()


def test_api_tree_post_legacy_disabled(tmp_path):
    """承诺:POST /api/tree(旧盲写入口)已关闭,返回 410 结构化错误,绝不写盘。"""
    gbc_root, _ = base.resolve_gbc(str(tmp_path / "proj"))
    srv, port = _serve()
    try:
        body = {"root": str(tmp_path / "proj"), "tree": {
            "name": "proj", "path": "", "intent": "sneaky", "constraints": "", "entries": []}}
        with pytest.raises(HTTPError) as ei:
            _post(port, "/api/tree", body)
        assert ei.value.code == 410
        err = json.loads(ei.value.read().decode("utf-8"))
        assert err["error"] == "legacy save endpoint disabled; use /api/save"
        # 绝未写盘
        assert not (gbc_root / "gbc.md").exists()
    finally:
        srv.shutdown()
        srv.server_close()
