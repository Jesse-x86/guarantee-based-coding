import subprocess

from app.config.executor import executors_config
from app.core.env import apply_env_actions, CLEAN_ENV
from app.models.errors import ExecutorNotFoundError

FILE_PLACEHOLDERS = ["{file}", "{f}"]

def has_executor(config: str) -> bool:
    return config in executors_config.executors

def execute(config: str, file: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
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

    result = subprocess.run(
        args=args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=executor_cfg.cwd,
        env=env,
    )

    return result

