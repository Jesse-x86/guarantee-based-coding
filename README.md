# Guarantee-Based Coding (GBC)

**与其让 AI 更聪明地理解代码，不如让代码更笨也能被安全修改。**

**English version: [README_EN.md](./README_EN.md)**

## 🚀 想让你的 Agent 用上 GBC?

几乎不用你动手——交给你的 coding agent 就好。先看你是谁:

- **你是人类** → [docs/for-humans.md](./docs/for-humans.md)
- **你是 agent** → [docs/for-agents.md](./docs/for-agents.md)

想亲自动手、或弄清每一步:[docs/manual.md](./docs/manual.md)(手动 / 详细文档)。

## 问题

Coding agents（Cursor, Aider, Devin 等）的核心失败模式不是写错代码——写错可以重试。真正的问题是**静默地破坏已有代码的隐含假设**。

当 Agent 修改了一个函数的返回格式，项目中其他依赖这个格式的模块可能会悄悄坏掉。没有任何机制告诉 Agent 这些依赖的存在，也没有任何机制在破坏发生时阻止它。

现有的 coding agents 主要优化的是上下文检索和 token 效率。但它们没有解决一个更基本的问题：

> **修改代码时，怎么知道什么不能被破坏？**

## 核心想法

代码之间的依赖关系本质上是一组**保证（guarantees）**。模块 A 依赖模块 B，不是依赖 B 的实现细节，而是依赖 B 的某些行为承诺——返回值的类型、格式、语义。

如果我们把这些保证从隐含变为**显式的、可执行的、可验证的**，那么：

- 每次修改时，自动验证所有保证是否仍然成立
- 如果某个保证被打破，精确知道是哪个保证、谁依赖它
- **正确性的判定从"AI 觉得自己改对了"变成"所有保证仍然通过"**——一个可以机械验证的布尔条件

## 它怎么工作

### 设计原则

1. **零侵入**：所有元数据存放在 `.gbc/` 目录下，代码库本身保持干净
2. **测试文件由用户管理**：GBC 不生成、不存储、不管理测试文件本身。用户在自己的项目目录里用自己喜欢的方式组织测试文件。GBC 只负责**记录哪些测试文件是哪些保证、运行它们、汇总结果**
3. **语言无关**：通过 executor 配置支持任何语言和测试框架

### 目录结构

```
my-project/
├── src/                                    # 你的代码
│   ├── llm_client/
│   │   └── client.py
│   └── conversation/
│       └── manager.py
│
├── tests/                                  # 你的测试文件，你自己管理
│   ├── test_client_returns_dict.py
│   ├── test_client_content_is_str.py
│   └── ...
│
└── .gbc/                                   # GBC 元数据目录（自动生成）
    └── src/
        └── llm_client/
            └── gbc.client.py.json          # client.py 的保证注册信息
```

### 核心概念

- **Provider**：提供保证的源文件（如 `src/llm_client/client.py`）
- **Consumer / Dependent**：依赖某保证的文件（如 `src/conversation/manager.py`）
- **Guarantee**：一条**具名**（全局唯一 id）的行为承诺，对应一个测试 + 一段描述；**多个 consumer 可共享同一条保证**
- **Executor**：定义如何运行测试的配置（命令模板、工作目录、环境变量等）

依赖边有两级:免费的**符号依赖**（依赖签名/符号存在）与**具名保证依赖**（依赖具体行为）。后者**双向登记**——provider 的 `provides[id].dependents` ⇄ consumer 的 `depends_on[].guarantees`，由工具兜底同步。

### Meta 文件示例

每个源文件可有一个同名 `.json`，记两件事:它**提供**了哪些保证（`provides`）、它**依赖**了谁（`depends_on`）。

`client.py`（provider）的 `.gbc/src/llm_client/gbc.client.py.json`：

```json
{
    "provides": {
        "llm_client.client.chat.content_is_str": {
            "desc": "chat() 返回的 result['content'] 是 str；manager 直接用它拼接对话历史",
            "test": "tests/test_client_content_is_str.py::test_content_is_str",
            "executor": "pytest",
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
            "guarantees": ["llm_client.client.chat.content_is_str"]
        }
    ]
}
```

保证 id 全局唯一（`<点分路径>.<符号>.<行为>`）；两个方向都由工具（CLI/MCP）双向写入，你不手编。

### Executor 配置示例

Executor 定义了如何运行测试。`{file}` 是占位符，运行时替换为 guarantee 的测试文件路径：

