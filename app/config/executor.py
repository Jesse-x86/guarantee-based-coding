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

from typing import Literal

from pydantic import BaseModel, ValidationError

from app.config.base import CONFIG_DIR
from app.utils.json_model_operator import load_model_from_json, save_model_to_json

# 路径
EXECUTORS_CONFIG_PATH = CONFIG_DIR / "executors.json"

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

# 执行器配置
class ExecutorsConfig(BaseModel):
    executors: dict[str, ExecutorModel]

# 初始化单例
def _init_executors_config() -> ExecutorsConfig:
    try:
        # 尝试加载已有文件
        return load_model_from_json(EXECUTORS_CONFIG_PATH, ExecutorsConfig)
    except FileNotFoundError as e:
        # 无文件
        return ExecutorsConfig(executors={})
    except (ValueError, ValidationError) as e:
        # 解析错误
        return ExecutorsConfig(executors={})

# 配置单例
executors_config = _init_executors_config()

# 保存执行器配置
def save_executors_config() -> None:
    """
    保存 Executors 配置
    :return:
    """
    global executors_config
    save_model_to_json(executors_config, EXECUTORS_CONFIG_PATH, num_backups = 0)