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

"""语言判定 + **从文件自动发现受支持语言**。

关键设计:受支持语言不硬编码,而是扫描资源文件推导——放一个 `catalog/ja.json`
(以及可选的 `texts/*.ja.md`)就自动支持日语,无需改代码。

判定优先级(高→低):显式 lang 参数 > 环境变量 GBC_LANG > 系统 locale > 默认 en。
"""
import locale
import os
from pathlib import Path

DEFAULT_LANG = "en"

_I18N_DIR = Path(__file__).resolve().parent
_CATALOG_DIR = _I18N_DIR / "catalog"

# 进程内当前语言(命令入口解析一次后 set_lang 固定;库函数读 current_lang)。
_current: str = DEFAULT_LANG


def supported_langs() -> tuple[str, ...]:
    """扫描 catalog 目录,把每个 `<lang>.json` 的文件名主干当作一门受支持语言。

    永远包含 DEFAULT_LANG(en 必须存在,作为兜底)。结果排序稳定,en 置首。
    """
    langs: set[str] = {DEFAULT_LANG}
    if _CATALOG_DIR.is_dir():
        for f in _CATALOG_DIR.glob("*.json"):
            langs.add(f.stem)
    ordered = [DEFAULT_LANG] + sorted(langs - {DEFAULT_LANG})
    return tuple(ordered)


def normalize(raw: str | None) -> str | None:
    """把形如 zh_CN.UTF-8 / zh-Hans / EN 的原始值归一到受支持码;不支持则 None。"""
    if not raw:
        return None
    low = raw.strip().lower().replace("_", "-")
    primary = low.split("-", 1)[0].split(".", 1)[0]
    if primary in supported_langs():
        return primary
    return None


def resolve_lang(explicit: str | None = None) -> str:
    """按优先级判定语言,永远返回一个受支持码(兜底 DEFAULT_LANG)。

    显式 explicit > 环境变量 GBC_LANG > 系统 locale > DEFAULT_LANG。
    """
    for candidate in (explicit, os.environ.get("GBC_LANG")):
        norm = normalize(candidate)
        if norm:
            return norm

    try:
        sys_lang, _ = locale.getlocale()
    except (ValueError, TypeError):
        sys_lang = None
    if not sys_lang:
        sys_lang = os.environ.get("LANG") or os.environ.get("LC_ALL")
    norm = normalize(sys_lang)
    if norm:
        return norm

    return DEFAULT_LANG


def set_lang(lang: str) -> str:
    """固定进程内当前语言(通常在命令入口解析后调用一次)。返回归一后的实际语言。"""
    global _current
    _current = normalize(lang) or DEFAULT_LANG
    return _current


def current_lang() -> str:
    """读取进程内当前语言。"""
    return _current
