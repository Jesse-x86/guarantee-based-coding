# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:静态资源定位入口 gbc.app.assets 的承诺。

集中在 gbc/assets/ 下的资源(i18n catalog/texts、editor 前端)必须在源码树里
真实存在、且指向已填充的资源——这是"资源丢失/被移走"回归的哨兵。它守着两件事:
    1. app.assets 的路径常量指向真实存在的目录;
    2. 每个目录里确有预期资源(catalog 的 en.json、texts 的 rules、editor 的 index.html),
       不是空壳。
定位方式变了、资源被挪走却忘了改常量,此测试立即飘红。
"""
from gbc.app import assets


def test_assets_dirs_exist():
    """承诺:四个资源目录都在源码树里真实存在。"""
    assert assets.I18N_CATALOG_DIR.is_dir()
    assert assets.I18N_TEXTS_DIR.is_dir()
    assert assets.EDITOR_FRONTEND_DIR.is_dir()
    assert assets.SKILLS_DIR.is_dir()


def test_setup_text_present():
    """承诺:texts 目录含 setup 接线指南(gbc setup 的资源)。"""
    assert (assets.I18N_TEXTS_DIR / "setup.en.md").is_file()


def test_catalog_has_default_lang():
    """承诺:catalog 目录含默认语言 en.json(i18n 兜底的根)。"""
    assert (assets.I18N_CATALOG_DIR / "en.json").is_file()


def test_texts_has_rules():
    """承诺:texts 目录含 rules 长文本(gbc rules 的资源)。"""
    assert (assets.I18N_TEXTS_DIR / "rules.en.md").is_file()


def test_editor_has_index():
    """承诺:editor 前端目录含 index.html(gbc editor up 的入口页)。"""
    assert (assets.EDITOR_FRONTEND_DIR / "index.html").is_file()
