# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Project-level verify all is a strict release gate."""

import asyncio
import json
import subprocess

import pytest

from click.testing import CliRunner

from gbc.app.interface import base, mcp
from gbc.app.config.executor import EnvAction, ExecutorModel, ExecutorsConfig
from gbc.app.models.meta import FileMeta, Guarantee
from gbc.app.models.verify import GuaranteeRef, ProjectVerifySummary, VerifyModel
from gbc.entry import get_wrapped_app


def _guarantee(*, heavy=0, disabled=False, **kwargs):
    return Guarantee(
        desc="behavior",
        test=kwargs.pop("test", "tests/test_behavior.py"),
        executor=kwargs.pop("executor", "pytest-fake"),
        heavy=heavy,
        disabled=disabled,
        **kwargs,
    )


@pytest.fixture
def recorded_execution(monkeypatch):
    config = ExecutorsConfig(executors={
        "pytest-fake": ExecutorModel(command=["pytest", "{file}"], cwd=".", timeout=30),
    })
    calls = []
    monkeypatch.setattr(base.executor, "get_executors_config", lambda: config)

    def run(**kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(kwargs["args"], 0, "checked", "")

    monkeypatch.setattr(base.executor.subprocess, "run", run)
    return config, calls


class TestBaseVerifyAll:
    @pytest.mark.parametrize("return_code", [0, 1])
    def test_shared_check_runs_once_and_fans_out_every_result(self, monkeypatch, recorded_execution, return_code):
        _, calls = recorded_execution
        metas = [
            ("a.py", FileMeta(provides={"shared": _guarantee(), "second": _guarantee(heavy=99)})),
            ("b.py", FileMeta(provides={"shared": _guarantee()})),
        ]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))

        def run(**kwargs):
            calls.append(kwargs)
            return subprocess.CompletedProcess(kwargs["args"], return_code, "raw stdout", "raw stderr")

        monkeypatch.setattr(base.executor.subprocess, "run", run)
        summary = base.verify_all()
        assert len(calls) == 1
        assert summary.test_runs == 1
        assert summary.executed == 3
        expected = [("a.py", "shared"), ("a.py", "second"), ("b.py", "shared")]
        bucket = summary.passed if return_code == 0 else summary.failed
        assert [(r.provider, r.id) for r in bucket] == expected
        assert not (summary.failed if return_code == 0 else summary.passed)
        for provider, gid in expected:
            assert summary.results[provider][gid] == VerifyModel(
                return_code=return_code, stdout="raw stdout", stderr="raw stderr"
            )
        assert summary.green is (return_code == 0)
        assert not summary.missing and not summary.disabled
        # This is per-call sharing, never a cache of yesterday's green result.
        base.verify_all()
        assert len(calls) == 2

    @pytest.mark.parametrize("field,value", [
        ("executor", "other"), ("test", "tests/test_behavior.py::test_other"),
        ("timeout_override", 31),
    ])
    def test_distinct_execution_identity_is_not_merged(self, monkeypatch, recorded_execution, field, value):
        config, calls = recorded_execution
        config.executors["other"] = config.executors["pytest-fake"].model_copy(deep=True)
        metas = [("a.py", FileMeta(provides={"one": _guarantee()})),
                 ("b.py", FileMeta(provides={"two": _guarantee(**{field: value})}))]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        summary = base.verify_all()
        assert len(calls) == summary.test_runs == 2
        assert summary.executed == 2 and summary.green

    @pytest.mark.parametrize("override,global_timeout,expected_runs,expected_timeout", [
        (30, -1, 1, 30), (31, -1, 2, 30), (31, 17, 1, 17),
        (0, 0, 1, 0), (-1, -1, 1, 30),
    ])
    def test_effective_timeout_controls_sharing(self, monkeypatch, recorded_execution,
                                              override, global_timeout, expected_runs, expected_timeout):
        _, calls = recorded_execution
        metas = [("a.py", FileMeta(provides={"one": _guarantee()})),
                 ("b.py", FileMeta(provides={"two": _guarantee(timeout_override=override)}))]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        summary = base.verify_all(timeout=global_timeout)
        assert len(calls) == summary.test_runs == expected_runs
        assert calls[0]["timeout"] == expected_timeout
        assert summary.executed == 2 and summary.green

    @pytest.mark.parametrize("field", ["command", "cwd", "timeout", "env_ops", "inherited_env"])
    def test_changed_execution_configuration_cannot_merge(self, monkeypatch, recorded_execution, field):
        config, calls = recorded_execution
        prepare = base.executor.prepare_execution
        snapshots = []

        def prepare_changing(*args):
            if snapshots:
                model = config.executors["pytest-fake"]
                if field == "command":
                    model.command = ["pytest", "-x", "{file}"]
                elif field == "cwd":
                    model.cwd = "different-workspace"
                elif field == "timeout":
                    model.timeout = 31
                elif field == "env_ops":
                    model.env_ops = [EnvAction(key="GBC_PLAN_TEST", action="set", value="second")]
                else:
                    monkeypatch.setenv("GBC_PLAN_TEST", "changed-parent-environment")
            plan = prepare(*args)
            snapshots.append(plan)
            return plan

        monkeypatch.setattr(base.executor, "prepare_execution", prepare_changing)
        metas = [("a.py", FileMeta(provides={"one": _guarantee()})),
                 ("b.py", FileMeta(provides={"two": _guarantee()}))]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        summary = base.verify_all()
        assert summary.green and summary.executed == 2
        assert len(calls) == summary.test_runs == 2
        # Execution uses the captured parameters, not the now-mutated executor.
        for call, plan in zip(calls, snapshots):
            assert call["args"] == list(plan.args)
            assert call["cwd"] == plan.cwd and call["timeout"] == plan.timeout
            assert call["env"] == dict(plan.env)
            assert call["stdin"] == subprocess.DEVNULL

    def test_default_timeout_is_resolved_before_grouping(self, monkeypatch, recorded_execution):
        config, calls = recorded_execution
        config.executors["pytest-fake"].timeout = -1
        meta = FileMeta(provides={"implicit": _guarantee(), "explicit": _guarantee(timeout_override=15)})
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter([("a.py", meta)]))
        summary = base.verify_all()
        assert summary.green and summary.executed == 2
        assert len(calls) == 1 and calls[0]["timeout"] == 15

    @pytest.mark.parametrize("no_result", ["timeout", "none"])
    def test_absent_result_marks_every_reference_missing(self, monkeypatch, recorded_execution, no_result):
        metas = [("a.py", FileMeta(provides={"one": _guarantee()})),
                 ("b.py", FileMeta(provides={"two": _guarantee()}))]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))

        def absent(plan):
            if no_result == "timeout":
                raise subprocess.TimeoutExpired(["private-argument"], 30)
            return None

        monkeypatch.setattr(base.executor, "verify_prepared", absent)
        summary = base.verify_all()
        assert summary.test_runs == 1 and summary.executed == 0
        assert len(summary.missing) == 2 and not summary.results
        assert not summary.passed and not summary.failed and not summary.green
        reason = "TimeoutExpired" if no_result == "timeout" else "MissingResult"
        assert summary.execution_errors == {"a.py": {"one": reason}, "b.py": {"two": reason}}
        assert "private-argument" not in summary.model_dump_json()

    def test_runs_every_enabled_guarantee_and_reports_gaps(self, monkeypatch, recorded_execution):
        metas = [
            ("a.py", FileMeta(provides={
                "a.heavy": _guarantee(heavy=9),
                "a.disabled": _guarantee(disabled=True),
            })),
            ("b.py", FileMeta(provides={"b.missing": _guarantee(test="missing.py", heavy=3)})),
            ("c.py", FileMeta(provides={"c.missing": _guarantee(test="missing.py")})),
        ]
        _, calls = recorded_execution

        def run(**kwargs):
            calls.append(kwargs)
            if kwargs["args"][-1] == "missing.py":
                raise FileNotFoundError("missing runner")
            return subprocess.CompletedProcess(kwargs["args"], 0, "ok", "")

        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        monkeypatch.setattr(base.executor.subprocess, "run", run)

        summary = base.verify_all(timeout=17)

        assert [(item.provider, item.id) for item in summary.passed] == [("a.py", "a.heavy")]
        assert [(item.provider, item.id) for item in summary.disabled] == [("a.py", "a.disabled")]
        assert [(item.provider, item.id) for item in summary.missing] == [
            ("b.py", "b.missing"), ("c.py", "c.missing")]
        assert summary.executed == 1
        assert summary.test_runs == len(calls) == 2
        assert summary.execution_errors == {"b.py": {"b.missing": "FileNotFoundError"},
                                            "c.py": {"c.missing": "FileNotFoundError"}}
        assert not summary.green
        assert [call["timeout"] for call in calls] == [17, 17]

    def test_missing_executor_does_not_hide_other_results(self, monkeypatch, recorded_execution):
        _, calls = recorded_execution
        metas = [("a.py", FileMeta(provides={"lost": _guarantee(executor="missing")})),
                 ("b.py", FileMeta(provides={"ok": _guarantee()}))]
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas))
        summary = base.verify_all()
        assert summary.missing == [GuaranteeRef(provider="a.py", id="lost")]
        assert summary.execution_errors == {"a.py": {"lost": "ExecutorNotFoundError"}}
        assert len(calls) == summary.test_runs == summary.executed == 1
        assert len(summary.passed) == 1 and not summary.green

    @pytest.mark.parametrize("disabled", [False, True])
    def test_no_enabled_checks_never_passes(self, monkeypatch, recorded_execution, disabled):
        _, calls = recorded_execution
        meta = FileMeta(provides={"off": _guarantee(disabled=True)} if disabled else {})
        monkeypatch.setattr(base, "_iter_all_metas", lambda: iter([("a.py", meta)]))
        summary = base.verify_all()
        assert not calls and summary.test_runs == summary.executed == 0
        assert len(summary.disabled) == int(disabled)
        assert not summary.green

    def test_real_scan_runs_heavy_and_fails_on_disabled(self, fake_project, tmp_path, monkeypatch):
        passing = tmp_path / "test_release_gate.py"
        passing.write_text("def test_ok(): assert True\n", encoding="utf-8")
        base.create_guarantee(
            "provider.py", "provider.heavy", "heavy behavior", str(passing),
            "pytest-fake", heavy=999,
        )
        for provider, gid in [("provider.py", "provider.second"), ("other.py", "other.shared")]:
            base.create_guarantee(provider, gid, "shared behavior", str(passing), "pytest-fake")
        base.create_guarantee(
            "disabled.py", "disabled.behavior", "disabled behavior", str(passing),
            "pytest-fake", disabled=True,
        )

        run = base.executor.subprocess.run
        calls = []

        def counted_run(**kwargs):
            calls.append(kwargs["args"])
            return run(**kwargs)

        monkeypatch.setattr(base.executor.subprocess, "run", counted_run)
        summary = base.verify_all()

        assert summary.executed == 3
        assert summary.test_runs == len(calls) == 1
        assert {(item.provider, item.id) for item in summary.passed} == {
            ("provider.py", "provider.heavy"), ("provider.py", "provider.second"),
            ("other.py", "other.shared"),
        }
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
        assert "test_runs=0" in result.output
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
        assert payload["test_runs"] == 0
        assert payload["execution_errors"] == {}
        assert payload["green"] is True
        assert payload["passed"] == [{"provider": "ok.py", "id": "ok.behavior"}]
        assert "verify_all" in {tool.name for tool in asyncio.run(mcp.mcp.list_tools())}
