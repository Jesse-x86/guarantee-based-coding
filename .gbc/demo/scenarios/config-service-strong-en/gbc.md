# 意图
强测试 scenario 英文版（与中文版逻辑一致，文案英文）。同时覆盖 productive path 和 edge path（get_config("nonexistent")），能捕获 missing key 返回 None 的回归。演示 GBC 成功拦截，验证「门禁能守住测试覆盖到的边界」。引用 config-service-en 项目。
