"""
测试：get_config() 永不为 None —— 强测试版。

本测试同时覆盖了正常路径（存在键）和边界路径（缺失键），
能够精准捕获「缺失键时返回 None」的回归问题。
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """验证 get_config 在任何情况下都不返回 None。

    关键：不仅测存在的 key，还要测不存在的 key。
    当上游把 .get(key, "") 改成 .get(key) 时，
    第二个断言会捕获：get_config("nonexistent") 返回 None → 测试失败。
    """
    loader = ConfigLoader({"port": "8080"})

    # productive path：存在的 key 必须不是 None
    assert loader.get_config("port") is not None

    # edge path：不存在的 key 也必须不是 None（原始实现返回 ""）
    assert loader.get_config("nonexistent") is not None
