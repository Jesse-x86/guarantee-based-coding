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

"""静态资源定位的单一入口。

所有随包分发的**数据**（i18n catalog/texts、editor 前端）集中在 `gbc/assets/`
下，与**代码**彻底分离。任何模块要读资源都从这里取路径，不各自
`Path(__file__).parent` ——加一类资源只需在此登记一处 + 打包声明一条。

打包：`pyproject.toml` 的 `[tool.setuptools.package-data]` 以 `"gbc" = ["assets/**"]`
把整个 assets 树纳入 wheel（散在各子包时易漏声明，这正是集中的理由）。
"""
from pathlib import Path

# assets 根：本文件在 gbc/app/assets.py，上溯到 gbc/ 再进 assets/。
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# i18n 短消息查表 与 长文本资源。
I18N_CATALOG_DIR = ASSETS_DIR / "i18n" / "catalog"
I18N_TEXTS_DIR = ASSETS_DIR / "i18n" / "texts"

# 意图编辑器 web 前端静态页。
EDITOR_FRONTEND_DIR = ASSETS_DIR / "editor"

# 给 CLI-only agent 的预组 skills（教 agent 怎么调 gbc 子命令，等价于 MCP 工具描述）。
# gbc setup 只告知此目录坐标，由用户自行放到其 agent 读 skill 的位置。
SKILLS_DIR = ASSETS_DIR / "skills"
