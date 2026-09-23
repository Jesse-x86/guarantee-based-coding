# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Public tree entry points preserve parameter semantics and plain text output."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from click.testing import CliRunner
import pytest

from gbc.app.config import project
from gbc.app.interface import base, mcp
from gbc.app.intent import base as intent_base
from gbc.entry import get_wrapped_app


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("GBC_LANG", "en")
    monkeypatch.setattr(project, "CURRENT_PROJECT", tmp_path)


class TestCliTree:
    @pytest.mark.parametrize("args, expected", [
        (["show"], {"folder": "", "depth": None, "detail": False, "gaps": False}),
        (["show", "--detail", "--gaps"],
         {"folder": "", "depth": None, "detail": True, "gaps": True}),
        (["show", "src", "--depth", "1", "--detail"],
         {"folder": "src", "depth": 1, "detail": True, "gaps": False}),
        (["folders", "src", "--depth", "0"],
         {"folder": "src", "depth": 0, "folders_only": True}),
    ])
    def test_browse_dispatch(self, monkeypatch, tmp_path, args, expected):
        calls = []
        def render(**kwargs):
            calls.append((kwargs, project.get_current_project()))
            return "[intent]\nplain text"
        monkeypatch.setattr(base, "render_tree", render)
        result = CliRunner().invoke(get_wrapped_app(), ["tree", *args, "-C", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert result.output == "[intent]\nplain text\n"
        assert calls == [(expected, tmp_path)]

    @pytest.mark.parametrize("with_project", [False, True])
    @pytest.mark.parametrize("lang", ["en", "zh"])
    def test_bare_tree_only_help(self, monkeypatch, tmp_path, with_project, lang):
        monkeypatch.setenv("GBC_LANG", lang)
        def forbidden(*args, **kwargs):
            pytest.fail("Bare tree must not resolve or read the project tree")
        monkeypatch.setattr(base, "render_tree", forbidden)
        monkeypatch.setattr(base, "render_tree_for", forbidden)
        monkeypatch.setattr(project, "get_current_project", forbidden)
        monkeypatch.setattr(project, "set_current_project", forbidden)
        args = ["tree"]
        if with_project:
            args += ["-C", str(tmp_path / "nonexistent-project")]
        result = CliRunner().invoke(get_wrapped_app(), args)
        assert result.exit_code == 0, result.output
        for command in ("show", "folders", "for"):
            assert command in result.output
        assert "cli.tree." not in result.output
        assert "--detail" not in result.output
        assert "--gaps" not in result.output

    @pytest.mark.parametrize("option", ["--detail", "-d", "--gaps", "-g"])
    @pytest.mark.parametrize("leaf", [[], ["show"], ["folders"], ["for", "a.py"]])
    @pytest.mark.parametrize("lang, message", [("en", "were removed"), ("zh", "已移除")])
    def test_removed_group_options(self, monkeypatch, option, leaf, lang, message):
        monkeypatch.setenv("GBC_LANG", lang)
        def forbidden(*args, **kwargs):
            pytest.fail("Removed options must not read the tree")
        monkeypatch.setattr(base, "render_tree", forbidden)
        monkeypatch.setattr(base, "render_tree_for", forbidden)
        result = CliRunner().invoke(get_wrapped_app(), ["tree", option, *leaf])
        assert result.exit_code != 0
        assert "tree show" in result.output
        assert message in result.output

    @pytest.mark.parametrize("args", [
        ["--detail", "show"], ["--gaps", "folders"], ["--detail", "for", "a.py"],
        ["for"], ["for", "a.py", "--depth", "1"], ["for", "a.py", "--folders"],
        ["for", "a.py", "--detail"],
    ])
    def test_reject_inapplicable_options(self, monkeypatch, args):
        calls = []
        monkeypatch.setattr(base, "render_tree", lambda **kw: calls.append(kw))
        monkeypatch.setattr(base, "render_tree_for", lambda files: calls.append(files))
        result = CliRunner().invoke(get_wrapped_app(), ["tree", *args])
        assert result.exit_code != 0
        assert calls == []

    @pytest.mark.parametrize("leaf", [[], ["show"], ["folders"], ["for"]])
    @pytest.mark.parametrize("lang", ["en", "zh"])
    def test_help(self, leaf, lang, monkeypatch):
        monkeypatch.setenv("GBC_LANG", lang)
        result = CliRunner().invoke(get_wrapped_app(), ["tree", *leaf, "--help"])
        assert result.exit_code == 0, result.output
        assert "cli.tree." not in result.output
        assert "--project" in result.output

    def test_for_multiple_files_real_entry(self, tmp_path):
        intent_base.set_intent(tmp_path / ".gbc", "", "ROOT CONTEXT")
        intent_base.set_intent(tmp_path / ".gbc", "src", "SOURCE CONTEXT")
        intent_base.set_file(tmp_path / ".gbc", "src", "a.py", "TARGET A")
        intent_base.set_file(tmp_path / ".gbc", "src", "b.py", "TARGET B")
        env = os.environ.copy()
        env["GBC_PROJECT_ROOT"] = str(tmp_path / "wrong-root")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "gbc.entry", "tree", "for",
             "src/a.py", "src/b.py", "-C", str(tmp_path)],
            cwd=Path(__file__).resolve().parents[1], env=env,
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        for text in ("ROOT CONTEXT", "SOURCE CONTEXT", "TARGET A", "TARGET B", "src/a.py", "src/b.py"):
            assert text in result.stdout

    def test_show_full_tree(self, tmp_path):
        intent_base.set_intent(tmp_path / ".gbc", "", "ROOT CONTEXT")
        intent_base.set_intent(tmp_path / ".gbc", "src", "SOURCE CONTEXT")
        intent_base.set_intent(tmp_path / ".gbc", "src/nested", "NESTED CONTEXT")
        intent_base.set_file(tmp_path / ".gbc", "src/nested", "a.py", "TARGET A")
        result = CliRunner().invoke(get_wrapped_app(), ["tree", "show", "-C", str(tmp_path)])
        assert result.exit_code == 0, result.output
        for text in ("ROOT CONTEXT", "NESTED CONTEXT", "TARGET A"):
            assert text in result.output

    @pytest.mark.parametrize("lang, message", [("en", "were removed"), ("zh", "已移除")])
    def test_removed_options_real_entry(self, lang, message):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "gbc.entry", "--lang", lang,
             "tree", "--detail"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        output = result.stdout + result.stderr
        assert result.returncode != 0
        assert "tree show" in output
        assert message in output
        assert "Traceback" not in output


class TestMcpTree:
    def test_registered_and_forwarded(self, monkeypatch):
        names = {tool.name for tool in asyncio.run(mcp.mcp.list_tools())}
        assert {"tree", "tree_for"} <= names
        calls = []
        monkeypatch.setattr(base, "render_tree", lambda **kw: calls.append(kw) or "[intent]\nraw")
        monkeypatch.setattr(base, "render_tree_for", lambda files: calls.append(files) or "[context]\nraw")
        assert mcp.tree() == "[intent]\nraw"
        assert calls.pop() == dict(detail=False, gaps=False, folder="", depth=None, folders_only=False)
        assert mcp.tree(True, True, "src", 0, True) == "[intent]\nraw"
        assert calls.pop() == dict(detail=True, gaps=True, folder="src", depth=0, folders_only=True)
        assert mcp.tree_for(["a.py", "b.py"]) == "[context]\nraw"
        assert calls.pop() == ["a.py", "b.py"]

    @pytest.mark.parametrize("name,args", [("tree", {}), ("tree_for", {"files": ["a.py"]})])
    def test_errors_are_structured(self, monkeypatch, name, args):
        def fail(*args, **kwargs):
            raise ValueError("invalid target")
        monkeypatch.setattr(base, "render_tree" if name == "tree" else "render_tree_for", fail)
        assert "invalid target" in json.loads(getattr(mcp, name)(**args))["error"]
