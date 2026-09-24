# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Verification reports distinguish a non-failing gate from completed checks."""
import json

import pytest
from click.testing import CliRunner

from gbc.app.interface import base, mcp
from gbc.app.models.verify import SkippedGuarantee, VerifyModel, VerifySummary
from gbc.entry import get_wrapped_app


@pytest.fixture(params=[
    (False, False, None),
    (False, False, "heavy"),
    (False, False, "disabled"),
    (True, False, "heavy"),
    (True, False, "disabled"),
    (True, False, None),
    (False, True, None),
    (False, True, "disabled"),
], ids=["empty", "heavy-only", "disabled-only", "pass-heavy", "pass-disabled",
        "pass", "fail", "fail-disabled"])
def summary(request):
    passed, failed, skip = request.param
    result = VerifySummary(
        passed=["checked.pass"] if passed else [],
        failed=["checked.fail"] if failed else [],
        skipped=[SkippedGuarantee(id="not.checked", heavy=1, reason=skip)] if skip else [],
    )
    for guarantee in result.passed + result.failed:
        result.results[guarantee] = VerifyModel(
            return_code=1 if guarantee in result.failed else 0,
            stdout="check output", stderr=None,
        )
    return result


class TestCliVerificationReporting:
    @pytest.mark.parametrize("lang", ["en", "zh"])
    def test_gate_and_execution_gaps_are_reported(self, monkeypatch, tmp_path, summary, lang):
        monkeypatch.setenv("GBC_CONFIG_HOME", str(tmp_path))
        monkeypatch.delenv("GBC_LANG", raising=False)
        monkeypatch.setattr(base, "verify_provider", lambda *args, **kwargs: summary)
        result = CliRunner().invoke(
            get_wrapped_app(), ["--lang", lang, "verify", "provider", "provider.py"]
        )
        output = result.output
        assert result.exit_code == (1 if summary.failed else 0), output
        assert ("RED" if summary.failed else "GREEN") in output
        assert f"passed={len(summary.passed)}" in output
        assert f"failed={len(summary.failed)}" in output
        assert f"skipped={len(summary.skipped)}" in output
        no_execution = "No guarantees were executed" if lang == "en" else "本次未执行任何保证"
        incomplete = "Verification is incomplete" if lang == "en" else "保证验证尚未完成"
        disabled = "Disabled guarantees remain unverified" if lang == "en" else "停用保证仍未验证"
        executed = bool(summary.passed or summary.failed)
        assert (no_execution in output) is (not executed), output
        assert (incomplete in output) is (executed and bool(summary.skipped)), output
        assert (disabled in output) is any(s.reason == "disabled" for s in summary.skipped), output
        for skipped in summary.skipped:
            assert skipped.id in output
            assert ("DISABLED" if skipped.reason == "disabled" else "heavy skipped") in output


class TestMcpVerificationReporting:
    def test_original_payload_preserves_gate_and_unexecuted_evidence(self, monkeypatch, summary):
        calls = []

        def verify(provider, **kwargs):
            calls.append((provider, kwargs))
            return summary

        monkeypatch.setattr(base, "verify_provider", verify)
        payload = json.loads(mcp.verify_provider("provider.py", auto_run_max_heavy=2, timeout=9))
        assert calls == [("provider.py", {"auto_run_max_heavy": 2, "timeout": 9})]
        assert payload == {**summary.model_dump(), "green": not summary.failed}
        assert set(payload["results"]) == set(payload["passed"] + payload["failed"])
        assert not ({s["id"] for s in payload["skipped"]} & payload["results"].keys())
