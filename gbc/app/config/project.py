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

import os
from pathlib import Path


GBC_PROJECT_ROOT = "GBC_PROJECT_ROOT"


def _normalize_project_path(path: str | os.PathLike[str]) -> Path:
    """Return an absolute, normalized project path without requiring it to exist."""
    raw_path = os.fspath(path)
    if not raw_path.strip():
        raise ValueError("project path must not be blank")
    return Path(raw_path).expanduser().resolve(strict=False)


# 初始化当前路径：进程启动时固定按 GBC_PROJECT_ROOT > cwd 选择一次，不向上搜索。
def _init_current_project() -> Path:
    configured_root = os.environ.get(GBC_PROJECT_ROOT)
    if configured_root is not None and configured_root.strip():
        return _normalize_project_path(configured_root)
    return _normalize_project_path(Path.cwd())


CURRENT_PROJECT = _init_current_project()


def set_current_project(new_path: str | os.PathLike[str]) -> None:
    """Explicitly override the current project root."""
    global CURRENT_PROJECT
    CURRENT_PROJECT = _normalize_project_path(new_path)


def get_current_project() -> Path:
    return CURRENT_PROJECT
