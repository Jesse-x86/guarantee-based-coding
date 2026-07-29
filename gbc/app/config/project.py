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

from gbc.app.config.base import PROJECT_ROOT

# 初始化当前路径
def _init_current_project() -> Path:
    var = os.environ.get("GBC_PROJECT_PATH", None)
    if var:
        var = Path(var)
        if var.exists():
            return var

    return PROJECT_ROOT / "workspace"

# 会被使用的当前路径变量
CURRENT_PROJECT = _init_current_project()

# 更新当前路径
def set_current_project(new_path: str):
    new_path = Path(new_path)

    global CURRENT_PROJECT
    CURRENT_PROJECT = new_path

def get_current_project():
    return CURRENT_PROJECT