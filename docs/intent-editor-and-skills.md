# 意图树编辑器、CLI,以及把 CLI 包装成你自己的 skill

**English version: [intent-editor-and-skills_EN.md](./intent-editor-and-skills_EN.md)**

> 入口:[for-agents.md](./for-agents.md)(面向 agent)/ [for-humans.md](./for-humans.md)(面向人类)。本页展开 [manual.md](./manual.md) 中「把意图 CLI 包装成 skill」这一步(Web 编辑器、完整命令面、SKILL.md 示例)。

GBC 有两条权限不同的轨道:

- **保证(Guarantees)** — agent 通过 MCP 自助 CRUD,机器门控。见 [integrate-mcp.md](./integrate-mcp.md)。
- **意图(Intent)** — 人类持有的架构真相,存在每个文件夹的 `gbc.md` 里。agent 只能「起草」,由人类审批。

本页覆盖第二条轨道:意图文档怎么编辑(Web 编辑器 / CLI),以及怎么**围绕 CLI 包装一个 skill**,让你的 agent 有一个单一合规入口来改意图,而不是手工编辑 `gbc.md`。

## 为什么不让 agent 手工编辑 gbc.md

`gbc.md` 采用三段式结构（`# 意图` / `# 内部约束` / `# 文件`），这种结构带有一种**刻意的冗余**：子文件夹的意图既需要写在它自己的 `gbc.md` 之内，也需要同步到**父**文件夹 `gbc.md` 的 `## sub/` 条目中。这种设计确保了 Agent 在作业时的“就近上下文 (Context Locality)”，但**如果依靠人工维护这两份副本，必然会导致架构漂移 (Drift)**。

确保结构正确、父子意图同步是一类确定性、枯燥的维护任务——最稳妥的做法是将其交给工具程序。GBC 工具将整棵树视为**单一事实源 (Single Source of Truth)**：您只需编写一次意图，工具在保存时会自动将其投影 (Project) 到对应位置。

由人类进行架构判断，由工具处理机械维护——这正是 GBC 的核心哲学。

## 怎么写 gbc.md(三段式 + spec-first)

每个 `gbc.md` 有三段,各司一职:

- **`# 意图`(Intent)** = 这个文件夹/文件**是什么、为什么存在**(角色 / 目的)。**就地解释概念或留一个链接**(见 ADR-0001)——别留下未定义的术语。

  **用 `[[项目相对路径]]` 引用代码。**当散文指向某个代码文件或符号时,写成 `[[app/core/models/game.py]]` 或 `[[app/core/models/game.py:GameSpec]]`——从仓库根算起的路径,用 `[[ ]]` 包起来。别用 `../` 相对路径:相对引用在任一侧移动时会失效,而且从不同引用方看读起来还不一样;而 `[[ ]]` 引用对每个目标是一个规范字符串,当目标移动时 `refactor_file` / `refactor_func` 工具会自动重写它。(数据目录、HTTP 路由、ADR 链接不需要 `[[ ]]`。)
- **`# 内部约束`(Internal constraints)** = 它**需要什么、必须做/必须不做什么**(义务与规则:它持有什么状态、消费什么、什么必须先于什么发生、什么绝不能碰)。「它需要什么、它该做什么」放这里——别一股脑塞进意图。
  > 约束**只在本地存在、不向上冒泡到父级**,但这 ≠「对外人保密」:判据是「**身份(→ 意图)还是规则(→ 约束)**」。即便外人必须遵守,一条规则仍然属于约束(比如「外人只能依赖本模块的接口」),只要它是一条规则而不是存在的理由。
- **`# 文件`(Files)** = 子文件夹(名字以 `/` 结尾)加上本文件夹的代码文件,每个配一行角色描述(同样的规则:解释概念或留链接)。

**三段其实是可见性作用域——分不清「意图 vs 约束」时,逐句问「谁需要知道这句话」。** `# 意图` = **外部**要知道的(public 契约);`# 内部约束` = **所有内部文件都要协调、外部不需要**的(package-private 共享不变量);`## file` 条目 = **只有该文件自己**要知道的(private)。这层可见性和上面「身份→意图 / 规则→约束」不冲突、而是补齐它的一个缺口:它主要拿来当**"内部细节漏进意图"的嗅探器**——实现底座(用 Pydantic 还是 dataclass)、磁盘布局(元数据落 `session.json`)、内部机制(类型闸怎么接线)都是内部细节,属**约束 / 文件条目**,不该住 `# 意图`。(它只单向抓"内部细节上浮到意图";一条规则即便外人必须遵守,仍归约束,那条判据不变。)

