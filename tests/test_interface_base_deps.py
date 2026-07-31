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

"""窄测试：gbc/app/interface/base.py 的 add_dependency / remove_dependency 包装层。

验证路径字符串被解析成项目内相对路径并真实落盘到 .gbc/，双向一致。
"""

import pytest

from gbc.app.interface.base import (
    add_dependency,
    remove_dependency,
    list_provides,
    list_depends_on,
    create_guarantee,
    check_consistency,
)
from gbc.app.models.errors import GuaranteeNotFoundError, MetaNotFoundError
from gbc.app.utils.file_utils import to_gbc_json_path


# ============================================================================
# add_dependency 免费依赖（guarantee_id=None）
# ============================================================================

class TestAddDependencyFree:
    """免费依赖：只动 consumer，不动 provider。"""

    def test_creates_consumer_depends_on_with_correct_symbol(self, fake_project):
        """consumer .gbc json 出现 depends_on 边，symbol 拼接正确，guarantees 为空。"""
        add_dependency("consumer.py", "provider.py", "my_func")

        deps = list_depends_on("consumer.py")
        assert len(deps) == 1
        assert deps[0].symbol == "provider.py:my_func"
        assert deps[0].guarantees == []

    def test_provider_untouched_for_free_dependency(self, fake_project):
        """provider 不存在也能成功——免费依赖不碰 provider 侧。"""
        add_dependency("consumer.py", "nonexistent_provider.py", "some_func")

        deps = list_depends_on("consumer.py")
        assert any(d.symbol == "nonexistent_provider.py:some_func" for d in deps)


# ============================================================================
# add_dependency 行为级依赖（guarantee_id 非 None）
# ============================================================================

