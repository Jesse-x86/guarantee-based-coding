# 意图
强测试 scenario：同时覆盖 productive path 和 edge path（get_config("nonexistent")），能捕获 missing key 返回 None 的回归。演示 GBC 成功拦截，验证「门禁能守住测试覆盖到的边界」。

# 文件

## tests/
强测试版 test_never_none.py：同时断言 get_config("port") 和 get_config("nonexistent") 都不为 None，覆盖 productive + edge 两条路径。

## scenario.json
强测试剧本 JSON。project: config-service。步骤同 weak 但测试不同——强测试的两条断言使得 edit 后的 verify 亮红，GBC 门禁成功拦截 None 回归。
