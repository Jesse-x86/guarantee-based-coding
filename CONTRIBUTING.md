# Contributing

> 语言：**简体中文** | [English](docs/en/CONTRIBUTING.md)

欢迎贡献！本文讲清怎么在本项目里安全地改代码。

## 特殊之处：GBC 自己吃自己的狗粮

本项目既是 GBC 工具的实现，也是它的第一个使用者。你的开发环境需要**两套隔离的 Python 环境**：

| 用途 | 环境 | 说明 |
|------|------|------|
| **跑测试 / 写代码** | conda / venv（你自己管理）| 装 `requirements.txt` 的依赖 |
| **调 GBC 工具** | pipx | `pipx install .` 冻结工具本身 |

**为什么分开？** 改源码时，你手里的 `gbc` 命令必须来自安装版——改坏代码不会炸掉自己脚下的梯子。

## 搭环境

```bash
# 1. 测试环境（你已有的 conda/venv）
pip install -r requirements.txt

# 2. GBC 工具本身（pipx 隔离安装）
pipx install -e .    # 开发时从源码安装（--editable 仍经 pipx venv）
```

## 跑测试

**关键：不能从项目根跑。** 否则 `import gbc` 命中源码而非安装版，测试跑的不是你要验证的那个包。

```bash
# 正确方式：从项目根外面跑
cd /tmp
GBC_PROJECT_PATH=/path/to/guarantee-based-coding \
  pytest /path/to/guarantee-based-coding/tests/
```

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
