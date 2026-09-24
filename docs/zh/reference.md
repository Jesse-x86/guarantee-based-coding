# 参考手册

> 语言：**简体中文** | [English](../en/reference.md)

命令 / 工具速查、executor 配置、跨平台接入细节。上手见 [quick-start.md](./quick-start.md)，
工作流见 [workflow.md](./workflow.md)。

GBC 能力可经 **CLI**（`gbc ...`）和 **MCP 工具**调用。**gbc-cli** skill 负责 shell 命令
适配；**gbc-workflow** 指导意图、行为测试及术语 / 决策复用，适用于两种入口，详见
[workflow.md](./workflow.md)。下表以 CLI 为主，标注对应的 MCP 工具名。

若 `gbc` 不在 PATH 上，任何 `gbc` 都可换成 `python -m gbc.entry`。

---

## 顶层命令

| 命令 | 作用 |
|------|------|
| `gbc mcp up [项目根]` | 启动 stdio MCP server（常驻）。省略时依次使用 `GBC_PROJECT_ROOT`、当前工作目录。 |
| `gbc editor up` | 启动意图编辑器 web 服务（常驻，给人用）。`--port` / `--host` / `--root`。 |
| `gbc lang [zh\|en\|auto]` | 查看或设置用户级持久语言偏好；省略参数显示当前偏好与实际语言，`auto` 清除显式偏好并恢复自动选择。日常使用建议只设置一次。 |
| `gbc setup` | 打印本地化接线指南：怎么把 MCP / skills 接入你的 agent。末尾的 `--lang zh/en` 仅覆盖本次调用。 |
| `gbc rules` | 打印作者推荐的围栏规则集（推荐默认，非强制沙箱）。末尾的 `--lang zh/en` 仅覆盖本次调用。 |
| `gbc tree` | 显示浏览命令帮助并成功退出。 |
| `gbc tree show [目录]` | 省略目录时渲染整棵 `.gbc` 依赖树，否则浏览指定子树；支持 `--depth N`，`--detail` 展开保证详情，`--gaps` 附登记缺口。 |
| `gbc tree folders [目录]` | 仅显示目录意图与内部约束；支持 `--depth N`。子目录没有文档时回退到父文档条目，同一目录的父子投影去重。 |
| `gbc tree for <文件>...` | 合并多个目标文件的修改上下文：文件条目、全部祖先意图与约束、直接依赖符号与具名保证、目标提供的保证及其消费者。 |
| `gbc doctor check` | 全局一致性体检：悬空引用 + 双向边漂移 + 停用保证（响亮报出）。 |

日常使用先运行一次 `gbc lang zh` 或 `gbc lang en`；临时切换 `setup` / `rules` 或 `doc` 叶命令输出时可使用末尾的 `--lang`。

### 项目根

保证引擎的叶命令（`guarantee`、`dep`、`verify`、`refactor`、`tree`、`doctor`、`executor`）默认按
`GBC_PROJECT_ROOT` > 当前工作目录（cwd）选择项目根，不会向父目录搜索。可在具体叶命令末尾用
`--project <项目根>` 或 `-C <项目根>` 显式覆盖，例如 `gbc doctor check -C /path/to/project`。

### Tree 浏览与修改上下文

原先渲染全树的 CLI 调用改用 `gbc tree show`；组级 `gbc tree --detail` / `--gaps` 现在报错并提示迁移，应改用 `gbc tree show --detail` / `--gaps`。MCP 的 `tree` 工具无参数时仍返回依赖树。

目录和文件路径相对于项目根，越界路径会被拒绝。浏览时，所选目录为深度 0，
`--depth 1` 显示直接孩子；省略深度则不限制，并用折叠标记提示被深度限制隐藏的内容。

```sh
gbc tree show gbc --depth 1 --detail -C /path/to/project
gbc tree folders gbc --depth 2 -C /path/to/project
gbc tree for gbc/entry.py gbc/app/interface/cli.py -C /path/to/project
```

`tree for` 的目标必须是文件，不接受 `--depth`、`--detail`、`--gaps` 等浏览选项。
输出合并去重并保留与各目标的关联，包含保证的测试引用和停用状态；依赖只展开一层，
不读取源码、测试内容或 `AGENTS.md`，也不运行测试。

对应 MCP：`tree(detail=False, gaps=False, folder="", depth=None, folders_only=False)`
用于浏览（`folders_only=True` 对应 `tree folders`）；`tree_for(files=[...])` 用于修改上下文。

---

