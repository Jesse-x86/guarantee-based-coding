"""测试：get_config() 永不为 None —— 弱测试版。

本测试只能测 productive path（get_config("port") 有值），
无法捕获 "missing key 分支返回 None" 的回归。
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
