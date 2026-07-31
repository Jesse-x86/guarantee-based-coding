# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""Guarantees for selecting and overriding the current project root."""

import os
from pathlib import Path

import pytest

from gbc.app.config import project


def _initialize_project(monkeypatch, cwd: Path, env_value: str | None) -> Path:
    """Exercise initialization deterministically without relying on import state."""
    monkeypatch.chdir(cwd)
    if env_value is None:
        monkeypatch.delenv(project.GBC_PROJECT_ROOT, raising=False)
    else:
        monkeypatch.setenv(project.GBC_PROJECT_ROOT, env_value)
    return project._init_current_project()


def test_project_root_constant_is_exported():
    assert project.GBC_PROJECT_ROOT == "GBC_PROJECT_ROOT"


def test_environment_root_wins_over_cwd(monkeypatch, tmp_path):
    cwd = tmp_path / "cwd"
    configured = tmp_path / "configured" / "new-project"
    cwd.mkdir()

    result = _initialize_project(monkeypatch, cwd, str(configured))

    assert result == configured.resolve(strict=False)
    assert isinstance(result, Path)


def test_cwd_is_used_when_environment_is_absent(monkeypatch, tmp_path):
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    assert _initialize_project(monkeypatch, cwd, None) == cwd.resolve(strict=False)


@pytest.mark.parametrize("env_value", ["", "   ", "\t\n"])
def test_blank_environment_falls_back_to_cwd(monkeypatch, tmp_path, env_value):
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    assert _initialize_project(monkeypatch, cwd, env_value) == cwd.resolve(strict=False)


def test_initialization_does_not_search_parent_for_gbc(monkeypatch, tmp_path):
    parent = tmp_path / "parent"
    cwd = parent / "nested" / "working-directory"
    (parent / ".gbc").mkdir(parents=True)
    cwd.mkdir(parents=True)

    assert _initialize_project(monkeypatch, cwd, None) == cwd.resolve(strict=False)


def test_set_current_project_explicitly_overrides_and_expands_pathlike(
    monkeypatch, tmp_path
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    if os.name == "nt":
        monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(project, "CURRENT_PROJECT", project.get_current_project())

    project.set_current_project(Path("~") / "projects" / ".." / "new-project")
    result = project.get_current_project()

    assert result == (home / "new-project").resolve(strict=False)
    assert isinstance(result, Path)


def test_set_current_project_accepts_and_normalizes_string(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(project, "CURRENT_PROJECT", project.get_current_project())

    project.set_current_project(str(Path("nested") / ".." / "new-project"))

    assert project.get_current_project() == (tmp_path / "new-project").resolve(strict=False)


def test_set_current_project_rejects_blank_string():
    with pytest.raises(ValueError, match="must not be blank"):
        project.set_current_project("   ")
