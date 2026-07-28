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

"""Tests: get_config() never returns None — deliberately wrong test.

The productive path (port) is correct, but the edge path asserts the wrong
value: get_config("nonexistent") actually returns "", the test expects "default".
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """get_config does not return None — but the second assert is wrong.

    Productive path is fine: port exists, returns "8080", not None.
    Edge path asserts the wrong value — expects "default", actual is "".
    """
    loader = ConfigLoader({"port": "8080"})

    # correct: present key is not None
    assert loader.get_config("port") is not None

    # wrong! get_config("nonexistent") returns "", not "default"
    assert loader.get_config("nonexistent") == "default"
