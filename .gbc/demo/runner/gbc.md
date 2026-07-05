# 意图
Runner 执行引擎 + 可视化。cli.py（Typer 入口，list/run 命令）、engine.py（ScenarioRunner：读 JSON → 搭 workspace → 逐步执行）、tools.py（模拟 LLM 工具：say 气泡 / edit 带 unified diff / gbc CLI 调用）、display.py（Rich 渲染）。

# 文件

## engine.py
ScenarioRunner：读 JSON 剧本 → 清空并搭建 workspace（复制项目源码 + 合并 scenario 测试/.gbc + 生成 executors.json）→ 按 delay 间隔逐步执行 say/edit/gbc。

## tools.py
模拟 LLM 工具实现：tool_say（Rich 气泡）、tool_edit（oldText→newText 精确替换 + unified diff 渲染）、tool_gbc（subprocess 调 GBC CLI，env 设 GBC_PROJECT_PATH 指向 workspace）。

## display.py
Rich 可视化：say_bubble（LLM 聊天气泡）、render_diff（彩色 unified diff 面板）、render_gbc_start/result（命令执行状态）、title/divider/summary。
