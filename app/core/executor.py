import subprocess

from app.config.executor import executors_config, ExecutorModel, save_executors_config
from app.core.env import apply_env_actions, get_clean_python_path
from app.models.errors import ExecutorNotFoundError
from app.models.verify import VerifyModel

FILE_PLACEHOLDERS = ["{file}", "{f}"]
DEFAULT_TIMEOUT = 15

def has_exec_config(config: str) -> bool:
    """
    是否存在该 config
    :param config:
    :return:
    """
    return config in executors_config.executors

def _execute(config: str, file: str, timeout: int = -1) -> subprocess.CompletedProcess[str]:
    """
    使用特定配置文件，执行单个测试
    :param config:
    :param file:
    :param timeout:
    :return:
    """
    if not has_exec_config(config):
        raise ExecutorNotFoundError(config)

    executor_cfg = executors_config.executors[config]

    args = executor_cfg.command.copy()
    args = [arg.replace("{file}", file).replace("{f}", file) for arg in args]

    env = apply_env_actions(get_clean_python_path(), executor_cfg.env_ops)

    if timeout < 0:
        timeout = executor_cfg.timeout

    if timeout < 0:
        timeout = DEFAULT_TIMEOUT

    result = subprocess.run(
        args=args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=executor_cfg.cwd,
        env=env,
    )

    return result

def verify_single(config: str, file: str, *, timeout: int = -1, return_model: bool = True) -> bool | VerifyModel:
    """
    验证单个测试
    :param config:
    :param file:
    :param timeout:
    :param return_model:
    :return:
    """
    result = _execute(config, file, timeout)

    if not return_model:
        return result.returncode == 0

    return VerifyModel(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )

def upsert_exec_config(config_name: str, model: ExecutorModel):
    """
    插入或更新执行器配置
    :param config_name:
    :param model:
    :return:
    """
    executors_config.executors[config_name] = model
    save_executors_config()

def remove_exec_config(config_name: str):
    """
    删除执行器配置
    :param config_name:
    :return:
    """
    if has_exec_config(config_name):
        del executors_config.executors[config_name]
    save_executors_config()

def get_all_exec_configs():
    """
    获取全部执行器配置
    :return:
    """
    return executors_config.copy()