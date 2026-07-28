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

"""Tests: get_config() never returns None — weak version.

Only covers the productive path (get_config("port") has a value), so it
cannot catch a regression where the missing-key branch returns None.
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """get_config does not return None.

    Weakness: only asserts a key that is always present.
    If upstream changes .get(key, "") to .get(key) (missing key → None),
    this test still passes — because port is in the dict.
    """
    loader = ConfigLoader({"port": "8080"})
    result = loader.get_config("port")
    assert result is not None
