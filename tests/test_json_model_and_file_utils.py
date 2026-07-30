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

"""json_model_operator + file_utils 窄测试合包"""

import json
from pathlib import Path

import pydantic
import pytest
from pydantic import BaseModel

from gbc.app.utils.file_utils import to_gbc_json_path
from gbc.app.utils.json_model_operator import (
    load_model_from_json,
    save_model_to_json,
)


# ---------------------------------------------------------------------------
# 最小测试模型——不依赖项目内部模型，纯粹测试 operator 的 round-trip
# ---------------------------------------------------------------------------

class _TestModel(BaseModel):
    name: str
    count: int = 0
    tags: list[str] = []


# ===========================================================================
# json_model_operator
# ===========================================================================

class TestSaveModel:
    def test_creates_missing_parent_dirs(self, tmp_path: Path):
        """save 到不存在的子目录 → 目录自动建好，文件存在。"""
        target = tmp_path / "a" / "b" / "c.json"
        assert not target.parent.exists()

        save_model_to_json(_TestModel(name="x"), target)

        assert target.exists()
        assert target.is_file()


class TestRoundTrip:
    def test_save_then_load_preserves_fields(self, tmp_path: Path):
        """写入后 load 回来 → 所有字段值一致。"""
        original = _TestModel(name="hello", count=42, tags=["a", "b"])
        target = tmp_path / "data.json"

        save_model_to_json(original, target)
        restored = load_model_from_json(target, _TestModel)

        assert restored.name == original.name
        assert restored.count == original.count
        assert restored.tags == original.tags


class TestLoadErrors:
    def test_file_not_found(self, tmp_path: Path):
        """文件不存在 → FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            load_model_from_json(tmp_path / "no_such.json", _TestModel)

    def test_invalid_json(self, tmp_path: Path):
        """文件内容不是合法 JSON → ValueError。"""
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")

        with pytest.raises(ValueError):
            load_model_from_json(bad, _TestModel)

    def test_json_with_wrong_field_type(self, tmp_path: Path):
        """合法 JSON 但字段类型不对 → pydantic.ValidationError。"""
        wrong = tmp_path / "wrong.json"
        wrong.write_text('{"count": "not_a_number"}', encoding="utf-8")

        with pytest.raises(pydantic.ValidationError):
            load_model_from_json(wrong, _TestModel)


class TestChineseRoundTrip:
    def test_write_chinese_preserves_raw_characters(self, tmp_path: Path):
        """写入含中文 → 原始文件包含真实中文字符，非 \\u 转义。"""
        target = tmp_path / "zh.json"
        save_model_to_json(_TestModel(name="中文测试", tags=["标签"]), target)

        raw = target.read_text(encoding="utf-8")

        assert "中文测试" in raw
        assert "标签" in raw
        assert "\\u" not in raw

        # 同时验证 round-trip 语义正确
        restored = load_model_from_json(target, _TestModel)
        assert restored.name == "中文测试"
        assert restored.tags == ["标签"]


# ===========================================================================
# file_utils
# ===========================================================================

class TestToGbcJsonPath:
    def test_root_level_file(self, fake_project):
        """项目根平级文件 → .gbc/gbc.<name>.json"""
        provider = fake_project / "a.py"
        result = to_gbc_json_path(provider)
        expected = fake_project / ".gbc" / "gbc.a.py.json"
        assert result == expected

    def test_nested_file(self, fake_project):
        """嵌套子目录文件 → .gbc/x/y/gbc.b.py.json"""
        provider = fake_project / "x" / "y" / "b.py"
        result = to_gbc_json_path(provider)
        expected = fake_project / ".gbc" / "x" / "y" / "gbc.b.py.json"
        assert result == expected
