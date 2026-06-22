# core —— 引擎 + 测试执行

保证系统的核心逻辑与"怎么真的把测试跑起来"。**纯模型操作**:不解析路径、不读写 `.gbc` 文件
(那是 base 的活)。进出本层的文件路径一律是**项目相对字符串**。

## guarantee.py

保证系统引擎,直接读写 `FileMeta` 模型:
- `create_guarantee` / `update_guarantee` — 出生即绿门禁(改动测试时当场跑,不过则拒)。
- `retire_guarantee` — 退休保护:`dependents` 非空则抛 `GuaranteeHasDependentsError`。
- `add_dependency` / `remove_dependency` — 跨文件**双向写**:同收 consumer 与 provider 两个 meta,
  维护 `depends_on` ⇄ `dependents` 一致;免费 symbol 依赖只动 consumer。
- `verify_provider`(heavy 阈值 + 三桶汇总)/ `verify_guarantee`(点名永远跑,无视 heavy)。
依赖 models.meta/verify/errors、core.executor(跑测试)。

## executor.py

按 executor 配置跑单个测试:`{file}` 替换 → subprocess 执行 → 产出 `VerifyModel`;并提供 executor
配置的增删查。是"语言无关"的落地点。依赖 config.executor、core.env、models.verify/errors。

## env.py

给测试子进程构造环境变量:清理 PYTHONPATH、按 `EnvAction`(set/append/prepend/remove)改写。
依赖 config.executor 的 `EnvAction`。
