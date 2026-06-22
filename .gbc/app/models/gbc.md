# models —— 数据契约

所有层共享的 pydantic 模型。**模型即契约**:无业务逻辑、无 IO。改一个字段就是改契约,下游(core /
interface / 落盘的 `.gbc` json)全靠它,要慎重。

## meta.py

`.gbc` 元数据模型,是整套系统的形状:
- `Guarantee` — 具名行为保证,**身份是 id(≠ test 路径)**;含 desc/test/executor/timeout_override/
  heavy/`dependents`(多对一的消费者清单)。
- `Dependency` — consumer 的一条依赖边,`symbol = "<provider 文件>:<符号>"`;`guarantees: []` = 免费
  symbol 依赖,非空 = 行为级。
- `FileMeta` — 单文件双段:`provides`(作 provider)+ `depends_on`(作 consumer)。
被 core.guarantee 读写、被 base 落盘。纯 pydantic,无内部依赖。

## verify.py

验证结果模型:
- `VerifyModel` — 单个测试跑完的原始结果(core.executor 产出)。
- `SkippedGuarantee` / `VerifySummary` — 三桶汇总(passed/failed/skipped)+ `green` 门禁判定
  (二元:green = 无 failed,skipped 不染红)。core.guarantee 汇总产出。

## errors.py

异常层级,`GBCError` 为根,按域分(Config/Executor/Guarantee/IllegalOperation…)。关键语义错误:
`GuaranteeTestFailedError`(出生即绿门禁不过)、`GuaranteeHasDependentsError`(退休保护拦截)。
表面层(cli/mcp)按类型分流渲染/包装。
