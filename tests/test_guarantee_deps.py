"""窄测试：guarantee.py 中依赖登记（add_dependency / remove_dependency）与反查函数。"""

import pytest
from gbc.app.models.meta import FileMeta, Guarantee, Dependency
from gbc.app.models.errors import GuaranteeNotFoundError, GuaranteeHasDependentsError
from gbc.app.core.guarantee import (
    add_dependency,
    remove_dependency,
    retire_guarantee,
    list_provides,
    list_depends_on,
    dependents_of,
)

PROVIDER_PATH = "app/core/provider.py"
CONSUMER_PATH = "app/core/consumer.py"
SYMBOL_NAME = "helper_func"
SYMBOL = f"{PROVIDER_PATH}:{SYMBOL_NAME}"
GID = "helper_func.returns_int"


def make_provider_meta(gid: str = GID) -> FileMeta:
    """创建一个 provider meta，预置一条保证。"""
    meta = FileMeta()
    meta.provides[gid] = Guarantee(desc="does something", test="test_x.py", executor="pytest-gbc")
    return meta


# ======================== add_dependency ========================

class TestAddDependencyFree:
    """add_dependency gid=None（免费 symbol 依赖）"""

    def test_adds_symbol_edge_with_empty_guarantees(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

        assert len(consumer_meta.depends_on) == 1
        dep = consumer_meta.depends_on[0]
        assert dep.symbol == SYMBOL
        assert dep.guarantees == []

    def test_provider_untouched(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

        assert provider_meta.provides == {}

    def test_same_symbol_twice_is_idempotent(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

        assert len(consumer_meta.depends_on) == 1


class TestAddDependencyBehavioral:
    """add_dependency gid 非 None（行为级依赖）"""

    def test_raises_when_gid_not_in_provider(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()  # no guarantees

        with pytest.raises(GuaranteeNotFoundError):
            add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

    def test_bidirectional_write(self):
        consumer_meta = FileMeta()
        provider_meta = make_provider_meta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

        # consumer 侧
        assert len(consumer_meta.depends_on) == 1
        dep = consumer_meta.depends_on[0]
        assert dep.symbol == SYMBOL
        assert GID in dep.guarantees

        # provider 侧
        assert CONSUMER_PATH in provider_meta.provides[GID].dependents

    def test_same_symbol_and_gid_twice_is_dedup(self):
        consumer_meta = FileMeta()
        provider_meta = make_provider_meta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

        # consumer: depends_on 仍只有一条、guarantees 里只有一个 GID
        assert len(consumer_meta.depends_on) == 1
        assert consumer_meta.depends_on[0].guarantees == [GID]

        # provider: dependents 里只有一个 consumer
        assert provider_meta.provides[GID].dependents == [CONSUMER_PATH]


# ======================== remove_dependency ========================

class TestRemoveDependency:
    def test_raises_when_symbol_edge_not_found(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()

        with pytest.raises(GuaranteeNotFoundError):
            remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

    def test_remove_full_symbol_edge_cleans_both_sides(self):
        consumer_meta = FileMeta()
        provider_meta = make_provider_meta()

        # 先建立一条行为级依赖
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

        # gid=None: 撤销整条 symbol 边
        remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

        # consumer 侧：边没了
        assert len(consumer_meta.depends_on) == 0
        # provider 侧：dependents 清掉了
        assert CONSUMER_PATH not in provider_meta.provides[GID].dependents

    def test_remove_one_gid_keeps_symbol_edge_and_other_gid(self):
        GID2 = "helper_func.raises_on_none"
        consumer_meta = FileMeta()
        provider_meta = make_provider_meta(GID)
        provider_meta.provides[GID2] = Guarantee(desc="d", test="t.py", executor="e")

        # 同一条 symbol 边上挂两个 gid
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID2)

        # 只摘掉 GID
        remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

        # consumer: symbol 边还在、只剩 GID2
        assert len(consumer_meta.depends_on) == 1
        dep = consumer_meta.depends_on[0]
        assert dep.symbol == SYMBOL
        assert GID not in dep.guarantees
        assert GID2 in dep.guarantees

        # provider: GID 的 dependents 清掉了 consumer，GID2 的还在
        assert CONSUMER_PATH not in provider_meta.provides[GID].dependents
        assert CONSUMER_PATH in provider_meta.provides[GID2].dependents


# ======================== list_provides / list_depends_on ========================

@pytest.mark.parametrize("whole_symbol", [False, True])
def test_shared_guarantee_keeps_retirement_guard_until_last_symbol_removed(whole_symbol):
    consumer_meta = FileMeta()
    provider_meta = make_provider_meta()
    for name in (SYMBOL_NAME, "other_helper"):
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, name, GID)

    gid = None if whole_symbol else GID
    remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid)

    assert dependents_of(provider_meta, GID) == [CONSUMER_PATH]
    assert any(dep.symbol == f"{PROVIDER_PATH}:other_helper" and GID in dep.guarantees
               for dep in consumer_meta.depends_on)
    with pytest.raises(GuaranteeHasDependentsError):
        retire_guarantee(provider_meta, PROVIDER_PATH, GID)

    remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, "other_helper", gid)

    assert dependents_of(provider_meta, GID) == []
    if whole_symbol:
        assert consumer_meta.depends_on == []
    else:
        assert len(consumer_meta.depends_on) == 2
        assert all(dep.guarantees == [] for dep in consumer_meta.depends_on)
    retire_guarantee(provider_meta, PROVIDER_PATH, GID)
    assert GID not in provider_meta.provides


@pytest.mark.parametrize("whole_symbol", [False, True])
def test_removing_dependency_preserves_other_consumer(whole_symbol):
    consumer_meta = FileMeta()
    other_consumer = FileMeta()
    other_path = "app/core/other_consumer.py"
    provider_meta = make_provider_meta()
    for meta, path in ((consumer_meta, CONSUMER_PATH), (other_consumer, other_path)):
        add_dependency(meta, path, provider_meta, PROVIDER_PATH, SYMBOL_NAME, GID)

    remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH,
                      SYMBOL_NAME, None if whole_symbol else GID)

    assert dependents_of(provider_meta, GID) == [other_path]
    assert other_consumer.depends_on[0].guarantees == [GID]
    with pytest.raises(GuaranteeHasDependentsError):
        retire_guarantee(provider_meta, PROVIDER_PATH, GID)


