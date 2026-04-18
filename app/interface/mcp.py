import json

from mcp.server.fastmcp import FastMCP

from . import base
from app.models.errors import GBCError
from app.models.meta import Guarantee
from app.models.verify import VerifyModel

mcp = FastMCP("gbc")


# ======== 显式序列化，每个对应一种已知返回类型 ========

def _dump_guarantees(items: list[Guarantee]) -> list[dict]:
    return [g.model_dump() for g in items]


def _dump_guarantee_map(data: dict[str, list[Guarantee]]) -> dict:
    return {k: _dump_guarantees(v) for k, v in data.items()}


def _dump_verify(item: VerifyModel) -> dict:
    return item.model_dump()


def _dump_verify_list(items: list[VerifyModel]) -> list[dict]:
    return [v.model_dump() for v in items]


def _dump_verify_map(data: dict[str, list[VerifyModel]]) -> dict:
    return {k: _dump_verify_list(v) for k, v in data.items()}


# ======== Guarantees 写操作 ========

@mcp.tool()
def register_guarantee(
    provider: str,
    config: str,
    target: str,
    guarantee_path: str,
    guarantee_spec: str,
    timeout_override: int = -1,
) -> str:
    """Register a new guarantee: target depends on a behavior of provider, verified by the test at guarantee_path.

    Args:
        provider: Source file providing the guarantee (e.g. "src/llm_client/client.py")
        config: Executor config name to run the test (e.g. "pytest")
        target: File that depends on this guarantee (e.g. "src/conversation/manager.py")
        guarantee_path: Test file path (e.g. "tests/test_client_returns_dict.py")
        guarantee_spec: Description of the guaranteed behavior
        timeout_override: Timeout in seconds; -1 uses executor default
    """
    try:
        base.register_guarantee(provider, config, target, guarantee_path, guarantee_spec, timeout_override)
        return "registered"
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def unregister_guarantee(provider: str, target: str, guarantee_path: str) -> str:
    """Unregister a specific guarantee by its test file path.

    Args:
        provider: Source file path
        target: Dependent file path
        guarantee_path: Test file path of the guarantee to remove
    """
    try:
        base.unregister_guarantee(provider, target, guarantee_path)
        return "unregistered"
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def unregister_all_guarantees(provider: str, target: str) -> str:
    """Unregister all guarantees for a target under a provider.

    Args:
        provider: Source file path
        target: Dependent file path whose guarantees will all be removed
    """
    try:
        base.unregister_all_guarantees(provider, target)
        return "unregistered"
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def update_guarantee(
    provider: str,
    target: str,
    guarantee_path: str,
    guarantee_spec: str,
    timeout_override: int = -1,
) -> str:
    """Update a guarantee's description and/or timeout.

    Args:
        provider: Source file path
        target: Dependent file path
        guarantee_path: Test file path of the guarantee to update
        guarantee_spec: New description of the guaranteed behavior
        timeout_override: New timeout in seconds; -1 uses executor default
    """
    try:
        base.update_guarantees(provider, target, guarantee_path, guarantee_spec, timeout_override)
        return "updated"
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


# ======== Guarantees 读操作 ========

@mcp.tool()
def list_guarantees_by_target(provider: str, target: str) -> str:
    """List all guarantees registered by a specific target under a provider.

    Args:
        provider: Source file path
        target: Dependent file path

    Returns:
        JSON array of guarantee objects
    """
    try:
        result = base.list_guarantees_of_one(provider, target)
        return json.dumps(_dump_guarantees(result), ensure_ascii=False)
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def list_all_guarantees(provider: str) -> str:
    """List all guarantees of all targets under a provider.

    Args:
        provider: Source file path

    Returns:
        JSON object mapping target paths to arrays of guarantee objects
    """
    try:
        result = base.list_guarantees_of_all(provider)
        return json.dumps(_dump_guarantee_map(result), ensure_ascii=False)
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


# ======== Verify 操作 ========

@mcp.tool()
def verify_all_guarantees(
    provider: str,
    timeout: int = -1,
) -> str:
    """Verify all guarantees of a provider by running all associated tests.

    Args:
        provider: Source file path
        timeout: Global timeout override in seconds; -1 uses per-guarantee or executor default

    Returns:
        JSON object mapping target paths to arrays of verify results
    """
    try:
        result = base.verify_all_guarantees(provider, timeout=timeout)
        return json.dumps(_dump_verify_map(result), ensure_ascii=False)
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def verify_guarantees_by_target(
    provider: str,
    target: str,
    timeout: int = -1,
) -> str:
    """Verify all guarantees registered by a specific target.

    Args:
        provider: Source file path
        target: Dependent file path
        timeout: Global timeout override; -1 uses default

    Returns:
        JSON array of verify results
    """
    try:
        result = base.verify_all_guarantees_of_one_target(provider, target, timeout=timeout)
        return json.dumps(_dump_verify_list(result), ensure_ascii=False)
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


@mcp.tool()
def verify_single_guarantee(
    provider: str,
    target: str,
    guarantee_path: str,
    timeout: int = -1,
) -> str:
    """Verify a single guarantee by running its test file.

    Args:
        provider: Source file path
        target: Dependent file path
        guarantee_path: Test file path of the guarantee to verify
        timeout: Timeout override; -1 uses guarantee or executor default

    Returns:
        JSON object with verify result (return_code, stdout, stderr)
    """
    try:
        result = base.verify_single_guarantee(provider, target, guarantee_path, timeout=timeout)
        return json.dumps(_dump_verify(result), ensure_ascii=False)
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)


# ======== Executors ========

@mcp.tool()
def upsert_executor(config_name: str, config_data: dict) -> str:
    """Create or update an executor configuration.

    An executor defines how to run tests: command template, working directory,
    timeout, and environment variable operations.

    Args:
        config_name: Executor name (e.g. "pytest", "jest")
        config_data: Executor config dict with keys:
            - command: list of command parts, {file} as test file placeholder
            - cwd: working directory
            - timeout: default timeout in seconds
            - env_ops: list of {key, action, value}; action is set/append/prepend/remove

    Returns:
        Confirmation string
    """
    try:
        base.upsert_executor(config_name, config_data)
        return "upserted"
    except GBCError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"}, ensure_ascii=False)