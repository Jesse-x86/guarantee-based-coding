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

"""窄测试——保证 CRUD 生命周期函数（create/update/disable/enable/retire）。

测试 [[gbc/app/core/guarantee.py]] 的核心承诺：
- 出生即绿门禁：测试不过拒绝写入
- 停用/启用生命周期
- 退休保护（有 dependents 拒绝删除）
"""

import pytest

from gbc.app.core.guarantee import (
    create_guarantee,
    update_guarantee,
    disable_guarantee,
    enable_guarantee,
    retire_guarantee,
)
from gbc.app.models.meta import FileMeta
from gbc.app.models.errors import (
    GuaranteeDuplicatedError,
    GuaranteeNotFoundError,
    GuaranteeTestFailedError,
    GuaranteeHasDependentsError,
)


# ============================================================================
# create_guarantee
# ============================================================================

def test_create_guarantee_passing(fake_project, passing_test_file):
    """用 passing 测试 → 成功注册，provides[gid] 存在。"""
    meta = FileMeta()
    g = create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    assert "func.ok" in meta.provides
    assert meta.provides["func.ok"] is g


def test_create_guarantee_failing(fake_project, failing_test_file):
    """用 failing 测试 → 抛 GuaranteeTestFailedError，不写入 provides。"""
    meta = FileMeta()
    with pytest.raises(GuaranteeTestFailedError):
        create_guarantee(
            meta, "fake.py", "func.bad",
            desc="test", test=failing_test_file, executor_name="pytest-fake",
        )
    assert "func.bad" not in meta.provides


def test_create_guarantee_duplicate(fake_project, passing_test_file):
    """重复 gid → 抛 GuaranteeDuplicatedError。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    with pytest.raises(GuaranteeDuplicatedError):
        create_guarantee(
            meta, "fake.py", "func.ok",
            desc="test2", test=passing_test_file, executor_name="pytest-fake",
        )


def test_create_guarantee_disabled_with_failing(fake_project, failing_test_file):
    """disabled=True 用 failing 测试 → 跳过门禁成功注册，disabled 为 True。"""
    meta = FileMeta()
    g = create_guarantee(
        meta, "fake.py", "func.disabled_ok",
        desc="test", test=failing_test_file, executor_name="pytest-fake",
        disabled=True,
    )
    assert "func.disabled_ok" in meta.provides
    assert g.disabled is True


# ============================================================================
# update_guarantee
# ============================================================================

def test_update_guarantee_desc_only_no_rerun(fake_project, passing_test_file):
    """只改 desc（非 runner 字段）→ 不重跑测试，即使 test 路径已损坏也成功。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="original", test=passing_test_file, executor_name="pytest-fake",
    )
    # 偷偷把 test 改成不存在的路径——若重跑门禁会因文件找不到而炸
    meta.provides["func.ok"].test = "/nonexistent/path/test.py"
    g = update_guarantee(meta, "fake.py", "func.ok", desc="updated")
    assert g.desc == "updated"


def test_update_guarantee_switch_to_failing(fake_project, passing_test_file, failing_test_file):
    """换成 failing 测试 → runner_changed，重跑门禁并抛 GuaranteeTestFailedError。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    with pytest.raises(GuaranteeTestFailedError):
        update_guarantee(meta, "fake.py", "func.ok", test=failing_test_file)


def test_update_guarantee_not_found():
    """找不到 gid → 抛 GuaranteeNotFoundError。"""
    meta = FileMeta()
    with pytest.raises(GuaranteeNotFoundError):
        update_guarantee(meta, "fake.py", "no.such", desc="x")


# ============================================================================
# disable_guarantee
# ============================================================================

def test_disable_guarantee_ok(fake_project, passing_test_file):
    """disable → disabled 变 True；已停用再调幂等。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    g = disable_guarantee(meta, "fake.py", "func.ok")
    assert g.disabled is True
    # 幂等
    g2 = disable_guarantee(meta, "fake.py", "func.ok")
    assert g2.disabled is True


def test_disable_guarantee_not_found():
    """找不到 gid → 抛 GuaranteeNotFoundError。"""
    meta = FileMeta()
    with pytest.raises(GuaranteeNotFoundError):
        disable_guarantee(meta, "fake.py", "no.such")


# ============================================================================
# enable_guarantee
# ============================================================================

def test_enable_guarantee_ok(fake_project, passing_test_file):
    """先 disable 再 enable(passing 测试) → 门禁通过，disabled 变 False。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    disable_guarantee(meta, "fake.py", "func.ok")
    assert meta.provides["func.ok"].disabled is True
    g = enable_guarantee(meta, "fake.py", "func.ok")
    assert g.disabled is False


def test_enable_guarantee_failing_test(fake_project, failing_test_file):
    """enable 底层测试会失败的保证 → 抛 GuaranteeTestFailedError，disabled 保持 True。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.bad",
        desc="test", test=failing_test_file, executor_name="pytest-fake",
        disabled=True,
    )
    with pytest.raises(GuaranteeTestFailedError):
        enable_guarantee(meta, "fake.py", "func.bad")
    # 门禁不过，disabled 必须仍是 True（不偷偷转正）
    assert meta.provides["func.bad"].disabled is True


# ============================================================================
# retire_guarantee
# ============================================================================

def test_retire_guarantee_ok(fake_project, passing_test_file):
    """无 dependents → 成功删除 gid，不在 provides 里。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    retire_guarantee(meta, "fake.py", "func.ok")
    assert "func.ok" not in meta.provides


def test_retire_guarantee_has_dependents(fake_project, passing_test_file):
    """有 dependents → 抛 GuaranteeHasDependentsError，gid 仍在 provides 里。"""
    meta = FileMeta()
    create_guarantee(
        meta, "fake.py", "func.ok",
        desc="test", test=passing_test_file, executor_name="pytest-fake",
    )
    meta.provides["func.ok"].dependents.append("consumer.py")
    with pytest.raises(GuaranteeHasDependentsError):
        retire_guarantee(meta, "fake.py", "func.ok")
    assert "func.ok" in meta.provides


def test_retire_guarantee_not_found():
    """找不到 gid → 抛 GuaranteeNotFoundError。"""
    meta = FileMeta()
    with pytest.raises(GuaranteeNotFoundError):
        retire_guarantee(meta, "fake.py", "no.such")
