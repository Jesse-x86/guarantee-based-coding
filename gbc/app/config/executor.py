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

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from gbc.app.config.project import get_current_project
from gbc.app.utils.json_model_operator import load_model_from_json, save_model_to_json


# ---- 落盘位置 --------------------------------------------------------------
# executor 配置是**每台机器都不同**的可变状态(解释器路径、项目路径),因此:
#   - 落在**目标项目**的 `.gbc/` 下(而非工具仓),让工具仓保持只读、可 pip 安装;
#   - 私有真配置 `executors.json` 应进 gitignore;
#   - 可提交的清单 `executors.example.json` 脱敏(只留名字 + 结构骨架),供协作者
#     知道"本项目需要配哪些 executor",而绝不泄露任何机器相关值或密钥。
EXECUTORS_FILENAME = "executors.json"
EXECUTORS_EXAMPLE_FILENAME = "executors.example.json"


def executors_config_path() -> Path:
    """当前目标项目的私有 executor 配置路径。随 `get_current_project()` 走。"""
    return get_current_project() / ".gbc" / EXECUTORS_FILENAME


def executors_example_path() -> Path:
    """当前目标项目的脱敏 executor 清单路径(可提交进 git)。"""
    return get_current_project() / ".gbc" / EXECUTORS_EXAMPLE_FILENAME


class EnvAction(BaseModel):
    # key: 环境变量名
    key: str
    # action: 支持 set (覆盖), append (后补), prepend (前缀), remove (删除)
    action: Literal["set", "append", "prepend", "remove"]
    # value: 操作的值 (remove 时可为 None)
    value: str | None = None


# 单个执行器
class ExecutorModel(BaseModel):
    command: list[str]
    cwd: str
    timeout: int = -1
    env_ops: None | list[EnvAction] = None
    # 人类可读说明:example 清单里唯一保留的"内容",由登记方**显式撰写**,
    # 用来告诉协作者这个 executor 是什么、该怎么填。绝不从 command 自动推导(可能含密钥)。
    comment: str | None = None


# 执行器配置
class ExecutorsConfig(BaseModel):
    executors: dict[str, ExecutorModel]


# ---- 惰性单例 --------------------------------------------------------------
# 关键:**不在 import 时读盘**。import 时项目根往往还没经 argv/set_current_project
# 设定好(MCP server 场景),此刻读盘只会命中错误位置。改为首次访问时按当前项目定位。
_cache: ExecutorsConfig | None = None
_cache_path: Path | None = None


def _load(path: Path) -> ExecutorsConfig:
    try:
        return load_model_from_json(path, ExecutorsConfig)
    except FileNotFoundError:
        return ExecutorsConfig(executors={})
    except (ValueError, ValidationError):
        return ExecutorsConfig(executors={})


def get_executors_config() -> ExecutorsConfig:
    """惰性获取当前项目的 executor 配置单例。

    随目标项目变化自动重载:当 `get_current_project()` 指向的项目变了(缓存路径
    与当前路径不一致),重新按新路径加载——保证一个进程内切换项目时不串配置。
    """
    global _cache, _cache_path
    path = executors_config_path()
    if _cache is None or _cache_path != path:
        _cache = _load(path)
        _cache_path = path
    return _cache


def _to_example(config: ExecutorsConfig) -> dict:
    """把真配置脱敏成可提交的清单。

    约定(已拍板):**全删机器相关字段**——只留 executor 名字(作 key)与显式
    `comment`。command/cwd/timeout/env_ops 一律**不出现**(不是置空、而是缺失),
    因为无注释的空占位 ≈ 字段缺失,那就选更简单的「缺失」;缺失不静默——
    Pydantic 必填校验与 `gbc doctor` 会替它嗊出「你需要配 X」。绝不拷任何原始值。
    """
    executors: dict[str, dict] = {}
    for name, model in config.executors.items():
        entry: dict = {}
        if model.comment is not None:
            entry["comment"] = model.comment
        executors[name] = entry
    return {"executors": executors}


def save_executors_config() -> None:
    """保存当前项目的 executor 配置,并同步重算脱敏清单 example。

    二者始终一起写,避免 example 腐烂。example 是宽松 dict(非 ExecutorModel),
    因为它故意缺字段。
    """
    import json

    config = get_executors_config()
    save_model_to_json(config, executors_config_path(), num_backups=0)

    example_path = executors_example_path()
    example_path.parent.mkdir(parents=True, exist_ok=True)
    example_path.write_text(
        json.dumps(_to_example(config), ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
