import os

import pytest

from gbc.app.config.executor import EnvAction
from gbc.app.core.env import apply_env_action, apply_env_actions, get_clean_python_path


# ── helpers ────────────────────────────────────────────────────────────────

SEP = os.pathsep

def ea(key, action, value=None):
    """Shorthand for EnvAction construction."""
    return EnvAction(key=key, action=action, value=value)


# ── apply_env_action ──────────────────────────────────────────────────────

class TestApplyEnvAction:
    """Narrow pure-function tests for apply_env_action."""

    def test_set_overwrites_existing_key(self):
        env = {"X": "old"}
        apply_env_action(env, ea("X", "set", "new"))
        assert env["X"] == "new"

    def test_set_creates_new_key(self):
        env: dict[str, str] = {}
        apply_env_action(env, ea("X", "set", "val"))
        assert env["X"] == "val"

    def test_remove_deletes_existing_key(self):
        env = {"X": "gone"}
        apply_env_action(env, ea("X", "remove"))
        assert "X" not in env

    def test_remove_missing_key_no_error(self):
        env: dict[str, str] = {}
        result = apply_env_action(env, ea("X", "remove"))
        assert result is env
        assert "X" not in env

    def test_append_on_existing_value(self):
        env = {"X": "a"}
        apply_env_action(env, ea("X", "append", "b"), sep=":")
        assert env["X"] == "a:b"

    def test_append_on_missing_key_no_separator(self):
        env: dict[str, str] = {}
        apply_env_action(env, ea("X", "append", "val"), sep=":")
        assert env["X"] == "val"

    def test_prepend_on_existing_value(self):
        env = {"X": "b"}
        apply_env_action(env, ea("X", "prepend", "a"), sep=":")
        assert env["X"] == "a:b"

    def test_prepend_on_missing_key_no_separator(self):
        env: dict[str, str] = {}
        apply_env_action(env, ea("X", "prepend", "val"), sep=":")
        assert env["X"] == "val"

    def test_value_none_treated_as_empty_string_append(self):
        env: dict[str, str] = {}
        apply_env_action(env, ea("X", "append", None), sep=":")
        # val="" → current="" → f"{current}{sep}{val}"→ ":" but current
        # is empty so we take the else branch: val="" → env["X"] = ""
        assert env["X"] == ""

    def test_value_none_treated_as_empty_string_set(self):
        env = {"X": "old"}
        apply_env_action(env, ea("X", "set", None))
        assert env["X"] == ""


# ── apply_env_actions ─────────────────────────────────────────────────────

class TestApplyEnvActions:
    """Narrow tests for apply_env_actions batch applicator."""

    def test_none_ops_returns_env_unchanged(self):
        env = {"X": "keep"}
        result = apply_env_actions(env, None)
        assert result is env
        assert result["X"] == "keep"

    def test_empty_ops_returns_env_unchanged(self):
        env = {"X": "keep"}
        result = apply_env_actions(env, [])
        assert result is env
        assert result["X"] == "keep"

    def test_multiple_ops_chain_correctly(self):
        """set then append — previous step's result feeds next."""
        env: dict[str, str] = {}
        ops = [
            ea("X", "set", "base"),
            ea("X", "append", "extra"),
        ]
        apply_env_actions(env, ops, sep=":")
        assert env["X"] == "base:extra"


# ── get_clean_python_path ────────────────────────────────────────────────

class TestGetCleanPythonPath:
    """Narrow test for get_clean_python_path."""

    def test_strips_first_segment_of_pythonpath(self, monkeypatch):
        monkeypatch.setenv("PYTHONPATH", f"a{SEP}b{SEP}c")
        # Also clear any other env vars that might interfere
        result = get_clean_python_path()
        assert result["PYTHONPATH"] == f"b{SEP}c"

    def test_single_segment_becomes_empty(self, monkeypatch):
        monkeypatch.setenv("PYTHONPATH", "only")
        result = get_clean_python_path()
        assert result["PYTHONPATH"] == ""

    def test_empty_pythonpath_stays_empty(self, monkeypatch):
        monkeypatch.setenv("PYTHONPATH", "")
        result = get_clean_python_path()
        assert result["PYTHONPATH"] == ""
