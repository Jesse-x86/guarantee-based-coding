# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:i18n 层的承诺。

- 语言判定优先级:显式 > GBC_LANG > locale > 默认 en。
- 受支持语言**从文件自动发现**:catalog 目录里放一个 <lang>.json 就被识别。
- 漏译检查:每门被发现的语言,其 catalog 键集应覆盖 en 的全部键(不漏译)。
- 长文本按当前语言读出,缺失语言回退默认 en。
"""
from gbc.app.i18n import lang as L
from gbc.app.i18n import t, load_text, supported_langs, catalog_keys, DEFAULT_LANG


def test_resolve_explicit_wins(monkeypatch):
    """承诺:显式 lang 优先级最高,压过环境变量。"""
    monkeypatch.setenv("GBC_LANG", "en")
    assert L.resolve_lang("zh") == "zh"


def test_resolve_env_over_locale(monkeypatch):
    """承诺:GBC_LANG 压过系统 locale。"""
    monkeypatch.setenv("GBC_LANG", "zh")
    assert L.resolve_lang(None) == "zh"


def test_resolve_falls_back_to_en(monkeypatch):
    """承诺:全都取不到时兜底 en。"""
    monkeypatch.delenv("GBC_LANG", raising=False)
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setattr(L.locale, "getlocale", lambda: (None, None))
    assert L.resolve_lang(None) == "en"


def test_supported_langs_discovered_from_files():
    """承诺:受支持语言从 catalog 文件自动发现,至少含 en 与 zh,且 en 兜底置首。"""
    langs = supported_langs()
    assert "en" in langs and "zh" in langs
    assert langs[0] == DEFAULT_LANG  # en 永远在,作兜底


def test_no_missing_translation():
    """承诺:每门被发现的语言都覆盖 en 的全部键(不漏译)。

    这条守着"加语言"的质量:放了 ja.json 却漏某个键,此测试立即飘红指名。
    """
    en_keys = catalog_keys("en")
    for lg in supported_langs():
        keys = catalog_keys(lg)
        missing = en_keys - keys
        assert not missing, f"language '{lg}' missing keys: {sorted(missing)}"


def test_t_formats_and_switches_language():
    """承诺:t() 按语言取串并填充占位。"""
    zh = t("err.executor_not_found", lang="zh", name="pytest")
    en = t("err.executor_not_found", lang="en", name="pytest")
    assert "pytest" in zh and "pytest" in en
    assert zh != en


def test_t_error_messages_localized():
    """承诺:报错前缀也走 catalog,中英不同(人类可读的本地化)。"""
    assert t("err.illegal_operation", lang="zh", msg="x") != t("err.illegal_operation", lang="en", msg="x")
    assert "非法" in t("err.illegal_operation", lang="zh", msg="x")


def test_t_unknown_key_returns_key():
    """承诺:未知键不炸,返回键本身。"""
    assert t("no.such.key") == "no.such.key"


def test_load_text_rules_both_langs():
    """承诺:长文本 rules 双语都能整篇读出,且强调"非强制沙箱"。"""
    zh = load_text("rules", lang="zh")
    en = load_text("rules", lang="en")
    assert len(zh) > 50 and len(en) > 50
    assert "强制" in zh
    assert "sandbox" in en.lower() or "enforce" in en.lower()
