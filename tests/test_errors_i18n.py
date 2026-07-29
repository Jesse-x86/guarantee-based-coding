# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:核心异常消息本地化。

每个带消息的异常类的 __str__ 都经 i18n(而非硬编码英文);切语言时消息随之变化,
且携带的关键信息(文件名、id 等)仍出现在消息里。
"""
from gbc.app.i18n import set_lang
from gbc.app.models import errors as E


def _reset():
    set_lang("en")


def test_meta_not_found_localized():
    e = E.MetaNotFoundError(original_file="a.py", target_file="b.json")
    set_lang("en")
    en = str(e)
    set_lang("zh")
    zh = str(e)
    _reset()
    assert en != zh                       # 切语言消息不同
    assert "b.json" in en and "b.json" in zh  # 关键信息仍在
    assert "not found" in en.lower()
    assert "未找到" in zh


def test_executor_not_found_localized():
    e = E.ExecutorNotFoundError("pytest-x")
    set_lang("en"); en = str(e)
    set_lang("zh"); zh = str(e)
    _reset()
    assert "pytest-x" in en and "pytest-x" in zh
    assert en != zh


def test_guarantee_has_dependents_localized():
    e = E.GuaranteeHasDependentsError(provider="p.py", guarantee_id="g.id", dependents=["c.py"])
    set_lang("en"); en = str(e)
    set_lang("zh"); zh = str(e)
    _reset()
    assert "g.id" in en and "g.id" in zh
    assert "c.py" in en and "c.py" in zh   # dependents 列表仍在
    assert en != zh


def test_all_message_exceptions_use_i18n():
    """承诺:所有带 __str__ 的异常都不再返回硬编码英文——切到 zh 后不应仍是纯英文原文。"""
    samples = [
        E.IllegalFilePathError("x"),
        E.ConfigNotFoundError("x"),
        E.ConfigParseError("x", "info"),
        E.ProjectNotFoundError("x"),
        E.MetaNotFoundError("o", "t"),
        E.GuaranteeDuplicatedError("t", "g"),
        E.GuaranteeNotFoundError("t", "g"),
        E.GuaranteeTestFailedError("t", "g", "info"),
        E.GuaranteeHasDependentsError("p", "g", ["c"]),
        E.ExecutorNotFoundError("x"),
        E.ExecutorConfigInvalidError("x"),
    ]
    for exc in samples:
        set_lang("en"); en = str(exc)
        set_lang("zh"); zh = str(exc)
        # key 回退不算数:消息里应有中文字符(说明真的走了 zh catalog)
        assert any("\u4e00" <= ch <= "\u9fff" for ch in zh), f"{type(exc).__name__} not localized: {zh}"
    _reset()
