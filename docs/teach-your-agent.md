# GBC:给 Coding Agent 的接入与使用指南

> **你是 coding agent?** 太好了,这份就是为你写的——照着做,你能把 GBC 装进当前项目、接上工具面,
> 并知道在 GBC 下怎么安全改代码。本文自包含。
>
> **你是人类?** 很抱歉，我们暂时还没有单独的人类向文档，麻烦您暂时和你的 agent 读同一份文档（本文档），并接受下文中我们假定自己在对 agent 说话的口气。
> 或者，更简单的做法是，直接把这份文档交给你信赖的 agent。
>
> 本文是一份**引导、推荐流程**,不是硬规矩。下面都按"正常情况下""推荐"来写;具体什么该你(agent)
> 自己做、什么该留给人类拍板,**按你的人类的偏好调整**。我们强烈建议和你的人类好好讨论一下围绕GBC的权限分配的事。

GBC 让"改代码会不会弄坏别处"从猜测变成可机械验证的布尔条件:依赖被显式登记成**保证(guarantee)**,
每条保证背后是一个窄测试;你改完跑保证,全绿=安全,有红=精确告诉你破坏了谁。

---

## 1. 安装

GBC 用它**自己的** Python 环境跑(和目标项目环境分开)。在 GBC 仓里:

```bash
pip install -r requirements.txt   # typer[all] / pydantic / mcp
```

> 正常情况下装环境这步推荐交人类执行;装好后继续。

## 2. 接 MCP(你的保证侧工具)

在**目标项目根**放一个 `.mcp.json`:

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

- `command` = 第 1 步装了依赖的解释器。
- `args[0]` = `serve.py` 绝对路径;`args[1]` = **目标项目根绝对路径**(必须 argv 传,不能靠环境变量)。
- 重启 agent 后,工具以 `mcp__gbc__*` 出现。
- WSL 调 Windows Python 有跨平台坑(路径/编码),已被 `serve.py` 兜掉——细节见
  [integrate-mcp.md](./integrate-mcp.md)。

## 3. 定义一个 executor(怎么跑测试)

建任何保证前,先告诉 GBC 用什么命令跑测试。调 `upsert_executor`:

```jsonc
// config_name: "pytest"
// config_data:
{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],  // {file} 替换成测试选择器
  "cwd": "/abs/path/to/your-project",
  "timeout": 30,
  "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your-project"}]
}
```

换语言只换 `command`(如 `["npx","jest","{file}"]`)。`env_ops` 动作:`set`/`append`/`prepend`/`remove`。

## 4. 把意图 CLI 包成 skill(你改意图的唯一入口)

每个文件夹的意图存在 `.gbc/<path>/gbc.md`,分三段:**`# 意图`**(是什么/为什么)、**`# 内部约束`**
(义务与规则:需要什么、必须/禁止做什么)、**`# 文件`**(子文件夹 + 文件各一句)。它的结构和父子一致性是
**确定性约束,你 NEVER 手编**——一律走 GBC 自带的意图 CLI(`gbc_doc.py`)。三段各写什么、spec-first
细节见 [intent-editor-and-skills.md](./intent-editor-and-skills.md)。把它包成一个薄 skill:

**wrapper**(钉死解释器 + 项目根,其余透传):

```bash
#!/usr/bin/env bash
exec /abs/path/to/python \
  /abs/path/to/guarantee-based-coding/tools/intent-editor/backend/gbc_doc.py \
  --root /abs/path/to/your-project "$@"
```

**SKILL.md**(让你知道何时用它):

```markdown
---
name: gbc-doc
description: 读/写 .gbc 意图文档(gbc.md)的唯一合规入口。查看/新建/改/体检 gbc.md 时用本 skill —— NEVER 手编 gbc.md。
---
调用:`bash /abs/path/to/gbc-doc.sh <命令> [参数...]`
命令:show / set-intent / set-constraints / set-file / rm-entry / check / sync / migrate
（命令面见第 6 节;人类做架构时也可跑 `python gbc_doc.py` 的 web 编辑器,见 intent-editor-and-skills.md）
```

## 5. 冒烟:确认接通

调一发只读工具:

- `check_consistency()` → 返回 `[]` 即 `.gbc` 图一致(空项目也是 `[]`)。
- `list_provides("<某源文件相对路径>")` → 返回该文件已登记的保证(没有则 `{}`)。

> 路径参数一律用**相对项目根**的 posix 路径(`app/core/maker/maker.py`),不是绝对路径。
> 接不通先回查第 2 步。

---

## 6. 工具速查

