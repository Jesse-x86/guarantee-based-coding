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

"""保证系统的核心逻辑（纯模型操作 + 跑测试，无文件 IO / 无路径解析）。

约定：
  - 所有进出本模块的文件路径都是「项目相对 POSIX 字符串」，路径解析由 base 层负责。
  - 本模块直接读写 FileMeta 模型对象；跨文件操作（注册依赖）同时收 consumer 与
    provider 两个 meta，原子地维护双向一致，但落盘仍由 base 层负责。
  - 「出生即绿」门禁：create / update 改动测试时当场跑测试，不过则拒绝（抛错），
    绝不留下一条没验证过的保证。
"""

from app.core import executor
from app.models.errors import (
    GuaranteeDuplicatedError,
    GuaranteeNotFoundError,
    GuaranteeTestFailedError,
    GuaranteeHasDependentsError,
)
from app.models.meta import FileMeta, Guarantee, Dependency
from app.models.verify import VerifyModel, VerifySummary, SkippedGuarantee


# ============================================================================
# 内部小工具
# ============================================================================

def _run_test(guarantee: Guarantee, *, timeout: int = -1) -> VerifyModel:
    """跑一条保证的测试，返回原始结果。timeout=-1 时回退到保证自带的 override。"""
    effective_timeout = timeout if timeout != -1 else guarantee.timeout_override
    return executor.verify_single(
        guarantee.executor, guarantee.test, timeout=effective_timeout, return_model=True
    )


def _gate(provider: str, gid: str, guarantee: Guarantee) -> None:
    """出生即绿门禁：跑测试，不过就抛 GuaranteeTestFailedError。"""
    result = _run_test(guarantee)
    if result.return_code != 0:
        # pytest 将断言错误输出到 stdout，stderr 通常是 warnings
        details = (result.stderr or "") + "\n" + (result.stdout or "")
        raise GuaranteeTestFailedError(
            target_file=provider, guarantee_path=gid, failure_info=details.strip()
        )


def _find_dependency(meta: FileMeta, symbol: str) -> Dependency | None:
    """在 consumer meta 的 depends_on 里按 symbol 找依赖边。"""
    for dep in meta.depends_on:
        if dep.symbol == symbol:
            return dep
    return None


# ============================================================================
# Provider 侧：保证生命周期
# ============================================================================

def create_guarantee(
    provider_meta: FileMeta,
    provider: str,
    gid: str,
    *,
    desc: str,
    test: str,
    executor_name: str,
    heavy: int = 0,
    timeout_override: int = -1,
    disabled: bool = False,
) -> Guarantee:
    """在 provider 上新建一条具名保证。

    默认出生即绿：当场跑测试，不过则拒绝。``disabled=True`` 则**跳过门禁**新建一条停用
    占位保证(用于循环依赖 bootstrap：测试还过不了时先占住 id 与边，待两边就绪再 enable)。
    停用保证是 born-green 的逃生口，必须靠 check_consistency 响亮报出、别让它静默留存。
    """
    if gid in provider_meta.provides:
        raise GuaranteeDuplicatedError(target_file=provider, guarantee_path=gid)

    guarantee = Guarantee(
        desc=desc,
        test=test,
        executor=executor_name,
        timeout_override=timeout_override,
        heavy=heavy,
        dependents=[],
        disabled=disabled,
    )
    if not disabled:
        _gate(provider, gid, guarantee)  # 先验证后落入模型；停用占位则不验证
    provider_meta.provides[gid] = guarantee
    return guarantee


def update_guarantee(
    provider_meta: FileMeta,
    provider: str,
    gid: str,
    *,
    desc: str | None = None,
    test: str | None = None,
    executor_name: str | None = None,
    heavy: int | None = None,
    timeout_override: int | None = None,
) -> Guarantee:
    """更新一条保证的元数据。只传想改的字段；若改动了测试/执行方式则重新跑门禁。"""
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)

    # 是否动了「怎么验证」——动了就要重新证明出生即绿
    runner_changed = (
        (test is not None and test != guarantee.test)
        or (executor_name is not None and executor_name != guarantee.executor)
        or (timeout_override is not None and timeout_override != guarantee.timeout_override)
    )

    if desc is not None:
        guarantee.desc = desc
    if test is not None:
        guarantee.test = test
    if executor_name is not None:
        guarantee.executor = executor_name
    if heavy is not None:
        guarantee.heavy = heavy
    if timeout_override is not None:
        guarantee.timeout_override = timeout_override

    # 停用态下「换测试只换不跑」：runner 变了也不重证门禁——门禁等到 enable 时再补。
    if runner_changed and not guarantee.disabled:
        _gate(provider, gid, guarantee)

    return guarantee


def disable_guarantee(provider_meta: FileMeta, provider: str, gid: str) -> Guarantee:
    """停用一条保证：置 disabled=True，id 与全部边(dependents/反向边)原样保留。

    幂等：已停用再调无副作用。停用 ≠ 退休——它不删任何东西、不动依赖关系，只是让门禁与
    批量 verify 暂缓执行它。用于重构窗口/在修保证：先 disable 守住边，改完测试再 enable。
    """
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)
    guarantee.disabled = True
    return guarantee


def enable_guarantee(provider_meta: FileMeta, provider: str, gid: str) -> Guarantee:
    """恢复一条停用的保证：当场补跑门禁(born-green)，过了才真正置 disabled=False。

    门禁不过则抛 GuaranteeTestFailedError 且**保持 disabled 不变**(enable 失败=仍停用)，
    绝不把一条没验证过的保证悄悄转正。幂等：对已启用的保证调用 = 重证一次门禁。
    """
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)
    _gate(provider, gid, guarantee)  # 不过则抛错，下面这行不执行 ⇒ 仍是 disabled
    guarantee.disabled = False
    return guarantee


