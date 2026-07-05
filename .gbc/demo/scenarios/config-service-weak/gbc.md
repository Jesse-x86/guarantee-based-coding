# 意图
弱测试 scenario：只测 productive path（get_config("port")），无法捕获 missing key 分支返回 None 的回归。演示 GBC 拦不住的情况，强调「测试的强度 = 安全网的强度」。

# 文件

## scenario.json
弱测试剧本 JSON。project: config-service。步骤：create_guarantee → add_dependency → verify（绿） → edit（去掉 .get() 默认值） → verify（仍绿！弱测试只测了 productive path）。

## tests/
弱测试版 test_never_none.py：只有一个 assert get_config("port") is not None，只测了 productive path（key 存在），未测 missing key 分支。
