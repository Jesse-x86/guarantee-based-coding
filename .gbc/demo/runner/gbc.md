# 意图
Runner 执行引擎 + 可视化。cli.py（Typer 入口，list/run 命令）、engine.py（ScenarioRunner：读 JSON → 搭 workspace → 逐步执行）、tools.py（模拟 LLM 工具：say 气泡 / edit 带 unified diff / gbc CLI 调用）、display.py（Rich 渲染）。

# 文件

## engine.py
ScenarioRunner：读 JSON 剧本 → 清空并搭建 workspace（复制项目源码 + 合并 scenario 测试/.gbc + 生成 executors.json）→ 按 delay 间隔逐步执行 say/edit/gbc。

## tools.py
模拟 LLM 工具实现（通过 MCP）：tool_say（Rich 气泡）、tool_edit（oldText→newText 精确替换 + unified diff）、tool_gbc（通过 McpClient 调 GBC MCP server，解析 verify_provider 的 GREEN/RED 状态）。

## display.py
Rich 可视化：say_bubble（LLM 聊天气泡）、render_diff（彩色 unified diff 面板）、render_gbc_start/result（命令执行状态）、title/divider/summary。

## mcp_client.py
最小 MCP JSON-RPC stdio 客户端：启动 serve.py 子进程，通过 stdin/stdout 行分隔 JSON 与 GBC MCP server 通信。纯 stdlib，零外部依赖。这是 Runner 与 GBC 主库的唯一边界——主库从 Python 迁 TS 时只换 serve.py 启动命令即可。
