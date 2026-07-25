"""Tests: get_config() never returns None — strong version.

Covers both the productive path and the missing-key edge path, so it can
catch a regression where the missing-key branch starts returning None.
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """get_config must not return None in any case.

    Critical: assert both an existing key and a missing key.
    If upstream changes .get(key, "") to .get(key), the second assertion
    catches it: get_config("nonexistent") returns None → test fails.
    """
    loader = ConfigLoader({"port": "8080"})

    # productive path: present key must not be None
    assert loader.get_config("port") is not None

    # edge path: missing key must not be None either (original impl returns "")
    assert loader.get_config("nonexistent") is not None
