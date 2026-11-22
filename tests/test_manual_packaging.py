"""The wheel build consumes canonical manuals without modifying the checkout."""
from pathlib import Path

import pytest
from setuptools import Distribution
from setuptools.errors import FileError

import build_support


def _build_command(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(build_support, "__file__", str(source / "build_support.py"))
    for language in ("en", "zh"):
        folder = source / "docs" / language
        folder.mkdir(parents=True)
        for topic in ("quick-start", "concepts", "workflow", "reference", "onboarding-agent"):
            (folder / f"{topic}.md").write_text(f"# {language}: {topic}\n", encoding="utf-8")
        (folder / "README.md").write_text("Not a manual topic", encoding="utf-8")
    distribution = Distribution({"name": "manual-build-test", "packages": []})
    distribution.script_name = "setup.py"
    command = build_support.BuildPy(distribution)
    command.ensure_finalized()
    command.build_lib = str(tmp_path / "built")
    return source, command


def test_manual_build_copies_exact_topics_and_reports_outputs(tmp_path, monkeypatch):
    source, command = _build_command(tmp_path, monkeypatch)
    command.run()
    destination = Path(command.build_lib) / "gbc/assets/docs"
    expected = {
        Path(language) / f"{topic}.md"
        for language in ("en", "zh")
        for topic in ("quick-start", "concepts", "workflow", "reference", "onboarding-agent")
    }
    assert {path.relative_to(destination) for path in destination.rglob("*.md")} == expected
    for relative in expected:
        assert (destination / relative).read_bytes() == (source / "docs" / relative).read_bytes()
    assert set(command.get_outputs()) == {str(destination / relative) for relative in expected}
    assert not (source / "gbc/assets/docs").exists()


def test_manual_build_rejects_missing_canonical_topic(tmp_path, monkeypatch):
    source, command = _build_command(tmp_path, monkeypatch)
    (source / "docs/zh/reference.md").unlink()
    with pytest.raises(FileError):
        command.run()
