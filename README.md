# Guarantee-Based Coding

**与其让 AI 更聪明地理解代码，不如让代码更笨也能被安全修改。**

**English version: [README_EN.md](./README_EN.md)**

## 问题

Coding agents（Cursor, Aider, Devin 等）的核心失败模式不是写错代码——写错可以重试。真正的问题是**静默地破坏已有代码的隐含假设**。

当 Agent A 修改了一个函数的返回格式，12 个文件夹外的另一个模块可能依赖这个格式。没有任何机制告诉 Agent A 这个依赖的存在，也没有任何机制在破坏发生时阻止它。

现有的 coding agents 主要优化的是**上下文检索和 token 效率**——怎么更快、更准确地理解代码库。但它们没有解决一个更基本的问题：

> **修改代码时，怎么知道什么不能被破坏？**

## 核心想法

代码之间的依赖关系本质上是一组**保证（guarantees）**。模块 A 依赖模块 B，不是依赖 B 的实现细节，而是依赖 B 的某些行为承诺——返回值的类型、格式、语义。

如果我们把这些保证从隐含变为**显式的、可执行的、归属明确的**，那么：

- 每次修改时，自动验证所有保证是否仍然成立
- 如果某个保证被打破，精确知道是哪个保证、谁依赖它
- 修改者必须显式声明"我知道我在打破什么"才能继续

**正确性的判定从"AI 觉得自己改对了"变成了"所有保证仍然通过"。** 这是一个可以机械验证的布尔条件，不依赖 AI 的判断。

## 它怎么工作

### 核心原则：零侵入

所有框架文件存放在独立的 `.gbc/` 目录下，代码库本身保持完全干净：

```
my-project/
├── src/                          # 你的代码，完全不被侵入
│   ├── llm_client/
│   │   └── client.py
│   └── conversation/
│       └── manager.py
│
└── .gbc/                         # 框架目录，镜像代码结构
    └── src/
        ├── llm_client/
        │   ├── design.client.py.md          # 设计稿：签名 + 行为意图
        │   ├── meta.client.py.yaml          # 元信息：依赖关系
        │   ├── guarantee.init.client.py     # 测试初始化（fixtures 等）
        │   ├── guarantee.root.client.py     # 自身正确性保证
        │   └── guarantee.1ef0a.client.py    # 外部注册的保证（hash 标识来源）
        └── conversation/
            ├── design.manager.py.md
            ├── meta.manager.py.yaml
            ├── guarantee.init.manager.py
            ├── guarantee.root.manager.py
            └── guarantee.a3b72.manager.py
```

- `.gbc/` 的目录结构**镜像** `src/` 的结构
- 每个源文件对应一组框架文件，通过文件名后缀关联
- Guarantee 文件就是标准的 **pytest** 测试文件，不引入任何新工具

### Design File 示例

```markdown
# design.client.py.md

## chat(messages: list[dict]) -> dict

向 LLM 发送对话请求，返回模型的回复。

**参数：**
- messages: OpenAI 格式的消息列表，每条消息包含 role 和 content

**返回值：**
- dict，格式为 {"role": "assistant", "content": str}

**异常：**
- LLMTimeoutError: 请求超时时抛出
- LLMAuthError: 认证失败时抛出

**设计约束：**
- 不管底层用什么模型，返回格式保持一致
- 不做任何对话历史管理，只负责单次请求
```

### Guarantee 示例

自身正确性保证：

```python
# guarantee.root.client.py

"""自身正确性保证：client.py 的基本行为契约"""

from llm_client.client import chat
import pytest

def test_returns_dict():
    result = chat([{"role": "user", "content": "hello"}])
    assert isinstance(result, dict)

def test_returns_required_keys():
    result = chat([{"role": "user", "content": "hello"}])
    assert "role" in result
    assert "content" in result

def test_timeout_raises():
    with pytest.raises(LLMTimeoutError):
        chat([{"role": "user", "content": "hello"}], timeout=0.001)
```

