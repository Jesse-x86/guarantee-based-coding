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

"""Server entry: starts from ConfigLoader's behavioral promises."""

from config_loader import ConfigLoader

loader = ConfigLoader({"port": "8080", "host": "0.0.0.0"})


def start_server() -> int:
    """Start the server from config and return the port.

    Trusts loader.get_config() never to be None —
    if get_config ever started returning None, int(None) would raise TypeError.
    """
    port_str = loader.get_config("port")
    # Downstream consumes it directly, trusting it is always str
    return int(port_str)


def get_timeout() -> int:
    """Read a timeout setting.

    Deliberately uses a likely-missing key ("timeout") to show missing-key
    behavior: the original impl returns "", and int("") would raise ValueError;
    without a default it returns None, and int(None) raises TypeError.
    """
    val = loader.get_config("timeout")
    return int(val) if val else 30  # "" → fall back to 30
