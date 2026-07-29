# 意图
让代码即使在不被完全理解的情况下也能被安全修改。把模块间的依赖从隐含变成**显式、可执行、可验证的保证**：修改后机械跑测试，正确性从"AI 觉得改对了"变成"所有被依赖的保证仍通过"的布尔判定。本仓既是这套方法的实现，也是它的第一个使用者（自己管理自己的 `.gbc`）。

**不可破的本体不变量（改任何层都要守）**：保证是一等公民、身份是具名 id（如 config.llm.get_model.returns_loaded，≠测试路径）；多对一——一条保证可被多个消费者共享，dependents 是消费者文件清单，命中已有保证则追加 dependent 复用、不另写测试；双段自包含 meta——每个代码文件一份 .gbc json，provides（作 provider）+ depends_on（作 consumer），symbol 级依赖"免费"（guarantees: []、无测试无反向边），依赖行为而非签名时才升级具名保证；出生即绿——create/改动测试时当场跑、不过则拒绝登记，这是唯一完整性不变量、没有后门；退休保护——dependents 非空的保证拒绝删除；门禁二元——跑了的测试只有过/挂，没跑的（heavy 跳过）响亮报告但不染红，green = 无 failed；heavy 是成本秩 int + 自动运行授权（批量只跑 heavy ≤ 阈值，register/点名 verify 无视它）；零侵入 + 语言无关——元数据全在 .gbc，怎么跑测试抽象成 executor 配置。

**分层（自外向内，依赖只能向内）**：interface（cli/mcp 表面、base 编排/IO）→ core（纯逻辑 + 跑测试）→ models（数据契约）；config/utils 为横切支撑。外层可换形态（cli/mcp/未来 GUI），引擎不动。

# 文件

## app/
实现本体的全部代码。分层自外向内、**依赖只能向内**:`interface`(表面 + 编排/IO)→ `core`
(纯逻辑 + 跑测试)→ `models`(数据契约);`config` 与 `utils` 为横切支撑,被各层使用但不反向依赖业务层。
每个子文件夹有自己的 `gbc.md` 说明意图与内部约束。

## demo/

## gbc/
GBC 工具本体的可分发 Python 包(pip install 后经 [project.scripts] 暴露 gbc 命令)。entry.py 是唯一入口纯分发器，把 app/ 下两个子系统(保证引擎 interface + 意图文档 intent)的表面组合成命令树。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。
