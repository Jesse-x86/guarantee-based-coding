# 意图
⚠️ OBSOLETE — 本目录已废弃，不再维护。

原用途：GBC 的交互式演示套件（Runner + 剧本 + 演示项目源码），用于展示 GBC 三条核心机制（强测试门禁拦截 / 弱测试门禁失效 / 出生即绿）及集成前后工作方式对比。

废弃原因：表现形式不佳，且当前无维护计划。文件保留供参考，但不应作为使用入口；新用户请直接读 docs/ 下的文档。

下属子目录（runner / scenarios / projects）随本目录一并废弃。

# 文件

## runner/
Runner 执行引擎 + 可视化。cli.py（Typer 入口，list/run 命令）、engine.py（ScenarioRunner：读 JSON → 搭 workspace → 逐步执行）、tools.py（模拟 LLM 工具：say 气泡 / edit 带 unified diff / gbc CLI 调用）、display.py（Rich 渲染）。

## scenarios/
演示剧本目录。每个子目录是一个 scenario：含 scenario.json（剧本定义，引用 project 字段指定用了哪个项目）、tests/（该场景专用的测试文件）、.gbc/（该场景预置的 GBC 元数据，初始通常为空）。

三类剧本 × 中英双语：
- config-service-weak / -en：弱测试，只测 productive path，演示门禁拦不住。
- config-service-strong / -en：强测试，覆盖 productive + edge，演示门禁成功拦截。
- config-service-bad-test / -en：错误测试，演示出生即绿拒绝登记。
- workflow-before-after / -en：工作方式演示剧本（引用 workflow-mini 项目），纯 say/show，对比集成 GBC 前后 Agent 思考与流程的变化。

一个项目可对应多个 scenario（源码相同但测试/剧本不同）。

## projects/
演示用项目源码（只读，无测试）。每个子目录是一个可独立运行的项目，被多个 scenario 共享。当前两类项目：
- config-service / -en：ConfigLoader provider（get_config() 承诺永不为 None）+ server.py consumer（int(port) 信任该承诺）。
- workflow-mini：演示「工作方式」变化的精简项目，llm_client/（LLM 调用）+ config/（配置读取），.gbc/ 已预置架构意图。

## requirements.txt
Demo Runner 独立依赖（rich + typer）。不依赖 GBC 主库——Runner 通过 MCP server 与 GBC 通信，主库环境变化不影响 Runner。

## run_demo.py
一键入口脚本：无参数弹出交互菜单，支持 list 和 run <name> 子命令。自行处理 sys.path，不需要用户设环境变量。纯 Python，全平台通用。

## EXAMPLE.md
交互式演示教程：给 agent 的指令，让它带着用户在 workspace 里逐步演示 GBC 的三条核心机制——强测试门禁拦截（RED）、弱测试门禁失效（GREEN）、出生即绿拒绝错误测试。每个步骤要求 agent 暂停解释，不等用户确认不继续。配合 demo/projects/ 和 demo/scenarios/ 的素材使用。

## EXAMPLE_EN.md
EXAMPLE.md 的英文版：交互式演示教程，给 agent 的指令，带用户逐步演示 GBC 的三条核心机制。

## workspace
Runner 运行时搭建的临时 workspace（复制 project 源码 + 合并 scenario 测试/.gbc + 生成 executors.json）。已被 .gitignore 忽略，不纳入意图管理。
