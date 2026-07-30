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
