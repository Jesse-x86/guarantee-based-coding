# 意图
弱测试版 test_never_none.py：只有一个 assert get_config("port") is not None，只测了 productive path（key 存在），未测 missing key 分支。
