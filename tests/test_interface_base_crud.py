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

"""窄测试 — interface/base.py 保证 CRUD 包装层（路径解析 + meta 落盘）。

测试 [[gbc/app/interface/base.py]] 中包装层的核心承诺：
- 真的落盘：create/disable/enable/update/retire 后 .gbc json 被创建/更新/清空
- 路径越界保护：_resolve 拒绝跳出项目根的路径，抛 IllegalFilePathError
- 核心层异常正确传播（MetaNotFoundError / GuaranteeNotFoundError / GuaranteeDuplicatedError
  / GuaranteeHasDependentsError / GuaranteeTestFailedError）
- list_provides 能读回落盘后的内容
"""

import pytest

from gbc.app.interface.base import (
    create_guarantee,
    disable_guarantee,
    enable_guarantee,
    update_guarantee,
    retire_guarantee,
    list_provides,
    meta_session,
)
from gbc.app.models.errors import (
    IllegalFilePathError,
    MetaNotFoundError,
    GuaranteeNotFoundError,
    GuaranteeDuplicatedError,
    GuaranteeHasDependentsError,
    GuaranteeTestFailedError,
)


# ============================================================================
# Group 1: 真的落盘
# ============================================================================

class TestDiskPersistence:
    """验证 interface 层 call 完之后 .gbc json 被真正写入/更新/删除。"""

    def test_create_writes_json_and_readable(self, fake_project, passing_test_file):
        """create → .gbc/gbc.a.py.json 存在，list_provides 可读。"""
        create_guarantee(
            "a.py", "func.ok", desc="test desc",
            test=passing_test_file, executor_name="pytest-fake",
        )
        json_path = fake_project / ".gbc" / "gbc.a.py.json"
        assert json_path.exists(), "create 未落盘"
        result = list_provides("a.py")
        assert "func.ok" in result
        assert result["func.ok"].desc == "test desc"

    def test_create_disabled_skips_gate_but_still_writes(self, fake_project, failing_test_file):
        """disabled=True 跳过门禁但照常落盘。"""
        create_guarantee(
            "b.py", "func.dis", desc="disabled guarantee",
            test=failing_test_file, executor_name="pytest-fake", disabled=True,
        )
        json_path = fake_project / ".gbc" / "gbc.b.py.json"
        assert json_path.exists()
        result = list_provides("b.py")
        assert result["func.dis"].disabled is True

    def test_disable_persists_to_disk(self, fake_project, passing_test_file):
        """disable 后 session 关闭，重读 → disabled=True。"""
        create_guarantee(
            "c.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        disable_guarantee("c.py", "func.ok")
        result = list_provides("c.py")
        assert result["func.ok"].disabled is True

    def test_enable_persists_to_disk(self, fake_project, passing_test_file):
        """先 create disabled → enable → 重读 disabled=False。"""
        create_guarantee(
            "d.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake", disabled=True,
        )
        enable_guarantee("d.py", "func.ok")
        result = list_provides("d.py")
        assert result["func.ok"].disabled is False

    def test_update_desc_persists_to_disk(self, fake_project, passing_test_file):
        """update desc → 打开新 session 读到新值。"""
        create_guarantee(
            "e.py", "func.ok", desc="original",
            test=passing_test_file, executor_name="pytest-fake",
        )
        update_guarantee("e.py", "func.ok", desc="updated")
        result = list_provides("e.py")
        assert result["func.ok"].desc == "updated"

    def test_retire_removes_from_disk(self, fake_project, passing_test_file):
        """retire → list_provides 不再有该 gid。"""
        create_guarantee(
            "f.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        retire_guarantee("f.py", "func.ok")
        result = list_provides("f.py")
        assert "func.ok" not in result

    def test_multi_guarantee_roundtrip(self, fake_project, passing_test_file):
        """同文件多条保证 → 全部落盘并可读回。"""
        create_guarantee(
            "g.py", "func.a", desc="alpha",
            test=passing_test_file, executor_name="pytest-fake",
        )
        create_guarantee(
            "g.py", "func.b", desc="beta",
            test=passing_test_file, executor_name="pytest-fake",
        )
        result = list_provides("g.py")
        assert len(result) == 2
        assert result["func.a"].desc == "alpha"
        assert result["func.b"].desc == "beta"


# ============================================================================
# Group 2: 路径越界保护
# ============================================================================

class TestPathBoundary:
    """验证 _resolve 拒绝跳出项目根的路径。

    当前 _resolve 用 Path.is_relative_to() 做词法前缀检查（不解析 .. 段），
    因此「../../etc/passwd」这类相对逃逸无法拦截——但已知且可接受：
    provider 路径由 GBC 工具/MCP 生成、非用户手输，不会出现 .. 逃逸。
    真正生效的闸门是「绝对路径不在项目内」。
    """

    def test_absolute_outside_project_rejected_for_create(self, fake_project, tmp_path):
        """绝对路径指向 fake_project(tmp_path) 之外 → create 抛 IllegalFilePathError。"""
        outside = str(tmp_path.parent / "outside.txt")
        with pytest.raises(IllegalFilePathError):
            create_guarantee(
                outside, "x.y", desc="x",
                test="t.py", executor_name="pytest-fake",
            )

    def test_absolute_outside_project_rejected_for_disable(self, fake_project, tmp_path):
        """disable 也走 _resolve → 绝对路径越界同样被拒。"""
        outside = str(tmp_path.parent / "outside.txt")
        with pytest.raises(IllegalFilePathError):
            disable_guarantee(outside, "x.y")

    def test_absolute_outside_project_rejected_for_retire(self, fake_project, tmp_path):
        """retire 也走 _resolve → 绝对路径越界同样被拒。"""
        outside = str(tmp_path.parent / "outside.txt")
        with pytest.raises(IllegalFilePathError):
            retire_guarantee(outside, "x.y")

    def test_relative_within_project_ok(self, fake_project, passing_test_file):
        """相对路径在项目内 → 正常落盘 = _resolve 过闸。"""
        create_guarantee(
            "subdir/file.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        result = list_provides("subdir/file.py")
        assert "func.ok" in result

    def test_absolute_within_project_ok(self, fake_project, passing_test_file):
        """绝对路径在项目内 → 正常落盘。"""
        abs_provider = str(fake_project / "abs_file.py")
        create_guarantee(
            abs_provider, "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        result = list_provides(abs_provider)
        assert "func.ok" in result


# ============================================================================
# Group 3: 异常传播
# ============================================================================

class TestErrorPropagation:
    """验证 interface 层正确穿透 meta_session 把核心异常透传上来。"""

    # --- 文件不存在 ---

    def test_disable_nonexistent_file_raises(self, fake_project):
        """从未注册的文件 → MetaNotFoundError（meta_session 中 _load_meta 抛）。"""
        with pytest.raises(MetaNotFoundError):
            disable_guarantee("no_such.py", "x.y")

    def test_enable_nonexistent_file_raises(self, fake_project):
        with pytest.raises(MetaNotFoundError):
            enable_guarantee("no_such.py", "x.y")

    def test_update_nonexistent_file_raises(self, fake_project):
        with pytest.raises(MetaNotFoundError):
            update_guarantee("no_such.py", "x.y", desc="new")

    def test_retire_nonexistent_file_raises(self, fake_project):
        with pytest.raises(MetaNotFoundError):
            retire_guarantee("no_such.py", "x.y")

    # --- gid 不存在 ---

    def test_disable_nonexistent_gid_raises(self, fake_project, passing_test_file):
        """文件存在但 gid 不存在 → GuaranteeNotFoundError。"""
        create_guarantee(
            "h.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            disable_guarantee("h.py", "no.such")

    def test_enable_nonexistent_gid_raises(self, fake_project, passing_test_file):
        create_guarantee(
            "h.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            enable_guarantee("h.py", "no.such")

    def test_retire_nonexistent_gid_raises(self, fake_project, passing_test_file):
        create_guarantee(
            "h.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeNotFoundError):
            retire_guarantee("h.py", "no.such")

    # --- 重复 gid ---

    def test_create_duplicate_raises(self, fake_project, passing_test_file):
        """重复 gid → GuaranteeDuplicatedError。"""
        create_guarantee(
            "i.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeDuplicatedError):
            create_guarantee(
                "i.py", "func.ok", desc="test2",
                test=passing_test_file, executor_name="pytest-fake",
            )

    # --- 出生即绿失败 ---

    def test_create_failing_test_raises_no_disk_write(self, fake_project, failing_test_file):
        """create 用 failing 测试 → GuaranteeTestFailedError，.gbc json 不创建。"""
        with pytest.raises(GuaranteeTestFailedError):
            create_guarantee(
                "j.py", "func.bad", desc="test",
                test=failing_test_file, executor_name="pytest-fake",
            )
        json_path = fake_project / ".gbc" / "gbc.j.py.json"
        assert not json_path.exists(), "门禁失败不应落盘"

    def test_enable_failing_keeps_disabled(self, fake_project, failing_test_file):
        """enable 底层测试失败的保证 → GuaranteeTestFailedError，disabled 保持 True。"""
        create_guarantee(
            "k.py", "func.bad", desc="test",
            test=failing_test_file, executor_name="pytest-fake", disabled=True,
        )
        with pytest.raises(GuaranteeTestFailedError):
            enable_guarantee("k.py", "func.bad")
        result = list_provides("k.py")
        assert result["func.bad"].disabled is True, "门禁不过不能偷偷转正"

    def test_update_test_to_failing_preserves_old(self, fake_project, passing_test_file, failing_test_file):
        """update test 换成 failing → 抛异常，旧 test 值仍留在磁盘。"""
        create_guarantee(
            "l.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        with pytest.raises(GuaranteeTestFailedError):
            update_guarantee("l.py", "func.ok", test=failing_test_file)
        result = list_provides("l.py")
        assert result["func.ok"].test == passing_test_file, "门禁失败 test 不应保存"

    # --- retire 有 dependents 保护 ---

    def test_retire_with_dependents_raises(self, fake_project, passing_test_file):
        """保证仍有 dependents → GuaranteeHasDependentsError，gid 仍在磁盘。"""
        create_guarantee(
            "m.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        # 直接往 meta 里塞一个 consumer（不走 add_dependency，避免依赖另一个文件）
        with meta_session("m.py") as meta:
            meta.provides["func.ok"].dependents.append("consumer.py")
        with pytest.raises(GuaranteeHasDependentsError):
            retire_guarantee("m.py", "func.ok")
        result = list_provides("m.py")
        assert "func.ok" in result, "有 dependents 时不能退休"


# ============================================================================
# Group 4: 嵌套路径
# ============================================================================

class TestNestedPaths:
    """验证 interface 层正确处理嵌套目录中的文件。"""

    def test_nested_file_creates_gbc_subdir(self, fake_project, passing_test_file):
        """'a/b/c.py' → .gbc/a/b/gbc.c.py.json 被创建。"""
        create_guarantee(
            "a/b/c.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        json_path = fake_project / ".gbc" / "a" / "b" / "gbc.c.py.json"
        assert json_path.exists()
        result = list_provides("a/b/c.py")
        assert "func.ok" in result

    def test_nested_disable_and_read_back(self, fake_project, passing_test_file):
        """嵌套路径 disable → 重读 disabled=True。"""
        create_guarantee(
            "x/y/z.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        disable_guarantee("x/y/z.py", "func.ok")
        result = list_provides("x/y/z.py")
        assert result["func.ok"].disabled is True

    def test_nested_retire_and_read_back(self, fake_project, passing_test_file):
        """嵌套路径 retire → 重读无该 gid。"""
        create_guarantee(
            "p/q/r.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        retire_guarantee("p/q/r.py", "func.ok")
        result = list_provides("p/q/r.py")
        assert "func.ok" not in result


# ============================================================================
# Group 5: update 非 runner 字段落盘
# ============================================================================

class TestUpdateNonRunner:
    """update 改 heavy / timeout 等非 runner 字段：不触发门禁但落盘。"""

    def test_update_heavy_persists(self, fake_project, passing_test_file):
        """update heavy=5 → 重读 heavy==5。"""
        create_guarantee(
            "n.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        update_guarantee("n.py", "func.ok", heavy=5)
        result = list_provides("n.py")
        assert result["func.ok"].heavy == 5

    def test_update_timeout_override_persists(self, fake_project, passing_test_file):
        """update timeout_override=120 → 重读确认。"""
        create_guarantee(
            "o.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        update_guarantee("o.py", "func.ok", timeout_override=120)
        result = list_provides("o.py")
        assert result["func.ok"].timeout_override == 120

    def test_update_multiple_non_runner_fields(self, fake_project, passing_test_file):
        """同时改 desc + heavy + timeout → 全部落盘。"""
        create_guarantee(
            "p.py", "func.ok", desc="test",
            test=passing_test_file, executor_name="pytest-fake",
        )
        update_guarantee("p.py", "func.ok", desc="multi", heavy=3, timeout_override=60)
        result = list_provides("p.py")
        assert result["func.ok"].desc == "multi"
        assert result["func.ok"].heavy == 3
        assert result["func.ok"].timeout_override == 60
