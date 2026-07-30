# 意图
演示剧本目录。每个子目录是一个 scenario：含 scenario.json（剧本定义，引用 project 字段指定用了哪个项目）、tests/（该场景专用的测试文件）、.gbc/（该场景预置的 GBC 元数据，初始通常为空）。

三类剧本 × 中英双语：
- config-service-weak / -en：弱测试，只测 productive path，演示门禁拦不住。
- config-service-strong / -en：强测试，覆盖 productive + edge，演示门禁成功拦截。
- config-service-bad-test / -en：错误测试，演示出生即绿拒绝登记。
- workflow-before-after / -en：工作方式演示剧本（引用 workflow-mini 项目），纯 say/show，对比集成 GBC 前后 Agent 思考与流程的变化。

一个项目可对应多个 scenario（源码相同但测试/剧本不同）。

# 文件

## config-service-weak/
弱测试 scenario：只测 productive path（get_config("port")），无法捕获 missing key 分支返回 None 的回归。演示 GBC 拦不住的情况，强调「测试的强度 = 安全网的强度」。

## config-service-strong/
强测试 scenario：同时覆盖 productive path 和 edge path（get_config("nonexistent")），能捕获 missing key 返回 None 的回归。演示 GBC 成功拦截，验证「门禁能守住测试覆盖到的边界」。

## config-service-bad-test/

## config-service-weak-en/
弱测试 scenario 英文版（与中文版逻辑一致，文案英文）。只测 productive path（get_config("port")），无法捕获 missing key 分支返回 None 的回归。演示 GBC 拦不住的情况，强调「测试的强度 = 安全网的强度」。引用 config-service-en 项目。

## config-service-strong-en/
强测试 scenario 英文版（与中文版逻辑一致，文案英文）。同时覆盖 productive path 和 edge path（get_config("nonexistent")），能捕获 missing key 返回 None 的回归。演示 GBC 成功拦截，验证「门禁能守住测试覆盖到的边界」。引用 config-service-en 项目。

## config-service-bad-test-en/
错误测试 scenario 英文版（与中文版逻辑一致，文案英文）。故意写错的测试（assert get_config("nonexistent") == "default"，但实现返回 ""），出生即绿机制当场拒绝登记并返回完整 pytest 报错信息。引用 config-service-en 项目。

## workflow-before-after/
演示「集成 GBC 前后 Agent 工作方式变化」的剧本（中文）。纯 say/show 步骤，无真实代码修改——对比集成前 Agent 为省事直接在 llm_client 塞环境变量读取、集成后受 Instruction + gbc.md 意图边界约束走「顶层规划→派 subagent→最终验收」流程。展示的是思考与流程的变化，而非代码修改细节。引用 workflow-mini 项目。

## workflow-before-after-en/
workflow-before-after 剧本的英文版。纯 say/show 步骤，演示集成 GBC 前后 Agent 工作方式的变化。引用 workflow-mini 项目。
