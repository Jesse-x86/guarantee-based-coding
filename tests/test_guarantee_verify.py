"""窄测试：verify_provider / verify_guarantee 的门禁二元性。

验证语义：
- verify_provider: disabled 跳过(不进 results)，heavy > 阈值跳过，其余真跑；
  passed/failed/skipped 三桶；green = failed 为空（skipped 不染红）。
- verify_guarantee: 点名验证无视 disabled 与 heavy，永远真跑一次；
  gid 不存在抛 GuaranteeNotFoundError。
"""

import pytest
from gbc.app.core.guarantee import verify_provider, verify_guarantee
from gbc.app.models.errors import GuaranteeNotFoundError
from gbc.app.models.meta import FileMeta, Guarantee
from gbc.app.models.verify import VerifyModel, VerifySummary, SkippedGuarantee


# ── verify_provider ────────────────────────────────────────────────


def test_verify_provider_mixed_buckets(fake_project, passing_test_file, failing_test_file):
    """mixed: 2条 heavy=0(passing+failing) + 1条 heavy=1 → failed桶非空 green=False。"""
    meta = FileMeta()
    meta.provides["a.passing"] = Guarantee(
        desc="passing", test=passing_test_file, executor="pytest-fake", heavy=0
    )
    meta.provides["b.failing"] = Guarantee(
        desc="failing", test=failing_test_file, executor="pytest-fake", heavy=0
    )
    meta.provides["c.heavy_skipped"] = Guarantee(
        desc="heavy", test=passing_test_file, executor="pytest-fake", heavy=1
    )

    summary = verify_provider(meta)

    assert "a.passing" in summary.passed
    assert "b.failing" in summary.failed
    assert "c.heavy_skipped" not in summary.passed
    assert "c.heavy_skipped" not in summary.failed
    assert any(s.id == "c.heavy_skipped" and s.reason == "heavy" for s in summary.skipped)
    assert summary.green is False


def test_verify_provider_all_passing_is_green(fake_project, passing_test_file):
    """全部 passing → failed 空，green=True。"""
    meta = FileMeta()
    meta.provides["a.ok"] = Guarantee(
        desc="ok", test=passing_test_file, executor="pytest-fake", heavy=0
    )

    summary = verify_provider(meta)

    assert "a.ok" in summary.passed
    assert not summary.failed
    assert summary.green is True


def test_verify_provider_disabled_skipped(fake_project, passing_test_file):
    """disabled 保证进 skipped(reason=disabled)，不进 results。"""
    meta = FileMeta()
    meta.provides["x.disabled"] = Guarantee(
        desc="disabled", test=passing_test_file, executor="pytest-fake",
        heavy=0, disabled=True,
    )

    summary = verify_provider(meta)

    assert not summary.passed
    assert not summary.failed
    assert any(s.id == "x.disabled" and s.reason == "disabled" for s in summary.skipped)
    assert "x.disabled" not in summary.results
    assert summary.green is True  # 没有 failed，即使有 skipped


def test_verify_provider_heavy_run_when_within_threshold(fake_project, passing_test_file):
    """auto_run_max_heavy=1 时 heavy=1 的保证应真跑并进 passed。"""
    meta = FileMeta()
    meta.provides["h.pass"] = Guarantee(
        desc="heavy1", test=passing_test_file, executor="pytest-fake", heavy=1
    )

    summary = verify_provider(meta, auto_run_max_heavy=1)

    assert "h.pass" in summary.passed
    assert "h.pass" not in [s.id for s in summary.skipped]


# ── verify_guarantee ───────────────────────────────────────────────


def test_verify_guarantee_passing(fake_project, passing_test_file):
    """点名验证一条 passing 保证 → return_code==0。"""
    meta = FileMeta()
    meta.provides["p.ok"] = Guarantee(
        desc="ok", test=passing_test_file, executor="pytest-fake"
    )

    result = verify_guarantee(meta, "fake.py", "p.ok")

    assert isinstance(result, VerifyModel)
    assert result.return_code == 0


def test_verify_guarantee_disabled_still_runs(fake_project, failing_test_file):
    """点名验证无视 disabled：挂 failing 测试的 disabled 保证仍真跑，return_code!=0。"""
    meta = FileMeta()
    meta.provides["d.fail"] = Guarantee(
        desc="disabled-but-run", test=failing_test_file, executor="pytest-fake",
        disabled=True,
    )

    result = verify_guarantee(meta, "fake.py", "d.fail")

    # 真跑了（不是被跳过），所以 return_code!=0
    assert result.return_code != 0


def test_verify_guarantee_not_found(fake_project, passing_test_file):
    """gid 不存在 → 抛 GuaranteeNotFoundError。"""
    meta = FileMeta()
    # 注册一个别的保证，验证查找严格性
    meta.provides["real.one"] = Guarantee(
        desc="real", test=passing_test_file, executor="pytest-fake"
    )

    with pytest.raises(GuaranteeNotFoundError):
        verify_guarantee(meta, "fake.py", "nonexistent")
