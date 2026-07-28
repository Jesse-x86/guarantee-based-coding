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

"""Config loader: key-value reads that promise never to return None."""


class ConfigLoader:
    """Read config entries from an internal dict.

    Guarantee: get_config(key) always returns str, never None.
    Missing keys yield the empty string "" rather than None.
    """

    def __init__(self, defaults: dict[str, str] | None = None):
        self._config: dict[str, str] = dict(defaults or {})

    def get_config(self, key: str) -> str:
        """Return a config value.

        :param key: config key
        :return: value as str; "" when the key is missing
        """
        # Critical line: the "" default is what keeps "never None" true
        return self._config.get(key, "")
