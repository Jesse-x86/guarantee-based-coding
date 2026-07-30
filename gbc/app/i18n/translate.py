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

"""翻译取值:短消息 t() + 长文本 load_text()。

短消息 catalog 从 `catalog/<lang>.json` 按需加载(带缓存);长文本从
`texts/<name>.<lang>.md` 整篇读出。两者都在缺当前语言时回退 DEFAULT_LANG。
放文件即加语言,无需改代码。
"""
import json

from gbc.app.assets import I18N_CATALOG_DIR as _CATALOG_DIR, I18N_TEXTS_DIR as _TEXTS_DIR
from gbc.app.i18n.lang import DEFAULT_LANG, current_lang

# 每语言 catalog 缓存:lang -> {key: str}
_catalog_cache: dict[str, dict[str, str]] = {}


def _load_catalog(lang: str) -> dict[str, str]:
    if lang not in _catalog_cache:
        path = _CATALOG_DIR / f"{lang}.json"
        if path.exists():
            try:
                _catalog_cache[lang] = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                _catalog_cache[lang] = {}
        else:
            _catalog_cache[lang] = {}
    return _catalog_cache[lang]


def t(key: str, *, lang: str | None = None, **kw) -> str:
    """取短消息:按 key 查当前语言 catalog,缺失回退 DEFAULT_LANG,再缺回退 key 本身。

    串内 {name} 占位用 **kw 填充;填充缺参时不炸,原样保留。
    """
    use = lang or current_lang()
    text = _load_catalog(use).get(key)
    if text is None and use != DEFAULT_LANG:
        text = _load_catalog(DEFAULT_LANG).get(key)
    if text is None:
        return key
    if kw:
        try:
            return text.format(**kw)
        except (KeyError, IndexError):
            return text
    return text


def load_text(name: str, *, lang: str | None = None) -> str:
    """整篇读出长文本资源(rules / init 引导等)。

    找 <name>.<当前语言>.md;缺则回退 <name>.<DEFAULT_LANG>.md;再缺抛 FileNotFoundError。
    """
    use = lang or current_lang()
    candidate = _TEXTS_DIR / f"{name}.{use}.md"
    if not candidate.exists():
        candidate = _TEXTS_DIR / f"{name}.{DEFAULT_LANG}.md"
    if not candidate.exists():
        raise FileNotFoundError(
            f"i18n long-text resource not found: {name} (lang={use}, dir={_TEXTS_DIR})"
        )
    return candidate.read_text(encoding="utf-8")


def catalog_keys(lang: str | None = None) -> set[str]:
    """某语言 catalog 的全部键(测试/校验漏译用)。默认 DEFAULT_LANG。"""
    return set(_load_catalog(lang or DEFAULT_LANG).keys())