**gbc.md 写的是"现状 + 禁令",不是"与过去状态的 diff"。** 它是**当前**契约,下面三类是最常见的漂移诱饵,写进去迟早腐坏、误导对着它干活的 agent:

- **阶段性/版本词汇** (`MVP`、`v0`、`v1`、`目前先`)：项目进度属于**全局事实**，应当记录在项目指令文件（如 `CLAUDE.md`）中；在每个文件夹的 `gbc.md` 中重复记录这些词汇会导致多份副本难以同步。请移除这些修饰词，保持事实描述的简洁。
- **路线图/愿望** (`日后会演化为复杂的 X`、`为更换后端预留接口`)：在最高契约中加入无法执行的愿望，会误导 Agent。**正确的做法是将其移除，或移交给 ADR (架构决策记录) / 路线图文档**。
- **迁移历史** (`不再使用 X`、`改为 Y`、`曾经……`)：`不再/改为` 这种描述对于阅读**当前**契约的人来说缺乏实质信息。它们要么是**历史遗迹**（X 已不存在）-> 应当删除；要么是**防回归禁令**（禁止重新引入 X）-> 应当作为约束明确写入 `# 内部约束`。
- **唯一合法的“过去”引用：显式标注的历史注记**。例如：「旧档兼容默认仍为 X —— 这是一个**客观事实**」。标注（`历史事实` / `兼容逻辑` / `已弃用`）的意义在于防止其被误读为当前的理想契约。未加标注的时间线描述往往是架构漂移的源头。

**spec-first(先写规格)**:在派 subagent / 写代码之前,先用 skill 把上面这些写好,自审或送审,再对着已写好的 gbc.md 去实现——**意图永远先于代码**。创建/移动文件夹或文件时,也要**先在这里登记它的 `# 文件` / 意图条目**;别等代码写完再补。

## 用法 1:Web 意图树编辑器

纯标准库,零依赖。适合做架构、想可视化编辑整棵树的人类。

```bash
cd tools/intent-editor/backend
python3 server.py                          # 127.0.0.1:8765,路径框留空
python3 server.py --root /path/to/.gbc     # 预填并自动加载
# 还有 --port / --host
```

在浏览器打开 http://localhost:8765。

- **Load**:在路径框里输入一个 `.gbc` 目录,点「Load」。路径无需已存在——你会得到一棵空树,点「Save」会从零创建目录和文件。
- **编辑子项**:名字以 `/` 结尾是子文件夹(实时切换),否则是文件。底部永远有一行空白的灰色子项;开始打字它就变成真的;把某行的名字和描述都清空再失焦即删除该行。
- **Save 只写、从不删**:移除一个条目 = 它不再被生成,但磁盘上的旧文件必须手工 / 通过 git 清理。用 `git diff` 检查回写了什么。

## 用法 2:意图 CLI(`gbc_doc.py`)

供 agent / 脚本调用。位于 `tools/intent-editor/backend/gbc_doc.py`。

```
python gbc_doc.py --root <项目目录或其 .gbc 目录> <command> [args...]
```

`<folder>` 是**项目相对路径**(如 `app/core/maker`);用 `""` 或 `.` 表示根。

| Command | 作用 |
|------|------|
| `show <folder>` | 查看一个文件夹的意图 / 约束 / 条目 |
| `set-intent <folder> "<text>"` | 设置意图;**自动单一事实源投影**到父文档的 `## <name>/` 条目 |
| `set-constraints <folder> "<text>"` | 设置 `# 内部约束`(只在本地存在,不向上冒泡到父级) |
| `set-file <folder> <name> "<desc>"` | 增加/修改一个**文件**条目(name 不含 `/`) |
| `rm-entry <folder> <name>` | 从文档移除一个条目(只改文档,不删磁盘上的文件——留给 git review) |
| `check` | 全树一致性 lint:`DRIFT`/`ORPHAN` = 错误(exit code 1);`STUB` = 提示(叶子文件夹正常会有) |
| `sync` | 确定性修复 `DRIFT`/`ORPHAN`:把子意图重新投影进父条目(只动父,不动子) |
| `migrate` | 逐个 gbc.md 解析→序列化重写,升级到带 `# 文件` 段的新格式 |

