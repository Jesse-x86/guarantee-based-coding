# TODO

## 0.4.1：源码发布分支

- [x] 准备本地 `release/0.4.1` 分支：包含现有开发版修复、README 叙事与双语案例，版本号为 `0.4.1`。
- [x] 完成全项目 GBC 源码验证：54 条保证通过，50 次实际测试运行；失败、停用、缺失结果均为 0。文档与案例复核见[验证记录](docs/development/0.4.1-validation.md)。
- [ ] 按后续授权推送分支及完成 GitHub 合并或发布。
- [ ] 按后续授权构建发行包、完成安装后验收并发布；本轮按要求暂不打包。

## 0.2.3：修复发布

- [x] 已于 2026-09-23 发布至 PyPI：共享保证依赖修复与 CLI 门禁退出码修复；本版本仅包含这两项修复。

## 0.3.0：命令职责与查询能力

以下为 0.3.0 的实现状态；已于 2026-09-23 发布至 [PyPI](https://pypi.org/project/guarantee-based-coding/0.3.0/)。

- [x] 实现 `tree show` / `tree folders` / `tree for` 及对应 MCP 能力。
- [x] 将 `gbc.md` 架构意图的读写入口从 `gbc doc` 改为 `gbc intent`；CLI 与 MCP 命名保持一致，不保留旧兼容别名，并同步相关 skills 与文档。
- [x] 将 `gbc doc list/read/search` 用于 GBC 离线说明文档查询；MCP 提供 `doc_list/doc_read/doc_search`。
  - 固定中英文主题：quick-start、concepts、workflow、reference、onboarding-agent。
  - docs/ 为内容单源；构建收入包资源，安装后不依赖仓库或当前工作目录。
  - `--help` 继续提供简短的命令用法。
  - 不采用 `gbc map` 命名。
- [x] 已于 2026-09-23 发布 [0.3.0](https://pypi.org/project/guarantee-based-coding/0.3.0/)（含上述命令变更及不兼容迁移说明）；PyPI wheel / sdist 下载文件的 SHA-256 与本地发布记录一致。

## 0.3.x：按实际问题修复

- [ ] 根据 0.3.0 发布后的实际问题安排修复版本。

## 0.4.0：工作流改进（已授权实现）

三项方向已获授权，本次通过随包 skill 与中英文文档落地；不改引擎模型 / API。实现、验证与发布状态分别记录。

- [x] 完善意图起草流程：先调查可查事实，识别影响方案的未决问题及决策依赖，再给出推荐判断；不对每个实现细节强制追问。仅在需要时提出 `gbc.md` 增量，沿用既有审批和授权。
- [x] 提高保证编写质量：明确 consumer 依赖的行为和公共接口测试边界；在适用场景验证目标缺陷辨识力，精确值属于契约时就精确检查。出生即绿不等于测试有辨识力，不修改保证数据协议，不要求所有测试强制先红。
- [x] 完善领域术语与设计理由记录：复用已有词汇表 / ADR，消除歧义、明确边界场景、记录重要取舍；`gbc.md` 保留当前职责与约束，不塞入讨论历史，不强制新增上下文文件。
- [x] 完成三个真实请求的独立只读前向评估与共享保证历史缺陷 GREEN / RED / GREEN 回放，记录有限证据与限制，不外推普遍有效性。
- [x] 完成顶层 GBC / 构建及安装后资源验收：7 个 provider / 12 条保证通过，13 项已安装 wheel 冒烟检查通过；验证报告的最终打包副本另做 payload 一致性检查。
- [x] 已于 2026-09-23 发布 [0.4.0](https://pypi.org/project/guarantee-based-coding/0.4.0/)；PyPI wheel / sdist 下载文件的 SHA-256 与本地发布记录一致。

本次以真实项目请求和受控缺陷回放验证流程，不由结果外推全面有效性。详见
[验证记录](docs/development/0.4.0-validation.md)。不复制整套 Matt 流程，不引入外部依赖或自动安装。

一手参考：[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)、[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)、[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)。
