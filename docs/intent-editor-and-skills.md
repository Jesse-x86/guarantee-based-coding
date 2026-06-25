# 意图树编辑器、CLI,与围绕 CLI 写你自己的 Skill

> 入口见 [for-agents.md](./for-agents.md)(给 agent)/ [for-humans.md](./for-humans.md)(给人类)。本文是手动文档 [manual.md](./manual.md) 中「把意图 CLI 包成 skill」一步的展开(web 编辑器、完整命令面、SKILL.md 范例)。

GBC 有两条线、权限不同:

- **保证(guarantee)**:agent 经 MCP 自助增删改查,机器门控。见 [integrate-mcp.md](./integrate-mcp.md)。
- **意图(intent)**:人类持有的架构真相,存在每个文件夹的 `gbc.md`。agent 只能"起草",人类批准。

本文讲第二条线:意图文档怎么编辑(web 编辑器 / CLI),以及怎么**围绕 CLI 包一个 Skill**,
让你的 agent 有一个"唯一合规的改意图入口",而不是去手编 `gbc.md`。

## 为什么不让 agent 手编 gbc.md

`gbc.md` 有结构(`# 意图` / `# 内部约束` / `# 文件` 下的 `## 条目`)和一层**刻意的重复**:
一个子文件夹的意图既写在它自己 `gbc.md` 的 `# 意图`,又写在**父**文件夹 `gbc.md` 的 `## sub/` 条目里。
重复是为了写代码的 agent 的上下文局部性,但**手维护两份必然漂移**。

结构是否正确、父子是否同步,是一类确定而又重复的约束——交给程序来保证最稳妥,不必依赖 agent 每次都记得。
工具把树当**单一事实源**:你对一个节点的意图只写一次,工具保存时同时投影到两个位置。
人做架构判断,工具担机械维护——与 GBC 哲学一致。

## 怎么写 gbc.md(三段分工 + spec-first)

每个 `gbc.md` 三段,各管一件事:

- **`# 意图`** = 这个文件夹/文件**是什么、为什么存在**(角色/目的)。**概念要么就地讲清,要么留链接**
  (`XX 概念见 ../models/yy.py`、`见 ADR-0001`)——别留下未定义的术语。
- **`# 内部约束`** = 它**需要什么、必须/禁止做什么**(义务与规则:持有什么状态、消费什么、什么之前
  必须先做什么、绝不碰什么)。「需要有什么、应该做什么」放这里,别堆进意图。
  > 约束**只活在本地、不冒泡到父**,但这 ≠「对外保密」:判据是「**身份(→意图)还是规则(→约束)**」。
  > 一条规则哪怕外部必须遵守(如"外部只能依赖本模块的接口"),只要它是规则、不是存在理由,就归约束。
- **`# 文件`** = 子文件夹(名末带 `/`)+ 本文件夹的代码文件,各一句角色描述(同样:概念解释或留链接)。

**spec-first**:派 subagent / 写代码前,先用 skill 把以上写好、自审或送人审,实现照着已写好的 gbc.md
干活——**意图永远先于代码**。新建/移动文件夹文件也**先在这登记其 `# 文件` / 意图条目**,别等代码写完再补。

## 用法一:Web 意图树编辑器

纯标准库、零依赖。适合人类做架构时可视化编辑整棵树。

```bash
cd tools/intent-editor/backend
python3 app.py                          # 127.0.0.1:8765,路径框留空
python3 app.py --root /path/to/.gbc     # 预填并自动加载
# 另可 --port / --host
```

浏览器开 http://localhost:8765 。

- **加载**:路径框填一个 `.gbc` 目录点「加载」。路径不存在也行——得到空树,「保存」时再从零建目录和文件。
- **子项编辑**:名称结尾带 `/` 即子文件夹(实时切换),否则是文件。底部常驻一条灰色空白子项,
  一输入就转正;把某条名称+说明都清空再失焦即删除。
- **保存只写不删**:删条目=不再生成它,旧盘上文件需手工 / 经 git 清理。用 `git diff` 复核写回结果。

## 用法二:意图 CLI(`gbc_doc.py`)

适合 agent / 脚本调用。位置 `tools/intent-editor/backend/gbc_doc.py`。

```
python gbc_doc.py --root <项目目录 或 其 .gbc 目录> <命令> [参数...]
```

`<folder>` 是**项目相对路径**(如 `app/core/maker`),根用 `""` 或 `.`。

