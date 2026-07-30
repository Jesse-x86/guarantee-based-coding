# 意图
演示用项目源码（只读，无测试）。每个子目录是一个可独立运行的项目，被多个 scenario 共享。当前两类项目：
- config-service / -en：ConfigLoader provider（get_config() 承诺永不为 None）+ server.py consumer（int(port) 信任该承诺）。
- workflow-mini：演示「工作方式」变化的精简项目，llm_client/（LLM 调用）+ config/（配置读取），.gbc/ 已预置架构意图。

# 文件

## config-service/
config-service 演示项目：ConfigLoader provider（get_config() 承诺永不为 None——找不到 key 返回 ""） + server.py consumer（int(port) 信任该承诺）。源码不含测试——测试由各 scenario 各自提供。

## config-service-en/
config-service 演示项目的英文版（源码逻辑与中文版一致，注释/文档英文）。ConfigLoader provider（get_config() 承诺永不为 None——找不到 key 返回 ""）+ server.py consumer（int(port) 信任该承诺）。源码不含测试——测试由各 scenario 各自提供。被英文版 scenario 引用。

## workflow-mini/
演示「工作方式」变化的精简项目。两模块：llm_client/（LLM 调用空桩）+ config/（配置读取）。.gbc/ 已预置架构意图——llm_client 禁止配置 IO、config 禁止调用 LLM。被 workflow-before-after scenario 引用。源码不含测试。
