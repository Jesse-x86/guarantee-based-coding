# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Project-level verify all is a strict release gate."""

import asyncio
import json

from click.testing import CliRunner

from gbc.app.interface import base, mcp
from gbc.app.models.meta import FileMeta, Guarantee
from gbc.app.models.verify import GuaranteeRef, ProjectVerifySummary, VerifyModel
from gbc.entry import get_wrapped_app


def _guarantee(*, heavy=0, disabled=False):
    return Guarantee(
        desc="behavior",
        test="tests/test_behavior.py",
        executor="pytest-fake",
        heavy=heavy,
        disabled=disabled,
    )


class TestBaseVerifyAll:
    def test_runs_every_enabled_guarantee_and_reports_gaps(self, monkeypatch):
        metas = [
            ("a.py", FileMeta(provides={
                "a.heavy": _guarantee(heavy=9),
                "a.disabled": _guarantee(disabled=True),
            })),
            ("b.py", FileMeta(provides={"b.missing": _guarantee(heavy=3)})),
        ]
        calls = []

        def verify(meta, *, auto_run_max_heavy, timeout):
            calls.append((meta, auto_run_max_heavy, timeout))
            if "a.heavy" in meta.provides:
                return type("Summary", (), {"results": {
                    "a.heavy": VerifyModel(return_code=0, stdout="ok", stderr=None)
                }})()
            return type("Summary", (), {"results": {}})()

        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        monkeypatch.setattr(base.gtee, "verify_provider", verify)

        summary = base.verify_all(timeout=17)

        assert [(item.provider, item.id) for item in summary.passed] == [("a.py", "a.heavy")]
        assert [(item.provider, item.id) for item in summary.disabled] == [("a.py", "a.disabled")]
        assert [(item.provider, item.id) for item in summary.missing] == [("b.py", "b.missing")]
        assert summary.executed == 1
        assert not summary.green
        assert [(maximum, timeout) for _, maximum, timeout in calls] == [(9, 17), (3, 17)]

    def test_real_scan_runs_heavy_and_fails_on_disabled(self, fake_project, tmp_path):
        passing = tmp_path / "test_release_gate.py"
        passing.write_text("def test_ok(): assert True\n", encoding="utf-8")
        base.create_guarantee(
            "provider.py", "provider.heavy", "heavy behavior", str(passing),
            "pytest-fake", heavy=999,
        )
        base.create_guarantee(
            "disabled.py", "disabled.behavior", "disabled behavior", str(passing),
            "pytest-fake", disabled=True,
        )

        summary = base.verify_all()

        assert summary.executed == 1
        assert [(item.provider, item.id) for item in summary.passed] == [
            ("provider.py", "provider.heavy")
        ]
        assert [(item.provider, item.id) for item in summary.disabled] == [
            ("disabled.py", "disabled.behavior")
        ]
        assert not summary.green


class TestCliVerifyAll:
    def test_reports_locations_and_uses_strict_exit_code(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path))
        summary = ProjectVerifySummary(
            passed=[GuaranteeRef(provider="ok.py", id="ok.behavior")],
            failed=[GuaranteeRef(provider="bad.py", id="bad.behavior")],
            disabled=[GuaranteeRef(provider="off.py", id="off.behavior")],
            missing=[GuaranteeRef(provider="lost.py", id="lost.behavior")],
            results={
                "ok.py": {"ok.behavior": VerifyModel(return_code=0, stdout="ok", stderr=None)},
                "bad.py": {"bad.behavior": VerifyModel(return_code=1, stdout="assertion", stderr=None)},
            },
        )
        monkeypatch.setattr(base, "verify_all", lambda **kwargs: summary)

        result = CliRunner().invoke(get_wrapped_app(), ["verify", "all"])

        assert result.exit_code == 1, result.output
        assert "passed=1 failed=1 disabled=1 executed=2 missing=1" in result.output
        for location in (
            "bad.py:bad.behavior", "off.py:off.behavior", "lost.py:lost.behavior"
        ):
            assert location in result.output

    def test_zero_execution_is_failure(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path))
        monkeypatch.setattr(base, "verify_all", lambda **kwargs: ProjectVerifySummary())

        result = CliRunner().invoke(get_wrapped_app(), ["--lang", "en", "verify", "all"])

        assert result.exit_code == 1, result.output
        assert "executed=0" in result.output
        assert "No guarantees were executed" in result.output

    def test_success_requires_executed_complete_project(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path))
        summary = ProjectVerifySummary(
            passed=[GuaranteeRef(provider="ok.py", id="ok.behavior")],
            results={
                "ok.py": {"ok.behavior": VerifyModel(return_code=0, stdout="ok", stderr=None)}
            },
        )
        monkeypatch.setattr(base, "verify_all", lambda **kwargs: summary)

        result = CliRunner().invoke(get_wrapped_app(), ["verify", "all", "--timeout", "5"])

        assert result.exit_code == 0, result.output
        assert "GREEN" in result.output
        assert "passed=1 failed=0 disabled=0 executed=1 missing=0" in result.output


class TestMcpVerifyAll:
    def test_returns_strict_project_summary(self, monkeypatch):
        summary = ProjectVerifySummary(
            passed=[GuaranteeRef(provider="ok.py", id="ok.behavior")],
            results={
                "ok.py": {"ok.behavior": VerifyModel(return_code=0, stdout="ok", stderr=None)}
            },
        )
        monkeypatch.setattr(base, "verify_all", lambda **kwargs: summary)

        payload = json.loads(mcp.verify_all(timeout=4))

        assert payload["executed"] == 1
        assert payload["green"] is True
        assert payload["passed"] == [{"provider": "ok.py", "id": "ok.behavior"}]
        assert "verify_all" in {tool.name for tool in asyncio.run(mcp.mcp.list_tools())}
