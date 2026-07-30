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


def _t(key: str, **kw) -> str:
    """惰性取本地化消息。在 __str__ 内部调用，避免 models 层模块级依赖 i18n，
    保持核心数据契约层干净。i18n 不可用时回退到 key。"""
    try:
        from gbc.app.i18n import t
        return t(key, **kw)
    except Exception:
        return key


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
class IntentDocError(IllegalOperationError):
    """意图文档(gbc.md)领域的非法操作。携带 i18n key + 参数，__str__ 时本地化。"""
    def __init__(self, msg_key: str, **params):
        super().__init__(msg_key)
        self.msg_key = msg_key
        self.params = params

    def __str__(self):
        return _t(self.msg_key, **self.params)


class IllegalFilePathError(IllegalOperationError):
    """
    非法操作，操作意图层面就是错误的
    """
    def __init__(self, target_file):
        super().__init__(target_file)
        self.target_file = target_file

    def __str__(self):
        return _t("exc.illegal_file_path", target=self.target_file)

# ======== Config ========

class ConfigNotFoundError(ConfigError):
    def __init__(self, target_file):
        super().__init__(target_file)
        self.target_file = target_file

    def __str__(self):
        return _t("exc.config_not_found", target=self.target_file)

class ConfigParseError(ConfigError):
    def __init__(self, target_file, failure_info):
        super().__init__(target_file)
        self.target_file = target_file
        self.failure_info = failure_info

    def __str__(self):
        return _t("exc.config_parse", target=self.target_file, info=self.failure_info)

# ======== Project ========

class ProjectNotFoundError(GBCError):
    def __init__(self, target_project):
        super().__init__(target_project)
        self.target_project = target_project

    def __str__(self):
        return _t("exc.project_not_found", target=self.target_project)

# ======== Meta ========

class MetaNotFoundError(GBCError):
    def __init__(self, original_file, target_file):
        super().__init__(target_file)
        self.original_file = original_file
        self.target_file = target_file

    def __str__(self):
        return _t("exc.meta_not_found", target=self.target_file, original=self.original_file)

# ======== Guarantee ========

class GuaranteeDuplicatedError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path

    def __str__(self):
        return _t("exc.guarantee_duplicated", gid=self.guarantee_path, target=self.target_file)

class GuaranteeNotFoundError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path

    def __str__(self):
        return _t("exc.guarantee_not_found", gid=self.guarantee_path, target=self.target_file)

class GuaranteeTestFailedError(GuaranteeError):
    def __init__(self, target_file: str, guarantee_path: str, failure_info: str):
        super().__init__(target_file)
        self.target_file = target_file
        self.guarantee_path = guarantee_path
        self.failure_info = failure_info

    def __str__(self):
        return _t("exc.guarantee_test_failed", gid=self.guarantee_path, target=self.target_file, info=self.failure_info)

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
        return _t("exc.guarantee_has_dependents", gid=self.guarantee_id,
                  provider=self.provider, count=len(self.dependents), dependents=self.dependents)

# ======== Executor ========

class ExecutorNotFoundError(ExecutorError):
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def __str__(self):
        return _t("exc.executor_not_found", name=self.config)


class ExecutorConfigInvalidError(ExecutorError):
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def __str__(self):
        return _t("exc.executor_config_invalid", name=self.config)