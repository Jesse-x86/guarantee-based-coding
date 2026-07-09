# 意图
演示剧本目录。每个子目录是一个 scenario：含 scenario.json（剧本定义，引用 project 字段指定用了哪个项目）、tests/（该场景专用的测试文件）、.gbc/（该场景预置的 GBC 元数据，初始通常为空）。一个项目可对应多个 scenario（如 weak/strong 两个版本，源码相同但测试不同）。

# 文件

## config-service-weak/
弱测试 scenario：只测 productive path（get_config("port")），无法捕获 missing key 分支返回 None 的回归。演示 GBC 拦不住的情况，强调「测试的强度 = 安全网的强度」。

## config-service-strong/
强测试 scenario：同时覆盖 productive path 和 edge path（get_config("nonexistent")），能捕获 missing key 返回 None 的回归。演示 GBC 成功拦截，验证「门禁能守住测试覆盖到的边界」。

## config-service-bad-test/
