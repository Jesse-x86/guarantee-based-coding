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


class GBCError(Exception):
    """
    所有GBC异常的基类
    """

class ConfigError(GBCError):
    """
    所有配置文件相关的Error
    """

class ExecutorError(GBCError):
    """
    执行器模块的Error
    """

class GuaranteeError(GBCError):
    """
    和保证相关的Error
    """

class IllegalOperationError(GBCError):
    """
    非法操作，操作意图层面就是错误的
    """

# ======== Illegal Operation ========
class IllegalFilePathError(IllegalOperationError):
    """
    非法操作，操作意图层面就是错误的
    """
    def __init__(self, target_file):
        super().__init__(target_file)
        self.target_file = target_file

    def __str__(self):
        return f"Operation intended to '{self.target_file}' is illegal"

# ======== Config ========

class ConfigNotFoundError(ConfigError):
    def __init__(self, target_file):
        super().__init__(target_file)
        self.target_file = target_file

    def __str__(self):
        return f"Config file '{self.target_file}' not found"

class ConfigParseError(ConfigError):
    def __init__(self, target_file, failure_info):
        super().__init__(target_file)
        self.target_file = target_file
        self.failure_info = failure_info

    def __str__(self):
        return f"Config file '{self.target_file}' failed to parse: \n{self.failure_info}"

# ======== Project ========

class ProjectNotFoundError(GBCError):
    def __init__(self, target_project):
        super().__init__(target_project)
        self.target_project = target_project

    def __str__(self):
        return f"Project '{self.target_project}' not found"

# ======== Meta ========

class MetaNotFoundError(GBCError):
    def __init__(self, original_file, target_file):
        super().__init__(target_file)
        self.original_file = original_file
        self.target_file = target_file

    def __str__(self):
        return f"Meta file '{self.target_file}' for '{self.original_file}' not found"

# ======== Guarantee ========

class GuaranteeDuplicatedError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path

    def __str__(self):
        return f"Guarantee '{self.guarantee_path}' already exists for '{self.target_file}'. If you're intended to update guarantee info, use 'update' instead of 'register'"

class GuaranteeNotFoundError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path

    def __str__(self):
        return f"Guarantee '{self.guarantee_path}' not found for '{self.target_file}'"

class GuaranteeTestFailedError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str, failure_info: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path
        self.failure_info = failure_info

    def __str__(self):
        return f"Guarantee '{self.guarantee_path}' failed for '{self.target_file}', failure info: \n {self.failure_info}"

class GuaranteeHasDependentsError(GuaranteeError):
    """退休保护：拒绝删除仍有 dependents 的保证。

    系统不替使用者「反射式」删掉一条还有人依赖的保证——那必然悄悄弄坏下游。
    必须先沿依赖线把 dependents 修复/迁移掉，dependents 清空后才允许退休。
    """
    def __init__(self, provider: str, guarantee_id: str, dependents: list[str]):
        super().__init__(guarantee_id)
        self.provider = provider
        self.guarantee_id = guarantee_id
        self.dependents = dependents

    def __str__(self):
        return (
            f"Guarantee '{self.guarantee_id}' on '{self.provider}' still has "
            f"{len(self.dependents)} dependent(s): {self.dependents}. "
            f"Repair or migrate them first; a guarantee can only be retired once its dependents are empty."
        )

# ======== Executor ========

class ExecutorNotFoundError(ExecutorError):
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def __str__(self):
        return f"Executor config '{self.config}' not found"


class ExecutorConfigInvalidError(ExecutorError):
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def __str__(self):
        return f"Parameters received for executor config '{self.config}' invalid"