# 意图
演示用项目源码（只读，无测试）。每个子目录是一个可独立运行的项目，被多个 scenario 共享。当前仅 config-service：ConfigLoader provider（get_config() 承诺永不为 None） + server.py consumer（int(port) 信任该承诺）。

# 文件

## config-service/
config-service 演示项目：ConfigLoader provider（get_config() 承诺永不为 None——找不到 key 返回 ""） + server.py consumer（int(port) 信任该承诺）。源码不含测试——测试由各 scenario 各自提供。
