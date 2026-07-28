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

"""
测试：get_config() 永不为 None —— 弱测试版。

本测试仅覆盖了正常路径（存在键），无法捕获「缺失键时返回 None」的回归问题。
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """验证 get_config 不返回 None。

    弱点：只测了一个 100% 存在的 key。
    当上游把 .get(key, "") 改成 .get(key)（missing key 返回 None），
    这个测试仍然通过——因为 port 在字典里。
    """
    loader = ConfigLoader({"port": "8080"})
    result = loader.get_config("port")
    assert result is not None
