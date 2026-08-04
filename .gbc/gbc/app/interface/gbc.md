# 意图
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/doc/setup/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。

# 内部约束
规则：
- 表面零业务逻辑：cli/mcp/editor 只做参数收集 → 调 base → 渲染结果/错误，不碰模型、不写文件。
- base 是唯一 IO/编排点：路径解析、meta 加载/保存、跨文件双向写、全局扫描都在这里；core 之下不碰磁盘。
- 依赖登记是跨两文件的双向写，由 base 兜底。
- 依赖删除的孤儿修复只能在 consumer meta 确实不存在、provider 保证确实存在且其 dependents 确实包含该 consumer、并且调用方明确给出 guarantee_id 时走 provider-only 清理；其余情况继续按正常双向边语义处理或拒绝，绝不猜测。
- 项目操作的 CLI 叶子命令用后置 --project/-C 显式覆盖 GBC_PROJECT_ROOT/cwd；不做全局参数位置重排。
- 读取全图的一致性体检在目标根缺少 .gbc 时必须失败，绝不把空图报告为 consistent；创建类操作仍可初始化新项目。
- gbc mcp up 是唯一常驻进程之一（另一是 gbc editor up）；其余子命令单次执行、跑完即退，两种生命周期不混。
- 面向用户文本经 i18n 层产出，语言判定遵循显式 > 环境 > 持久偏好 > locale > en。
- gbc rules/setup 的局部 --lang 只在明确给值时覆盖；不给时必须保留根 callback 已选语言。
- gbc rules 输出 stdout 纯文本，是推荐围栏而非强制沙箱，措辞须讲清强制靠用户 agent 框架。
- gbc setup 与 gbc rules 同构：输出 stdout 纯文本的本地化接线指南，只给坐标，具体接入取决于用户 agent。
- MCP 表面暴露保证引擎与意图文档能力；意图写入的人类确认闸门由用户 agent 框架承担。

# 文件

## mcp.py
MCP 工具面(FastMCP)：把两个子系统的能力暴露成 agent 可调用工具——保证引擎(guarantee/dep/verify/refactor/tree/consistency/executor) + 意图文档(doc show/check/set-*/sync/migrate)。所有工具只调 base(interface.base 或 intent.base)、返回 JSON 字符串，出错统一 {error}。run_server 以 stdio 启动，项目根经显式参数传入。

## cli.py
Typer 命令面，镜像 base 能力并经 rich/i18n 渲染。所有项目操作叶子命令接受后置 --project/-C 并在调用 base 前显式设置目标根；不做 argv 重排。根 --lang 仍是单次覆盖入口。

## base.py
IO/编排层：路径解析、meta 加载/保存、保证 CRUD、依赖双向写、全局反查/一致性与树渲染。正常依赖删除维护双边；consumer meta 已不存在时，只有明确 guarantee_id 且 provider 反向边确实包含该 consumer 才可 provider-only 摘除，并且不得新建空 consumer meta。check_consistency 在目标根没有 .gbc 时失败，杜绝空图假绿。
