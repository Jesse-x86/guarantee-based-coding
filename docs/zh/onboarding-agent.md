# 给 Agent 的上手指令

> 语言：**简体中文** | [English](../en/onboarding-agent.md)

你好。如果你在读这份文档，说明你正在某个项目里工作，而你的人类想用上 GBC——很高兴由你来接线。
不难：先确认工具就绪，再把它接进当前项目，然后按推荐工作流干活。

两个贯穿始终的角色：

- **工作项目** — 你现在所在的项目，GBC 接进这里。
- **GBC 工具** — 已作为 `gbc` 命令安装好的独立工具。你调用它、指向工作项目。

---

## ① 确认工具就绪

GBC 作为一个独立命令行工具分发。确认它已安装：

```bash
gbc --help
```

若没有，请人类装（或在你被授权时自己装）：`pipx install guarantee-based-coding`。装好后 `gbc`
命令在 PATH 上，任意项目复用同一个安装。

> 想看一份本地化的接线指南（端点 / skill 文件在哪），随时可跑 `gbc setup`。

---

## ② 把 GBC 接进当前项目

GBC 的能力有两条接入路径，用你支持的那条（也可都用）：

### 路径 A — MCP（推荐）

把 GBC 的 MCP server 注册给自己，指向工作项目。启动命令：

```
gbc mcp up <工作项目根的绝对路径>
```

以你的框架添加 MCP server 的方式注册它（Claude Code 是项目根的 `.mcp.json`）。注册后重连 /
重启，工具就会出现。MCP 暴露**两个子系统**：保证引擎 + 意图文档（`doc_*` 工具）。

### 路径 B — Skills

跑 `gbc setup`，它会打印随包分发的 skill 文件的绝对路径。把它们拷到你的框架发现 skill 的位置
（GBC 把文件准备好，放到哪由你定）。`gbc-cli` skill 教你用全部 `gbc` 命令。

### 每个项目做一次

GBC 指向工作项目，测试 executor 跟着该项目的环境和语言走——换项目自然需要重新配。所以每开一个
新项目，重跑一次接入即可（几分钟）。

---

## ③ 注册 executor + 冒烟验证

- 注册测试 executor（怎么跑测试）：见 [reference.md](./reference.md#executor-配置)。给它
  **项目级名字**（`pytest-<项目名>`），因为 executor 按名字跨项目共享。
- 冒烟验证：跑 `gbc tree` 或 `gbc doctor check`（经 MCP 则调 `tree` / `check_consistency`）。
  能返回结果就说明接通了。

---

## ④ 动代码前：别让保证烂成虚假安全

接线只是把工具接上，拦不住你让它们说谎。一条保证只保护它真能抓到的东西，几个动作就能悄悄把它
变成摆设。这三条最值得从第一天记住，因为它们**静默**失效（完整陷阱清单见
[workflow.md](./workflow.md#几个静默失效的陷阱)）：

- **保证测试必须能变红**：fixture 只走 happy path、行为坏了还一直绿 = 什么都没守住。
- **把你真正依赖的行为提升为具名保证**：非空 / 非 None / 抛异常 / 有序 / 幂等是行为不是签名，
  免费符号依赖没有测试守护它们。
- **保证变红时恢复它或宣告它，绝不松测试**：松 / 退保证装绿会静默把真保证降级成虚假安全。

每次登记依赖或保证时问自己：**「如果我在乎的行为现在就坏了，会有测试真的变红吗？」** 若否，
先修那个。

---

## ⑤ 分层与权限：守在自己的范围内

- **顶层 agent（架构 / 主导）**：你主导意图。经 `gbc doc`（MCP doc 工具 / CLI）起草 gbc.md
  改动（绝不手编），经 GBC 工具登记保证，子任务交回后做最终集成验证。
- **Subagent（任务执行）**：聚焦的执行者。应对 GBC 图和意图文档**只读**：读 gbc.md 懂目标的
  意图和内部约束，用 `verify_provider` / `verify_guarantee` 自证。
- **护栏**：若框架支持 hook（如 Claude Code 的 `pre-tool-use`），建议人类**对 subagent 屏蔽
  所有 GBC 修改类工具**。只有顶层 agent 能改意图或保证图。强制力来自框架，跟走 MCP 还是 CLI
  无关。

---

完整的「在 GBC 下安全工作」见 [workflow.md](./workflow.md)；命令 / 工具速查见
[reference.md](./reference.md)；核心概念见 [concepts.md](./concepts.md)。
