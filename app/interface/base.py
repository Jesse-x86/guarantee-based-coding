"""IO / 编排层：路径解析、meta 文件读写、跨文件双向写、全局扫描。

core 层是纯模型操作（不碰磁盘）；这里负责把「provider/consumer 文件字符串」解析成
项目相对路径、加载/保存对应的 .gbc json，并把 core 的纯操作包成可被 cli / mcp 调用的
函数。依赖登记是跨两个文件的双向写，这里用双文件 session 统一处理。
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from pydantic import ValidationError

from app.config.backups import META_BACKUPS
from app.config.executor import ExecutorModel
from app.config.project import get_current_project
from app.core import executor
from app.core import guarantee as gtee
from app.models.errors import (
    IllegalFilePathError,
    ExecutorConfigInvalidError,
    MetaNotFoundError,
)
from app.models.meta import FileMeta, Guarantee, Dependency
from app.models.verify import VerifyModel, VerifySummary
from app.utils.file_utils import to_gbc_json_path
from app.utils.json_model_operator import load_model_from_json, save_model_to_json


# ============================================================================
# 路径与持久化基元
# ============================================================================

def _resolve(file_str: str) -> Path:
    """把输入文件路径解析到项目内并校验。

    相对路径按**当前项目根**(get_current_project())解释，而非进程 cwd——这样工具作为
    MCP server 在任意 cwd 下启动（其 app 包与目标项目可能重名）都能正确定位目标项目的文件。
    """
    project = get_current_project()
    path = Path(file_str)
    if not path.is_absolute():
        path = project / path
    if not path.is_relative_to(project):
        raise IllegalFilePathError(path)
    return path


def _to_rel(file_str: str) -> str:
    """项目相对 POSIX 字符串——一切存进 .gbc 的路径都用这种形式（稳定、可移植）。"""
    return _resolve(file_str).relative_to(get_current_project()).as_posix()


def _load_meta(abs_path: Path, *, create_if_missing: bool) -> FileMeta:
    """加载某源文件的 FileMeta；不存在时按需新建空模型或抛 MetaNotFoundError。"""
    json_path = to_gbc_json_path(abs_path)
    if json_path.exists():
        return load_model_from_json(json_path, FileMeta)
    if create_if_missing:
        return FileMeta()
    raise MetaNotFoundError(original_file=abs_path, target_file=json_path)


def _save_meta(meta: FileMeta, abs_path: Path) -> None:
    save_model_to_json(meta, to_gbc_json_path(abs_path), META_BACKUPS)


@contextmanager
def meta_session(file_str: str, *, readonly: bool = False, create_if_missing: bool = False):
    """单文件 session：加载 → yield → （非只读时）保存。"""
    abs_path = _resolve(file_str)
    meta = _load_meta(abs_path, create_if_missing=create_if_missing)
    yield meta
    if not readonly:
        _save_meta(meta, abs_path)


@contextmanager
def dual_session(consumer_str: str, provider_str: str):
    """双文件 session：依赖登记要同时改 consumer（depends_on）与 provider（dependents）。

    consumer 允许不存在（首次声明依赖时新建）；provider 必须存在（行为级依赖的保证
    必须已在 provider 上）。两个文件都会被保存。
    """
    consumer_path = _resolve(consumer_str)
    provider_path = _resolve(provider_str)
    consumer_meta = _load_meta(consumer_path, create_if_missing=True)
    provider_meta = _load_meta(provider_path, create_if_missing=False)
    yield consumer_meta, provider_meta
    _save_meta(consumer_meta, consumer_path)
    _save_meta(provider_meta, provider_path)


def _iter_all_metas() -> Iterator[tuple[str, FileMeta]]:
    """遍历 .gbc 树下所有 meta，产出 (源文件项目相对路径, FileMeta)。

    反推：`.gbc/<dir>/gbc.<name>.json` → 源文件 `<dir>/<name>`。
    """
    gbc_root = get_current_project() / ".gbc"
    if not gbc_root.exists():
        return
    for json_file in gbc_root.rglob("gbc.*.json"):
        rel_dir = json_file.parent.relative_to(gbc_root)
        src_name = json_file.name[len("gbc."):-len(".json")]
        src_rel = (rel_dir / src_name).as_posix()
        try:
            meta = load_model_from_json(json_file, FileMeta)
        except (ValueError, ValidationError):
            continue  # 损坏的 meta 跳过，由 check_consistency 之外的手段处理
        yield src_rel, meta


# ============================================================================
# Provider 侧：保证生命周期
# ============================================================================

def create_guarantee(
    provider: str,
    gid: str,
    desc: str,
    test: str,
    executor_name: str,
    heavy: int = 0,
    timeout_override: int = -1,
) -> None:
    provider_rel = _to_rel(provider)
    with meta_session(provider, create_if_missing=True) as meta:
        gtee.create_guarantee(
            meta, provider_rel, gid,
            desc=desc, test=test, executor_name=executor_name,
            heavy=heavy, timeout_override=timeout_override,
        )


def update_guarantee(
    provider: str,
    gid: str,
    *,
    desc: str | None = None,
    test: str | None = None,
    executor_name: str | None = None,
    heavy: int | None = None,
    timeout_override: int | None = None,
) -> None:
    provider_rel = _to_rel(provider)
    with meta_session(provider) as meta:
        gtee.update_guarantee(
            meta, provider_rel, gid,
            desc=desc, test=test, executor_name=executor_name,
            heavy=heavy, timeout_override=timeout_override,
        )


def retire_guarantee(provider: str, gid: str) -> None:
    provider_rel = _to_rel(provider)
    with meta_session(provider) as meta:
        gtee.retire_guarantee(meta, provider_rel, gid)


# ============================================================================
# Consumer 侧：依赖边（双向写）
# ============================================================================

def add_dependency(consumer: str, provider: str, symbol: str, guarantee_id: str | None = None) -> None:
    consumer_rel = _to_rel(consumer)
    provider_rel = _to_rel(provider)

    if guarantee_id is None:
        # 免费 symbol 依赖：只动 consumer 一个文件
        with meta_session(consumer, create_if_missing=True) as cmeta:
            gtee.add_dependency(cmeta, consumer_rel, FileMeta(), provider_rel, symbol, None)
        return

    with dual_session(consumer, provider) as (cmeta, pmeta):
        gtee.add_dependency(cmeta, consumer_rel, pmeta, provider_rel, symbol, guarantee_id)


def remove_dependency(consumer: str, provider: str, symbol: str, guarantee_id: str | None = None) -> None:
    consumer_rel = _to_rel(consumer)
    provider_rel = _to_rel(provider)

    if guarantee_id is None:
        # 撤销整条 symbol 边：可能涉及 provider 反向边，走双文件
        with dual_session(consumer, provider) as (cmeta, pmeta):
            gtee.remove_dependency(cmeta, consumer_rel, pmeta, provider_rel, symbol, None)
        return

    with dual_session(consumer, provider) as (cmeta, pmeta):
        gtee.remove_dependency(cmeta, consumer_rel, pmeta, provider_rel, symbol, guarantee_id)


# ============================================================================
# 读 / 反查
# ============================================================================

def list_provides(provider: str) -> dict[str, Guarantee]:
    with meta_session(provider, readonly=True) as meta:
        return gtee.list_provides(meta)


def list_depends_on(consumer: str) -> list[Dependency]:
    with meta_session(consumer, readonly=True) as meta:
        return gtee.list_depends_on(meta)


def who_depends_on(
    provider: str,
    *,
    symbol: str | None = None,
    guarantee_id: str | None = None,
) -> dict:
    """反查谁依赖 provider。

    - 给 guarantee_id：O(1) 直接读该保证的 dependents（行为级，免费反向边）。
    - 否则：全局扫描所有文件的 depends_on，找出 symbol 指向本 provider 的依赖边
      （symbol 进一步过滤到具体符号）。这是 symbol 级免费依赖唯一的反查途径。
    """
    provider_rel = _to_rel(provider)

    if guarantee_id is not None:
        with meta_session(provider, readonly=True) as meta:
            return {
                "guarantee": guarantee_id,
                "dependents": gtee.dependents_of(meta, guarantee_id),
            }

    prefix = f"{provider_rel}:"
    wanted_symbol = f"{provider_rel}:{symbol}" if symbol is not None else None
    hits: list[dict] = []
    for src_rel, meta in _iter_all_metas():
        for dep in meta.depends_on:
            if wanted_symbol is not None:
                if dep.symbol != wanted_symbol:
                    continue
            elif not dep.symbol.startswith(prefix):
                continue
            hits.append({
                "consumer": src_rel,
                "symbol": dep.symbol,
                "guarantees": list(dep.guarantees),
            })
    return {"provider": provider_rel, "symbol": symbol, "dependents": hits}


def check_consistency() -> list[dict]:
    """全局一致性体检：扫描 .gbc 树，报告悬空引用与双向边漂移。

    检查项：
      - dangling_guarantee : 某 consumer 依赖了一个 provider 上不存在的保证 id。
      - missing_reverse    : consumer 挂了 gid，但 provider 的 dependents 里没有该 consumer。
      - missing_forward    : provider 的 dependents 列了某 consumer，但 consumer 没有对应依赖边。
    """
    # 先建 provides 索引：(provider_rel, gid) -> dependents
    provides_index: dict[tuple[str, str], list[str]] = {}
    metas: dict[str, FileMeta] = {}
    for src_rel, meta in _iter_all_metas():
        metas[src_rel] = meta
        for gid, guarantee in meta.provides.items():
            provides_index[(src_rel, gid)] = guarantee.dependents

    violations: list[dict] = []

    # 正向：consumer.depends_on -> provider.provides
    for consumer_rel, meta in metas.items():
        for dep in meta.depends_on:
            provider_rel = dep.symbol.split(":", 1)[0]
            for gid in dep.guarantees:
                key = (provider_rel, gid)
                if key not in provides_index:
                    violations.append({
                        "type": "dangling_guarantee",
                        "consumer": consumer_rel,
                        "provider": provider_rel,
                        "guarantee": gid,
                    })
                elif consumer_rel not in provides_index[key]:
                    violations.append({
                        "type": "missing_reverse",
                        "consumer": consumer_rel,
                        "provider": provider_rel,
                        "guarantee": gid,
                    })

    # 反向：provider.dependents -> consumer.depends_on
    for (provider_rel, gid), dependents in provides_index.items():
        for consumer_rel in dependents:
            cmeta = metas.get(consumer_rel)
            ok = cmeta is not None and any(
                dep.symbol.startswith(f"{provider_rel}:") and gid in dep.guarantees
                for dep in cmeta.depends_on
            )
            if not ok:
                violations.append({
                    "type": "missing_forward",
                    "consumer": consumer_rel,
                    "provider": provider_rel,
                    "guarantee": gid,
                })

    return violations


# ============================================================================
# 验证
# ============================================================================

def verify_provider(provider: str, *, auto_run_max_heavy: int = 0, timeout: int = -1) -> VerifySummary:
    with meta_session(provider, readonly=True) as meta:
        return gtee.verify_provider(meta, auto_run_max_heavy=auto_run_max_heavy, timeout=timeout)


def verify_guarantee(provider: str, gid: str, *, timeout: int = -1) -> VerifyModel:
    provider_rel = _to_rel(provider)
    with meta_session(provider, readonly=True) as meta:
        return gtee.verify_guarantee(meta, provider_rel, gid, timeout=timeout)


# ============================================================================
# Executors
# ============================================================================

def upsert_executor(config_name: str, config_data: dict) -> None:
    try:
        model = ExecutorModel(**config_data)
    except ValidationError:
        raise ExecutorConfigInvalidError(config_name)
    executor.upsert_exec_config(config_name=config_name, model=model)
