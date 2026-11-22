# 用两个例子看懂 GBC

[English](../en/walkthrough.md) · [返回 README](../../README.md) · [快速开始](quick-start.md)

AI 修改代码时，既可能把职责放错地方，也可能破坏其他模块依赖的行为。
这两个例子分别展示 GBC 的意图层和保证层如何帮助一次修改。
无需安装或运行旧 demo；以下是独立的教学示例，不是一次 agent 实测的运行记录。

## 例一：功能跑通了，职责却漂移了

需求很简单：**让模型客户端用 API Key 发起请求。**

项目已经约定：

| 位置 | 当前职责和约束 |
|---|---|
| `config/` | 读取并校验配置，包括密钥；不发起模型调用 |
| `llm_client/` | 负责模型请求；从调用方接收密钥，不读取配置 |
| 调用方 | 组装配置和客户端，发起业务操作 |

直接在客户端加入下面的代码，可能让功能正常工作：

```python
# llm_client/client.py — 违反上述职责约定的改法
import os

def chat(prompt):
    api_key = os.environ["MODEL_API_KEY"]
    return send_request(prompt, api_key=api_key)
```

`send_request` 代表项目已有的请求函数。问题不是环境变量读取本身，而是配置读取被放进了
只负责模型请求的模块。只检查“请求能否成功”的测试，未必能发现这种职责漂移。

### 修改前，查清相关的职责

在 GBC 中，上表的设计存于对应目录的意图文档，并通过 `gbc intent` 工具维护。
agent 可以围绕目标文件查询上下文：

```bash
gbc tree for llm_client/client.py config/settings.py
```

该查询提供目标文件的祖先意图、文件角色、直接依赖和保证上下文，不会运行测试。
文档按代码位置组织，局部任务可以只读相关部分。

遵循已有边界的修改是：由配置模块加载密钥，客户端接收参数，调用方将两者连接起来。

```python
# config/settings.py
import os

def load_api_key():
    return os.environ["MODEL_API_KEY"]

# llm_client/client.py
def chat(prompt, api_key):
    return send_request(prompt, api_key=api_key)
```

这只是职责分配片段，省略了项目自己的校验和请求实现。
完成调用方接线与相关测试后，再验证本次修改涉及的保证。
一个 agent 或多个 agent 都可以完成这个任务，分工方式不改变契约。

**GBC 在这里提供的是修改前可查询的设计依据。** 意图文档记录当前职责与约束；ADR 可以记录
为何选择这种设计。自然语言意图不会自动阻止错误代码，也不能由意图一致性检查证明已经实现。
若确实需要改变职责，应先协调相应设计变更，再通过意图工具维护当前契约。

## 例二：简化了一行，弄坏了另一个模块

这次看一个完整的行为依赖。配置模块约定：**缺失键返回空字符串，已有键保留其字符串值。**

```python
# config_loader.py
def get_config(config, key):
    return config.get(key, "")
```

界面模块依赖这个行为，对可选标题直接去掉首尾空白：

```python
# display.py
from config_loader import get_config

def display_title(config):
    return get_config(config, "title").strip() or "Untitled"
```

当配置为空时，`get_config({}, "title")` 返回 `""`，界面正常显示 `"Untitled"`。
这里真正被依赖的是缺失配置的处理方式，不只是函数名或参数列表。

### 把承诺、消费者和检查连接起来

项目用自己的测试保护这项行为：

```python
# tests/test_config.py
from config_loader import get_config

def test_string_values_and_missing_default():
    assert get_config({"title": "  Hello  "}, "title") == "  Hello  "
    assert get_config({}, "title") == ""
```

精确值是这份契约的一部分，因此测试检查实际返回值。
假设已按[快速开始](quick-start.md)为这个示例项目配置名为 `pytest-example` 的执行器，
通过 CLI 登记（MCP 也提供对应工具）：

```bash
gbc guarantee create config_loader.py get_config.string_values_and_missing_default tests/test_config.py::test_string_values_and_missing_default pytest-example "Preserve configured strings; return an empty string for missing keys."
gbc dep add display.py config_loader.py get_config -g get_config.string_values_and_missing_default
```

第一步当场运行测试，通过后登记保证。第二步记录 `display.py` 依赖这条保证。
此后围绕 `config_loader.py` 查询上下文，就能看到它提供的承诺和已登记的消费者。
其他消费者可以复用同一条保证，无需各自重复登记相同承诺。

### 同一个改动，两处可观察结果

现在 agent 为了“简化”代码，移除了默认值：

```diff
- return config.get(key, "")
+ return config.get(key)
```

已有标题仍能正常读取，缺失标题时却变成了 `None`：

| 检查 | 修改前 | 修改后 |
|---|---|---|
| `get_config({}, "title")` | `""` | `None` |
| `display_title({})` | `"Untitled"` | `.strip()` 抛出 `AttributeError` |
| 缺失键断言 | 通过 | 失败 |

agent 在当前任务里运行：

```bash
gbc verify provider config_loader.py
```

登记的测试会因第二条断言失败而报错。GBC 提供失败的保证与测试结果，并维护可查询的消费者
关系；agent 据此恢复契约，或协调被依赖行为的变更，再验证。这些结果来自显式查询和运行，
不是后台自动监视，也不是 GBC 自己修复代码。

### 如果测试只检查已有键呢？

假设登记时关联的是下面这个测试：

```python
def test_existing_key_only():
    assert get_config({"title": "Hello"}, "title") == "Hello"
```

同样的破坏发生后，它仍然通过，而 `display_title({})` 仍然会出错。
这个测试能检查已有键，却不足以支撑“缺失键返回空字符串”的承诺。
GBC 不会从保证描述中自动推导出缺失的断言；测试和契约变更需要审查。

### 登记时运行测试，说明了什么？

若测试要求 `get_config({}, "title") == "default"`，原始实现就无法通过。
正常启用保证的创建会被拒绝，这就是“出生即绿”：不把当前检查已经失败的行为登记为可依赖的保证。

它不证明测试要求正确或充分。开发时仍可先写失败测试，再实现到通过，最后正式登记；
无需为了这种开发反馈创建停用的占位保证。

## 带回自己的项目

先选择一个真实的修改范围：查清已有职责，找出实际被依赖的行为，复用或登记相应保证，
在修改过程中验证并修正。是否强制阻止提交或合并，取决于项目的接入与权限设置。

- [快速开始](quick-start.md)：安装、接入 agent、冒烟验证。
- [核心概念](concepts.md)：数据关系、与 ADR / AGENTS.md / CI 的区别及能力边界。
- [工作流](workflow.md)：如何维护意图、设计窄测试和完成最终验收。

这页改编自已废弃 demo 的案例思路，修正了原配置示例的消费者路径，并省略了播放流程。
旧脚本与剧本仅保留为历史资料，不是当前上手入口。本页是仓库中的案例文档；
`gbc doc` 的离线手册仍提供 quick-start、concepts、workflow、reference、onboarding-agent 五个主题。
