# 把 GBC 接入你的 agent

GBC 已经装好了。这是一份**接线指南**：它告诉你**端点和文件在哪**，好让你的 agent
够得着它们。它**不**规定*具体怎么接*——那取决于你所用的 agent 框架如何加载 MCP
server 和 skill。GBC 只给你坐标，接线由你（或你的 agent）来做。

给 agent 赋予 GBC 能力有两条彼此独立的路。你的 agent 支持哪条就用哪条，也可以都用。

---

## 方案 A —— MCP（你的 agent 会说 MCP 时推荐）

GBC 自带一个 stdio MCP server，暴露两个子系统：保证引擎（guarantee / dep / verify /
refactor / tree / consistency / executor）**以及**意图文档（doc show / check / set-* /
sync / migrate）。

**端点** —— 用下面的命令启动 server：

```
gbc mcp up <你项目根的绝对路径>
```

把这条命令注册为 MCP server，注册位置在你框架存放 MCP 配置的地方。一个典型的 stdio
条目形如（按你框架的 schema 调整）：

```
{{
  "command": "gbc",
  "args": ["mcp", "up", "/abs/path/to/your/project"]
}}
```

说明：
- 项目根作为那个参数传入；server 把一切可变状态放在你项目的 `.gbc/` 下（首次写入时
  自动创建——你不必预先建它）。
- 如果启动器的 PATH 上没有 `gbc`，改用解释器形式：
  `<python> -m gbc.entry mcp up <项目根>`。
- 注册后重新加载 / 重连 MCP，让你的 agent 拉到这些工具。

---

## 方案 B —— Skills（给不用 MCP、或 MCP 不方便的 agent）

因为 GBC 的每一项能力同时也是一条普通的 `gbc ...` 命令，一个能跑 shell 的 agent 可以
通过一套**预组 skill** 来使用 GBC——这些 skill 教它该敲哪些命令，等价于 CLI 侧的 MCP
工具描述。

**文件** —— 随包分发的 skill 在这里：

```
{skills_dir}
```

把这些 skill 文件拷贝（或软链）到你的 agent 发现 skill 的位置。GBC 不替你放置它们，
因为每个框架读 skill 的位置都不同——把文件准备好是我们的事，放到哪由你决定。

---

## 验证是否接通

接好后，让你的 agent 跑一次只读调用——比如经 MCP 调 `tree` 工具，或在 CLI 敲
`gbc tree`。如果它返回了你项目的依赖树（新项目则是一棵空树），说明 GBC 已经够得着了。

## 用之前，先记住三件事

- **gbc.md 是现状快照，不是圣旨。** 它防的是架构漂移，不是架构演进——想改就走「起草 →
  送人类审批 → 经 gbc doc 落库」，正当演进不是违规。别因为「不能手编」就把职责全塞进已有
  文件——上帝文件正是防漂移机制的本末倒置。
- **保证 ≠ 全面测试。** 每条保证是窄测试守护的具名行为承诺，只登记你在乎且被依赖的行为，能复用
  先复用；没人在乎的保证是负债。
- **多与人类沟通。** 做完一步汇报一步，不确定就问，别闷头憋大招到「完美」才交。

## 有一件事 GBC 不替你做

GBC 给的是能力，不是约束。安全规则（谁能改 `.gbc/`、意图变更何时需人类签字）由
`gbc rules` 打印，而它们的**强制执行**必须来自你的 agent 框架（例如 pre-tool-use
hook）——无论能力是经 MCP 还是 CLI 到达，同一个 hook 都适用。装了 GBC 并不会让你自动
安全；请读 `gbc rules`，并自己把强制执行接上。