要点:

- **创建子文件夹**只需对它 `set-intent`;父条目会**自动登记**——别手工往父文档加 `## xxx/`。
- 子文件夹的意图是**单一事实源**;父文档里的描述是投影,所以别在父文档里单独改它(会被 `sync` 覆盖)。
- 编辑后跑 `check` 确认干净(无错误)。所有改动**仍需人类审批**(看 `git diff`):CLI 只保证「改动结构正确、父子同步」——它不替代审查。

## 把 CLI 包装成你自己的 skill

如果你的 agent 框架支持「skills / 自定义命令」(像 Claude Code 的 skills),最佳实践是**把这个 CLI 包装成一个 skill**,作为 agent 改意图的**单一入口**,并在 skill 描述里硬写「NEVER 手工编辑 gbc.md」。这样一来,agent 想改意图时永远只走这个确定性程序。

一个 skill = 两样东西:**一个薄包装脚本(wrapper)** + **一个 SKILL.md**(何时用、命令面)。

### 1)薄包装脚本

包装脚本只做三件事:**钉死解释器、钉死 `--root`、把其余透传**。这是一个真实可用的例子(WSL 调用 Windows conda python 去改某项目的意图):

```bash
#!/usr/bin/env bash
# gbc-doc — the only compliant edit entry for gbc.md. Wraps the intent-editor CLI (gbc_doc.py).
# gbc.md's structure and parent/child consistency are a deterministic constraint that must be
# kept by this program — never hand-edit gbc.md.
exec /mnt/c/Users/<you>/miniconda3/envs/<env>/python.exe \
  D:/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root D:/path/to/your-project \
  "$@"
```

- 解释器 + `--root` 在包装脚本里硬编码 → agent 调用时只提供命令和参数,选不错环境或项目根。
- `"$@"` 透传 → `gbc_doc.py` 的所有子命令(`show`/`set-intent`/`check`/…)都能原样使用。
- 在单一平台上(纯 Linux / Windows),只需把解释器和路径换成原生绝对路径——逻辑不变。

### 2)SKILL.md

给 agent 读的「何时用 + 怎么用」。Claude Code 的 skills 用 YAML frontmatter 声明 `name`/`description`(description 决定 agent 何时自动选它);正文给出调用方式 + 命令表 + 规则。骨架:

```markdown
---
name: gbc-doc
description: The only compliant entry for reading/writing .gbc intent docs (gbc.md). Use this skill
  whenever you view/create/change/lint gbc.md — NEVER hand-edit gbc.md (its structure and
  parent/child consistency are a deterministic constraint, only kept through this program).
---

# gbc-doc: the compliant edit entry for gbc.md

## Invocation
\`\`\`bash
bash /abs/path/to/gbc-doc.sh <command> [args...]
\`\`\`

## Commands
(copy the command table from "Usage 2" above)

## When to use / rules
- Use it before and after changing architecture (intent/constraints/adding/removing folders & files); run `check` to confirm it's clean.
- A subfolder's intent is the single source of truth; don't edit it separately in the parent doc (it gets overwritten by `sync`).
- All gbc.md changes still need human approval (review the diff). This skill only guarantees structural correctness and parent/child sync — it doesn't replace review.
```

### 同理:保证侧的 CLI 也能包装

除了意图侧的 `gbc_doc.py`,GBC 还有一个**核心保证 CLI** `app/interface/cli.py`(一个 typer 实现,与 MCP 工具一一对应),子命令有:`guarantee` / `dep` / `verify` / `doctor` / `executor`。从工具仓库根把它当模块跑:

```bash
python -m app.interface.cli verify provider <source file>
python -m app.interface.cli guarantee list <source file>
python -m app.interface.cli dep who <source file>
```

如果你的 agent 不走 MCP、更偏好命令行,你可以用上面同样的 wrapper + SKILL.md 模式把它包装成 skill。保证侧用 MCP 还是 CLI 取决于你的 agent;意图侧则推荐永远走 `gbc_doc.py`(那个 skill),这样「改意图只有一扇门」。
