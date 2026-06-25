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
from app.models.errors import GBCError

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
) -> str:
    """Create a new named guarantee on a provider file. Born-green: the test is run
    immediately and creation is rejected if it fails.

    Args:
        provider: Source file that provides this guarantee (e.g. "app/config/llm.py")
        id: Semantic guarantee id, e.g. "config.llm.get_model.returns_loaded" (identity; not the test path)
        desc: What behavior is promised and why it matters
        test: Test selector passed to the executor ({file} substitution), e.g. "tests/test_x.py::test_y"
        executor: Executor config name that knows how to run the test
        heavy: Cost rank; 0 runs in batch, >=1 is skipped in batch verify (and reported)
        timeout_override: Per-guarantee timeout in seconds; -1 uses executor default
    """
    try:
        base.create_guarantee(provider, id, desc, test, executor, heavy, timeout_override)
        return "created"
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
    """Global lint of the .gbc graph: report dangling guarantee refs and broken
    bidirectional edges (dangling_guarantee / missing_reverse / missing_forward).

    Returns: JSON array of violation objects (empty array = consistent)
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


# ======== 入口 ========

def main() -> None:
    """以 stdio transport 启动 gbc MCP server。"""
    mcp.run()


if __name__ == "__main__":
    main()
