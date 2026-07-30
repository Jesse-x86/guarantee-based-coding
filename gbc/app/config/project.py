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


# 初始化当前路径：进程启动时的 cwd。CLI 单次命令默认就用这个——“当前项目 = 跑命令时所在目录”，
# 无需环境变量，不会静默回退到包安装位置。常驻服务（mcp up / editor up）cwd 不可靠，
# 它们自己收显式参数覆盖，不依赖这个默认值。
def _init_current_project() -> Path:
    return Path.cwd()

# 会被使用的当前路径变量
CURRENT_PROJECT = _init_current_project()

# 更新当前路径
def set_current_project(new_path: str):
    new_path = Path(new_path)

    global CURRENT_PROJECT
    CURRENT_PROJECT = new_path

def get_current_project():
    return CURRENT_PROJECT