# GBC 手册:手动安装 + 在 GBC 下工作

**English version: [manual_EN.md](./manual_EN.md)**

> **这是 GBC 的手册 / 详细参考。** 如果你想要**自动**安装,让你的 agent 按 [for-agents.md](./for-agents.md)
> 安装并运行 `setup-gbc` skill——它会交互式地替你完成下面的 §1–5。本文档是**手把手手动安装**(§1–5)
> 以及**装好之后如何在 GBC 下安全工作**(§6–8)的完整参考。
>
> 全文都是以对 agent 说话的口吻写的——人类也可以照样读,或者直接交给你信任的 agent。它按"正常 /
> 推荐"的情形来写;请按照你和你的人类商定的权限划分,调整哪些由 agent 自己做、哪些留给人类决定。

GBC 把"这次改动会不会弄坏别处?"从一个猜测变成一个机械可验证的布尔值:依赖被显式登记为**保证**,
每条保证由一个窄测试兜底;你做出改动、跑保证,全绿 = 安全,任一红 = 一份关于你弄坏了谁的精确报告。

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

**角色默认(顶层 agent)。** 本手册,以及 `setup-gbc` 注入项目的 operating rules,都默认
**你是顶层 agent**:推荐流程是 规划 → 对齐意图 → 派 subagent(每个 brief 带上裁切好的 gbc.md
**意图和内部约束**、**可写目标文件**、其余路径**只读**) → subagent 本范围自证 → **你**经 GBC
工具做最终验收(默认走 MCP——不要手跑底层测试命令)。小改动可以规划与实现一体;日常写代码不是
顶层 agent 的默认职责。经 `setup-gbc` 接入的项目会在 instruction file 里拿到完整写法——以那
一段为现行工作流。

**两层契约。** ① **意图**(gbc.md):架构真相,最高契约,**由人类持有并审批**;你只能起草。
② **保证**:一个文件当前提供、且有下游依赖方的**具名行为**;你可以演进它,但破坏它 = 你必须让每个依赖方都改好。

**用 `[[project-relative-path]]` 引用代码。** 当 gbc.md 散文指向一个代码文件或符号时,写成
`[[app/core/models/game.py]]` 或 `[[app/core/models/game.py:GameSpec]]`——一个从仓库根出发、包在
`[[ ]]` 里的路径。不要用 `../` 相对路径:相对引用在任一侧移动时就会失效,而且从每个引用者看去读起来都不一样;
而 `[[ ]]` 引用是每个目标一个规范字符串,当目标移动时 `refactor_file` / `refactor_func` 工具会自动重写它。
(数据目录、HTTP 路由和 ADR 链接不需要 `[[ ]]`。)保证 id 遵循同样的精神但不带路径:
`<symbol>.<behavior>`(例如 `make_game.returns_html`),每个提供者内唯一。

**每次变更有两个相位,而且顺序要紧——想清楚架构后别一下子跳到写代码:**

1. **架构相(先草案;默认安装要求人类显式批准再落库)。** 人类有新需求时,把本次涉及的**全部**
   gbc.md 增量作为**草案**(文本)与人类核对;只有**显式批准之后**才经 gbc-doc 落库,并跑 `check`
   确认干净。**已落库的 gbc.md = 你实现的 spec。** 安装默认把「意图须确认」写进 operating rules /
   instruction。若人类嫌烦、要求你把 instruction 里**这一句删掉**,删掉后你的上下文里就**不再有**
   「意图必须确认」——可以更自动地行动;这是允许的,但**没人盯着意图落库时,静默架构漂移风险上升**。
   规则还在时不要私自搞 bypass:要么指令里有这条(确认),要么人类删了这条(你看不到它)。
2. **实现相(机器门控)。** 优先 **一个 subagent 对应一个目标文件**(brief 写明可写列表;其余**只读**)。
   按依赖拓扑序(先被依赖者)。实现方:
   - 读已批准范围(brief / gbc.md)+ 接口 → 写实现。
   - 依赖或新暴露的行为:签名级免费 `add_dependency`;真实行为则**主动写窄测试并
     `create_guarantee` / 挂上**(能复用就复用)。未登记的行为依赖 = 没做完。
   - **本范围自证**:只经 GBC 工具跑 `verify_provider` / `verify_guarantee`(不要裸跑测试命令)。
   - 意图中途发现不对 → 停,回架构相;禁止静默漂移。
3. **最终验收(顶层)。** subagent 交回后,顶层 / 架构 agent 再经 GBC 工具跑受影响保证。不要因为
   subagent 自称全绿就跳过这一步。

**关于窄测试的一条小纪律:** 断言**承诺**,不断言**实现**。写 `assert r is not None`,不写 `== 某个具体值`;
写 `with pytest.raises(X)`,不去纠缠具体的错误消息。**坚决偏窄**——偶尔漏报可以容忍,但误报会逐渐侵蚀对整个
系统的信任,那才是你真正要避免的。

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
