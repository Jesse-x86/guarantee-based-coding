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

# 初始化备份数量
def _init_meta_backups() -> int:
    var = os.environ.get("GBC_META_BACKUPS", None)
    if var and var.isdigit():
        return int(var)

    return 0

META_BACKUPS = _init_meta_backups()