**保证侧(gbc MCP,`mcp__gbc__*`):**

| 工具 | 干什么 |
|------|--------|
| `add_dependency(provider, consumer, symbol[, guarantee_id])` | 登记依赖。给 `guarantee_id`=行为依赖(自动写反向边);不给=免费符号依赖 |
| `create_guarantee(provider, id, desc, test, executor[, heavy])` | 新建具名保证。**出生即跑测,失败拒绝创建** |
| `update_guarantee` / `retire_guarantee` | 改 / 退休。退休对仍有 dependents 的保证**拒绝** |
| `verify_guarantee(provider, id)` / `verify_provider(provider)` | 跑单条 / 跑某文件全部保证(门禁) |
| `who_depends_on(provider[, symbol, guarantee_id])` | 反查谁依赖我(取代 grep) |
| `list_provides(provider)` / `list_depends_on(consumer)` | 看我提供的保证 / 我声明的依赖 |
| `check_consistency()` | 全图体检:悬空引用、双向边漂移 |

**意图侧(gbc-doc skill → `gbc_doc.py`):**

| 命令 | 干什么 |
|------|--------|
| `show <folder>` | 看某文件夹意图/约束/条目 |
| `set-intent <folder> "<text>"` | 设意图,自动单源投影到父条目 |
| `set-constraints <folder> "<text>"` / `set-file <folder> <name> "<desc>"` | 设内部约束 / 新增改文件条目 |
| `rm-entry <folder> <name>` | 删一个文档条目(不删盘上文件) |
| `check` / `sync` | 一致性体检 / 确定性修复父子漂移 |

`<folder>` 用项目相对路径,根用 `""` 或 `.`。

---

## 7. 在 GBC 下改代码:工作流

**两层契约。** ① **意图**(gbc.md):架构真相、最高契约、**人类持有人类批**;你只能起草。
② **保证**(guarantee):某文件当前提供、有下游依赖的**具名行为**;你可演进,但破坏=必须让所有 dependents 修。

**改动分两相,NEVER 想完架构就直接写代码:**

1. **架构相(先草案、谈定才落库)**:把本次改动涉及的**全部** gbc.md 增量先作为**草案**(文本)交人类
   讨论修改;**谈定后**才经 gbc-doc skill 落库、跑 `check` 确认干净。skill 只落已批准内容。
   **已落库的 gbc.md = 你实现的 spec。**(意图归人类拍板是 GBC 的设计;正常情况下推荐这么走。)
2. **实现相(机器门控)**:按依赖**拓扑序**实现(先做被依赖者)。每个文件:
   - 读已批 gbc.md + 依赖方接口 → 写实现。
   - 想清"我依赖了它的哪些**行为**":
     - 只依赖签名/符号存在 → `add_dependency(provider, consumer, symbol)`(免费)。
     - 依赖具体**行为**(非空、异常语义……)→ 命中已有保证就 `add_dependency(..., guarantee_id=...)` 复用;
       没有就**先写一个_窄_测试**,再 `create_guarantee(...)`。
   - 跑 `verify_provider` / `verify_guarantee`,全绿才算这步成立。
   - 若实现中发现**意图本身**要改 → 回架构相重新起草谈定,别偷偷偏离。

**窄测试的纪律**:断**承诺**、不断**实现**。`assert r is not None` 而非 `== 具体值`;
`with pytest.raises(X)` 而非断言 message。**坚决偏窄**——漏报可容忍,误报会让人无视整个系统。

---

## 8. 常见错误(别犯)

| ❌ 别这么做 | ✅ 要这么做 |
|---|---|
| 手编 `.gbc/**` 的 `gbc.md` 或 `*.json` | gbc.md 走 gbc-doc skill;依赖/保证走 gbc MCP |
| 想完架构直接写代码 | 先草拟 gbc.md → 人批 → 再按拓扑序实现 |
| 测试断言具体返回值(`== "<html>..."`) | 断承诺:非空 / 类型 / 抛错 |
| 给所有依赖都建具名保证 | 默认免费符号依赖;**只**对行为依赖升级,且懒创建 |
| 退休还有 dependents 的保证 | 先迁移/修好 dependents(`retire` 会拒绝) |
| 用绝对路径调工具 | 一律相对项目根的 posix 路径 |
| 一次改一堆文件 | 按拓扑序、一步一个文件,每步跑保证 |

---

更细的接入(跨平台、自研客户端)见 [integrate-mcp.md](./integrate-mcp.md);意图编辑器与 skill 范例见
[intent-editor-and-skills.md](./intent-editor-and-skills.md)。
