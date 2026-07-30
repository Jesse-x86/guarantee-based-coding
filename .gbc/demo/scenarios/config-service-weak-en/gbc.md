# 意图
弱测试 scenario 英文版（与中文版逻辑一致，文案英文）。只测 productive path（get_config("port")），无法捕获 missing key 分支返回 None 的回归。演示 GBC 拦不住的情况，强调「测试的强度 = 安全网的强度」。引用 config-service-en 项目。
