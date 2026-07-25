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