class TestAddDependencyBehavioral:
    """行为级依赖：双向落盘，consumer 与 provider 两边一致。"""

    def test_bidirectional_persistence(self, fake_project, passing_test_file):
        """consumer depends_on 含 gid，provider 对应保证的 dependents 含 consumer。"""
        create_guarantee(
            "provider.py", "my_gid",
            desc="test guarantee",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        add_dependency("consumer.py", "provider.py", "my_func", guarantee_id="my_gid")

        # consumer 侧从盘上读回
        deps = list_depends_on("consumer.py")
        assert len(deps) == 1
        assert deps[0].symbol == "provider.py:my_func"
        assert "my_gid" in deps[0].guarantees

        # provider 侧从盘上读回
        provides = list_provides("provider.py")
        assert "my_gid" in provides
        assert "consumer.py" in provides["my_gid"].dependents

    def test_nonexistent_guarantee_raises(self, fake_project, passing_test_file):
        """provider 上不存在该 gid 时抛 GuaranteeNotFoundError。"""
        # 先让 provider meta 存在（建一条别的保证）
        create_guarantee(
            "provider.py", "existing_gid",
            desc="test guarantee",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            add_dependency(
                "consumer.py", "provider.py", "my_func",
                guarantee_id="nonexistent",
            )


# ============================================================================
# remove_dependency
# ============================================================================

class TestRemoveDependency:
    """撤销依赖：单向摘除或整条边撤销，consumer 与 provider 双向清理。"""

    def test_remove_entire_symbol_edge(self, fake_project, passing_test_file):
        """gid=None 撤销整条 symbol 边，consumer 与 provider 两边都清理。"""
        create_guarantee(
            "provider.py", "my_gid",
            desc="test guarantee",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        add_dependency(
            "consumer.py", "provider.py", "my_func",
            guarantee_id="my_gid",
        )

        remove_dependency("consumer.py", "provider.py", "my_func")

        # consumer 侧找不到这条 symbol 了
        deps = list_depends_on("consumer.py")
        assert not any(d.symbol == "provider.py:my_func" for d in deps)

        # provider 侧 dependents 也不含 consumer 了
        provides = list_provides("provider.py")
        assert "consumer.py" not in provides["my_gid"].dependents

    def test_remove_single_guarantee_keeps_other(self, fake_project, passing_test_file):
        """symbol 边挂两个 gid，只摘一个——另一个还在，provider 侧也只摘对应反向边。"""
        create_guarantee(
            "provider.py", "gid_a",
            desc="guarantee A",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        create_guarantee(
            "provider.py", "gid_b",
            desc="guarantee B",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        add_dependency(
            "consumer.py", "provider.py", "my_func",
            guarantee_id="gid_a",
        )
        add_dependency(
            "consumer.py", "provider.py", "my_func",
            guarantee_id="gid_b",
        )

        remove_dependency(
            "consumer.py", "provider.py", "my_func",
            guarantee_id="gid_a",
        )

        deps = list_depends_on("consumer.py")
        symbol_deps = [d for d in deps if d.symbol == "provider.py:my_func"]
        assert len(symbol_deps) == 1
        assert "gid_a" not in symbol_deps[0].guarantees
        assert "gid_b" in symbol_deps[0].guarantees

        provides = list_provides("provider.py")
        assert "consumer.py" not in provides["gid_a"].dependents
        assert "consumer.py" in provides["gid_b"].dependents

    def test_remove_nonexistent_symbol_raises(self, fake_project, passing_test_file):
        """找不到该 symbol 边时抛 GuaranteeNotFoundError。"""
        # 先让 provider 和 consumer 的 meta 都存在
        create_guarantee(
            "provider.py", "my_gid",
            desc="test guarantee",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        add_dependency("consumer.py", "provider.py", "existing_func")

        with pytest.raises(GuaranteeNotFoundError):
            remove_dependency("consumer.py", "provider.py", "nonexistent_func")

    def test_orphan_cleanup_removes_reverse_only_and_restores_consistency(
        self, fake_project, passing_test_file,
    ):
        """consumer meta 丢失后，gid 精确清理 provider 反向边且不重建空 meta。"""
        consumer_source = fake_project / "consumer.py"
        consumer_source.write_text("# consumer\n", encoding="utf-8")
        create_guarantee(
            "provider.py", "my_gid",
            desc="test guarantee",
            test=passing_test_file,
            executor_name="pytest-fake",
        )
        add_dependency(
            "consumer.py", "provider.py", "my_func", guarantee_id="my_gid",
        )

        consumer_json = to_gbc_json_path(consumer_source)
        consumer_json.unlink()
        consumer_source.unlink()
        assert {
            (v["type"], v.get("guarantee")) for v in check_consistency()
        } == {("missing_forward", "my_gid")}

        # orphan reverse edges do not retain symbol; explicit gid is the safe identity.
        remove_dependency(
            "consumer.py", "provider.py", "unverifiable_symbol", guarantee_id="my_gid",
        )

        assert "consumer.py" not in list_provides("provider.py")["my_gid"].dependents
        assert not consumer_json.exists()
        assert check_consistency() == []

    def test_orphan_cleanup_without_gid_rejected(self, fake_project, passing_test_file):
        """consumer meta 不存在时不可按无法验证的 symbol 猜测反向边。"""
        create_guarantee(
            "provider.py", "my_gid", "test guarantee", passing_test_file, "pytest-fake",
        )
        with pytest.raises(MetaNotFoundError):
            remove_dependency("consumer.py", "provider.py", "my_func")

        assert list_provides("provider.py")["my_gid"].dependents == []
        assert not to_gbc_json_path(fake_project / "consumer.py").exists()

    def test_orphan_cleanup_missing_provider_guarantee_rejected(
        self, fake_project, passing_test_file,
    ):
        """点名 gid 不在 provider 时拒绝，且不创建 consumer meta。"""
        create_guarantee(
            "provider.py", "existing_gid",
            "test guarantee", passing_test_file, "pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            remove_dependency(
                "consumer.py", "provider.py", "my_func", guarantee_id="missing_gid",
            )

        assert not to_gbc_json_path(fake_project / "consumer.py").exists()

    def test_orphan_cleanup_unlisted_consumer_rejected(
        self, fake_project, passing_test_file,
    ):
        """provider 保证存在但未列该 consumer 时拒绝。"""
        create_guarantee(
            "provider.py", "my_gid", "test guarantee", passing_test_file, "pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            remove_dependency(
                "consumer.py", "provider.py", "my_func", guarantee_id="my_gid",
            )

        assert list_provides("provider.py")["my_gid"].dependents == []
        assert not to_gbc_json_path(fake_project / "consumer.py").exists()

    def test_existing_consumer_wrong_symbol_does_not_detach_valid_edge(
        self, fake_project, passing_test_file,
    ):
        """consumer meta 存在时仍按 core symbol 语义；错 symbol 不得摘反向边。"""
        create_guarantee(
            "provider.py", "my_gid", "test guarantee", passing_test_file, "pytest-fake",
        )
        add_dependency(
            "consumer.py", "provider.py", "valid_func", guarantee_id="my_gid",
        )

        with pytest.raises(GuaranteeNotFoundError):
            remove_dependency(
                "consumer.py", "provider.py", "wrong_func", guarantee_id="my_gid",
            )

        deps = list_depends_on("consumer.py")
        assert any(
            d.symbol == "provider.py:valid_func" and "my_gid" in d.guarantees
            for d in deps
        )
        assert "consumer.py" in list_provides("provider.py")["my_gid"].dependents
