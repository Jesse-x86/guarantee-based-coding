# 意图
把引擎能力暴露成"人/agent 能用的形态",并把"外部形态"与"内部实现"彻底解耦:cli、mcp(未来可
能还有 GUI)都只是薄表面,真正的编排、路径解析、文件读写收在 `base` 一处。换表面不动引擎。

# 内部约束
- **表面零业务逻辑**：cli/mcp 只做"参数收集 → 调 base → 渲染结果/错误"，不碰模型、不写文件。
- **base 是唯一 IO/编排点**：路径解析（项目相对 POSIX）、meta 加载/保存、跨文件双向写、全局扫描都在这里；core 之下不碰磁盘。
- **依赖登记是跨两个文件的双向写**，由 base 兜底（consumer 的 depends_on ⇄ provider 的 dependents），调用方不必手工在两处读写。

# 文件

## base.py
编排/IO 层。意图:让 core 保持纯粹,把一切"脏活"(解析、加载、保存、扫描)挡在这里。
- 单文件 `meta_session` 与**双文件 `dual_session`**(依赖登记要同时改 consumer 与 provider)。
- `who_depends_on`:给 guarantee_id 走 O(1) 反向边;否则**全局扫描** `.gbc` 树——这是 symbol 级
  免费依赖唯一的反查途径(它们没有反向边)。
- `check_consistency`:全局体检,报告 `dangling_guarantee` / `missing_reverse` / `missing_forward`
  三类双向边漂移。
- 依赖 `core.guarantee`(纯操作)、`core.executor`(跑测试)、`config`(项目根/备份/executor)、
  `utils`(路径映射、json 读写)。

## cli.py
Typer 命令面,镜像 base 能力(guarantee / dep / verify / doctor / executor 子命令),rich 渲染。
仅依赖 `interface.base` 与 `models.errors`。

## mcp.py
FastMCP 工具面,与 cli 一一对应。所有工具返回 JSON 字符串,异常统一包成 `{"error": ...}`,
**绝不向 MCP 运行时抛异常,也绝不向 stdout 打非协议内容**(stdout 是 MCP 的协议通道)。
仅依赖 `interface.base` 与 `models.errors`。