| 命令 | 作用 |
|------|------|
| `show <folder>` | 看某文件夹的意图 / 约束 / 条目 |
| `set-intent <folder> "<text>"` | 设意图;**自动单源投影**到父文档的 `## <name>/` 条目 |
| `set-constraints <folder> "<text>"` | 设 `# 内部约束`(只活在本地,不冒泡到父) |
| `set-file <folder> <name> "<desc>"` | 新增/改一个**文件**条目(name 不带 `/`) |
| `rm-entry <folder> <name>` | 从文档删一个条目(只改文档,不删盘上文件,留给 git 复核) |
| `check` | 全树一致性体检:`DRIFT`/`ORPHAN`=错误(退出码 1);`STUB`=提示(叶子文件夹正常) |
| `sync` | 确定性修复 `DRIFT`/`ORPHAN`:把子意图重投影到父条目(只动父,不碰子) |
| `migrate` | 把所有 gbc.md parse→serialize 重写,升级到带 `# 文件` 段的新格式 |

要点:

- **新建子文件夹**只需对它 `set-intent`,父条目会**自动补登记**——不要手动去父文档加 `## xxx/`。
- 子文件夹意图是**唯一事实源**;父文档里的描述是投影,别在父文档单独编辑它(会被 `sync` 覆盖)。
- 改完用 `check` 验证干净(errors 为空)。所有改动**仍需人类批**(看 `git diff`):CLI 只保证
  "改得结构正确、父子同步",不替代审批。

## 围绕 CLI 写你自己的 Skill

如果你的 agent 框架支持"skill / 自定义命令"(如 Claude Code 的 skills),最佳实践是
**把这个 CLI 包成一个 skill**,作为 agent 改意图的**唯一入口**,并在 skill 描述里写死
"NEVER 手编 gbc.md"。这样 agent 想改意图时只会走这个确定性程序。

一个 skill = 两件东西:**一个薄 wrapper 脚本** + **一份 SKILL.md**(说明何时用、命令面)。

### 1) 薄 wrapper 脚本

wrapper 只干三件事:**钉死解释器、钉死 `--root`、把其余参数透传**。
下面是一个真实可用的范例(WSL 调 Windows conda python,改意图给某项目):

```bash
#!/usr/bin/env bash
# gbc-doc —— gbc.md 的唯一合规编辑入口。封装 intent-editor CLI(gbc_doc.py)。
# gbc.md 的结构与父子一致性是确定性约束,必须由本程序保证——绝不手编 gbc.md。
exec /mnt/c/Users/<you>/miniconda3/envs/<env>/python.exe \
  D:/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root D:/path/to/your-project \
  "$@"
```

- 解释器 + `--root` 写死在 wrapper 里 → agent 调用时只管命令和参数,不会填错环境或项目根。
- `"$@"` 透传 → `gbc_doc.py` 的全部子命令(`show`/`set-intent`/`check`/…)原样可用。
- 同平台(纯 Linux / Windows)把解释器和路径换成原生绝对路径即可,逻辑不变。

### 2) SKILL.md

给 agent 看的"何时用 + 怎么用"。Claude Code 的 skill 用 YAML frontmatter 声明 `name`/`description`
(description 决定 agent 何时自动选用它),正文给调用方式 + 命令表 + 规则。骨架:

```markdown
---
name: gbc-doc
description: 读/写 .gbc 意图文档(gbc.md)的唯一合规入口。任何查看/创建/修改/体检 gbc.md
  时用本 skill —— NEVER 手编 gbc.md(结构与父子一致性是确定性约束,只能经此程序)。
---

# gbc-doc:gbc.md 的合规编辑入口

## 调用
\`\`\`bash
bash /abs/path/to/gbc-doc.sh <命令> [参数...]
\`\`\`

## 命令
（把上面「用法二」的命令表抄进来）

## 何时用 / 规则
- 改架构(意图/约束/增删文件夹文件)前后都用它;改完 `check` 验证干净。
- 子文件夹意图是唯一事实源,别在父文档单独编辑(会被 `sync` 覆盖)。
- 所有 gbc.md 改动仍需人类批(看 diff)。本 skill 只保证结构正确、父子同步,不替代审批。
```

### 同理:也可以包"保证侧"的 CLI

意图侧的 `gbc_doc.py` 之外,GBC 还有一个**核心保证 CLI** `app/interface/cli.py`(typer 实现,
与 MCP 工具一一对应),子命令:`guarantee` / `dep` / `verify` / `doctor` / `executor`。
从工具仓根目录按模块跑:

```bash
python -m app.interface.cli verify provider <源文件>
python -m app.interface.cli guarantee list <源文件>
python -m app.interface.cli dep who <源文件>
```

如果你的 agent 不走 MCP、而偏好命令行,同样可以用上面的 wrapper + SKILL.md 模式把它包成 skill。
保证侧用 MCP 还是 CLI 取决于你的 agent;意图侧推荐始终经 `gbc_doc.py`(skill),保证"只有一个改意图的门"。
