# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Public guarantees for offline manual queries and their CLI surface."""

import json

import pytest
from typer.testing import CliRunner

from gbc.app.documentation import base
from gbc.app.documentation.cli import doc_app
from gbc.app.i18n import lang as language

TOPICS = ["quick-start", "concepts", "workflow", "reference", "onboarding-agent"]


@pytest.fixture(autouse=True)
def restore_language(monkeypatch):
    monkeypatch.setattr(language, "_current", "en")


@pytest.fixture
def tiny_manual(tmp_path, monkeypatch):
    root = tmp_path / "manual"
    for lang in ("en", "zh"):
        for topic in TOPICS:
            path = root / lang / f"{topic}.md"
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(f"# {lang} {topic}\n", encoding="utf-8")
    monkeypatch.setattr(base, "DOCS_DIR", root)
    return root


class TestManualBase:
    def test_bundled_topics_are_readable_without_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from gbc.app.config import project

        def no_project(*args, **kwargs):
            pytest.fail("Manual queries must not inspect a target project")

        monkeypatch.setattr(project, "get_current_project", no_project)
        for lang in ("en", "zh"):
            result = base.list_topics(lang)
            assert result["language"] == lang
            assert [topic["id"] for topic in result["topics"]] == TOPICS
            assert all(topic["title"] for topic in result["topics"])
            for topic in TOPICS:
                assert base.read_topic(topic, lang).startswith("# ")
        assert list(tmp_path.iterdir()) == []

    def test_language_is_per_request_and_reuses_resolution(self, monkeypatch):
        monkeypatch.setenv("GBC_LANG", "zh")
        language.set_lang("en")
        assert base.list_topics()["language"] == "zh"
        assert base.list_topics("EN-us")["language"] == "en"
        assert base.list_topics("zh_CN.UTF-8")["language"] == "zh"
        assert language.current_lang() == "en"

    @pytest.mark.parametrize("topic", ["../reference", "reference.md", "/reference", "", "unknown"])
    def test_topic_ids_are_whitelisted(self, topic):
        with pytest.raises(base.DocumentationError):
            base.read_topic(topic, "en")

    @pytest.mark.parametrize("lang", ["fr", "../en", "", "  "])
    def test_invalid_language_is_explicit_error(self, lang):
        with pytest.raises(base.DocumentationError):
            base.list_topics(lang)

    def test_literal_search_lines_limits_and_no_matches(self, tiny_manual):
        (tiny_manual / "en" / "quick-start.md").write_text(
            "# Intro\nLiteral A.*B\nAxxB\nliteral a.*b repeated a.*b\n", encoding="utf-8")
        result = base.search_docs("a.*b", "en", 1)
        assert result["query"] == "a.*b"
        assert result["language"] == "en"
        assert result["matches"] == [{"topic": "quick-start", "line": 2, "text": "Literal A.*B"}]
        assert result["truncated"] is True
        all_matches = base.search_docs("A.*B", "en", 2)
        assert [match["line"] for match in all_matches["matches"]] == [2, 4]
        assert all_matches["truncated"] is False
        empty = base.search_docs("not-in-this-manual", "en")
        assert empty["matches"] == [] and empty["truncated"] is False

    def test_snippets_are_bounded_and_contain_late_unicode_match(self, tiny_manual):
        line = "ß" * 500 + "FindME猫" + "界" * 500
        (tiny_manual / "en" / "quick-start.md").write_text(line, encoding="utf-8")
        match = base.search_docs("findme猫", "en")["matches"][0]
        assert match["line"] == 1
        assert "FindME猫" in match["text"]
        assert len(match["text"]) <= 240

    @pytest.mark.parametrize("query", ["", " \n\t"])
    def test_blank_queries_rejected(self, query):
        with pytest.raises(base.DocumentationError):
            base.search_docs(query, "en")

    @pytest.mark.parametrize("limit", [0, -1, 101, 1.5, True, "20"])
    def test_invalid_limits_rejected(self, limit):
        with pytest.raises(base.DocumentationError):
            base.search_docs("gbc", "en", limit)

    def test_missing_resource_has_localized_domain_error(self, tiny_manual):
        (tiny_manual / "zh" / "reference.md").unlink()
        with pytest.raises(base.DocumentationError) as error:
            base.read_topic("reference", "zh")
        assert "无法读取" in str(error.value)
        assert language.current_lang() == "en"


class TestManualCLI:
    def test_bare_doc_is_help(self):
        result = CliRunner().invoke(doc_app, [])
        assert result.exit_code == 0, result.output
        assert all(command in result.output for command in ("list", "read", "search"))

    def test_inherits_current_language_and_local_override(self):
        language.set_lang("zh")
        inherited = CliRunner().invoke(doc_app, ["list"])
        assert inherited.exit_code == 0, inherited.output
        assert json.loads(inherited.stdout)["language"] == "zh"
        override = CliRunner().invoke(doc_app, ["list", "--lang", "en"])
        assert override.exit_code == 0, override.output
        assert json.loads(override.stdout)["language"] == "en"
        assert language.current_lang() == "zh"

    def test_read_and_search_forward_to_base(self):
        runner = CliRunner()
        read = runner.invoke(doc_app, ["read", "quick-start", "--lang", "en"])
        assert read.exit_code == 0, read.output
        assert read.stdout.rstrip() == base.read_topic("quick-start", "en").rstrip()
        search = runner.invoke(doc_app, ["search", "gbc", "--limit", "1", "--lang", "en"])
        assert search.exit_code == 0, search.output
        assert json.loads(search.stdout) == base.search_docs("gbc", "en", 1)

    @pytest.mark.parametrize("args", [["read", "../secret"], ["list", "--lang", "fr"],
                                     ["search", " "], ["search", "gbc", "--limit", "0"]])
    def test_query_errors_are_clean(self, args):
        result = CliRunner().invoke(doc_app, args)
        assert result.exit_code == 1
        assert result.output.strip()
        assert "Traceback" not in result.output
