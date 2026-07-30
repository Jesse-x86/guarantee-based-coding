# 核心概念

> 语言：**简体中文** | [English](../en/concepts.md)

本页解释 GBC 的核心概念——它到底在保护什么、怎么保护。要动手的话先看
[quick-start.md](./quick-start.md)，要工作流看 [workflow.md](./workflow.md)。

---

## 问题：修改代码时，怎么知道什么不能被破坏？

Coding agent 的核心失败模式不是写错代码——写错可以重试。真正的问题是**静默地破坏已有代码的
隐含假设**。当 agent 改了一个函数的返回格式，项目里其他依赖这个格式的模块可能悄悄坏掉，而没有
任何机制告诉 agent 这些依赖存在，也没有任何机制在破坏发生时拦住它。

## 核心想法：把隐含依赖变成显式保证

代码之间的依赖本质上是一组**保证（guarantee）**。模块 A 依赖模块 B，不是依赖 B 的实现细节，
而是依赖 B 的某些行为承诺——返回值的类型、格式、语义。

把这些保证从隐含变成**显式、可执行、可验证**，就能：

- 每次修改时，机械地验证所有保证是否仍成立；
- 某个保证被打破时，精确知道是哪条、谁依赖它；
- **正确性的判定从「AI 觉得自己改对了」变成「所有被依赖的保证仍通过」**——一个可机械验证的
  布尔条件。

![无 GBC vs 有 GBC](../assets/workflow-comparison.svg)

---

## 架构

![GBC 架构](../assets/architecture.svg)

### 三条设计原则

1. **源码零侵入**：所有元数据存在目标项目的 `.gbc/` 目录下，不改源代码、不加装饰器/注解。
2. **测试文件用户自管**：GBC 不生成、不存储、不管理测试文件本身。你在自己项目里用自己喜欢的
   方式组织测试；GBC 只**记录哪些测试对应哪些保证、运行它们、汇总结果**。
3. **语言无关**：通过 executor 配置支持任何语言和测试框架。

---

## 两层契约

GBC 用两层契约锁定变更影响：

1. **意图层（Intent）**：存于 `.gbc/**/gbc.md`。用自然语言（Markdown）定义文件夹的职责、
   内部约束和架构意图。它是「真理之源」，告诉 agent「你在这里该做什么、不该做什么」。由**人类
   持有**，agent 只起草。
2. **行为层（Guarantee）**：存于 `.gbc/**/*.json`。可执行、被测试覆盖的具体行为承诺。

改代码时，agent 必须同时遵守意图层（不违背初衷）和行为层（不破坏具体功能）。

意图文档怎么写（三段式：意图 / 内部约束 / 文件），见 [workflow.md](./workflow.md#意图文档怎么写)。

---

## 核心术语

- **Provider**：提供保证的源文件（如 `src/llm_client/client.py`）。
- **Consumer / Dependent**：依赖某保证的文件（如 `src/conversation/manager.py`）。
- **Guarantee**：一条**具名**（id 形如 `<symbol>.<behavior>`，路径无关）的行为承诺，对应一个
  测试 + 一段描述。**多个 consumer 可共享同一条保证。**
- **Executor**：定义如何运行测试的配置（命令模板、工作目录、环境变量等）。

### 依赖边的两个层级

- **符号依赖（免费）**：只依赖签名或符号存在，无测试、无反向边。
- **具名保证依赖**：依赖具体行为。通过反向边机制**双向登记**——提供方的
  `provides[id].dependents` ⇄ 消费者的 `depends_on[].guarantees`，由工具链保证状态同步。

> 默认用免费符号依赖；**只**在依赖具体行为（而非签名）时才升级为具名保证，且懒升级。

---

## 不可破的本体不变量

无论换 CLI / MCP / 未来 GUI 哪种表面，这些引擎级不变量都不变：

- **保证是一等公民、身份是具名 id**（如 `get_config.never_none`，≠ 测试路径）。
- **多对一**：一条保证可被多个消费者共享；命中已有保证则追加 dependent 复用，不另写测试。
- **双段自包含 meta**：每个代码文件一份 `.gbc` json，`provides`（作 provider）+ `depends_on`
  （作 consumer）。
- **出生即绿（born-green）**：create / 改测试时当场跑，不过则拒绝登记——唯一的完整性不变量，
  没有后门。
- **退休保护**：仍有 dependents 的保证拒绝删除。
- **门禁二元**：跑了的测试只有过 / 挂；没跑的（heavy 跳过）响亮报告但不染红。green = 无
  failed。
- **heavy** 是成本秩（int）+ 自动运行授权：批量只跑 heavy ≤ 阈值，点名 verify 无视它。

### Meta 文件长什么样

`client.py`（provider）的 `.gbc/src/llm_client/gbc.client.py.json`：

```json
{
  "provides": {
    "chat.content_is_str": {
      "desc": "chat() 返回的 result['content'] 是 str；manager 直接用它拼接对话历史",
      "test": "tests/test_client_content_is_str.py::test_content_is_str",
      "executor": "pytest-myproject",
      "heavy": 0,
      "dependents": ["src/conversation/manager.py"]
    }
  }
}
```

`manager.py`（consumer）的 `.gbc/src/conversation/gbc.manager.py.json` 登记反向边：

```json
{
  "depends_on": [
    {
      "symbol": "src/llm_client/client.py:chat",
      "guarantees": ["chat.content_is_str"]
    }
  ]
}
```

两个方向都由工具（CLI / MCP）双向写入，你不手编。

---

## 它不是什么

GBC **不是**另一个要挑战 Cursor / Aider 的 AI 编程助手。它填补的是它们在大型复杂项目里缺失的
一环：**机器可判定的变更边界**。

- **与 Cursor / Aider 配合**：它们擅长找代码、改代码，但缺乏对跨模块依赖的显式感知，容易静默
  破坏。GBC 给它们一层「约束护栏」——改前查依赖树，改后必须跑通所有相关保证。
- **与 CI 的区别**：CI 是「事后」的，提交后才发现错误；GBC 是「准入制」的，是 agent 工作流里
  的一个门禁，错误在落地前就被拦在 agent 的上下文中。

### 和已有概念的区别

**「这不就是 Design by Contract 吗？」** 传统契约式编程是模块**自己**声明契约。GBC 的关键区别：
保证是**依赖方注册的**（"我依赖你的什么行为"来自使用者）、**带归属信息**（谁注册、为什么，
打破时可精确定位影响）、**目标是 AI agent**（提供修改边界，而非运行时检查）。

**「这不就是测试吗？」** 技术上，保证就是测试文件。区别在：**带归属**（记录谁注册、保护哪条
跨模块依赖）、**实时门控**（不是 CI 事后跑，而是 agent 改代码时的准入条件）、**用户自管**
（GBC 不管理测试文件本身，只管元数据和运行）。

---

## 局限性（诚实地说）

- **保护能力上限 = 测试质量**：GBC 只能拦测试能抓到的错误。测试只走 happy path，保证就是虚假
  安全感。（只用 happy-path 测试就是典型例子。）
- **手动登记负担**：依赖关系需 agent 或人类主动登记。单次开销小，但覆盖率随项目增长需要持续
  投入。
- **运行性能**：每次验证都真实跑测试，有一定延迟成本。