外部注册的保证：

```python
# guarantee.1ef0a.client.py

"""
外部保证，来源: conversation/manager.py
原因: manager 直接用 result["content"] 拼接对话历史，
      依赖返回值的 content 字段为 str 类型
"""

from llm_client.client import chat

def test_content_is_string():
    result = chat([{"role": "user", "content": "hello"}])
    assert isinstance(result["content"], str), \
        "content 必须是 str，conversation.manager 依赖此行为"
```

这些就是普通的 pytest 文件。运行保证就是 `pytest .gbc/` ——不需要学任何新东西。

### Coding Agent 的工作流

当 coding agent 需要修改 `src/llm_client/client.py` 时，它看到的上下文是：

```
1. src/llm_client/client.py                  ← 要改的代码
2. .gbc/src/llm_client/design.client.py.md   ← 设计意图和约束
3. 依赖方的 design.*.md                       ← 接口信息（不含实现）
4. 如果是重试：上次的错误信息
```

修改完成后：

```
1. 自动运行 .gbc/src/llm_client/guarantee.*.client.py
2. 全部通过 → 修改被接受
3. 有失败 →
   a) Agent 尝试修复，不破坏 guarantee
   b) 如果必须打破某个 guarantee → 显式声明，通知注册方适配
```

**上下文大小取决于当前文件的复杂度，与项目整体规模无关。** 10 个文件的项目和 100 个文件的项目，修改同一个文件时 agent 看到的上下文量是一样的。

## 和现有方案的对比

| | 上下文优化方案 (Cursor, Aider) | 完整 Agent 方案 (Devin, OpenHands) | Guarantee-Based Coding |
|---|---|---|---|
| 核心策略 | 更好地检索相关代码 | 端到端自动化 | 用约束消除对理解的依赖 |
| 正确性保证 | 无 | Agent 自我验证 | Guarantee 门控 |
| 修改影响感知 | 无 | Agent 推理（不可靠） | 显式注册 + 自动检测 |
| 上下文增长 | 随项目增长 | 随项目增长 | 随单文件复杂度增长，与项目规模无关 |
| 对代码库的侵入 | 低 | 中 | **零**（所有框架文件在 `.gbc/` 下） |

## 和已有概念的区别

**"这不就是 Design by Contract 吗？"**

传统的契约式编程（Eiffel 语言的 precondition/postcondition）是模块**自己**声明自己的契约。Guarantee-Based Coding 的关键区别是：

- **Guarantee 是依赖方注册的**，不是提供方自己写的。"我依赖你的什么行为"这个信息来自使用者，而不是作者的善意。
- **Guarantee 带有归属信息**——知道是谁注册的、为什么注册的，打破时可以精确通知。
- **设计目标是面向 AI agent 的**——为 coding agent 提供明确的修改边界，而不是为人类程序员提供运行时检查。

**"这不就是测试吗？"**

Guarantee 和普通测试的区别：

- **带归属**：每个 guarantee 知道是谁注册的、保护的是什么跨模块依赖
- **修改时门控**：不是事后在 CI 里跑的，而是在 agent 修改代码时**实时触发**的准入条件
- **语义明确**：每个 guarantee 只验证一个具体的行为承诺，不是笼统的"这个功能能用"

技术上，guarantee 就是 pytest 测试。概念上，它是一套**面向 AI agent 的、带归属的、实时门控的行为契约系统**。

## 当前状态

🚧 **早期阶段** — 核心架构设计中，完整实现 coming soon。

- [ ] 核心架构设计文档
- [ ] guarantee 注册和运行机制
- [ ] design file 生成工具
- [ ] coding agent 集成（与现有 agent 对接）
- [ ] 示例项目：LLM Chatbot
- [ ] benchmark 和评估

## 联系

如果你对这个方向感兴趣，欢迎 star、issue 或者直接联系我。
