# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证: config.project 管理当前目标项目根的运行时状态。

窄测试验证**承诺**而非实现:
- get_current_project() 默认返回进程启动时的 cwd（无环境变量、不回退包安装位置）
- set_current_project() 显式覆盖后，get_current_project() 返回新值
- 一切 .gbc 路径都相对它（这是 GBC 工具仓无状态、可 pip 安装的前提）
"""
from pathlib import Path

from gbc.app.config import project


def test_default_is_cwd():
    """承诺: 默认当前项目 = 进程启动时的 cwd（不是环境变量、不是包安装位置）。"""
    # get_current_project 返回的路径应等于当前进程的 cwd
    assert Path(project.get_current_project()) == Path.cwd()


def test_set_then_get_roundtrip(tmp_path):
    """承诺: set_current_project 显式覆盖后，get_current_project 返回新值。"""
    project.set_current_project(str(tmp_path))
    result = project.get_current_project()
    assert Path(result) == tmp_path


def test_set_accepts_string_and_returns_pathlike(tmp_path):
    """承诺: set_current_project 收字符串，get_current_project 返回的对象可当路径用。"""
    project.set_current_project(str(tmp_path))
    # get_current_project 的返回值能被 Path() 接受并用于拼接 .gbc 路径
    gbc_dir = Path(project.get_current_project()) / ".gbc"
    assert str(gbc_dir).endswith("/.gbc")
