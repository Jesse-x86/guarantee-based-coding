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

"""配置加载器：提供 key-value 配置读取，承诺永不为 None。"""


class ConfigLoader:
    """从内部字典读取配置项。

    保证：get_config(key) 永远返回 str，绝不返回 None。
    找不到 key 时返回空字符串 ""（而非 None）。
    """

    def __init__(self, defaults: dict[str, str] | None = None):
        self._config: dict[str, str] = dict(defaults or {})

    def get_config(self, key: str) -> str:
        """获取配置值。

        :param key: 配置键名
        :return:     配置值（str）；key 不存在时返回 ""
        """
        # 关键行：.get() 的第二个参数 "" 保证「永不为 None」
        return self._config.get(key, "")
