# 意图
让代码即使在不被完全理解的情况下也能被安全修改。把模块间的依赖从隐含变成**显式、可执行、可验证的保证**：修改后机械跑测试，正确性从"AI 觉得改对了"变成"所有被依赖的保证仍通过"的布尔判定。本仓既是这套方法的实现，也是它的第一个使用者（自己管理自己的 `.gbc`）。

**不可破的本体不变量（改任何层都要守）**：保证是一等公民、身份是具名 id（如 config.llm.get_model.returns_loaded，≠测试路径）；多对一——一条保证可被多个消费者共享，dependents 是消费者文件清单，命中已有保证则追加 dependent 复用、不另写测试；双段自包含 meta——每个代码文件一份 .gbc json，provides（作 provider）+ depends_on（作 consumer），symbol 级依赖"免费"（guarantees: []、无测试无反向边），依赖行为而非签名时才升级具名保证；出生即绿——create/改动测试时当场跑、不过则拒绝登记，这是唯一完整性不变量、没有后门；退休保护——dependents 非空的保证拒绝删除；门禁二元——跑了的测试只有过/挂，没跑的（heavy 跳过）响亮报告但不染红，green = 无 failed；heavy 是成本秩 int + 自动运行授权（批量只跑 heavy ≤ 阈值，register/点名 verify 无视它）；零侵入 + 语言无关——元数据全在 .gbc，怎么跑测试抽象成 executor 配置。

**分层（自外向内，依赖只能向内）**：interface（cli/mcp 表面、base 编排/IO）→ core（纯逻辑 + 跑测试）→ models（数据契约）；config/utils 为横切支撑。外层可换形态（cli/mcp/未来 GUI），引擎不动。

# 文件

## demo/
⚠️ OBSOLETE — 本目录已废弃，不再维护。

原用途：GBC 的交互式演示套件（Runner + 剧本 + 演示项目源码），用于展示 GBC 三条核心机制（强测试门禁拦截 / 弱测试门禁失效 / 出生即绿）及集成前后工作方式对比。

废弃原因：表现形式不佳，且当前无维护计划。文件保留供参考，但不应作为使用入口；新用户请直接读 docs/ 下的文档。

下属子目录（runner / scenarios / projects）随本目录一并废弃。

## gbc/
GBC 可分发 Python 包，pip 安装后提供 gbc。entry.py 是纯分发器，组合保证引擎、架构意图 intent、离线手册 doc 和服务入口。随包手册来自 docs/ 单一内容源，安装后独立于源码仓库；项目状态仍由目标项目 .gbc/ 持有。

## build_support.py
setuptools 构建扩展：将 docs/en 与 docs/zh 五个手册主题复制到 wheel 的 gbc/assets/docs；源分发保留手册及构建支持，可独立重建 wheel。
