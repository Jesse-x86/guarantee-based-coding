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
from pathlib import Path
import runpy

from gbc.app import assets


def test_assets_dirs_exist():
    """承诺:四个资源目录都在源码树里真实存在。"""
    assert assets.I18N_CATALOG_DIR.is_dir()
    assert assets.I18N_TEXTS_DIR.is_dir()
    assert assets.EDITOR_FRONTEND_DIR.is_dir()
    assert assets.SKILLS_DIR.is_dir()
    assert assets.DOCS_DIR.is_dir()


def test_manual_topics_readable_after_cwd_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    located = runpy.run_path(str(Path(assets.__file__).resolve()))["DOCS_DIR"]
    for language in ("en", "zh"):
        for topic in ("quick-start", "concepts", "workflow", "reference", "onboarding-agent"):
            assert (located / language / f"{topic}.md").read_text(encoding="utf-8").strip()


def test_manual_location_is_package_first_and_checkout_anchored(tmp_path, monkeypatch):
    installed = tmp_path / "installed"
    module = installed / "gbc/app/assets.py"
    module.parent.mkdir(parents=True)
    module.write_text(Path(assets.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    source_docs = installed / "docs"
    source_docs.mkdir()
    marker = installed / "pyproject.toml"
    marker.write_text('[project]\nname = "guarantee-based-coding"\n', encoding="utf-8")
    foreign = tmp_path / "foreign"
    (foreign / "docs").mkdir(parents=True)
    (foreign / "pyproject.toml").write_text(marker.read_text(), encoding="utf-8")
    monkeypatch.chdir(foreign)
    assert runpy.run_path(str(module))["DOCS_DIR"] == source_docs
    packaged = installed / "gbc/assets/docs"
    packaged.mkdir(parents=True)
    assert runpy.run_path(str(module))["DOCS_DIR"] == packaged
    packaged.rmdir()
    marker.write_text('[project]\nname = "unrelated-project"\n', encoding="utf-8")
    assert runpy.run_path(str(module))["DOCS_DIR"] == packaged
    marker.unlink()
    assert runpy.run_path(str(module))["DOCS_DIR"] == packaged


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


def test_editor_frontend_structure():
    """承诺:editor 前端是零构建的多文件 ES 模块结构,index.html 引用的入口与样式真实存在。

    前端已从单页拆成 index.html + app.js(module 入口)+ i18n.js + js/*.js + css/*.css。
    任何一个模块被删/被改名都会让编辑器在浏览器里静默崩掉——本测试是结构级哨兵。
    """
    front = assets.EDITOR_FRONTEND_DIR
    assert (front / "app.js").is_file()
    assert (front / "i18n.js").is_file()
    for css in ("foundation.css", "workspace.css", "review.css"):
        assert (front / "css" / css).is_file()
    for mod in ("dom.js", "semantic.js", "diff.js", "api.js", "state.js",
                "tree-view.js", "editor-view.js", "review-view.js", "actions.js"):
        assert (front / "js" / mod).is_file()
    html = (front / "index.html").read_text(encoding="utf-8")
    assert 'type="module"' in html
    assert 'src="app.js"' in html
    for css in ("foundation.css", "workspace.css", "review.css"):
        assert f"css/{css}" in html