```json
{
    "executors": {
        "pytest": {
            "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],
            "cwd": "/path/to/my-project",
            "timeout": 30,
            "env_ops": [
                {"key": "PYTHONPATH", "action": "prepend", "value": "/path/to/my-project/src"}
            ]
        },
        "jest": {
            "command": ["npx", "jest", "{file}"],
            "cwd": "/path/to/my-project",
            "timeout": 30,
            "env_ops": null
        }
    }
}
```

支持的环境变量操作：`set`、`append`、`prepend`、`remove`。

### 工作流程

```
修改 client.py
       │
       ▼
verify_provider(src/llm_client/client.py)
       │
       ├── 运行 tests/test_client_content_is_str.py  (for manager.py)
       ├── 运行 tests/test_client_returns_dict.py     (for handler.py)
       │
       ▼
  全部通过 → 修改安全
  有失败   → 精确报告：哪个保证失败、谁依赖它、为什么
```

### 与 Coding Agent 的集成

GBC 提供两组集成点，CLI 与 MCP 皆可：

- **修改前**：`list_provides` / `list_depends_on` / `who_depends_on` — agent 了解文件有哪些保证、依赖了谁、谁依赖它
- **登记**：`add_dependency` / `create_guarantee` — 把"我依赖你的某行为"显式登记（具名保证出生即跑测）
- **修改后**：`verify_provider` / `verify_guarantee` — 运行保证，门控修改是否可接受

上下文大小取决于当前文件的 guarantee 数量，**与项目整体规模无关**。

GBC 同时提供 **CLI 和 MCP** 两种接口；并给出一套**推荐的 agent 工作流**——把 [docs/for-agents.md](./docs/for-agents.md) 交给你的 agent 即可上手。

## 🎬 演示

项目内置了一个交互式 Demo Runner，用真实的 GBC 门禁演示「弱测试 vs 强测试」的对比效果：

```bash
pip install -r demo/requirements.txt
python demo/run_demo.py
```

弹出菜单后选择要运行的剧本：

| 剧本 | 演示什么 |
|------|----------|
| `config-service-bad-test` | **出生即绿拒之门外**——测试有 bug，登记时当场被拒 |
| `config-service-strong` | **门禁成功拦截**——强测试覆盖所有路径，改坏后亮 RED |
| `config-service-weak` | **门禁没拦住**——弱测试只测一条路径，改坏后仍是 GREEN |

每个剧本会逐步展示：源码 → 测试代码 → 登记保证 → 模拟破坏性修改 → 门禁结果，全部是真实执行（Runner 通过 MCP 启动 GBC server 真正跑 pytest）。

详见 [demo/](./demo/) 目录。

## 和现有方案的对比

| | 上下文优化方案 (Cursor, Aider) | 完整 Agent 方案 (Devin, OpenHands) | GBC |
|---|---|---|---|
| 核心策略 | 更好地检索相关代码 | 端到端自动化 | 用约束消除对理解的依赖 |
| 正确性保证 | 无 | Agent 自我验证 | Guarantee 门控 |
| 修改影响感知 | 无 | Agent 推理（不可靠） | 显式注册 + 自动检测 |
| 上下文增长 | 随项目增长 | 随项目增长 | 随单文件保证数增长，与项目规模无关 |
| 对代码库的侵入 | 低 | 中 | **零** |
| 语言绑定 | 通常绑定 | 通常绑定 | 语言无关 |

## 和已有概念的区别

**"这不就是 Design by Contract 吗？"**

传统契约式编程是模块**自己**声明自己的契约。GBC 的关键区别是：

- **Guarantee 是依赖方注册的**——"我依赖你的什么行为"来自使用者，不是提供者
- **带归属信息**——知道是谁注册的、为什么，打破时可以精确定位影响范围
- **设计目标是 AI agent**——为 coding agent 提供修改边界，而非运行时检查

**"这不就是测试吗？"**

技术上，guarantee 就是测试文件。概念上的区别：

- **带归属**：每条 guarantee 记录了谁注册的、保护的是什么跨模块依赖
- **实时门控**：不是 CI 里事后跑的，而是 agent 修改代码时的准入条件
- **用户自管**：GBC 不管理测试文件本身，只管理元数据和运行

## 路线图

🚧 **当前：Python 原型验证**

- [x] 核心保证注册 / 验证 / 更新 / 注销机制（具名保证 id、多对一、退休保护、反查）
- [x] 多语言 executor 配置
- [x] 原子文件写入 + 备份机制
- [x] CLI 接口
- [x] MCP 接口
- [x] Demo Runner（交互式演示系统，对比弱测试 vs 强测试的门禁效果）
- [x] 使用文档（[docs/](./docs/)）
- [ ] 完整测试覆盖
- [ ] **TypeScript 重写**，发布到 npm

## 联系

如果你对这个方向感兴趣，欢迎 star、issue 或者直接联系我。