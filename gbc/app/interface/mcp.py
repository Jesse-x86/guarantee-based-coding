# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MCP 工具面：把 base 层的能力暴露成 agent 可调用的工具。

设计取向（相对旧版 mcp）：
  - 保证为一等公民、具名 id；依赖支持「多消费者共享同一保证」。
  - 依赖登记是双向写（consumer.depends_on ⇄ provider.dependents），由工具兜底，
    agent 不必手工在两处读写。
  - 退休保护：retire_guarantee 对仍有 dependents 的保证直接拒绝——把「别删还有人
    依赖的保证」从靠自觉变成机制兜底。
  - 反查与体检：who_depends_on / check_consistency 取代手工 grep。

所有工具返回 JSON 字符串；出错统一返回 {"error": ...}，不抛异常给 MCP 运行时。
"""

import json

from mcp.server.fastmcp import FastMCP

from . import base
from gbc.app.intent import base as intent_base
from gbc.app.models.errors import GBCError

mcp = FastMCP("gbc")


def _ok(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _err(e: Exception) -> str:
    if isinstance(e, GBCError):
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


# ======== 保证生命周期（provider 侧） ========

@mcp.tool()
def create_guarantee(
    provider: str,
    id: str,
    desc: str,
    test: str,
    executor: str,
    heavy: int = 0,
    timeout_override: int = -1,
    disabled: bool = False,
) -> str:
    """Create a new named guarantee on a provider file. Born-green: the test is run
    immediately and creation is rejected if it fails.

    A guarantee is a NAMED BEHAVIORAL PROMISE guarded by a narrow test — NOT full test
    coverage. Register only behaviors you actually care about and that are depended on;
    prefer reusing an existing guarantee over creating a new one. desc should state the
    promised behavior; test must be able to genuinely go red.

    Id convention: `<symbol>.<behavior>` (e.g. "make_game.returns_html", "store.roundtrip").
    Do NOT encode the provider path in the id — the path is already carried by the
    provider arg here and by the consumer's symbol field. Ids need only be unique
    PER provider, not globally (every lookup is keyed by (provider, id)).

    Args:
        provider: Source file that provides this guarantee (e.g. "app/config/llm.py")
        id: Semantic guarantee id `<symbol>.<behavior>`, e.g. "get_model.returns_loaded" (identity, path-free)
        desc: What behavior is promised and why it matters
        test: Test selector passed to the executor ({file} substitution), e.g. "tests/test_x.py::test_y"
        executor: Executor config name that knows how to run the test
        heavy: Cost rank; 0 runs in batch, >=1 is skipped in batch verify (and reported)
        timeout_override: Per-guarantee timeout in seconds; -1 uses executor default
        disabled: Create as a DISABLED placeholder, SKIPPING born-green — only for breaking
            circular dependencies (register the id+edge before its test can pass yet). The
            disabled guarantee is surfaced loudly by check_consistency until you enable it.
    """
    try:
        base.create_guarantee(provider, id, desc, test, executor, heavy, timeout_override, disabled)
        return "created" if not disabled else "created (disabled placeholder — enable it once the test passes)"
    except Exception as e:
        return _err(e)


@mcp.tool()
def disable_guarantee(provider: str, id: str) -> str:
    """Temporarily disable a guarantee: its id and all edges (dependents/reverse edges)
    are kept intact, but born-green and batch verify are SUSPENDED for it (not run, not
    failed — reported as skipped/disabled). Disable is NOT retire: it deletes nothing and
    touches no dependency. Use it to hold an edge across a refactor window or while a test
    is under repair: disable → fix the test → enable to re-prove born-green.

    A disabled guarantee is a hole in the born-green wall, so it stays LOUD: check_consistency
    reports it (and anything depending on it) until you enable it back.

    Args:
        provider: Source file path
        id: Guarantee id to disable
    """
    try:
        base.disable_guarantee(provider, id)
        return "disabled"
    except Exception as e:
        return _err(e)


@mcp.tool()
def enable_guarantee(provider: str, id: str) -> str:
    """Re-enable a disabled guarantee: born-green is re-run NOW, and disabled is cleared
    only if the test passes. If it fails, the guarantee STAYS disabled (enable is refused) —
    a guarantee is never silently promoted back without proof.

    Args:
        provider: Source file path
        id: Guarantee id to enable
    """
    try:
        base.enable_guarantee(provider, id)
        return "enabled"
    except Exception as e:
        return _err(e)


@mcp.tool()
def update_guarantee(
    provider: str,
    id: str,
    desc: str | None = None,
    test: str | None = None,
    executor: str | None = None,
    heavy: int | None = None,
    timeout_override: int | None = None,
) -> str:
    """Update fields of an existing guarantee. Only pass what you want to change.
    If the test/executor/timeout changes, the test is re-run (born-green is re-proven).

    Args:
        provider: Source file path
        id: Guarantee id to update
        desc/test/executor/heavy/timeout_override: New values; omit to leave unchanged
    """
    try:
        base.update_guarantee(
            provider, id,
            desc=desc, test=test, executor_name=executor,
            heavy=heavy, timeout_override=timeout_override,
        )
        return "updated"
    except Exception as e:
        return _err(e)


@mcp.tool()
def retire_guarantee(provider: str, id: str) -> str:
    """Retire (delete) a guarantee. REFUSED if it still has dependents — repair or
    migrate the dependents first. This guards against silently breaking downstream code.

    Args:
        provider: Source file path
        id: Guarantee id to retire
    """
    try:
        base.retire_guarantee(provider, id)
        return "retired"
    except Exception as e:
        return _err(e)


# ======== 依赖边（consumer 侧，双向写） ========

@mcp.tool()
def add_dependency(provider: str, consumer: str, symbol: str, guarantee_id: str | None = None) -> str:
    """Register that `consumer` depends on a `symbol` of `provider`.

    A free symbol dependency covers only the symbol's existence/signature, not its
    behavior — upgrade to a named guarantee only when you rely on concrete behavior
    (lazy upgrade). Prefer free dependencies by default.

    - guarantee_id omitted: a FREE symbol-level dependency (depends on the symbol
      existing / its signature, not on any specific behavior; no test, no reverse edge).
    - guarantee_id given: a BEHAVIOR dependency. The guarantee must already exist on the
      provider (create it first if not). The reverse edge (provider's dependents) is
      written automatically. Multiple consumers may share one guarantee.

    Args:
        provider: Source file providing the symbol
        consumer: File that depends on it
        symbol: Symbol name on the provider (e.g. "get_model"); stored as "<provider>:<symbol>"
        guarantee_id: Existing guarantee id to attach, or omit for a free symbol dependency
    """
    try:
        base.add_dependency(consumer, provider, symbol, guarantee_id)
        return "added"
    except Exception as e:
        return _err(e)


@mcp.tool()
def remove_dependency(provider: str, consumer: str, symbol: str, guarantee_id: str | None = None) -> str:
    """Remove a dependency edge (inverse of add_dependency; keeps both directions in sync).

    - guarantee_id given: detach only that guarantee from the edge.
    - guarantee_id omitted: remove the whole symbol edge and detach the consumer from
      every guarantee it carried.

    Args:
        provider: Source file path
        consumer: Dependent file path
        symbol: Symbol name on the provider
        guarantee_id: Specific guarantee to detach, or omit to remove the whole edge
    """
    try:
        base.remove_dependency(consumer, provider, symbol, guarantee_id)
        return "removed"
    except Exception as e:
        return _err(e)


# ======== Refactor / 重定位 ========

@mcp.tool()
def refactor_file(old: str, new: str, disable_guarantees: bool = True) -> str:
    """Relocate a file (or a whole directory subtree) and fix EVERY graph reference to it
    in one shot — the move primitive the dependency graph lacked.

    GBC does the structural + metadata part: moves the code file/dir + its .gbc artifacts
    (json/.pyi) with `git mv` (history preserved), rewrites all path references graph-wide
    (consumers' symbol path-prefix, providers' dependents entries), and auto-disables the
    guarantees the moved file provides (their tests break on stale imports until fixed).
    Guarantee IDS ARE NOT TOUCHED — ids are path-free (`<symbol>.<behavior>`), so a move
    never changes them. To rename ids/symbols, use refactor_func.

    Then YOU (the agent) do the content + verification part: fix imports in the moved file
    and its consumers, move/rename test files and `update_guarantee(test=...)` their
    selectors, then `enable_guarantee` each disabled id (born-green re-runs at the new path).

    The move is idempotent: if the file was already moved by hand (old gone, new present),
    GBC skips the move and just reconciles the stale graph references — so this also cleans
    up a half-finished manual relocation.

    Args:
        old: Current path of the file or directory (project-relative)
        new: Destination path
        disable_guarantees: Auto-disable guarantees under the moved path (default True; set
            False only if you know the tests still pass as-is)

    Returns: JSON report {old, new, code_move, gbc_move, refs_rewritten, disabled, next_steps}
    """
    try:
        return _ok(base.refactor_file(old, new, disable_guarantees=disable_guarantees))
    except Exception as e:
        return _err(e)


@mcp.tool()
def rename_guarantee(provider: str, old_id: str, new_id: str) -> str:
    """Rename a guarantee id (old_id -> new_id), keeping both directions consistent.

    The id lives in two places — the provider's provides key and every dependent consumer's
    `guarantees` list. This rewrites both: the provider re-keys the guarantee (its object —
    disabled flag, dependents, test — is preserved), then every consumer that depends on it
    gets old_id swapped to new_id. Pure id rename: touches no test, no symbol, no path.

    Use it to normalize legacy path-prefixed ids into path-free `<symbol>.<behavior>` form
    (e.g. "core.maker.make_game.returns_html" -> "make_game.returns_html").

    Args:
        provider: Source file that provides the guarantee
        old_id: Current guarantee id
        new_id: New guarantee id (must be free on this provider)

    Returns: JSON {provider, old_id, new_id, consumers_updated}
    """
    try:
        return _ok(base.rename_guarantee(provider, old_id, new_id))
    except Exception as e:
        return _err(e)


@mcp.tool()
def refactor_func(provider: str, old_symbol: str, new_symbol: str, disable_guarantees: bool = True) -> str:
    """Rename a symbol on a provider (old_symbol -> new_symbol) and fix every graph reference.

    GBC does the metadata part: rewrites consumers' `provider:old_symbol` dependency symbols to
    `provider:new_symbol`, renames the guarantee ids under that symbol (`old_symbol` / `old_symbol.*`
    -> `new_symbol[...]`, per the `<symbol>.<behavior>` convention, both directions), and auto-disables
    those guarantees (their tests still call the old name and would fail).

    GBC does NOT edit the symbol definition in source (that's an AST-level content edit). YOU rename
    `def old_symbol` and its call sites + tests, then `enable_guarantee` each renamed id. Paths are
    untouched; only the symbol segment of the id changes.

    Args:
        provider: Source file path
        old_symbol: Current symbol name (e.g. "make_game")
        new_symbol: New symbol name
        disable_guarantees: Auto-disable affected guarantees (default True)

    Returns: JSON {provider, old_symbol, new_symbol, symbol_refs_rewritten, ids_renamed, disabled, next_steps}
    """
    try:
        return _ok(base.refactor_func(provider, old_symbol, new_symbol, disable_guarantees=disable_guarantees))
    except Exception as e:
        return _err(e)


# ======== 读 / 反查 ========

@mcp.tool()
def list_provides(provider: str) -> str:
    """List all guarantees a provider offers, each with its dependents.

    Returns: JSON object mapping guarantee id -> guarantee object
    """
    try:
        result = base.list_provides(provider)
        return _ok({gid: g.model_dump() for gid, g in result.items()})
    except Exception as e:
        return _err(e)


@mcp.tool()
def list_depends_on(consumer: str) -> str:
    """List all dependency edges a file declares (what it depends on).

    Returns: JSON array of dependency objects ({symbol, guarantees})
    """
    try:
        result = base.list_depends_on(consumer)
        return _ok([d.model_dump() for d in result])
    except Exception as e:
        return _err(e)


@mcp.tool()
def who_depends_on(provider: str, symbol: str | None = None, guarantee_id: str | None = None) -> str:
    """Reverse lookup: who depends on this provider. Replaces ad-hoc grep.

    - guarantee_id given: O(1) read of that guarantee's dependents.
    - otherwise: global scan of every file's dependency edges pointing at this provider
      (optionally filtered to a single symbol). This is the only way to find free
      symbol-level dependents (they have no reverse edge).

    Args:
        provider: Source file path
        symbol: Optional symbol name to narrow the scan
        guarantee_id: Optional guarantee id for the fast O(1) path
    """
    try:
        return _ok(base.who_depends_on(provider, symbol=symbol, guarantee_id=guarantee_id))
    except Exception as e:
        return _err(e)


@mcp.tool()
def tree(detail: bool = False, gaps: bool = False) -> str:
    """Render the whole `.gbc` tree as one AI-readable dependency document.

    Backbone = every folder's intent / internal constraints / file entries (from
    gbc.md); each file leaf is annotated with its dependency edges (→ provider:symbol
    [guarantee]) and the guarantees it provides (⊕ guarantee ← dependents). A single
    read-only call that replaces opening many gbc.md/json files to grasp the architecture.

    detail: also expand each guarantee's desc/test/heavy, and list other artifacts
            (.pyi stubs) present in each .gbc folder (absence => interface not materialized).
    gaps:   append a "registration gaps" section — purely graph-derived (no filesystem
            scan, zero false positives on config/assets): files that have .gbc json or
            are depended-upon yet have no gbc.md file entry.
    """
    try:
        # 文档型工具：直接返回原始文本(不经 _ok 的 json.dumps)，让 MCP 当文本块发出，
        # 换行是字面换行、零转义开销。是「工具返回 JSON 字符串」约定的有意例外。
        return base.render_tree(detail=detail, gaps=gaps)
    except Exception as e:
        return _err(e)


@mcp.tool()
def check_consistency() -> str:
    """Global lint of the .gbc graph. Reports two classes, distinguished by `type`:

    Errors (graph inconsistency): dangling_guarantee / missing_reverse / missing_forward.
    Disabled notices (loud, not errors): disabled_guarantee (a guarantee with born-green
    suspended) / depends_on_disabled (a consumer relying on a disabled guarantee).

    The list is empty ONLY when fully consistent AND nothing is disabled — so any disabled
    guarantee keeps this non-empty until it's enabled back. Filter by `type` to separate
    hard errors from disabled notices.

    Returns: JSON array of objects (empty array = consistent and nothing disabled)
    """
    try:
        return _ok(base.check_consistency())
    except Exception as e:
        return _err(e)


# ======== 验证 ========

@mcp.tool()
def verify_provider(provider: str, auto_run_max_heavy: int = 0, timeout: int = -1) -> str:
    """Verify all guarantees a provider offers. Guarantees with heavy > auto_run_max_heavy
    are skipped and reported (not failed). Gate is green iff `failed` is empty.

    Verification runs each guarantee's narrow test(s) — the point is guarding
    behavioral promises, not full-suite coverage.

    Args:
        provider: Source file path
        auto_run_max_heavy: Run only guarantees with heavy <= this (default 0); higher ones are skipped
        timeout: Global timeout override; -1 uses per-guarantee/executor default

    Returns: JSON {passed, failed, skipped, results, green}
    """
    try:
        summary = base.verify_provider(provider, auto_run_max_heavy=auto_run_max_heavy, timeout=timeout)
        payload = summary.model_dump()
        payload["green"] = summary.green
        return _ok(payload)
    except Exception as e:
        return _err(e)


@mcp.tool()
def verify_guarantee(provider: str, id: str, timeout: int = -1) -> str:
    """Verify a single guarantee by id — always runs, ignoring the heavy threshold.

    Runs the guarantee's own narrow test — guarding a promise, not full-suite coverage.

    Args:
        provider: Source file path
        id: Guarantee id
        timeout: Timeout override; -1 uses guarantee/executor default

    Returns: JSON verify result {return_code, stdout, stderr}
    """
    try:
        return _ok(base.verify_guarantee(provider, id, timeout=timeout).model_dump())
    except Exception as e:
        return _err(e)


# ======== Executors ========

@mcp.tool()
def upsert_executor(config_name: str, config_data: dict) -> str:
    """Create or update an executor configuration (how to run tests).

    Args:
        config_name: Executor name (e.g. "pytest_conda")
        config_data: {command: [parts with {file} placeholder], cwd, timeout, env_ops:[{key,action,value}]}
    """
    try:
        base.upsert_executor(config_name, config_data)
        return "upserted"
    except Exception as e:
        return _err(e)


# ======== 意图文档（gbc.md：与 cli(gbc doc)/editor 对称的第三个薄表面）========
# 读(show/check)与写(set-*/sync/migrate)都经 MCP；写入的「改前须人类确认」闸门
# 由用户 agent 框架(hook/rules)承担——MCP 与 CLI 对称，隐藏写入通道不产生额外安全。

def _doc_root():
    """当前目标项目的 gbc 根(镜像层)。与 intent.cli._gbc_root 同源。"""
    from gbc.app.config.project import get_current_project
    gbc_root, _ = intent_base.resolve_gbc(str(get_current_project()))
    return gbc_root


@mcp.tool()
def doc_show(folder: str = "") -> str:
    """Show a folder's intent / internal constraints / entries from its gbc.md.

    Args:
        folder: project-relative folder path; use "" for the root.

    Returns: plain text rendering (same as `gbc doc show`).
    """
    try:
        return intent_base.show(_doc_root(), folder)
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_check() -> str:
    """Whole-tree intent consistency check (DRIFT/ORPHAN are errors, STUB is a note).

    Returns: JSON {errors: [...], notes: [...]} (errors empty = tree consistent).
    """
    try:
        errors, notes = intent_base.check(_doc_root())
        return _ok({"errors": errors, "notes": notes})
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_set_intent(folder: str, text: str) -> str:
    """Set a folder's intent (auto single-source projection into the parent doc entry).

    Writing intent changes the human-held architecture truth — your agent framework's
    hook/rules decide whether this needs human sign-off; GBC does not gate it here.

    Args:
        folder: project-relative folder path ("" for root).
        text: the intent prose.

    Returns: JSON list of written gbc.md paths.
    """
    try:
        return _ok([str(p) for p in intent_base.set_intent(_doc_root(), folder, text)])
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_set_constraints(folder: str, text: str) -> str:
    """Set a folder's internal constraints (local only, not projected to the parent).

    Args:
        folder: project-relative folder path ("" for root).
        text: the constraints prose.

    Returns: JSON list of written gbc.md paths.
    """
    try:
        return _ok([str(p) for p in intent_base.set_constraints(_doc_root(), folder, text)])
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_set_file(folder: str, name: str, desc: str) -> str:
    """Add/update a file entry in a folder's gbc.md (name must not contain '/').

    Args:
        folder: project-relative folder path ("" for root).
        name: file name (no slash).
        desc: the file's description.

    Returns: JSON list of written gbc.md paths.
    """
    try:
        return _ok([str(p) for p in intent_base.set_file(_doc_root(), folder, name, desc)])
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_rm_entry(folder: str, name: str) -> str:
    """Remove an entry from a folder's gbc.md (doc only; the on-disk file is left for git review).

    Args:
        folder: project-relative folder path ("" for root).
        name: entry name to remove.

    Returns: JSON list of written gbc.md paths.
    """
    try:
        return _ok([str(p) for p in intent_base.rm_entry(_doc_root(), folder, name)])
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_sync() -> str:
    """Deterministically fix DRIFT/ORPHAN: re-project child intents into parent entries.

    Returns: JSON list of fix descriptions (empty = nothing to sync).
    """
    try:
        return _ok(intent_base.sync(_doc_root()))
    except Exception as e:
        return _err(e)


@mcp.tool()
def doc_migrate() -> str:
    """Upgrade all gbc.md files to the latest format.

    Returns: JSON list of migrated paths (empty = all up to date).
    """
    try:
        return _ok(intent_base.migrate(_doc_root()))
    except Exception as e:
        return _err(e)


# ======== 入口（MCP 表面自己的启动器）========

def run_server(project_root: str | None = None) -> None:
    """以 stdio transport 启动 gbc MCP server。

    为什么这样:GBC 常被从任意 cwd(甚至 WSL→Windows)拉起,实测环境变量传递
    不可靠、目标项目可能有同名包按 cwd 抢占 import。因此项目根由**显式参数**
    传入,而非依赖 env 或 cwd。stdout 是 JSON-RPC 协议通道,强制 UTF-8避免本地码页污染。
    """
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if project_root:
        from gbc.app.config import project
        project.set_current_project(str(Path(project_root).expanduser()))

    mcp.run()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
