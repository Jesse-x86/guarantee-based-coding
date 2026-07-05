# 意图

# 文件

## runner/
Runner 执行引擎 + 可视化。cli.py（Typer 入口，list/run 命令）、engine.py（ScenarioRunner：读 JSON → 搭 workspace → 逐步执行）、tools.py（模拟 LLM 工具：say 气泡 / edit 带 unified diff / gbc CLI 调用）、display.py（Rich 渲染）。

## scenarios/
演示剧本目录。每个子目录是一个 scenario：含 scenario.json（剧本定义，引用 project 字段指定用了哪个项目）、tests/（该场景专用的测试文件）、.gbc/（该场景预置的 GBC 元数据，初始通常为空）。一个项目可对应多个 scenario（如 weak/strong 两个版本，源码相同但测试不同）。

## projects/
演示用项目源码（只读，无测试）。每个子目录是一个可独立运行的项目，被多个 scenario 共享。当前仅 config-service：ConfigLoader provider（get_config() 承诺永不为 None） + server.py consumer（int(port) 信任该承诺）。

## requirements.txt
Demo Runner 独立依赖（rich + typer）。不依赖 GBC 主库——Runner 通过 MCP server 与 GBC 通信，主库环境变化不影响 Runner。

## run_demo.py
一键入口脚本：无参数弹出交互菜单，支持 list 和 run <name> 子命令。自行处理 sys.path，不需要用户设环境变量。纯 Python，全平台通用。
