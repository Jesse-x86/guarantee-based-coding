# 意图
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/doc/init/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。

# 内部约束
- 表面零业务逻辑：cli/mcp/editor 只做「参数收集 → 调 base → 渲染结果/错误」，不碰模型、不写文件。
- base 是唯一 IO/编排点：路径解析、meta 加载/保存、跨文件双向写、全局扫描都在这里；core 之下不碰磁盘。
- 依赖登记是跨两文件的双向写，由 base 兜底。
- gbc mcp up 是唯一常驻进程之一(另一是 gbc editor up)；其余子命令单次执行、跑完即退，两种生命周期不混。
- 面向用户文本经 i18n 层(t/load_text)，语言判定 --lang > GBC_LANG > locale > en。
- gbc rules 输出 stdout 纯文本，是推荐围栏而非强制沙箱，措辞须讲清强制靠用户 agent 框架。
