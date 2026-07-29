# GBC Interactive Demo (for Agents)

> 英文平行版 → [`EXAMPLE_EN.md`](./EXAMPLE_EN.md)（`config-service-en` / `*-en` 剧本）

**你是人类** → 把本文交给你的 coding agent，对它说："按这个走一遍，每步停一下解释给我听。"

**你是 agent** → 你好！你的任务是用 GBC 工具做一次交互式演示，让人类看到它怎么工作。
三步场景：强测试拦截破坏 → 弱测试没拦住 → 错误测试被出生即绿拒绝。
每做完一步停下来解释，等人类确认再继续。

## 前置：确保 GBC 可用

先确认 GBC 的 MCP server 已经接入了。如果还没有：

1. 人类已经 clone 了 `guarantee-based-coding` 仓。找它。
2. `pip install -r requirements.txt`（装进合适的 Python 环境）。
3. 用 `gbc mcp up <项目根>` 启动 MCP server（Python 用上一步的环境），然后在 `.mcp.json` 中注册。

> 详细说明见 [docs/zh/onboarding-agent.md](../docs/zh/onboarding-agent.md)。

你需要这些 MCP 工具：`create_guarantee`、`add_dependency`、`verify_provider`、`upsert_executor`。

演示素材：
- 项目源码（只读，不要修改）：`demo/projects/config-service/`
- 测试文件（只读）：`demo/scenarios/<name>/tests/`

## Workspace 管理

演示**不会**直接操作 `demo/` 下的源文件——那些是只读的模板。每一步都在一个独立的 workspace 里进行。

你自己选一个合适的位置作为 workspace（比如本仓的 `demo/workspace/` 或系统临时目录），按下面的规则操作：

- **第一轮（第二步）开始前**：创建 workspace 目录，从 `demo/projects/config-service/` **复制** `config_loader.py` 和 `server.py` 到 workspace 根目录。从 `demo/scenarios/config-service-strong/tests/` **复制** `test_never_none.py` 到 `workspace/tests/`（手动建目录）。
- **第二轮（第三步）开始前**：**清空**整个 workspace，重新复制源码（同上），但测试文件改为从 `demo/scenarios/config-service-weak/tests/` 复制。
- **第三轮（第四步）开始前**：**清空** workspace，重新复制源码（同上），测试文件改为从 `demo/scenarios/config-service-bad-test/tests/` 复制。

> ⚠️ 所有源文件都是**复制**进来的，不要移动——`demo/` 下的模板文件必须保持原样不动。

---

## 第一步：带人类看代码

打开 `config_loader.py`，向人类解释：

> `get_config(key)` 保证永远返回 str——找不到 key 时返回 `""`，不是 `None`。
> 第 21 行的 `.get(key, "")` 就是这条承诺。

打开 `server.py`：

> 下游 `int(get_config("port"))` 信任它永不为 None。如果某天违约返回 None，`int(None)` → TypeError。

**等人类确认看懂了。**

---

## 第二步：强测试 — 门禁拦截（核心演示）

用 `demo/scenarios/config-service-strong/tests/test_never_none.py`。

打开这个测试文件，向人类解释：

> 两条断言：`get_config("port")` 不为 None **且** `get_config("nonexistent")` 也不为 None。
> 第二条覆盖了 edge path——这就是"强"的地方。

然后操作：

1. **注册 executor**：`upsert_executor`，config_name=`demo-pytest`。command 用当前 Python 的 `-m pytest {file} -x -q`，cwd 和 PYTHONPATH 指向 workspace。

2. **登记保证**：`create_guarantee`，provider=`config_loader.py`，id=`config_loader.get_config.never_none`，用刚复制的测试文件。**这步会当场跑测试——把 PASS 展示出来，解释"出生即绿"。**

3. **登记依赖**：`add_dependency`，consumer=`server.py`，provider=`config_loader.py`，symbol=`get_config`，guarantee_id=`config_loader.get_config.never_none`。

4. **初始验证**：`verify_provider config_loader.py` → 应该 **GREEN**。解释："所有保证通过，代码健康。"

5. **模拟破坏**：把 `config_loader.py` 的 `.get(key, "")` 改成 `.get(key)`（删掉默认值）。**展示 diff**，解释："找不到 key 时现在返回 None——一次看起来很无害的简化。"

6. **再验证**：`verify_provider config_loader.py` → 应该 **RED**！

向人类解释：
> `get_config("nonexistent")` 现在返回 None，强测试第二条断言抓住了它。门禁亮红——在真实项目中，agent 会收到阻止信号，不会让这个改动落地。

**🎉 这就是 GBC 的核心。等人类消化完。**

---

## 第三步：弱测试 — 对比，门禁失效

清理 workspace，重新复制源码。这次用 `demo/scenarios/config-service-weak/tests/test_never_none.py`。

打开测试文件，向人类解释：

> 只有一条断言：`get_config("port")` 不为 None。没测 `get_config("nonexistent")`。
> missing key 分支完全不在测试覆盖范围内。

重复第二步的全部操作（注册 executor → 登记保证 → 登记依赖 → 初始验证 → 同样的改动 → 再验证）。

最后一步应该显示 **GREEN**——测试通过了，改动被放行！

向人类解释：
> 弱测试只测了 productive path。`get_config("port")` 永远返回 `"8080"`，测试永远过。
> 但 `get_config("nonexistent")` 已经悄悄从 `""` 变成了 `None`——只是测试不知道。
>
> **结论：GBC 的门禁能拦住的，是你测试覆盖到的边界。**

---

## 第四步（可选）：错误测试 — 出生即绿拒绝

清理 workspace，用 `demo/scenarios/config-service-bad-test/tests/test_never_none.py`（故意写错的测试——断言 `get_config("nonexistent") == "default"`，但代码返回 `""`）。

直接调 `create_guarantee`——它应该**失败**，返回 pytest 断言错误。

向人类解释：
> GBC 不仅在修改代码后拦截破坏——它在**登记时**就要求测试本身是对的。
> 一条连注册都过不了的保证，根本不可能进入系统。这是第一道防线。

---

## 结束

向人类总结三条：
1. **GBC = 把测试变成门禁**：改代码 → 跑保证 → 全绿才放行
2. **门禁的强度 = 测试的强度**：弱测试覆盖不到的边界，门禁也看不见
3. **出生即绿**：保证登记的那一刻就跑测试——坏的测试进不来

然后告诉人类：想在自己的项目里用 GBC → 把 [docs/zh/onboarding-agent.md](../docs/zh/onboarding-agent.md) 交给你就行。
