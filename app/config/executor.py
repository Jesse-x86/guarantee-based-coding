from pydantic import BaseModel, ValidationError

from app.config.base import CONFIG_DIR
from app.utils.json_model_operator import load_model_from_json, save_model_to_json

# 路径
EXECUTORS_CONFIG_PATH = CONFIG_DIR / "executors.json"

# 单个执行器
class Executor(BaseModel):
    core_file: str
    command: list[str]
    cwd: str
    env_add: None | dict[str, list[str] | str] = None
    env_remove: None | dict[str, list[str] | str] = None

# 执行器配置
class ExecutorsConfig(BaseModel):
    executors: dict[str, Executor]

# 初始化单例
def _init_executors_config() -> ExecutorsConfig:
    try:
        # 尝试加载已有文件
        return load_model_from_json(EXECUTORS_CONFIG_PATH, ExecutorsConfig)
    except FileNotFoundError as e:
        # 无文件
        return ExecutorsConfig(executors={})
    except ValueError or ValidationError as e:
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