@pytest.mark.parametrize("whole_symbol", [False, True])
def test_same_guarantee_id_on_other_provider_does_not_keep_removed_reverse_edge(whole_symbol):
    consumer_meta = FileMeta()
    provider_meta = make_provider_meta()
    other_provider = make_provider_meta()
    other_path = "app/core/provider.py.extra"
    for meta, path in ((provider_meta, PROVIDER_PATH), (other_provider, other_path)):
        add_dependency(consumer_meta, CONSUMER_PATH, meta, path, SYMBOL_NAME, GID)

    remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH,
                      SYMBOL_NAME, None if whole_symbol else GID)

    assert dependents_of(provider_meta, GID) == []
    assert dependents_of(other_provider, GID) == [CONSUMER_PATH]
    assert any(dep.symbol == f"{other_path}:{SYMBOL_NAME}" and GID in dep.guarantees
               for dep in consumer_meta.depends_on)
    retire_guarantee(provider_meta, PROVIDER_PATH, GID)
    with pytest.raises(GuaranteeHasDependentsError):
        retire_guarantee(other_provider, other_path, GID)


def test_removing_gid_not_attached_to_target_symbol_preserves_valid_dependency():
    consumer_meta = FileMeta()
    provider_meta = make_provider_meta()
    add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)
    add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, "other_helper", GID)
    before_consumer = consumer_meta.model_dump()
    before_provider = provider_meta.model_dump()

    remove_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, GID)

    assert consumer_meta.model_dump() == before_consumer
    assert provider_meta.model_dump() == before_provider
    with pytest.raises(GuaranteeHasDependentsError):
        retire_guarantee(provider_meta, PROVIDER_PATH, GID)

class TestListFunctions:
    def test_list_provides_returns_provides_copy(self):
        meta = make_provider_meta()
        result = list_provides(meta)
        assert GID in result
        assert result[GID].desc == "does something"

    def test_list_provides_empty_when_no_guarantees(self):
        meta = FileMeta()
        assert list_provides(meta) == {}

    def test_list_depends_on_returns_depends_on_copy(self):
        consumer_meta = FileMeta()
        provider_meta = FileMeta()
        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME)

        result = list_depends_on(consumer_meta)
        assert len(result) == 1
        assert result[0].symbol == SYMBOL

    def test_list_depends_on_empty_when_no_deps(self):
        meta = FileMeta()
        assert list_depends_on(meta) == []


# ======================== dependents_of ========================

class TestDependentsOf:
    def test_returns_dependents_when_gid_exists(self):
        provider_meta = make_provider_meta()
        consumer_meta = FileMeta()

        add_dependency(consumer_meta, CONSUMER_PATH, provider_meta, PROVIDER_PATH, SYMBOL_NAME, gid=GID)

        result = dependents_of(provider_meta, GID)
        assert CONSUMER_PATH in result

    def test_empty_when_no_dependents(self):
        provider_meta = make_provider_meta()
        result = dependents_of(provider_meta, GID)
        assert result == []

    def test_raises_when_gid_not_found(self):
        provider_meta = FileMeta()
        with pytest.raises(GuaranteeNotFoundError):
            dependents_of(provider_meta, "nonexistent.id")
