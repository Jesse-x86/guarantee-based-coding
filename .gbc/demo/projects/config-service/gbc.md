# 意图
config-service 演示项目：ConfigLoader provider（get_config() 承诺永不为 None——找不到 key 返回 ""） + server.py consumer（int(port) 信任该承诺）。源码不含测试——测试由各 scenario 各自提供。

# 文件

## config_loader.py
ConfigLoader provider：dict.get(key, '') 保证永不为 None。演示的破坏性修改是将 .get(key, '') 改为 .get(key)（missing key 返回 None）。

## server.py
Consumer：int(loader.get_config('port')) 信任 get_config() 永不为 None。若上游违约返回 None，int(None) 会抛 TypeError。
