# GBC 手册:手动安装 + 在 GBC 下工作

**English version: [manual_EN.md](./manual_EN.md)**

> **这是 GBC 的手册 / 详细参考。** 如果你想要**自动**配置，可以让你的 Agent 按照 [for-agents.md](./for-agents.md)
> 安装并运行 `setup-gbc` skill——它会通过交互方式替你完成下面的第 1 至 5 步。本文档提供了**手动安装**(§1–5)
> 以及**集成 GBC 后如何安全工作**(§6–8)的完整参考。
>
> 全文采用面向 Agent 的口吻编写——人类也可以阅读，或将其交给信任的 Agent。内容基于“推荐/标准”场景编写；
> 请根据实际的权限划分，灵活调整由 Agent 处理或留给人类决策的部分。

GBC 将“这次改动是否会破坏其他模块”从主观猜测转变为机械可验证的事实：依赖关系被显式登记为**保证**，
每条保证由一个窄测试（Narrow Test）负责。做出改动后运行验证：全绿则代表安全，任一飘红则会给出
关于受影响方的精确报告。

---

## 1. 安装

GBC 跑在**它自己的** Python 环境里(和你当前在做的项目分开)。从 GBC 仓库里:

```bash
pip install -r requirements.txt   # typer[all] / pydantic / mcp
```

> 正常情形下,安装环境最好交给人类;装好之后,继续。

## 2. 接上 MCP(你的保证侧工具)

在**你正在做的项目的根目录**放一个 `.mcp.json`:

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/abs/path/to/python",
      "args": ["/abs/path/to/guarantee-based-coding/serve.py", "/abs/path/to/your-project"]
    }
  }
}
```

- `command` = 你在第 1 步装依赖用的那个解释器。
- `args[0]` = `serve.py` 的绝对路径;`args[1]` = **工作项目根的绝对路径**(必须作为 argv 传,不能靠环境变量)。
- 重启 agent 后,工具会以 `mcp__gbc__*` 出现。
- 从 WSL 调用 Windows Python 有跨平台坑(路径 / 编码);`serve.py` 已经处理好了——细节见
  [integrate-mcp.md](./integrate-mcp.md)。

## 3. 定义 executor(测试怎么跑)

在创建任何保证之前,先告诉 GBC 用什么命令跑测试。调用 `upsert_executor`:

```jsonc
// config_name: "pytest"
// config_data:
{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],  // {file} 会被替换成测试 selector
  "cwd": "/abs/path/to/your-project",
  "timeout": 30,
  "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your-project"}]
}
```

要切换语言,只需换掉 `command`(例如 `["npx","jest","{file}"]`)。`env_ops` 的 action:
`set` / `append` / `prepend` / `remove`。

## 4. 把意图 CLI 封装成一个 skill(你改意图的唯一入口)

每个文件夹的意图存在 `.gbc/<path>/gbc.md` 里,分三个小节:**`# 意图`(Intent)**(它是什么、为什么),
**`# 内部约束`(Internal constraints)**(义务与规则:它需要什么、必须或必须不做什么),以及
**`# 文件`(Files)**(子文件夹和文件各一行)。它的结构,以及父子文档之间的一致性,由一个程序维护——所以
**永远经 GBC 自己的意图 CLI(`gbc_doc.py`)编辑;不要手编 gbc.md**,这样约束工具才能替你守护它们。三个小节
里各放什么、以及 spec-first 的细节,都在 [intent-editor-and-skills.md](./intent-editor-and-skills.md) 里。
下面把那个 CLI 封装成一个薄 skill:

**wrapper**(钉死解释器 + 项目根,其余透传):

```bash
#!/usr/bin/env bash
exec /abs/path/to/python \
  /abs/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root /abs/path/to/your-project "$@"
```

**SKILL.md**(好让你知道何时用它):

```markdown
---
name: gbc-doc
description: The only compliant entry for reading/writing .gbc intent docs (gbc.md). Use this skill to view/create/change/lint gbc.md — NEVER hand-edit gbc.md.
---
Invoke: `bash /abs/path/to/gbc-doc.sh <command> [args...]`
Commands: show / set-intent / set-constraints / set-file / rm-entry / check / sync / migrate
(command surface in §6; for architecture work a human can also run `python gbc_doc.py`'s web editor — see intent-editor-and-skills.md)
```

**用 `[[project-relative-path]]` 引用代码。** 当 gbc.md 散文指向一个代码文件或符号时,写成
`[[app/core/models/game.py]]` 或 `[[app/core/models/game.py:GameSpec]]`——一个从仓库根出发、包在
`[[ ]]` 里的路径。不要用 `../` 相对路径:相对引用在任一侧移动时就会失效,而且从每个引用者看去读起来都不一样;
而 `[[ ]]` 引用是每个目标一个规范字符串,当目标移动时 `refactor_file` / `refactor_func` 工具会自动重写它。
(数据目录、HTTP 路由和 ADR 链接不需要 `[[ ]]`。)

