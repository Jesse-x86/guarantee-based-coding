# 意图
演示「集成 GBC 前后 Agent 工作方式变化」的剧本（中文）。纯 say/show 步骤，无真实代码修改——对比集成前 Agent 为省事直接在 llm_client 塞环境变量读取、集成后受 Instruction + gbc.md 意图边界约束走「顶层规划→派 subagent→最终验收」流程。展示的是思考与流程的变化，而非代码修改细节。引用 workflow-mini 项目。
