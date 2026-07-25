"""服务器入口：依赖 ConfigLoader 的行为承诺来启动服务。"""

from config_loader import ConfigLoader

loader = ConfigLoader({"port": "8080", "host": "0.0.0.0"})


def start_server() -> int:
    """根据配置启动服务器，返回分配的端口号。

    内部信任 loader.get_config() 永不为 None——
    如果 get_config 某天开始返回 None，int(None) 会抛出 TypeError。
    """
    port_str = loader.get_config("port")
    # 下游直接消费，信任它一定是 str
    return int(port_str)


def get_timeout() -> int:
    """获取超时配置。

    这里故意用一个 likely missing 的 key ("timeout")，
    来演示「找不到 key 时的行为」——原始实现返回 ""，
    int("") 抛 ValueError；但如果没有默认值返回 None，
    则是 int(None) 抛 TypeError。
    """
    val = loader.get_config("timeout")
    return int(val) if val else 30  # "" → 用默认 30
