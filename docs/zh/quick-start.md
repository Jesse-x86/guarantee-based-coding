# 快速开始

> 语言：**简体中文** | [English](../en/quick-start.md)

本页带你从零把 GBC 用起来：安装 → 接入你的 agent → 冒烟验证。几分钟即可。

GBC 是一个独立命令行工具。装一次，任意项目都能用；它把自己的可变状态放在**目标项目**的
`.gbc/` 目录下，从不污染你的源码。

---

## 1. 安装

```bash
pip install guarantee-based-coding
```

装好后 `gbc` 命令就在 PATH 上：

```bash
gbc --help
```

> 也可以用 `pipx install guarantee-based-coding`（隔离环境）或 `uvx guarantee-based-coding`
> （即用即弃）。GBC 的依赖很轻（typer / pydantic / mcp）。

---

## 2. 让你的 agent 用上 GBC

GBC 的能力有两条接入路径，用你的 agent 支持的那条即可（也可以都用）。**运行 `gbc setup`
会打印一份本地化的接线指南**，讲清端点和文件在哪：

```bash
gbc setup
```

下面是两条路径的要点。

### 路径 A — MCP（你的 agent 会说 MCP 时推荐）

GBC 自带一个 stdio MCP server，暴露**两个子系统**的能力：保证引擎（guarantee / dep / verify /
refactor / tree / consistency / executor）**以及**意图文档（doc show / check / set-* / sync /
migrate）。

启动命令是：

```bash
gbc mcp up <你项目根的绝对路径>
```

把它注册为一个 MCP server。以 Claude Code 为例，在项目根放一个 `.mcp.json`：

```json
{
  "mcpServers": {
    "gbc": {
      "command": "gbc",
      "args": ["mcp", "up", "/abs/path/to/your/project"]
    }
  }
}
```

- 一个 server 实例锁定一个项目根（作为参数传入，不靠环境变量）。多项目就配多个条目。
- 若启动器的 PATH 上没有 `gbc`，改用解释器形式：`python -m gbc.entry mcp up <项目根>`。
- 注册后重连 / 重启 agent，工具就会出现（Claude Code 里形如 `mcp__gbc__*`）。

跨平台细节（WSL 调 Windows Python 等）见 [reference.md](./reference.md)。

### 路径 B — Skills（不用 MCP、或 MCP 不方便时）

因为 GBC 的每项能力同时是一条 `gbc ...` 命令，一个能跑 shell 的 agent 可以通过一套**随包分发的
skill** 使用 GBC。`gbc setup` 会打印这些 skill 文件的绝对路径；把它们拷到你的 agent 发现 skill
的位置即可（每个框架读 skill 的位置不同——GBC 把文件准备好，放到哪由你决定）。

---

## 3. 定义一个 executor（测试怎么跑）

在登记任何保证之前，先告诉 GBC 用什么命令跑测试。executor 按名字存在目标项目里，一次定义、
之后复用。经 MCP 调 `upsert_executor`，或经 CLI：

```bash
gbc executor upsert pytest-myproject --json '{
  "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],
  "cwd": "/abs/path/to/your/project",
  "timeout": 30,
  "env_ops": [{"key": "PYTHONPATH", "action": "prepend", "value": "/abs/path/to/your/project"}]
}'
```

- `{file}` 是占位符，运行时替换成保证的测试选择器。
- 换语言只需换 `command`（如 `["npx", "jest", "{file}"]`）。
- 给它一个**项目级的名字**（如 `pytest-<项目名>`）——executor 按名字跨项目共享，裸名 `pytest`
  会和别的项目撞车。
- `env_ops` 的完整字段与 `action` 取值（`set`/`append`/`prepend`/`remove`）见
  [reference.md](./reference.md#executor-配置)。

---

## 4. 冒烟验证：确认接通了

让你的 agent（或你自己）跑一发只读命令：

```bash
gbc tree                 # 渲染整棵 .gbc 依赖树（空项目是一棵空树）
gbc doctor check         # 一致性体检，干净时报 "✔ consistent"
```

经 MCP 的话，调 `tree` 或 `check_consistency` 工具。能返回结果就说明 GBC 接通了。

---

## 5. 下一步

- 想懂 GBC 到底在保护什么 → [concepts.md](./concepts.md)（核心概念）
- 要在 GBC 下安全地改代码 → [workflow.md](./workflow.md)（推荐工作流）
- 查命令 / 工具 / executor 配置 → [reference.md](./reference.md)（速查）
- 你是 agent，人类让你接入 GBC → [onboarding-agent.md](./onboarding-agent.md)

> **一件 GBC 不替你做的事**：GBC 给的是能力，不是约束。谁能改 `.gbc/`、意图变更何时需人类
> 签字——这些规则由 `gbc rules` 打印，它们的**强制执行**必须来自你的 agent 框架（如
> pre-tool-use hook）。装了 GBC 不等于自动安全；请读 `gbc rules` 并自己接上强制执行。
