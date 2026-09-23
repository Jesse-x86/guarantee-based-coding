# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Intent editing and bundled documentation have separate MCP namespaces."""
import asyncio
import json

import pytest

from gbc.app.config import project
from gbc.app.interface import mcp as M


@pytest.fixture(autouse=True)
def isolate_project_and_language(monkeypatch, tmp_path):
    monkeypatch.setattr(project, "CURRENT_PROJECT", tmp_path)
    monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("GBC_LANG", "en")


class TestIntentTools:
    def test_registered_without_old_aliases(self):
        names = {tool.name for tool in asyncio.run(M.mcp.list_tools())}
        for suffix in ("show", "check", "set_intent", "set_constraints", "set_file",
                       "rm_entry", "sync", "migrate"):
            assert "intent_" + suffix in names
            assert "doc_" + suffix not in names
            assert not hasattr(M, "doc_" + suffix)

    def test_edit_show_check_roundtrip(self, tmp_path):
        written = json.loads(M.intent_set_intent("sub", "intent via mcp"))
        assert isinstance(written, list) and written
        assert "intent via mcp" in M.intent_show("sub")
        assert "error" not in json.loads(M.intent_set_constraints("sub", "local only"))
        assert "error" not in json.loads(M.intent_set_file("sub", "item.py", "file purpose"))
        shown = M.intent_show("sub")
        assert "local only" in shown and "file purpose" in shown
        assert "error" not in json.loads(M.intent_rm_entry("sub", "item.py"))
        assert "file purpose" not in M.intent_show("sub")
        result = json.loads(M.intent_check())
        assert result["errors"] == [] and isinstance(result["notes"], list)
        assert isinstance(json.loads(M.intent_sync()), list)
        assert isinstance(json.loads(M.intent_migrate()), list)
        assert (tmp_path / ".gbc" / "sub" / "gbc.md").is_file()


class TestDocumentationTools:
    def test_registered_queries_read_real_bundled_docs_without_project(self, monkeypatch, tmp_path):
        def forbidden():
            pytest.fail("Documentation must not resolve the target project")
        monkeypatch.setattr(project, "get_current_project", forbidden)
        names = {tool.name for tool in asyncio.run(M.mcp.list_tools())}
        assert {"doc_list", "doc_read", "doc_search"} <= names
        listed = json.loads(M.doc_list(lang="en"))
        assert listed["language"] == "en"
        assert {row["id"] for row in listed["topics"]} == {
            "quick-start", "concepts", "workflow", "reference", "onboarding-agent"
        }
        text = M.doc_read("quick-start", lang="en")
        assert isinstance(text, str) and "gbc" in text.lower()
        found = json.loads(M.doc_search("gbc", lang="en", limit=1))
        assert found["language"] == "en"
        assert len(found["matches"]) == 1
        match = found["matches"][0]
        assert "gbc" in match["text"].lower()
        source = M.doc_read(match["topic"], lang="en")
        assert match["text"] in source.splitlines()[match["line"] - 1]
        assert not (tmp_path / ".gbc").exists()

    @pytest.mark.parametrize("name,args", [
        ("doc_list", {"lang": "unsupported"}),
        ("doc_read", {"topic": "../outside", "lang": "en"}),
        ("doc_read", {"topic": "missing", "lang": "en"}),
        ("doc_search", {"query": " ", "lang": "en"}),
        ("doc_search", {"query": "gbc", "limit": 0, "lang": "en"}),
    ])
    def test_invalid_queries_are_structured_errors(self, name, args):
        result = json.loads(getattr(M, name)(**args))
        assert isinstance(result["error"], str) and result["error"]

    def test_explicit_language_does_not_change_following_requests(self):
        from gbc.app.i18n import current_lang
        before = current_lang()
        assert json.loads(M.doc_list(lang="zh"))["language"] == "zh"
        assert current_lang() == before
        assert json.loads(M.doc_list())["language"] == "en"
