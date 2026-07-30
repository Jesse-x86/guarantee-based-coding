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

import subprocess

from gbc.app.config.executor import get_executors_config, ExecutorModel, save_executors_config
from gbc.app.core.env import apply_env_actions, get_clean_python_path
from gbc.app.models.errors import ExecutorNotFoundError
from gbc.app.models.verify import VerifyModel

FILE_PLACEHOLDERS = ["{file}", "{f}"]
DEFAULT_TIMEOUT = 15

def has_exec_config(config: str) -> bool:
    """
    是否存在该 config
    :param config:
    :return:
    """
    return config in get_executors_config().executors

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

    executor_cfg = get_executors_config().executors[config]

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
        # 绝不让被测进程继承父进程的 stdin。作为 MCP server 运行时父进程 stdin 是
        # JSON-RPC 协议管道，子进程继承后会阻塞（"终端能跑、当服务挂"的经典坑）。
        stdin=subprocess.DEVNULL,
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
    get_executors_config().executors[config_name] = model
    save_executors_config()

def remove_exec_config(config_name: str):
    """
    删除执行器配置
    :param config_name:
    :return:
    """
    if has_exec_config(config_name):
        del get_executors_config().executors[config_name]
    save_executors_config()

def get_all_exec_configs():
    """
    获取全部执行器配置
    :return:
    """
    return get_executors_config().copy()