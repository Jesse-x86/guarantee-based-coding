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

"""refactor_file / rename_guarantee / refactor_func 三件套窄测试。

验证全图路径/符号/保证 id 重写的正确性、幂等性、以及错误路径。
"""

import pytest

from gbc.app.interface import base
from gbc.app.models.errors import (
    GuaranteeDuplicatedError,
    GuaranteeNotFoundError,
    IllegalFilePathError,
)


# ============================================================================
# refactor_file
# ============================================================================


def test_refactor_file_basic_move(fake_project, passing_test_file):
    """refactor_file 基本移动：源码/产物搬家 + 全图路径重写 + 保证自动停用"""
    tmp = fake_project

    # 源码文件必须真实存在才能触发 code_move
    (tmp / "a.py").write_text("# provider\n", encoding="utf-8")
    (tmp / "b.py").write_text("# consumer\n", encoding="utf-8")

    base.create_guarantee(
        "a.py", "g1",
        desc="basic guarantee",
        test=passing_test_file,
        executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "sym", "g1")

    report = base.refactor_file("a.py", "a2.py")

    # 返回 dict 基本字段
    assert report["old"] == "a.py"
    assert report["new"] == "a2.py"
    assert report["code_move"] in ("git", "fs")
    assert report["gbc_move"] == "moved"
    assert report["refs_rewritten"] >= 1  # b.py 的 dep.symbol 至少被改写一次
    assert isinstance(report.get("md_refs_rewritten"), int)
    assert isinstance(report.get("next_steps"), str)

    # 消费者依赖的 symbol 已从 a.py:sym 改写成 a2.py:sym
    deps = base.list_depends_on("b.py")
    assert len(deps) == 1
    assert deps[0].symbol == "a2.py:sym"
    assert deps[0].guarantees == ["g1"]

    # 保证 g1 现在挂在新路径 a2.py 下，且 disabled=True
    provides = base.list_provides("a2.py")
    assert "g1" in provides
    assert provides["g1"].disabled is True

    # disabled 报告格式：[{provider, guarantee}]
    assert len(report["disabled"]) == 1
    assert report["disabled"][0]["provider"] == "a2.py"
    assert report["disabled"][0]["guarantee"] == "g1"

    # old 路径的 meta 已不存在
    with pytest.raises(Exception):
        base.list_provides("a.py")


def test_refactor_file_idempotent(fake_project, passing_test_file):
    """refactor_file 幂等：第二次调 old 已不在 new 已在 → code_move="already" 不报错"""
    tmp = fake_project

    (tmp / "a.py").write_text("# provider\n", encoding="utf-8")
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "sym", "g1")

    report1 = base.refactor_file("a.py", "a2.py")
    assert report1["code_move"] in ("git", "fs")

    # 第二次：old 已不存在，new 已在
    report2 = base.refactor_file("a.py", "a2.py")
    assert report2["code_move"] == "already"
    assert report2["gbc_move"] == "already"


def test_refactor_file_both_exist_raises(fake_project, passing_test_file):
    """refactor_file 两端文件都存在 → IllegalFilePathError"""
    tmp = fake_project

    (tmp / "a.py").write_text("# provider\n", encoding="utf-8")
    (tmp / "a2.py").write_text("# already there\n", encoding="utf-8")

    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )

    with pytest.raises(IllegalFilePathError):
        base.refactor_file("a.py", "a2.py")


def test_refactor_file_code_move_neither(fake_project, passing_test_file):
    """refactor_file 两端源码都不存在 → code_move="neither"，仍做图引用收尾"""
    # 不建 a.py / a2.py 实体文件——只靠 meta 在
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "sym", "g1")

    report = base.refactor_file("a.py", "a2.py")
    assert report["code_move"] == "neither"
    assert report["gbc_move"] == "moved"  # meta json 仍搬走

    # 图引用仍被重写
    deps = base.list_depends_on("b.py")
    assert deps[0].symbol == "a2.py:sym"


def test_refactor_file_disable_guarantees_false(fake_project, passing_test_file):
    """refactor_file：disable_guarantees=False 时不自动停用"""
    tmp = fake_project

    (tmp / "a.py").write_text("# provider\n", encoding="utf-8")
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )

    report = base.refactor_file("a.py", "a2.py", disable_guarantees=False)
    assert report["disabled"] == []

    provides = base.list_provides("a2.py")
    assert provides["g1"].disabled is False


# ============================================================================
# rename_guarantee
# ============================================================================


def test_rename_guarantee_basic(fake_project, passing_test_file):
    """rename_guarantee：id 改名 + consumer guarantees 同步改名，id 改名前后 disabled 状态不变"""
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "sym", "g1")

    result = base.rename_guarantee("a.py", "g1", "g2")

    assert result["provider"] == "a.py"
    assert result["old_id"] == "g1"
    assert result["new_id"] == "g2"
    assert result["consumers_updated"] == ["b.py"]

    provides = base.list_provides("a.py")
    assert "g1" not in provides
    assert "g2" in provides

    deps = base.list_depends_on("b.py")
    assert deps[0].guarantees == ["g2"]


