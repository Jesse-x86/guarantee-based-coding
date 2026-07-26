"""
测试：get_config() 永不为 None —— 故意写错的测试。

本测试针对存在键的验证是正确的，但针对缺失键（第 19 行）的断言有误：
代码实际返回 ""，测试却期待 "default"。
这演示了 GBC 如何在初始登记阶段拦截错误的测试。
"""

from config_loader import ConfigLoader


def test_get_config_never_returns_none():
    """验证 get_config 不返回 None —— 但写错了！

    productive path 是对的：port 存在，返回 "8080"，不为 None。
    但 edge path 断言错误的值——期待 "default"，实际返回 ""。
    """
    loader = ConfigLoader({"port": "8080"})

    # ✅ 正确：存在的 key 不为 None
    assert loader.get_config("port") is not None

    # ❌ 错误！get_config("nonexistent") 返回 ""，不是 "default"
    assert loader.get_config("nonexistent") == "default"