## 5. 冒烟测试:确认接上了

调用一两个只读工具:

- `check_consistency()` → 当 `.gbc` 图一致时返回 `[]`(空项目也是 `[]`)。
- `list_provides("<某个源文件的相对路径>")` → 返回登记在该文件上的保证(没有则 `{}`)。

> 路径参数永远是**项目根相对**的 posix 路径(`app/core/maker/maker.py`),不是绝对路径。如果连不上,
> 回去重新检查第 2 步。

---

## 6. 工具速查

**保证侧(gbc MCP,`mcp__gbc__*`):**

| 工具 | 作用 |
|------|--------------|
| `add_dependency(provider, consumer, symbol[, guarantee_id])` | 登记一条依赖。传 `guarantee_id` = 行为依赖(自动写反向边);省略它 = 免费符号依赖 |
| `create_guarantee(provider, id, desc, test, executor[, heavy, disabled])` | 新建一条具名保证。**出生即绿:创建时跑测试,失败则拒绝。** 传 `disabled` 可以创建为挂起状态 |
| `update_guarantee` / `retire_guarantee` | 修改 / 退休。退休一条仍有依赖方的保证会被**拒绝** |
| `refactor_file(old, new)` | 移动一个文件 / 目录 + 它的 `.gbc` 元数据;在全图重写每一处路径引用(依赖边、反向 `dependents`、以及 gbc.md 里的 `[[ ]]` 散文引用);自动禁用被移动文件的保证。幂等——能对已移动的文件做对账。 |
| `refactor_func(provider, old_symbol, new_symbol)` | 重命名一个符号:重写消费者的依赖符号 + 它下面的保证 id + `[[path:symbol]]` 散文引用;自动禁用。源码里的符号由你自己改名。 |
| `rename_guarantee(provider, old_id, new_id)` | 重命名一个保证 id,双向(提供者键 + 每个消费者)。 |
| `disable_guarantee(provider, id)` / `enable_guarantee(provider, id)` | 挂起 / 恢复一条保证的出生即绿,同时保留它的 id 和边。`enable` 会重跑出生即绿,若仍失败则拒绝。被禁用的保证在 `check_consistency` 里仍然吵闹(`disabled_guarantee` / `depends_on_disabled`)。 |
| `verify_guarantee(provider, id)` / `verify_provider(provider)` | 跑一条 / 跑一个文件的全部保证(门禁) |
| `who_depends_on(provider[, symbol, guarantee_id])` | 反查谁依赖我(取代 grep) |
| `list_provides(provider)` / `list_depends_on(consumer)` | 看我提供的保证 / 我声明的依赖 |
| `check_consistency()` | 全图 lint:悬空引用、双向边漂移 |

**意图侧(gbc-doc skill → `gbc_doc.py`):**

| 命令 | 作用 |
|---------|--------------|
| `show <folder>` | 查看一个文件夹的意图 / 约束 / 条目 |
| `set-intent <folder> "<text>"` | 设置意图,自动单一事实源投影到父条目 |
| `set-constraints <folder> "<text>"` / `set-file <folder> <name> "<desc>"` | 设置内部约束 / 新增或修改一个文件条目 |
| `rm-entry <folder> <name>` | 移除一个文档条目(不删磁盘上的文件) |
| `check` / `sync` | 一致性 lint / 确定性修复父子漂移 |

`<folder>` 用项目根相对路径;根用 `""` 或 `.`。

---

## 7. 在 GBC 下工作:工作流

**角色默认（顶层 Agent）。** 本手册以及 `setup-gbc` 注入项目的作业准则都默认
**你是顶层 Agent**：推荐流程为：规划 → 对齐意图 → 派发任务（每个任务简报需包含裁剪后的 `gbc.md`
**意图与内部约束**、**可写的单一目标文件**，其余路径设为**只读**）→ 任务执行方自证 → **你**通过 GBC
工具进行最终验收（默认使用 MCP 接口——禁止直接调用底层测试命令）。小范围改动允许规划与实现一体化；
但日常编码并非顶层 Agent 的默认职责。集成 GBC 的项目会在指令文件中包含完整的工作流说明。

**两层契约。** ① **架构意图**(gbc.md)：项目架构的唯一事实源（Single Source of Truth），作为最高契约**由人类持有并审批**；Agent 负责起草。
② **行为保证**：一个模块当前提供且已被下游依赖的**具名行为承诺**；你可以演进它，但如果产生破坏性变更，则必须确保所有依赖方已同步修复。

