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

"""[[gbc/app/core/executor.py]] 真实子进程执行路径窄测试。

覆盖 verify_single / has_exec_config / upsert_exec_config / remove_exec_config
的核心行为：命令占位符替换、return_model、超时优先级、executor 未注册报错。
"""

import subprocess
import sys

import pytest

from gbc.app.config.executor import ExecutorModel
from gbc.app.core.executor import (
    has_exec_config,
    remove_exec_config,
    upsert_exec_config,
    verify_single,
    prepare_execution,
    verify_prepared,
)
from gbc.app.models.errors import ExecutorNotFoundError
from gbc.app.models.verify import VerifyModel


class TestVerifySingle:
    """verify_single 真实子进程执行路径"""

    def test_passing_returns_model(self, fake_project, passing_test_file):
        """return_model=True 对通过测试返回 VerifyModel，return_code==0"""
        result = verify_single("pytest-fake", passing_test_file, return_model=True)
        assert isinstance(result, VerifyModel)
        assert result.return_code == 0

    def test_passing_return_bool(self, fake_project, passing_test_file):
        """return_model=False 对通过测试返回 True"""
        result = verify_single("pytest-fake", passing_test_file, return_model=False)
        assert result is True

    def test_failing_returns_nonzero(self, fake_project, failing_test_file):
        """return_model=True 对失败测试返回非零 return_code"""
        result = verify_single("pytest-fake", failing_test_file, return_model=True)
        assert isinstance(result, VerifyModel)
        assert result.return_code != 0

    def test_failing_return_bool(self, fake_project, failing_test_file):
        """return_model=False 对失败测试返回 False"""
        result = verify_single("pytest-fake", failing_test_file, return_model=False)
        assert result is False

    def test_nonexistent_config_raises_executor_not_found(self, fake_project, passing_test_file):
        """不存在的 config 名字抛 ExecutorNotFoundError"""
        with pytest.raises(ExecutorNotFoundError):
            verify_single("nonexistent-config-foo", passing_test_file)

    def test_timeout_expired(self, fake_project, passing_test_file):
        """短 timeout + 会卡住的子进程 → subprocess.TimeoutExpired 向外传播"""
        upsert_exec_config(
            "blocking-test-exec",
            ExecutorModel(
                command=[sys.executable, "-c", "import time; time.sleep(10)"],
                cwd=".",
                timeout=1,
            ),
        )
        with pytest.raises(subprocess.TimeoutExpired):
            verify_single("blocking-test-exec", passing_test_file, timeout=1)


class TestHasExecConfig:
    """has_exec_config 查询"""

    def test_registered_returns_true(self, fake_project):
        assert has_exec_config("pytest-fake") is True

    def test_unregistered_returns_false(self, fake_project):
        assert has_exec_config("no-such-executor") is False


class TestUpsertAndRemove:
    """upsert/remove exec config 完整生命周期"""

    def test_upsert_then_remove(self, fake_project):
        config_name = "temp-lifetime-exec"
        upsert_exec_config(
            config_name,
            ExecutorModel(
                command=[sys.executable, "-c", "print('ok')"],
                cwd=".",
                timeout=10,
            ),
        )
        assert has_exec_config(config_name) is True
        remove_exec_config(config_name)
        assert has_exec_config(config_name) is False


class TestPreparedExecution:
    def test_plan_and_single_execution_use_identical_process_arguments(self, fake_project, monkeypatch):
        from gbc.app.config.executor import EnvAction
        upsert_exec_config("planned", ExecutorModel(
            command=[sys.executable, "{file}", "--selector={f}"], cwd=".", timeout=17,
            env_ops=[EnvAction(key="GBC_PLAN_TEST", action="set", value="planned")],
        ))
        calls = []

        def run(**kwargs):
            calls.append(kwargs)
            return subprocess.CompletedProcess(kwargs["args"], 7, "stdout", "stderr")

        monkeypatch.setattr("gbc.app.core.executor.subprocess.run", run)
        plan = prepare_execution("planned", "check.py::case", 9)
        direct = verify_single("planned", "check.py::case", timeout=9)
        planned = verify_prepared(plan)
        assert direct == planned == VerifyModel(return_code=7, stdout="stdout", stderr="stderr")
        assert calls[0] == calls[1]
        assert calls[1]["args"] == [sys.executable, "check.py::case", "--selector=check.py::case"]
        assert calls[1]["timeout"] == 9
        assert calls[1]["env"]["GBC_PLAN_TEST"] == "planned"
        assert calls[1]["stdin"] == subprocess.DEVNULL
        # A prepared plan must not read a new configuration at execution time.
        upsert_exec_config("planned", ExecutorModel(command=["changed"], cwd="other", timeout=1))
        verify_prepared(plan)
        assert calls[2] == calls[1]


class TestOutputDecoding:
    @pytest.mark.parametrize("prepared", [False, True])
    @pytest.mark.parametrize("exit_code", [0, 7])
    @pytest.mark.parametrize("invalid_bytes", [False, True])
    def test_output_survives_non_utf8_locale(self, fake_project, monkeypatch,
                                           prepared, exit_code, invalid_bytes):
        # Exercise real pipes and Windows reader threads. Force subprocess's
        # locale fallback even if pytest itself was launched with -X utf8.
        monkeypatch.setattr(subprocess, "_text_encoding", lambda: "gbk")
        stdout = "中文 € 🚀\n".encode("utf-8")
        stderr = "错误诊断 €\n".encode("utf-8")
        if invalid_bytes:
            stdout += b"bad:\xff\x82\ntruncated:\xe2\x82"
            stderr += b"bad:\xfe\nend"
        script = (f"import os; os.write(1, {stdout!r}); "
                  f"os.write(2, {stderr!r}); raise SystemExit({exit_code})")
        upsert_exec_config("bytes-output", ExecutorModel(
            command=[sys.executable, "-c", script], cwd=str(fake_project), timeout=10,
        ))
        if prepared:
            result = verify_prepared(prepare_execution("bytes-output", "unused"))
        else:
            result = verify_single("bytes-output", "unused")
        expected_stdout = "中文 € 🚀\n"
        expected_stderr = "错误诊断 €\n"
        if invalid_bytes:
            expected_stdout += r"bad:\xff\x82" + "\n" + r"truncated:\xe2\x82"
            expected_stderr += r"bad:\xfe" + "\nend"
        assert result.return_code == exit_code
        assert result.stdout == expected_stdout
        assert result.stderr == expected_stderr
        assert VerifyModel.model_validate_json(result.model_dump_json()) == result
