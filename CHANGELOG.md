# Changelog

> 中文 / English

## 0.2.1 (2026-08-04)

### 新增 / Added

- `GBC_PROJECT_ROOT` 环境变量：确定性指定项目根（优先级高于 cwd，不向上搜索）。
  Deterministic project-root override (`GBC_PROJECT_ROOT` > cwd, no upward search).
- `gbc lang zh|en|auto`：查看 / 设置持久语言偏好（存于 `~/.config/gbc/lang`）。
  Persistent language preference via `gbc lang` (stored in `~/.config/gbc/lang`).
- 叶子命令支持 `--project/-C` 后置项目覆盖。
  Trailing `--project/-C` project override on leaf commands.
- CLI 帮助全量 i18n 化：guarantee/dep/verify/refactor/executor 子命令的参数帮助统一走语言目录（此前为硬编码中文）。
  CLI help fully i18n-ized: leaf-command argument help now resolves through the language catalogs (previously hard-coded Chinese).
- CLI/MCP 提示点明保证边界：`gbc guarantee --help` 与 `create_guarantee`/`add_dependency`/`verify_*` 描述明确「保证 = 窄测试守护的具名行为承诺，不是全面测试；只登记你在乎且被依赖的行为，复用优先」。
  CLI/MCP surface states the guarantee boundary: guarantees are narrow-test-guarded behavioral promises, NOT full test coverage — register only what you care about and is depended on, reuse first.

### 修复 / Fixed

- 修正 agent 围栏指南：实现 subagent 应随代码维护语言/项目要求的接口产物、登记自身依赖、维护窄保证测试并自证；只限制意图修改与未授权跨范围破坏，不再一刀切屏蔽全部 GBC 修改工具。
  Corrected agent guardrails: implementation subagents maintain language/project-specific interface artifacts with code, register their own dependencies, maintain narrow guarantee tests, and self-verify; only intent changes and unauthorized cross-scope destructive operations are restricted instead of blanket-blocking all GBC mutations.
- 依赖图孤儿反向边安全清理（consumer 元数据缺失时仅凭显式 guarantee id）。
  Safe orphaned reverse-edge cleanup (provider-only removal by explicit guarantee id).
- 无 `.gbc` 图时一致性检查直接报错，杜绝空图假绿。
  Consistency checks reject a missing graph instead of reporting false green.
- `python -m gbc` 失败退出码正确传播。
  Module-entry failure exit codes are now propagated.

### 文档 / Docs

- quick-start 补充「界面语言」说明（zh/en）。
  quick-start now covers the `gbc lang` language preference (zh/en).
- rules/setup 传达正确态度：gbc.md 是现状快照不是圣旨（起草→审批→落库即正当演进，别造上帝文件）；保证≠全面测试；多与人类沟通、及时汇报。
  rules/setup now convey the right attitude: gbc.md is a snapshot, not sacred (evolve via draft→sign-off→commit, don't build god files); guarantees ≠ full coverage; communicate with the human often.
- concepts 新增「意图文档系统（gbc.md）」章节：三段可见性作用域、父子投影确定性约束、与保证层的关系（防方向漂移 vs 防行为破坏）。
  concepts gains an "intent document system (gbc.md)" section: three visibility scopes, deterministic parent/child projection, and its relation to the guarantee layer.
- 意图编辑入口统一为 `gbc doc`（MCP doc 工具 / CLI），移除废弃的 gbc-doc skill 引用；发布前文档措辞修正。
  Intent editing converges on `gbc doc` (MCP doc tools / CLI); stale gbc-doc references removed; pre-release doc wording fixes.

## 0.2.0 (2026-07-30)

### 架构重构 / Architecture

- **可分发 pip 包** / Distributable pip package：项目从源码仓库重构为标准 Python 分发包，`pip install guarantee-based-coding` 即可安装。
  Restructured from a source repo into a standard Python distribution.
- **对称双子系统** / Symmetric dual subsystems：保证引擎（guarantee/dep/verify/refactor）与意图文档（gbc doc）各自拥有完整的 CLI + MCP + base 层。
  The guarantee engine and intent docs subsystem each have a full CLI + MCP + base layer.
- **集中静态资源** / Centralized static assets：i18n catalog/texts、editor 前端、skills 统一收进 `gbc/assets/`，解决资源不进 wheel 的打包缺陷。
  All static assets consolidated under `gbc/assets/`, fixing the wheel packaging gap.

### 新增 / Added

- `gbc setup`：打印本地化接线指南（MCP 端点 / skill 文件位置），与 `gbc rules` 同构。
  Prints a localized wiring guide (MCP endpoints / skill file locations), same shape as `gbc rules`.
- `gbc doc` 全进 MCP：新增 8 个 doc 工具（show/check/set-*/sync/migrate）。
  Full doc coverage over MCP: 8 new doc tools (show/check/set-*/sync/migrate).
- 意图编辑器 web 服务 / Intent editor web service：`gbc editor up`
- 随包分发 `gbc-cli` skill：给 CLI-only agent 的操作手册。
  Bundled `gbc-cli` skill: an operations manual for CLI-only agents.
- Demo Runner：交互式演示弱/强测试门禁对比（**已废弃**，后续版本移除）。
  Interactive demo contrasting weak vs. strong test gates (**deprecated**, to be removed in a later version).

### 变更 / Changed

- 退休旧 `app/` 结构、旧 `serve.py`、旧 `tools/intent-editor`。
  Retired old `app/` structure, old `serve.py`, old `tools/intent-editor`.
- 删弃用的 `gbc init`（首次写入自动建 `.gbc`）。
  Removed deprecated `gbc init` (first write auto-creates `.gbc`).
- Demo 从仓库内嵌 workspace 重构为独立的 Runner 执行引擎（该 Runner 已于后续废弃）。
  Demo restructured from in-repo workspaces to a standalone Runner engine (the Runner was later deprecated).

## 0.1.x (2026-06 ~ 2026-07)

- 核心保证机制（具名 id、多对一、出生即绿、退休保护、反查）
  Core guarantee mechanism (named ids, many-to-one, born-green, retirement protection, reverse lookup)
- 多语言 executor 配置 / Language-agnostic executor config
- CLI + MCP 双接口 / CLI + MCP dual interface
- 意图文档子系统初版 / Initial intent-doc subsystem
- 原子文件写入 + 备份 / Atomic file writes + backups
- 中英双语文档 / Bilingual (zh/en) documentation
