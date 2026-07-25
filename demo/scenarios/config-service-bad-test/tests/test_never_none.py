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