def retire_guarantee(provider_meta: FileMeta, provider: str, gid: str) -> None:
    """退休一条保证。退休保护：仍有 dependents 则拒绝（抛 GuaranteeHasDependentsError）。

    系统不替使用者反射式删掉还有人依赖的保证；必须先沿依赖线修复/迁移 dependents。
    """
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)

    if guarantee.dependents:
        raise GuaranteeHasDependentsError(
            provider=provider, guarantee_id=gid, dependents=list(guarantee.dependents)
        )

    del provider_meta.provides[gid]


# ============================================================================
# Consumer 侧：依赖边（跨文件，双向写）
# ============================================================================

def add_dependency(
    consumer_meta: FileMeta,
    consumer: str,
    provider_meta: FileMeta,
    provider: str,
    symbol_name: str,
    gid: str | None = None,
) -> None:
    """登记 consumer 对 provider 的一条依赖。

    - gid 为 None：symbol 级「免费依赖」——只在 consumer.depends_on 记一条 symbol 边，
      不挂保证、无反向边。
    - gid 非 None：行为级依赖——gid 必须已存在于 provider.provides（消费者不能凭空要求
      新行为；要新行为先让 provider create_guarantee）。双向写：consumer 边挂上 gid，
      provider 该保证的 dependents 追加 consumer。
    """
    symbol = f"{provider}:{symbol_name}"

    # 保证 consumer 侧有这条 symbol 边
    dep = _find_dependency(consumer_meta, symbol)
    if dep is None:
        dep = Dependency(symbol=symbol, guarantees=[])
        consumer_meta.depends_on.append(dep)

    if gid is None:
        return  # 免费依赖，到此为止

    if gid not in provider_meta.provides:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)

    # 双向写（各自去重）
    if gid not in dep.guarantees:
        dep.guarantees.append(gid)
    dependents = provider_meta.provides[gid].dependents
    if consumer not in dependents:
        dependents.append(consumer)


def remove_dependency(
    consumer_meta: FileMeta,
    consumer: str,
    provider_meta: FileMeta,
    provider: str,
    symbol_name: str,
    gid: str | None = None,
) -> None:
    """撤销一条依赖（add_dependency 的逆操作，同样维护双向一致）。

    - gid 非 None：只摘掉这一个保证依赖（consumer 边去掉 gid，provider 反向边去掉 consumer），
      symbol 边若还挂着别的保证则保留。
    - gid 为 None：整条 symbol 边连同它挂的所有保证一起撤销，并从各保证的 dependents 摘除 consumer。
    """
    symbol = f"{provider}:{symbol_name}"
    dep = _find_dependency(consumer_meta, symbol)
    if dep is None:
        raise GuaranteeNotFoundError(target_file=consumer, guarantee_path=symbol)

    def _detach(target_gid: str) -> None:
        guarantee = provider_meta.provides.get(target_gid)
        if guarantee and consumer in guarantee.dependents:
            guarantee.dependents.remove(consumer)

    if gid is None:
        for g in list(dep.guarantees):
            _detach(g)
        consumer_meta.depends_on.remove(dep)
        return

    if gid in dep.guarantees:
        dep.guarantees.remove(gid)
    _detach(gid)
    # symbol 边变空（无保证）后是否保留：保留——它仍是一条有效的免费 symbol 依赖。


# ============================================================================
# 读 / 反查
# ============================================================================

def list_provides(provider_meta: FileMeta) -> dict[str, Guarantee]:
    """provider 提供的全部保证（含各自 dependents）。"""
    return dict(provider_meta.provides)


def list_depends_on(consumer_meta: FileMeta) -> list[Dependency]:
    """consumer 声明的全部依赖边。"""
    return list(consumer_meta.depends_on)


def dependents_of(provider_meta: FileMeta, gid: str) -> list[str]:
    """谁依赖 provider 的这条保证——O(1) 直接读反向边。"""
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file="<provider>", guarantee_path=gid)
    return list(guarantee.dependents)


# ============================================================================
# 验证
# ============================================================================

def verify_provider(
    provider_meta: FileMeta,
    *,
    auto_run_max_heavy: int = 0,
    timeout: int = -1,
) -> VerifySummary:
    """批量验证 provider 提供的所有保证，按 heavy 阈值跳过并三桶汇总。

    批量只跑 heavy <= auto_run_max_heavy 的；其余进 skipped 桶并被响亮报告。
    门禁二元：green = failed 桶为空（skipped 不染红）。
    """
    summary = VerifySummary()
    for gid, guarantee in provider_meta.provides.items():
        if guarantee.disabled:
            # 停用 = 缺席的另一种：不跑、不染红，进 skipped 并标 reason=disabled 响亮报出。
            summary.skipped.append(
                SkippedGuarantee(id=gid, heavy=guarantee.heavy, reason="disabled")
            )
            continue
        if guarantee.heavy > auto_run_max_heavy:
            summary.skipped.append(SkippedGuarantee(id=gid, heavy=guarantee.heavy))
            continue
        result = _run_test(guarantee, timeout=timeout)
        summary.results[gid] = result
        if result.return_code == 0:
            summary.passed.append(gid)
        else:
            summary.failed.append(gid)
    return summary


def verify_guarantee(
    provider_meta: FileMeta,
    provider: str,
    gid: str,
    *,
    timeout: int = -1,
) -> VerifyModel:
    """点名验证单条保证——无视 heavy 阈值，永远跑（你点了名就是要跑）。"""
    guarantee = provider_meta.provides.get(gid)
    if guarantee is None:
        raise GuaranteeNotFoundError(target_file=provider, guarantee_path=gid)
    return _run_test(guarantee, timeout=timeout)
