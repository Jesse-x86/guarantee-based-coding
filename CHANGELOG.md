# Changelog

> 中文 / English

## 0.4.1 (未发布 / Unreleased)

### 验证与修复 / Verification and fixes

- 新增 `gbc verify all` 与 MCP `verify_all` 全项目验收入口：运行全部启用保证（含 heavy），失败、停用、缺失结果或零执行均导致验收失败。
  Added CLI and MCP whole-project verification: run every enabled guarantee, including heavy ones, and fail on failed or disabled guarantees, missing results, or zero executions.
- 同一次全项目验证合并等价的测试执行，保留每条保证的结果，并分别报告保证执行数与实际测试运行数。
  Deduplicated equivalent test executions within each whole-project verification while preserving per-guarantee results and reporting guarantee counts separately from test runs.
- 修复 Windows 非 UTF-8 locale 下测试输出解码失败的问题；子进程输出采用 UTF-8 解码，非法字节以转义形式保留。
  Fixed test-output decoding under non-UTF-8 Windows locales with UTF-8 decoding and escaped invalid bytes.
- 明确报告零执行、跳过与停用的检查；工作流区分开发期定向测试与最终 GBC 验收，允许未登记测试先获得失败反馈。
  Clarified zero-execution, skipped, and disabled checks; separated targeted development feedback from final GBC acceptance, including failing tests before registration.

### 文档 / Documentation

- 重排中英文 README：先说明 AI 修改中的连带破坏，再介绍工作方式、与 ADR / AGENTS.md / 测试 / CI 的关系及上手入口。
  Reorganized both READMEs around unintended regressions during AI edits, followed by the workflow, comparisons with ADRs / AGENTS.md / tests / CI, and onboarding.
- 将旧 demo 的案例思路改编为双语阅读指南，展示职责漂移、真实消费者回归、测试覆盖不足和登记时验证；旧演示保留为历史资料。
  Adapted the retired demo into bilingual walkthroughs covering responsibility drift, an actual consumer regression, insufficient test coverage, and checks at registration; old demos remain historical material.
- 修正核心概念中对 CI、保证身份和验证能力的表述。案例页为仓库文档，离线手册仍保留五个主题；上述文档调整不改变运行接口。
  Corrected the concepts manual's descriptions of CI, guarantee identity, and verification limits. Walkthroughs are repository documents; the offline manual retains five topics. These documentation edits introduce no runtime interface changes.
- 统一中英文快速开始中的执行器作用域说明：配置及名称属于目标项目。
  Corrected both quick-start guides: executor configuration and names are scoped to the target project.

验证范围与结果见 [0.4.1 validation](docs/development/0.4.1-validation.md)。未打包或发布。
See [0.4.1 validation](docs/development/0.4.1-validation.md) for checks and limitations. Not built or published.

## 0.4.0 (2026-09-23)

### 新增与调整 / Added and changed

- 新增 `gbc-workflow` skill，通用于 MCP / CLI：先调查证据再起草意图，只询问实质未决选择；按消费者行为设计窄测试；复用术语与重要决策理由。`gbc-cli` 保留为命令适配器。
  Added the transport-neutral `gbc-workflow` skill for evidence-first intent drafting, consequential questions, consumer behavior tests, and vocabulary/decision reuse; `gbc-cli` remains the command adapter.
- 中英文手册及接入 / 规则指南同步：精确值属于契约时应精确断言；区分目标缺陷辨识力、mock 自证与环境故障；保留现有审批权限、免费符号依赖和 born-green，不强制所有测试先红或新增 ADR / CONTEXT 文件。
  Updated bilingual manuals and setup/rules guidance: assert exact values when contractual, distinguish defect sensitivity from mock-only or environment failures, and preserve existing authority, free symbol dependencies, and born-green without mandatory red-first or new ADR / CONTEXT files.
- 选择性借鉴 Matt Pocock 的 grilling / tdd / domain-modeling，来源和 GBC 的调整边界见工作流文档；不新增外部运行依赖、命令、手册主题或数据协议。
  Selectively adapted ideas from Matt Pocock's grilling / tdd / domain-modeling; attribution and GBC-specific boundaries are in the workflow manual. No new external runtime dependencies, commands, manual topics, or data schema.

