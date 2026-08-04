# 参考手册

> 语言：**简体中文** | [English](../en/reference.md)

命令 / 工具速查、executor 配置、跨平台接入细节。上手见 [quick-start.md](./quick-start.md)，
工作流见 [workflow.md](./workflow.md)。

GBC 的每项能力都有三种等价形态：**CLI**（`gbc ...`）、**MCP 工具**（agent 调用）、以及
**gbc-cli skill**。下表以 CLI 为主，标注对应的 MCP 工具名。

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
| `gbc tree` | 渲染整棵 `.gbc` 依赖树。`--detail` 展开保证详情，`--gaps` 附登记缺口。 |
| `gbc doctor check` | 全局一致性体检：悬空引用 + 双向边漂移 + 停用保证（响亮报出）。 |

日常使用先运行一次 `gbc lang zh` 或 `gbc lang en`；只有临时切换 `setup` / `rules` 输出时才使用末尾的 `--lang`。

### 项目根

保证引擎的叶命令（`guarantee`、`dep`、`verify`、`refactor`、`tree`、`doctor`、`executor`）默认按
`GBC_PROJECT_ROOT` > 当前工作目录（cwd）选择项目根，不会向父目录搜索。可在具体叶命令末尾用
`--project <项目根>` 或 `-C <项目根>` 显式覆盖，例如 `gbc doctor check -C /path/to/project`。

---

## 保证 — `gbc guarantee` / MCP

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc guarantee create <provider> <id> <test> <executor> <desc>` | `create_guarantee` | 新建具名保证。**出生即绿**：当场跑测试，不过则拒绝。`--heavy N` / `--timeout S` / `--disabled`（跳过门禁建占位，仅用于破循环依赖）。 |
| `gbc guarantee update <provider> <id>` | `update_guarantee` | 改字段：`--desc` / `--test` / `--executor` / `--heavy` / `--timeout`。改测试 / executor 会重跑门禁。 |
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

## 意图文档 — `gbc doc` / MCP

| CLI | MCP 工具 | 作用 |
|-----|----------|------|
| `gbc doc show <folder>` | `doc_show` | 查看文件夹的意图 / 约束 / 条目。根用 `""` 或 `.`。 |
| `gbc doc check` | `doc_check` | 全树一致性体检（DRIFT/ORPHAN 为错误，STUB 为提示）。 |
| `gbc doc set-intent <folder> "<text>"` | `doc_set_intent` | 设意图（自动单源投影到父条目）。 |
| `gbc doc set-constraints <folder> "<text>"` | `doc_set_constraints` | 设内部约束（只在本地）。 |
| `gbc doc set-file <folder> <name> "<desc>"` | `doc_set_file` | 新增 / 更新文件条目（name 不带 `/`）。 |
| `gbc doc rm-entry <folder> <name>` | `doc_rm_entry` | 删条目（不删盘上文件，留给 git 复核）。 |
| `gbc doc sync` | `doc_sync` | 确定性修复父子漂移。 |
| `gbc doc migrate` | `doc_migrate` | 把所有 gbc.md 升级到最新格式。 |

> `<text>` 以 `-` 开头时，在它前面加 `--`，避免被当成选项：
> `gbc doc set-intent app -- "- 以短横线开头的一行"`。

**写意图是在改人类持有的架构真理。** 是否需人类签字由你的框架规则 / hook 决定，不由工具设阻。
绝不手编 gbc.md。

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
- MCP 现在暴露**两个子系统**：保证引擎 + 意图文档（doc 工具）。写意图的人类确认闸门由你的
  框架承担，不靠藏通道。
- 路径参数一律用**项目根相对**的 posix 路径（`gbc/app/core/maker.py`），不是绝对路径。