def test_rename_guarantee_new_id_exists_raises(fake_project, passing_test_file):
    """rename_guarantee：new_id 已存在且 ≠ old_id → GuaranteeDuplicatedError"""
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.create_guarantee(
        "a.py", "g2", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )

    with pytest.raises(GuaranteeDuplicatedError):
        base.rename_guarantee("a.py", "g1", "g2")


def test_rename_guarantee_old_id_not_found_raises(fake_project, passing_test_file):
    """rename_guarantee：old_id 不存在 → GuaranteeNotFoundError"""
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )

    with pytest.raises(GuaranteeNotFoundError):
        base.rename_guarantee("a.py", "nonexistent", "g2")


def test_rename_guarantee_idempotent_noop(fake_project, passing_test_file):
    """rename_guarantee：old_id == new_id 不抛错（幂等退化为 no-op），仍正常返回"""
    base.create_guarantee(
        "a.py", "g1", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )

    result = base.rename_guarantee("a.py", "g1", "g1")
    assert result["old_id"] == "g1"
    assert result["new_id"] == "g1"
    assert "g1" in base.list_provides("a.py")


# ============================================================================
# refactor_func
# ============================================================================


def test_refactor_func_basic(fake_project, passing_test_file):
    """refactor_func：consumer symbol 同步改名 + 保证 id 改名 + 自动 disable"""
    base.create_guarantee(
        "a.py", "foo", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "foo", "foo")

    result = base.refactor_func("a.py", "foo", "bar")

    assert result["provider"] == "a.py"
    assert result["old_symbol"] == "foo"
    assert result["new_symbol"] == "bar"
    assert result["symbol_refs_rewritten"] == 1
    assert result["ids_renamed"] == [{"old": "foo", "new": "bar"}]
    # refactor_func 的 disabled 是字符串列表(保证 id)，不是 dict
    assert result["disabled"] == ["bar"]
    assert isinstance(result.get("md_refs_rewritten"), int)
    assert isinstance(result.get("next_steps"), str)

    deps = base.list_depends_on("b.py")
    assert deps[0].symbol == "a.py:bar"
    assert deps[0].guarantees == ["bar"]

    provides = base.list_provides("a.py")
    assert "foo" not in provides
    assert "bar" in provides
    assert provides["bar"].disabled is True


def test_refactor_func_dotted_guarantee_id(fake_project, passing_test_file):
    """refactor_func：<symbol>.<behavior> 保证 id —— foo.something → bar.something"""
    base.create_guarantee(
        "a.py", "foo.something", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "foo", "foo.something")

    result = base.refactor_func("a.py", "foo", "bar")
    assert result["ids_renamed"] == [{"old": "foo.something", "new": "bar.something"}]
    assert result["disabled"] == ["bar.something"]

    provides = base.list_provides("a.py")
    assert "bar.something" in provides
    assert provides["bar.something"].disabled is True


def test_refactor_func_multiple_guarantees(fake_project, passing_test_file):
    """refactor_func：同一符号下多条保证 id 全部改名（foo 和 foo.x 都被改）"""
    base.create_guarantee(
        "a.py", "foo", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.create_guarantee(
        "a.py", "foo.alpha", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.create_guarantee(
        "a.py", "foo.beta", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "foo", "foo")

    result = base.refactor_func("a.py", "foo", "bar")

    renamed = {(r["old"], r["new"]) for r in result["ids_renamed"]}
    assert renamed == {("foo", "bar"), ("foo.alpha", "bar.alpha"), ("foo.beta", "bar.beta")}
    assert set(result["disabled"]) == {"bar", "bar.alpha", "bar.beta"}


def test_refactor_func_disable_guarantees_false(fake_project, passing_test_file):
    """refactor_func：disable_guarantees=False → 不自动停用"""
    base.create_guarantee(
        "a.py", "foo", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.add_dependency("b.py", "a.py", "foo", "foo")

    result = base.refactor_func("a.py", "foo", "bar", disable_guarantees=False)
    assert result["disabled"] == []

    provides = base.list_provides("a.py")
    assert provides["bar"].disabled is False


def test_refactor_func_only_matching_provider(fake_project, passing_test_file):
    """refactor_func：只改写恰好指向本 provider 的符号，不影响其它 provider 的同名符号"""
    base.create_guarantee(
        "a.py", "foo", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    base.create_guarantee(
        "other.py", "foo", desc="desc",
        test=passing_test_file, executor_name="pytest-fake",
    )
    # b 依赖 a.py:foo；c 依赖 other.py:foo
    base.add_dependency("b.py", "a.py", "foo", "foo")
    base.add_dependency("c.py", "other.py", "foo", "foo")

    base.refactor_func("a.py", "foo", "bar")

    # b 的符号应改成 a.py:bar
    assert base.list_depends_on("b.py")[0].symbol == "a.py:bar"
    # c 的符号应保持 other.py:foo
    assert base.list_depends_on("c.py")[0].symbol == "other.py:foo"
