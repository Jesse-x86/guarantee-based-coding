# 意图
强测试版 test_never_none.py：同时断言 get_config("port") 和 get_config("nonexistent") 都不为 None，覆盖 productive + edge 两条路径。