验证证据与限制见 [0.4.0 validation](docs/development/0.4.0-validation.md)。
Validation evidence and limitations are recorded in [0.4.0 validation](docs/development/0.4.0-validation.md).

## 0.3.0 (2026-09-23)

### 不兼容变更 / Breaking changes

- 项目架构意图从 `gbc doc` 改为 `gbc intent`，八个 MCP 意图工具从 `doc_*` 改为 `intent_*`；不保留旧兼容别名。请更新脚本与 agent 指令。
  Project intent moves from `gbc doc` to `gbc intent`; the eight MCP intent tools move from `doc_*` to `intent_*`, without compatibility aliases. Update scripts and agent instructions.
- CLI 全树渲染改用 `gbc tree show`；`gbc tree` 仅显示浏览帮助。MCP `tree()` 无参数仍可渲染全树。
  CLI tree rendering uses `gbc tree show`; `gbc tree` displays browsing help. MCP `tree()` still renders the full tree without arguments.

### 新增 / Added

- `tree show` 支持目录与深度；`tree folders` 浏览目录意图和约束；`tree for` 合并目标文件的修改上下文，对应 MCP `tree` 与 `tree_for`。
  Folder/depth browsing in `tree show`, intent/constraint browsing in `tree folders`, and combined modification context in `tree for`, exposed through MCP `tree` and `tree_for`.
- `gbc doc list/read/search` 与 MCP `doc_list/doc_read/doc_search` 离线查询随版本附带的中英文手册：quick-start、concepts、workflow、reference、onboarding-agent。`--help` 继续负责简短语法。
  Offline versioned English/Chinese manuals through `gbc doc list/read/search` and MCP `doc_list/doc_read/doc_search`, with five fixed topics. `--help` remains short syntax help.
- 手册以 `docs/` 为单源，构建时收入包资源；支持从 sdist 构建 wheel，安装后无需仓库或目标项目。
  Manuals have a single source in `docs/`, copied into package resources during builds, including wheels built from sdists; installed queries need no checkout or target project.

## 0.2.3 (2026-09-23)

本版本保持 0.2.2 的命令结构，`gbc tree` 与 `gbc doc` 不改名。
This release preserves the 0.2.2 command structure; `gbc tree` and `gbc doc` retain their names.

### 修复 / Fixed

- 同一 consumer 的多个 symbol 依赖同一 provider 的同一保证时，删除其中一条依赖仍保留其余依赖所需的反向记录和保证退休保护。
  When multiple symbols in one consumer depend on the same guarantee from the same provider, removing one dependency preserves the reverse record and guarantee retirement protection required by the remaining dependencies.
- `gbc verify single`、`gbc verify provider` 验证失败，以及 `gbc doctor check` 发现一致性错误时，CLI 返回非零退出码。
  The CLI now returns a nonzero exit code when `gbc verify single` or `gbc verify provider` fails, or when `gbc doctor check` finds consistency errors.

## 0.2.2

### 新增 / Added

- 重做意图编辑器：模块化原生前端、中英 i18n、文件夹与文件一等节点，以及文件保证/依赖的只读接口视图。
  Rebuilt the intent editor with a modular native frontend, zh/en i18n, first-class folder/file nodes, and a read-only guarantee/dependency interface view.
- 新增当前内存、加载快照、硬盘状态三态 diff，可复制或下载为 LLM 可读文本。
  Added three-way intent diff views for current memory, loaded snapshot, and disk state, exportable as LLM-readable text.

### 修复 / Fixed

- 保存改为冲突感知的字段级三方合并与选择性写盘：只写变化的 gbc.md，保留无关外部改动，并关闭旧的整树盲写 HTTP 入口。
  Saving now uses conflict-aware field-level three-way merging and selective writes, preserving unrelated external edits and disabling the legacy blind whole-tree HTTP write endpoint.
- 文件元数据只读接口增加语义路径校验，防止路径穿越读取。
  Added semantic-path validation to the read-only file metadata endpoint to prevent path traversal.

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
