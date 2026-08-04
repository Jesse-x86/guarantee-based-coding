"""窄测试 for gbc.app.interface.base 的全局反查/一致性检查函数。

测试 target: who_depends_on / check_consistency / render_tree。
"""

import pytest


def test_who_depends_on_by_guarantee_id(fake_project, passing_test_file):
    """who_depends_on 用 guarantee_id 精确查询：返回 dependents 里含 consumer。"""
    from gbc.app.interface.base import create_guarantee, add_dependency, who_depends_on

    (fake_project / "provider.py").write_text("# provider")
    (fake_project / "consumer.py").write_text("# consumer")

    create_guarantee("provider.py", "func.beh", "a behavior", passing_test_file, "pytest-fake")
    add_dependency("consumer.py", "provider.py", "func", "func.beh")

    result = who_depends_on("provider.py", guarantee_id="func.beh")
    assert result["guarantee"] == "func.beh"
    assert "consumer.py" in result["dependents"]


def test_who_depends_on_global_scan_symbol_filter(fake_project, passing_test_file):
    """who_depends_on 全局扫描（不给 guarantee_id）：symbol= 过滤只返回匹配的 symbol。"""
    from gbc.app.interface.base import create_guarantee, add_dependency, who_depends_on

    (fake_project / "prov.py").write_text("# provider")
    (fake_project / "c1.py").write_text("# consumer 1")
    (fake_project / "c2.py").write_text("# consumer 2")

    create_guarantee("prov.py", "a.beh", "a behavior", passing_test_file, "pytest-fake")
    create_guarantee("prov.py", "b.beh", "b behavior", passing_test_file, "pytest-fake")
    add_dependency("c1.py", "prov.py", "a", "a.beh")
    add_dependency("c2.py", "prov.py", "b", "b.beh")

    result = who_depends_on("prov.py", symbol="a")
    assert result["provider"] == "prov.py"
    assert result["symbol"] == "a"
    consumers = [d["consumer"] for d in result["dependents"]]
    assert "c1.py" in consumers
    assert "c2.py" not in consumers


def test_check_consistency_requires_gbc_directory(fake_project):
    """缺少 .gbc 时必须报错；显式初始化的空 .gbc 才是空图。"""
    from gbc.app.config.project import set_current_project
    from gbc.app.interface.base import check_consistency
    from gbc.app.models.errors import MetaNotFoundError

    project_root = fake_project / "uninitialized"
    project_root.mkdir()
    set_current_project(project_root)
    gbc_root = project_root / ".gbc"

    with pytest.raises(MetaNotFoundError) as exc_info:
        check_consistency()

    assert exc_info.value.original_file == project_root
    assert exc_info.value.target_file == gbc_root

    gbc_root.mkdir()
    assert check_consistency() == []


def test_check_consistency_clean_graph(fake_project, passing_test_file):
    """check_consistency：一致图没有 dangling/missing_reverse/missing_forward 错误。"""
    from gbc.app.interface.base import create_guarantee, add_dependency, check_consistency

    (fake_project / "p.py").write_text("# provider")
    (fake_project / "c.py").write_text("# consumer")

    create_guarantee("p.py", "f.beh", "desc", passing_test_file, "pytest-fake")
    add_dependency("c.py", "p.py", "f", "f.beh")

    violations = check_consistency()
    error_types = {v["type"] for v in violations}
    assert "dangling_guarantee" not in error_types
    assert "missing_reverse" not in error_types
    assert "missing_forward" not in error_types


def test_check_consistency_dangling_guarantee(fake_project, passing_test_file):
    """check_consistency：手动在 consumer meta 加不存在的 gid → dangling_guarantee。"""
    from gbc.app.interface.base import create_guarantee, add_dependency, check_consistency
    from gbc.app.utils.json_model_operator import load_model_from_json, save_model_to_json
    from gbc.app.utils.file_utils import to_gbc_json_path
    from gbc.app.models.meta import FileMeta

    (fake_project / "p.py").write_text("# provider")
    (fake_project / "c.py").write_text("# consumer")

    create_guarantee("p.py", "f.beh", "desc", passing_test_file, "pytest-fake")
    add_dependency("c.py", "p.py", "f", "f.beh")

    # 手动破坏图：往 consumer meta 里塞一条指向不存在 gid 的依赖
    json_path = to_gbc_json_path(fake_project / "c.py")
    meta = load_model_from_json(json_path, FileMeta)
    for dep in meta.depends_on:
        if dep.symbol.startswith("p.py:"):
            dep.guarantees.append("f.nonexistent")
            break
    save_model_to_json(meta, json_path)

    violations = check_consistency()
    dangling = [v for v in violations if v["type"] == "dangling_guarantee"]
    assert len(dangling) >= 1
    assert dangling[0]["guarantee"] == "f.nonexistent"


def test_check_consistency_disabled_guarantee(fake_project, passing_test_file):
    """check_consistency：disable_guarantee → disabled_guarantee + depends_on_disabled。"""
    from gbc.app.interface.base import (
        create_guarantee, add_dependency, disable_guarantee, check_consistency,
    )

    (fake_project / "p.py").write_text("# provider")
    (fake_project / "c.py").write_text("# consumer")

    create_guarantee("p.py", "f.beh", "desc", passing_test_file, "pytest-fake")
    add_dependency("c.py", "p.py", "f", "f.beh")
    disable_guarantee("p.py", "f.beh")

    violations = check_consistency()
    types = [v["type"] for v in violations]
    assert "disabled_guarantee" in types
    assert "depends_on_disabled" in types


def test_render_tree_basic(fake_project, passing_test_file):
    """render_tree 基本渲染：含保证 id 文本和 provider 文件名。"""
    from gbc.app.interface.base import create_guarantee, render_tree
    from gbc.app.intent.base import set_intent, set_file

    (fake_project / "my_prov.py").write_text("# provider")

    create_guarantee("my_prov.py", "my_func.works", "it works", passing_test_file, "pytest-fake")

    gbc_root = fake_project / ".gbc"
    set_intent(gbc_root, "", "根意图")
    set_file(gbc_root, "", "my_prov.py", "my provider file")

    tree = render_tree()
    assert "my_func.works" in tree
    assert "my_prov.py" in tree
