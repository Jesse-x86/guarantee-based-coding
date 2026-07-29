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

"""GBC 面向用户输出的多语言层。

对外提供三件事:
- `resolve_lang(...)`  语言判定:显式 lang > GBC_LANG > 系统 locale > 默认 en。
- `t(key, **kw)`       短消息查表(catalog),按当前语言取串并做 str.format 填充。
- `load_text(name)`    长文本(rules / init 引导)按当前语言整篇读出 Markdown 资源。

设计取舍:短消息用**轻量 dict catalog**(见 catalog.py)而非 gettext——无编译步骤、
随包走、透明易测;若将来规模变大可平滑迁移。
"""
from gbc.app.i18n.lang import (
    DEFAULT_LANG,
    supported_langs,
    resolve_lang,
    set_lang,
    current_lang,
)
from gbc.app.i18n.translate import t, load_text, catalog_keys

__all__ = [
    "DEFAULT_LANG",
    "supported_langs",
    "resolve_lang",
    "set_lang",
    "current_lang",
    "t",
    "load_text",
    "catalog_keys",
]