## 保证 — `gbc guarantee` / MCP

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc guarantee create <provider> <id> <test> <executor> <desc>` | `create_guarantee` | 新建具名保证。**正常启用创建须出生即绿**：当场跑测试，不过则拒绝。`--heavy N` / `--timeout S` / `--disabled`（跳过门禁建占位，仅用于破循环依赖）。 |
| `gbc guarantee update <provider> <id>` | `update_guarantee` | 改字段：`--desc` / `--test` / `--executor` / `--heavy` / `--timeout`。启用保证改测试 / executor 会重跑门禁；停用保证更新仍暂缓门禁，enable 时补跑。 |
| `gbc guarantee retire <provider> <id>` | `retire_guarantee` | 退休。仍有 dependents 则**拒绝**（退休保护）。 |
| `gbc guarantee disable <provider> <id>` | `disable_guarantee` | 停用：保留 id 与全部边，暂缓门禁 / 批量 verify。停用 ≠ 退休。 |
| `gbc guarantee enable <provider> <id>` | `enable_guarantee` | 恢复：当场补跑出生即绿，过了才转正，不过保持停用。 |
| `gbc guarantee list <provider>` | `list_provides` | 列出该 provider 的全部保证及 dependents。 |

**id 约定**：`<symbol>.<behavior>`（如 `get_config.never_none`），路径无关，provider 内唯一即可。

---

## 依赖 — `gbc dep` / MCP

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc dep add <consumer> <provider> <symbol>` | `add_dependency`（无 guarantee_id） | 免费符号依赖：依赖符号存在，无测试无反向边。 |
| `gbc dep add <consumer> <provider> <symbol> -g <id>` | `add_dependency`（带 guarantee_id） | 行为依赖：挂到已有保证，自动写反向边。多消费者可共享一条保证。 |
| `gbc dep remove <consumer> <provider> <symbol> [-g <id>]` | `remove_dependency` | 摘一条保证（`-g`）或撤整条 symbol 边（无 `-g`）。 |
| `gbc dep of <consumer>` | `list_depends_on` | 列出某文件声明的全部依赖边。 |
| `gbc dep who <provider> [-s <symbol>] [-g <id>]` | `who_depends_on` | 反查谁依赖 provider（取代手工 grep）。 |

---

## 验证 — `gbc verify` / MCP

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc verify provider <provider>` | `verify_provider` | 跑该 provider 的全部保证。heavy 超阈值的跳过并报告（不算失败）。`--max-heavy N`。**GREEN 当且仅当无 failed。** |
| `gbc verify single <provider> <id>` | `verify_guarantee` | 点名跑单条，无视 heavy 永远跑。`-v` 显示完整 stdout/stderr。 |

**门禁语义**：跑了的测试只有过 / 挂；跳过的（heavy）响亮报告但不染红。green = 无 failed。
这不代表验收完整：heavy 跳过、停用保证和零执行须明确列为未验证范围。开发期可在正确环境中
直接跑未登记测试；正常启用保证的正式创建及测试 / executor 更新仍须出生即绿。停用不是 TDD 步骤，
最终验收经 GBC，并审查契约与测试变更。

---

## 重构 — `gbc refactor` / MCP（别手工修图）

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc refactor file <old> <new>` | `refactor_file` | 移动文件 / 目录 + 其 `.gbc` 元数据，全图重写路径引用（依赖边、反向 dependents、gbc.md 里的 `[[ ]]`），自动停用被移动方的保证。id 不动（路径无关）。幂等。 |
| `gbc refactor func <provider> <old_symbol> <new_symbol>` | `refactor_func` | 符号改名：重写消费者 symbol 字段 + 该符号名下的保证 id + `[[path:symbol]]`，自动停用。源码 def / 调用处由你改。 |
| `gbc refactor rename-id <provider> <old_id> <new_id>` | `rename_guarantee` | 保证 id 改名，双向同步（提供方 + 每个消费者）。 |

重构后：修 import、搬测试并 `gbc guarantee update <p> <id> --test ...`、再逐个
`gbc guarantee enable`。

---

## 离线 GBC 手册 — `gbc doc` / MCP

手册随当前安装的 GBC 版本分发，任意工作目录下都可离线查询，无需目标项目，也不读取或修改
项目的 `.gbc`。`--help` 继续提供简短的命令用法。

| CLI | MCP 工具 | 返回内容 |
|-----|----------|----------|
| `gbc doc list [--lang en\|zh]` | `doc_list(lang=None)` | 所选语言、固定主题 ID 与标题。 |
| `gbc doc read <topic> [--lang en\|zh]` | `doc_read(topic, lang=None)` | 完整主题 Markdown。 |
| `gbc doc search "<query>" [--lang en\|zh] [--limit 20]` | `doc_search(query, lang=None, limit=20)` | 不区分大小写的字面子串匹配，含主题 ID、从 1 开始的行号和行文本。 |

固定主题为 `quick-start`、`concepts`、`workflow`、`reference`、`onboarding-agent`。
语言沿用 GBC 的偏好优先级，叶命令后的 `--lang` 只覆盖本次查询。搜索只查选定语言，
不解释正则表达式，默认最多返回 20 条，条数范围为 1–100；空查询、未知主题报错。
每条文本以匹配处为中心截取，最多 240 个字符，避免超长行淹没结果。
`truncated` 表示还有未返回的匹配，避免把截断结果当成完整结果。

