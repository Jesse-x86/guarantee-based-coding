# TODO

## 0.2.3：修复发布

- [ ] 发布共享保证依赖修复与 CLI 门禁退出码修复；本版本仅包含这两项修复。

## 0.3.0：命令职责与查询能力

- [ ] 发布新的 `tree show` / `tree folders` / `tree for` 及对应 MCP 能力：实现已提交，尚未发布，等待随 0.3.0 发布。
- [ ] 将 `gbc.md` 架构意图的读写入口从 `gbc doc` 改为 `gbc intent`；CLI 与 MCP 命名保持一致，不保留旧兼容别名，并同步相关 skills 与文档。
- [ ] 将 `gbc doc` 用于 GBC 说明文档查询；具体查询行为与实现设计仍待细化。
  - `--help` 继续提供简短的命令用法。
  - 不采用 `gbc map` 命名。

## 0.3.x：按实际问题修复

- [ ] 根据 0.3.0 发布后的实际问题安排修复版本。

## 0.4.0 候选：Matt Pocock skills 借鉴

以下保留为 0.4.0 候选待办，尚未授权实现；先通过真实任务验证，再决定具体方案与是否纳入版本。

- [ ] 完善意图起草流程：先调查可查事实，识别影响方案的未决问题及决策依赖，再给出推荐判断；不对每个实现细节强制追问。产出衔接现有 `gbc.md`。
- [ ] 提高保证编写质量：明确 consumer 依赖的行为和公共接口测试边界；在适用场景验证测试能因目标错误变红，再修复至绿。出生即绿不等于测试有辨识力，优先完善 skill / 流程，不预设修改保证数据协议，也不要求所有测试强制先红。
- [ ] 完善领域术语与设计理由记录：复用已有词汇表 / ADR，消除歧义、明确边界场景、记录重要取舍；`gbc.md` 保留当前职责与约束，不塞入讨论历史。

实施前先用真实任务验证候选流程的效果，再决定是否需要模型 / 接口变更，不预设引擎重构。不复制整套 Matt 流程，不引入依赖或安装。

一手参考：[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)、[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)、[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)。
