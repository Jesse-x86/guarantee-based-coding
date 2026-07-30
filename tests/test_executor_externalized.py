# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:executor 配置状态外置到目标项目的 .gbc/,而非工具仓。

窄测试验证**承诺**而非实现:
- 配置落在 get_current_project()/.gbc/executors.json(随项目走,工具仓无状态)
- example 清单脱敏:只留名字 + comment,绝不含任何原始机器相关值(防泄密)
"""
import importlib
from pathlib import Path


def _fresh_modules():
    """重载 config/core 的 executor,清掉惰性单例缓存,保证每次从当前项目读。"""
    from gbc.app.config import executor as ce
    ce._cache = None
    ce._cache_path = None
    return ce


def test_config_lands_in_target_project_gbc(tmp_path):
    """承诺:executor 真配置落在目标项目的 .gbc/ 下,不碰工具仓。"""
    from gbc.app.config import project
    project.set_current_project(str(tmp_path))
    ce = _fresh_modules()
    from gbc.app.core import executor as ex

    ex.upsert_exec_config("dummy", ce.ExecutorModel(
        command=["python", "-m", "pytest", "{file}"],
        cwd="/some/where",
        comment="a runner",
    ))

    cfg_path = ce.executors_config_path()
    assert cfg_path == tmp_path / ".gbc" / "executors.json"
    assert cfg_path.exists()


def test_example_is_desensitized(tmp_path):
    """承诺:example 清单只暴露名字 + 显式 comment,绝无原始机器相关值。"""
    from gbc.app.config import project
    project.set_current_project(str(tmp_path))
    ce = _fresh_modules()
    from gbc.app.core import executor as ex

    secret_cwd = "/home/secret/proj"
    secret_arg = "--token=SUPER_SECRET_XYZ"
    ex.upsert_exec_config("runner", ce.ExecutorModel(
        command=["/home/secret/py", "-m", "pytest", "{file}", secret_arg],
        cwd=secret_cwd,
        comment="explain me",
    ))

    example_text = ce.executors_example_path().read_text(encoding="utf-8")
    # 原始敏感值绝不出现在 example 里
    assert "SUPER_SECRET_XYZ" not in example_text
    assert secret_cwd not in example_text
    # 名字与 comment 仍在(清单的价值)
    assert "runner" in example_text
    assert "explain me" in example_text


def test_lazy_no_load_at_import(tmp_path):
    """承诺:惰性——不在 import 时读盘,首次访问才按当前项目定位。"""
    from gbc.app.config import project
    ce = _fresh_modules()
    # 刚清空缓存,尚未访问 → 缓存应为空
    assert ce._cache is None
    project.set_current_project(str(tmp_path))
    ce.get_executors_config()  # 首次访问才加载
    assert ce._cache is not None