MCP list 返回 `{language, topics: [{id, title}]}`；read 返回 Markdown 字符串；search 返回
`{language, query, matches: [{topic, line, text}], truncated}`。
`docs/en/` 与 `docs/zh/` 是内容单源，构建时将这十篇主题复制为包资源，源码中不维护第二份。

```sh
gbc doc list --lang zh
gbc doc read workflow --lang zh
gbc doc search "保证" --lang zh --limit 10
```

## 意图文档 — `gbc intent` / MCP

**0.3.0 不兼容迁移：**原来的意图 `gbc doc ...` 全部改为 `gbc intent ...`，八个旧 `doc_*`
MCP 工具改为 `intent_*`，不保留兼容别名。请同步脚本与 agent 指令；`doc` 现在用于查询 GBC 手册。

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc intent show <folder>` | `intent_show` | 查看文件夹的意图 / 约束 / 条目。根用 `""` 或 `.`。 |
| `gbc intent check` | `intent_check` | 全树一致性体检（DRIFT/ORPHAN 为错误，STUB 为提示）。 |
| `gbc intent set-intent <folder> "<text>"` | `intent_set_intent` | 设意图（自动单源投影到父条目）。 |
| `gbc intent set-constraints <folder> "<text>"` | `intent_set_constraints` | 设内部约束（只在本地）。 |
| `gbc intent set-file <folder> <name> "<desc>"` | `intent_set_file` | 新增 / 更新文件条目（name 不带 `/`）。 |
| `gbc intent rm-entry <folder> <name>` | `intent_rm_entry` | 删条目（不删盘上文件，留给 git 复核）。 |
| `gbc intent sync` | `intent_sync` | 确定性修复父子漂移。 |
| `gbc intent migrate` | `intent_migrate` | 把所有 gbc.md 升级到最新格式。 |

> `<text>` 以 `-` 开头时，在它前面加 `--`，避免被当成选项：
> `gbc intent set-intent app -- "- 以短横线开头的一行"`。

**写意图是在改人类持有的架构真理。** 是否需人类签字由你的框架规则 / hook 决定，不由工具设阻。
绝不手编 gbc.md。
推荐工作流中，已授权目标与职责内的普通实现、辅助文件拆分和文件条目维护无需重复架构审批；
改变用途、职责、兼容性、权限或重要约束才需相应授权。已有授权持续有效。

---

## Executor 配置

executor 定义「如何跑测试」，按名字存在目标项目里。

```bash
gbc executor upsert <name> --json '<JSON>'
# 或
gbc executor upsert <name> --file <path.json>
```

配置结构：

```jsonc
{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],  // {file} 替换成测试 selector
  "cwd": "/abs/path/to/your-project",
  "timeout": 30,
  "env_ops": [
    {"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your-project"}
  ]
}
```

- 换语言只换 `command`（如 `["npx", "jest", "{file}"]`）。
- `env_ops` 的 action：`set` / `append` / `prepend` / `remove`。
- 给**项目级名字**（`pytest-<项目名>`）——executor 按名字跨项目共享，裸名会撞车。

> ⚠️ **安全提示**：executor 配置本质上允许运行任意 shell 命令。请审计 agent 写入的 executor
> 配置，确保安全可控。

---

## 跨平台接入：WSL 调 Windows Python

若 agent 跑在 WSL、GBC 的 Python 在 Windows（如 conda env），`gbc mcp up` 已替你扛掉两个坑
（env 变量传不进、cwd import 抢占），只要遵守启动契约即可：

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/mnt/c/Users/<you>/miniconda3/envs/<env>/Scripts/gbc.exe",
      "args": ["mcp", "up", "D:/path/to/your-project"]
    }
  }
}
```

- `command` 用 WSL 能看到的路径（`/mnt/c/...`）；`args` 里的项目根用 **Windows 形式**
  （`D:/...`），因为它们是传给 Windows 进程的 argv。
- 同平台（纯 Linux / 纯 Windows）不需要操心这些，用各自原生绝对路径即可。
- 若装的是包入口不方便定位，也可用 `<python.exe> -m gbc.entry mcp up <项目根>`。

---

## 心智模型

- 一个 MCP server 实例 = 一个项目根。多项目配多个条目（不同项目根参数）。
- MCP 暴露保证引擎、项目意图（`intent_*`）与离线 GBC 手册（`doc_list` / `doc_read` / `doc_search`）。写意图的人类确认闸门由你的
  框架承担，不靠藏通道。
- 路径参数一律用**项目根相对**的 posix 路径（`gbc/app/core/maker.py`），不是绝对路径。
