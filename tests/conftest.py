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

"""共享 pytest fixture —— 为后续测试提供可复用的基础设施。

提供:
- fake_project     : 把"当前项目"指向临时目录,注册 pytest-fake executor
- passing_test_file: 在 tmp_path 下写一个必定通过的 pytest 测试文件
- failing_test_file: 在 tmp_path 下写一个必定失败的 pytest 测试文件
"""

import sys
from pathlib import Path

import pytest


@pytest.fixture
def fake_project(tmp_path):
    """把"当前项目"指向 tmp_path,注册 pytest-fake executor,返回 tmp_path。

    对 executor 模块级缓存做重置(跟随项目切换),保证每次
    fixture 生命周期内 executor 配置从当前项目加载。
    """
    from gbc.app.config import project
    from gbc.app.config import executor as ce
    from gbc.app.core import executor as ex
    from gbc.app.config.executor import ExecutorModel

    project.set_current_project(str(tmp_path))

    # 重置 executor 模块级惰性缓存
    ce._cache = None
    ce._cache_path = None

    # 注册一个真实的 subprocess pytest executor
    ex.upsert_exec_config(
        "pytest-fake",
        ExecutorModel(
            command=[sys.executable, "-m", "pytest", "{file}", "-x", "-q"],
            cwd=".",
            timeout=30,
        ),
    )

    yield tmp_path


@pytest.fixture
def passing_test_file(tmp_path: Path) -> str:
    """在 tmp_path 下写一个必定通过的 pytest 测试文件,返回绝对路径字符串。"""
    p = tmp_path / "test_pass.py"
    p.write_text("def test_ok(): assert True\n", encoding="utf-8")
    return str(p)


@pytest.fixture
def failing_test_file(tmp_path: Path) -> str:
    """在 tmp_path 下写一个必定失败的 pytest 测试文件,返回绝对路径字符串。"""
    p = tmp_path / "test_fail.py"
    p.write_text('def test_bad(): assert False, "intentional failure"\n', encoding="utf-8")
    return str(p)
