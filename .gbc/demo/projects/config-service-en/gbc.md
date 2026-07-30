# 意图
config-service 演示项目的英文版（源码逻辑与中文版一致，注释/文档英文）。ConfigLoader provider（get_config() 承诺永不为 None——找不到 key 返回 ""）+ server.py consumer（int(port) 信任该承诺）。源码不含测试——测试由各 scenario 各自提供。被英文版 scenario 引用。
