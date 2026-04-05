import subprocess

from app.config.executor import executors_config, Executor, save_executors_config
from app.core.env import apply_env_actions, CLEAN_ENV
from app.models.errors import ExecutorNotFoundError
from app.models.verify import VerifyModel

FILE_PLACEHOLDERS = ["{file}", "{f}"]
DEFAULT_TIMEOUT = 15

def has_executor(config: str) -> bool:
    return config in executors_config.executors

def execute(config: str, file: str, timeout: int = -1) -> subprocess.CompletedProcess[str]:
    if not has_executor(config):
        raise ExecutorNotFoundError(config)

    executor_cfg = executors_config.executors[config]

    args = executor_cfg.command.copy()
    indexes = []
    for index, arg in enumerate(args):
        if arg in FILE_PLACEHOLDERS:
            indexes.append(index)
    for index in indexes:
        args[index] = file

    env = apply_env_actions(CLEAN_ENV.copy(), executor_cfg.env_ops)

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
    result = execute(config, file, timeout)

    if not return_model:
        return result.returncode == 0

    return VerifyModel(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )

def upsert_executor(config_name: str, model: Executor):
    executors_config.executors[config_name] = model
    save_executors_config()