**使用 `[[项目相对路径]]` 引用代码。** 当 `gbc.md` 的内容指向具体的代码文件或符号时，请书写为
`[[app/core/models/game.py]]` 或 `[[app/core/models/game.py:GameSpec]]` —— 即从仓库根目录出发、并包裹在
`[[ ]]` 中的路径。**禁止使用 `../` 等相对路径**：相对引用会在文件移动时失效，且在不同引用者视角下的描述不一；
而 `[[ ]]` 引用是目标的规范全局标识，当目标移动或更名时，`refactor_file` / `refactor_func` 工具会自动重写这些引用。
（注：数据目录、HTTP 路由和 ADR 链接无需使用 `[[ ]]`。）保证 ID 遵循类似原则但不包含路径：
格式为 `<symbol>.<behavior>`（例如 `make_game.returns_html`），确保在提供方内部唯一。

**每次变更分为两个相位，且顺序至关重要——在厘清架构前切勿直接编写代码：**

1. **架构相位（草案先行；默认规则要求人类显式批准后落库）。** 当收到新需求时，将涉及的**所有**
   `gbc.md` 增量内容作为**草案**与人类核对；仅在获得**显式批准**后，方可通过 `gbc-doc` 工具落库并运行 `check`
   确保一致性。**已落库的 `gbc.md` 即为您实现的规范 (Spec)。** 默认安装会将“意图需确认”写入作业准则。
   如果人类主动删除了该确认规则，您可以获得更高的自动化权限，但随之而来的是更高的静默架构漂移风险。
   只要规则依然存在，请勿尝试略过该流程。
2. **实现相位（机器门控）。** 推荐采用“一个子任务对应一个目标文件”的模式（在简报中指明可写文件，其余**只读**）。
   遵循依赖拓扑顺序（先处理被依赖项）。任务执行方：
   - 阅读已批准的范围（简报 / gbc.md）及接口定义 -> 编写实现。
   - 对于依赖的行为或新暴露的行为：签名级变更使用 `add_dependency`；具体行为则**主动编写窄测试并通过
     `create_guarantee` 登记保证**。未登记的行为依赖视为未完成任务。
   - **局部自证**：仅通过 GBC 工具运行 `verify_provider` 或 `verify_guarantee`（禁止直接运行 `pytest`）。
   - 实现过程中若发现架构意图有误 -> 立即停止，返回架构相位；严禁私自产生架构漂移。
3. **最终验收（顶层 Agent）。** 任务执行方提交后，顶层 Agent 需再次通过 GBC 工具验证受影响的保证。
   即使执行方自称全绿，也不得跳过此步骤。

**关于窄测试 (Narrow Test) 的准则：** 断言**行为承诺**，而非**内部实现**。示例：使用 `assert r is not None` 而非具体的硬编码值；
使用 `with pytest.raises(X)` 而非校验具体的错误消息。**坚持“非窄不写”**——偶尔的漏报是可以接受的，但在重构时由于测试写得太死而导致的误报，会迅速侵蚀团队对验证系统的信任。

---

## 8. 几个容易踩的坑

先知道这些能替你省掉一些弯路:

| 容易踩的坑 | 改成这样做 |
|---|---|
| 手编 `.gbc/**` 下的 `gbc.md` 或 `*.json` | gbc.md 经 gbc-doc skill;依赖 / 保证经 gbc MCP |
| 想清楚架构后就直接跳去写代码 | 先起草 gbc.md → 人类批准(默认)→ 再拓扑实现;仅当人类要求从 instruction 删掉确认句时才不再强制确认 |
| subagent「顺手」改半棵树 | brief 写明可写目标文件;其余只读 |
| subagent 说全绿就跳过顶层 verify | subagent 自证;顶层仍做最终验收 |
| 确认规则还在却不经人类看就落 gbc.md | 先显式批准;或人类已主动删掉确认规则 |
| 测试断言一个具体的返回值(`== "<html>..."`) | 断言承诺:非空 / 类型 / 抛异常 |
| 给每条依赖都命名一个保证 | 默认用免费符号依赖;**只**升级行为依赖,而且懒升级 |
| 退休一条仍有依赖方的保证 | 先迁移 / 修好依赖方(`retire` 会拒绝) |
| 用绝对路径调用工具 | 永远用项目根相对的 posix 路径 |
| 一次改一大堆文件 | 拓扑序,每步一个文件,每步跑保证 |
| 移动文件或重命名符号后手工修引用 | 用 `refactor_file` / `refactor_func`——它们一次性重写 json 图_和_ gbc.md 里的 `[[ ]]` 散文引用(而且 `refactor_file` 幂等) |

---

更深入的安装(跨平台、自定义客户端)见 [integrate-mcp.md](./integrate-mcp.md);意图编辑器和 skill 示例见
[intent-editor-and-skills.md](./intent-editor-and-skills.md)。
