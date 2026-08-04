# Contributing

> 语言：**简体中文** | [English](docs/en/CONTRIBUTING.md)

欢迎贡献！本文讲清怎么在本项目里安全地改代码。

## 两种安装方式：贡献 vs 只用

本项目既是 GBC 工具的实现，也是它的第一个使用者。按你的目的选安装方式：

| 目的 | 安装命令 | 说明 |
|------|----------|------|
| **贡献代码 / 跑测试** | `pip install -e .` | 可编辑安装，`import gbc` 直接命中源码——改完不用重装 |
| **只想用工具** | `pipx install .` | 不带 `-e`，装的是定格包，不会被本地源码目录干扰 |

## 搭环境（贡献者）

```bash
# 1. 测试依赖（你已有的 conda/venv）
pip install -r requirements.txt

# 2. GBC 工具本身，可编辑安装
pip install -e .
```

> **注：** 若项目目录位于某些特殊挂载文件系统上（比如 WSL 的 9p 共享盘），`pip install -e .`
> 可能因为 `chmod` 不被支持而失败（setuptools 生成 egg-info 时会调 `chmod`）。遇到这种情况，
> 先把仓库复制到普通本地文件系统路径（如 `/tmp` 或 home 目录下）再装。

## 跑测试

用 `pip install -e .` 装好后，`import gbc` 本来就该命中源码（editable 安装用 `.pth`/finder 直接映射），**在项目根里面跑 pytest 没有问题**：

```bash
cd /path/to/guarantee-based-coding
pytest tests/
```

> GBC 默认项目根优先级为 `GBC_PROJECT_ROOT` > 进程启动时的 cwd，不会向上搜索。本仓测试通过
> `set_current_project()` 显式注入临时项目根。

## 工作流

遵循本项目的 `.gbc` 意图文档。

核心节奏：
1. **规划** — 读相关 `.gbc/**/gbc.md`，弄清改动影响范围
2. **意图先行** — 需求 → 起草 gbc.md 变更 → 人类审批 → `gbc doc` 落库
3. **实现** — 写代码 → 写窄测试 → `gbc guarantee create` 登记 → `gbc verify` 自证
4. **验收** — 顶层 `gbc verify` 跑受影响的保证

绝不手编 `.gbc/**/*.json` 或 `.gbc/**/gbc.md`。

## 保证登记规范

- id 格式：`<symbol>.<behavior>`（如 `get_config.never_none`）
- 测试写窄：断言行为承诺（非空 / 类型 / 抛异常），不校验实现细节
- 出生即绿：`create_guarantee` 当场跑测试，不过拒绝登记

## 提交

- 提交信息用中文或英文均可
- 大的重构分步提交，保持每步可独立回滚
- 动了保证图或意图文档的提交，在 body 里写清影响范围
