# 意图
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/doc/setup/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。

# 内部约束
- 表面零业务逻辑：cli/mcp/editor 只做「参数收集 → 调 base → 渲染结果/错误」，不碰模型、不写文件。
- base 是唯一 IO/编排点：路径解析、meta 加载/保存、跨文件双向写、全局扫描都在这里；core 之下不碰磁盘。
- 依赖登记是跨两文件的双向写，由 base 兜底。
- gbc mcp up 是唯一常驻进程之一(另一是 gbc editor up)；其余子命令单次执行、跑完即退，两种生命周期不混。
- 面向用户文本经 i18n 层(t/load_text)，语言判定 --lang > GBC_LANG > locale > en。
- gbc rules 输出 stdout 纯文本，是推荐围栏而非强制沙箱，措辞须讲清强制靠用户 agent 框架。
- gbc setup 与 gbc rules 同构：输出 stdout 纯文本的本地化接线指南，只给坐标(MCP 端点/skill 文件位置/如何验证跑通)，具体怎么接入取决于用户 agent，不代为决定。
- MCP 表面暴露两个子系统的能力：保证引擎(guarantee/dep/verify/refactor/tree/consistency/executor) + 意图文档(doc show/check/set-*/sync/migrate)。意图写入类工具「改前须人类确认」的强制力由用户 agent 的 hook/rules 承担，不靠「藏起通道」——MCP 与 CLI 对称，隔离写入通道不产生额外安全。

# 文件

## mcp.py
MCP 工具面(FastMCP)：把两个子系统的能力暴露成 agent 可调用工具——保证引擎(guarantee/dep/verify/refactor/tree/consistency/executor) + 意图文档(doc show/check/set-*/sync/migrate)。所有工具只调 base(interface.base 或 intent.base)、返回 JSON 字符串，出错统一 {error}。run_server 以 stdio 启动，项目根经显式参数传入。

## cli.py
Typer 命令面,镜像 base 能力(guarantee/dep/verify/doctor/executor/refactor/tree 子命令),rich 渲染。仅依赖 interface.base 与 models.errors。

## base.py
IO/编排层：路径解析(_resolve/_to_rel，相对当前项目根)、meta 文件加载/保存(meta_session/dual_session)、保证 CRUD 与依赖登记的落盘包装、refactor 三件套(refactor_file/refactor_func/rename_guarantee，重定位文件/改符号名/改保证 id 并全图重写引用)、全局反查与一致性检查(who_depends_on/check_consistency)、全树渲染(render_tree)。core 之下不碰磁盘，这里是唯一 IO/编排点。
