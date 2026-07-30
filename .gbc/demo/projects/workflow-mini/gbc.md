# 意图
演示「工作方式」变化的精简项目。两模块：llm_client/（LLM 调用空桩）+ config/（配置读取）。.gbc/ 已预置架构意图——llm_client 禁止配置 IO、config 禁止调用 LLM。被 workflow-before-after scenario 引用。源码不含测试。
