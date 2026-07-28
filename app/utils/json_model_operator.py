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

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.utils.safe_file_writer import SafeFileWriter

T = TypeVar("T", bound=BaseModel)


def load_model_from_json(
        filepath: str | Path,
        model_class: type[T]
) -> T:
    """
    从指定的 JSON 文件中读取并还原为 Pydantic 模型。

    Args:
        filepath: 明确的完整文件路径。
        model_class: 用于解析的 Pydantic 模型类。

    Returns:
        实例化后的模型对象。

    Raises:
        FileNotFoundError: 当指定路径不存在时抛出。
        ValidationError: 当 JSON 内容不符合模型定义时抛出。
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"未找到指定的模型文件: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"解析 JSON 文件失败: {path}, 错误详情: {e}")

    try:
        return model_class(**raw_data)
    except ValidationError as e:
        # 在这里可以记录日志或者直接抛出
        raise e

def save_model_to_json(
        model: BaseModel,
        filepath: str | Path,
        num_backups: int = 0
) -> None:
    """
    将 Pydantic 模型安全地序列化为 JSON 文件。

    Args:
        model: 要保存的 Pydantic 模型对象。
        filepath: 明确的完整文件路径。
        num_backups: 备份数量，由 SafeFileWriter 处理。
    """
    path = Path(filepath)

    # 确保父目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    writer = SafeFileWriter(path, num_backups=num_backups)

    # 获取字典数据
    data = model.model_dump()

    with writer.open(mode='w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)