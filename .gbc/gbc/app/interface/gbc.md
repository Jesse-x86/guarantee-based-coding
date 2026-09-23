# 意图
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/intent/doc/setup/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。
gbc intent 管理目标项目的架构意图，gbc doc 查询随版本分发的 GBC 手册；旧意图 doc 命令与 doc_* MCP 工具不保留兼容别名。手册查询 CLI/MCP 复用 documentation.base。

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
- gbc setup 输出面向 AI 的本地化接入指南，指导 AI 检查环境、为当前项目持久配置 MCP 并验证；无 MCP 时提供 CLI 接入方式。命令本身只输出 stdout 纯文本指南，不执行安装。
- MCP 表面暴露保证引擎与意图文档能力；意图写入的人类确认闸门由用户 agent 框架承担。
- CLI 验证失败（verify single/provider）或 doctor check 发现一致性错误时，进程必须返回非零退出码；成功返回 0，仅有 heavy 跳过或停用提示时保持原有非失败语义。
- tree 提供目录浏览、仅目录视图和按目标文件组织的修改上下文；CLI 使用 tree show [目录]、tree folders [目录]、tree for <文件...>，裸 gbc tree 仅显示帮助、不读取项目树；完整树经 tree show 查看，旧组级 --detail/--gaps 拒绝并提示迁移到 tree show；子命令支持后置 --project/-C。
- 浏览目录为项目相对路径，所选目录深度为 0；达到深度边界时保留折叠标记。folders 仅显示目录意图与内部约束，父子投影不重复展示，子文档缺失时使用父目录条目描述。
- tree for 合并目标文件条目、祖先意图和内部约束、直接依赖的符号和具名保证，以及目标提供的保证和消费者；包含测试引用及停用状态，去重并保留目标关联，缺失登记明确提示。不递归展开依赖、不执行测试、不读取 AGENTS.md。
- tree 的 CLI 与 MCP 表面复用 base 层选择与渲染能力，新增用户文本经 i18n；MCP tree 与 base.render_tree 的无参数调用保持兼容；CLI 裸 tree 仅显示帮助。

# 文件

## mcp.py
MCP 薄表面：保证引擎、intent_* 架构意图操作、doc_list/doc_read/doc_search 手册查询，复用各子系统 base，统一错误返回；文档结果纯文本，结构化结果 JSON。旧意图 doc_* 名移除。tree/tree_for 复用 interface.base。stdio 启动并显式绑定项目根。

## cli.py
Typer 命令面，镜像 base 能力并经 rich/i18n 渲染。所有项目操作叶子命令接受后置 --project/-C 并在调用 base 前显式设置目标根；不做 argv 重排。根 --lang 仍是单次覆盖入口。tree 命令组提供 show/folders/for，裸 tree 仅显示帮助；--detail/--gaps 移至 show，旧组级用法明确提示迁移；只收集参数并调用 base。

## base.py
IO/编排层：路径解析、meta 加载/保存、保证 CRUD、依赖双向写、全局反查/一致性与树渲染。正常依赖删除维护双边；consumer meta 已不存在时，只有明确 guarantee_id 且 provider 反向边确实包含该 consumer 才可 provider-only 摘除，并且不得新建空 consumer meta。check_consistency 在目标根没有 .gbc 时失败，杜绝空图假绿。统一选择并渲染目录树、仅目录视图及目标文件修改上下文，维护深度边界、意图去重、直接契约范围和缺失提示。
