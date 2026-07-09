# 意图树编辑器、CLI,以及把 CLI 包装成你自己的 skill

**English version: [intent-editor-and-skills_EN.md](./intent-editor-and-skills_EN.md)**

> 入口:[for-agents.md](./for-agents.md)(面向 agent)/ [for-humans.md](./for-humans.md)(面向人类)。本页展开 [manual.md](./manual.md) 中「把意图 CLI 包装成 skill」这一步(Web 编辑器、完整命令面、SKILL.md 示例)。

GBC 有两条权限不同的轨道:

- **保证(Guarantees)** — agent 通过 MCP 自助 CRUD,机器门控。见 [integrate-mcp.md](./integrate-mcp.md)。
- **意图(Intent)** — 人类持有的架构真相,存在每个文件夹的 `gbc.md` 里。agent 只能「起草」,由人类审批。

本页覆盖第二条轨道:意图文档怎么编辑(Web 编辑器 / CLI),以及怎么**围绕 CLI 包装一个 skill**,让你的 agent 有一个单一合规入口来改意图,而不是手工编辑 `gbc.md`。

## 为什么不让 agent 手工编辑 gbc.md

`gbc.md` 有结构(`# 意图` / `# 内部约束` / `# 文件` 三段之下各有 `## entries`),并且带一层**刻意的重复**:一个子文件夹的意图既写在它自己的 `gbc.md` 的 `# 意图` 里,也写在**父**文件夹 `gbc.md` 的 `## sub/` 条目里。这层重复服务于写代码的 agent 的上下文就近性(context locality),但**靠手工维护两份副本必然漂移(drift)**。

结构是否正确、父子是否保持同步,是一类确定性、重复出现的约束——最稳妥的做法是交给程序,而不是指望 agent 每次都记得。工具把整棵树当作**单一事实源(single source of truth)**:你只写一次某个节点的意图,保存时工具会把它投影(project)到两处。

人类做架构判断,工具处理机械维护——与 GBC 的哲学一致。

## 怎么写 gbc.md(三段式 + spec-first)

每个 `gbc.md` 有三段,各司一职:

- **`# 意图`(Intent)** = 这个文件夹/文件**是什么、为什么存在**(角色 / 目的)。**就地解释概念或留一个链接**(见 ADR-0001)——别留下未定义的术语。

  **用 `[[项目相对路径]]` 引用代码。**当散文指向某个代码文件或符号时,写成 `[[app/core/models/game.py]]` 或 `[[app/core/models/game.py:GameSpec]]`——从仓库根算起的路径,用 `[[ ]]` 包起来。别用 `../` 相对路径:相对引用在任一侧移动时会失效,而且从不同引用方看读起来还不一样;而 `[[ ]]` 引用对每个目标是一个规范字符串,当目标移动时 `refactor_file` / `refactor_func` 工具会自动重写它。(数据目录、HTTP 路由、ADR 链接不需要 `[[ ]]`。)
- **`# 内部约束`(Internal constraints)** = 它**需要什么、必须做/必须不做什么**(义务与规则:它持有什么状态、消费什么、什么必须先于什么发生、什么绝不能碰)。「它需要什么、它该做什么」放这里——别一股脑塞进意图。
  > 约束**只在本地存在、不向上冒泡到父级**,但这 ≠「对外人保密」:判据是「**身份(→ 意图)还是规则(→ 约束)**」。即便外人必须遵守,一条规则仍然属于约束(比如「外人只能依赖本模块的接口」),只要它是一条规则而不是存在的理由。
- **`# 文件`(Files)** = 子文件夹(名字以 `/` 结尾)加上本文件夹的代码文件,每个配一行角色描述(同样的规则:解释概念或留链接)。

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
