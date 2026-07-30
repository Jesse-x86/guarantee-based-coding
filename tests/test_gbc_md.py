# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""窄测试: gbc/app/utils/gbc_md.py 的 gbc.md 解析/序列化 round-trip 保真 + 宽松解析。
"""
from gbc.app.utils.gbc_md import parse, serialize, Entry


def test_parse_full_doc():
    """完整 gbc.md: intent + constraints + 两个 entries（一文件一子文件夹）。"""
    text = """# 意图
应用层入口，协调各子系统。

# 内部约束
不得直接引入数据库模块，必须走 service 层。

# 文件
## main.py
主入口文件，初始化 FastAPI app。

## maker/
游戏制作子模块，包含模板渲染与资源管理。
"""
    doc = parse(text)
    assert doc.intent == "应用层入口，协调各子系统。"
    assert doc.constraints == "不得直接引入数据库模块，必须走 service 层。"
    assert len(doc.entries) == 2
    assert doc.entries[0].name == "main.py"
    assert doc.entries[0].is_dir is False
    assert doc.entries[0].desc == "主入口文件，初始化 FastAPI app。"
    assert doc.entries[1].name == "maker/"
    assert doc.entries[1].is_dir is True
    assert doc.entries[1].desc == "游戏制作子模块，包含模板渲染与资源管理。"


def test_parse_no_constraints():
    """没有 # 内部约束 标题时 constraints 为空。"""
    text = """# 意图
简单意图。

# 文件
## foo.py
一个文件。
"""
    doc = parse(text)
    assert doc.intent == "简单意图。"
    assert doc.constraints == ""
    assert len(doc.entries) == 1
    assert doc.entries[0].name == "foo.py"
    assert doc.entries[0].is_dir is False
    assert doc.entries[0].desc == "一个文件。"


def test_parse_no_files_heading_lenient():
    """没有 # 文件 但直接有 ## 子标题（老格式宽松解析）。"""
    text = """# 意图
老格式意图。

## bar.py
老格式下的文件描述。
"""
    doc = parse(text)
    assert doc.intent == "老格式意图。"
    assert doc.constraints == ""
    assert len(doc.entries) == 1
    assert doc.entries[0].name == "bar.py"
    assert doc.entries[0].is_dir is False
    assert doc.entries[0].desc == "老格式下的文件描述。"


def test_serialize_no_constraints_heading():
    """constraints 为空时 serialize 不含 # 内部约束。"""
    text = serialize("hello intent", "", [])
    assert "hello intent" in text
    assert "# 内部约束" not in text


def test_serialize_no_files_heading():
    """entries 为空时 serialize 不含 # 文件。"""
    text = serialize("hello intent", "some constraints", [])
    assert "# 文件" not in text
    assert "# 内部约束" in text  # constraints 非空应有


def test_round_trip_full():
    """serialize → parse round-trip：全量字段保真。"""
    entries = [
        Entry(name="main.py", is_dir=False, desc="主入口文件。"),
        Entry(name="maker/", is_dir=True, desc="游戏制作子模块。"),
    ]
    intent = "应用层入口，协调各子系统。"
    constraints = "不得直接引入数据库模块。"
    text = serialize(intent, constraints, entries)
    doc = parse(text)
    assert doc.intent == intent
    assert doc.constraints == constraints
    assert len(doc.entries) == 2
    assert doc.entries[0].name == "main.py"
    assert doc.entries[0].is_dir is False
    assert doc.entries[0].desc == "主入口文件。"
    assert doc.entries[1].name == "maker/"
    assert doc.entries[1].is_dir is True
    assert doc.entries[1].desc == "游戏制作子模块。"


def test_multi_paragraph_intent_round_trip():
    """多段落意图（含换行）round-trip 保真。"""
    entries = [Entry(name="x.py", is_dir=False, desc="a file.")]
    intent = """第一段。

第二段。

第三段。"""
    constraints = "约束只有一行。"
    text = serialize(intent, constraints, entries)
    doc = parse(text)
    assert doc.intent == intent
    assert doc.constraints == constraints
    assert len(doc.entries) == 1
    assert doc.entries[0].name == "x.py"
    assert doc.entries[0].is_dir is False
    assert doc.entries[0].desc == "a file."
