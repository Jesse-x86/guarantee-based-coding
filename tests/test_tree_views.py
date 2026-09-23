"""Read-only scoped browsing and direct change-context contracts."""
import pytest

from gbc.app.interface import base
from gbc.app.i18n import current_lang, set_lang
from gbc.app.models.meta import FileMeta, Guarantee, Dependency


@pytest.fixture
def view_project(fake_project, monkeypatch):
    root = fake_project
    previous = current_lang()
    set_lang("en")
    docs = {
        "": "# 意图\nROOT_INTENT\n# 内部约束\nROOT_RULE\n# 文件\n## app/\nCHILD_INTENT\n## outside.py\nOUTSIDE\n",
        "app": "# 意图\nCHILD_INTENT\n# 内部约束\nCHILD_RULE\n# 文件\n## target.py\nTARGET_DESC\n## second.py\nSECOND_DESC\n## deep/\nDEEP_INTENT\n## undocumented/\nFALLBACK_INTENT\n",
        "app/deep": "# 意图\nDEEP_INTENT\n# 内部约束\nDEEP_RULE\n# 文件\n## leaf.py\nLEAF_DESC\n",
    }
    for folder, text in docs.items():
        path = root / ".gbc" / folder / "gbc.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "app/target.py").write_text("", encoding="utf-8")
    (root / "plain.py").write_text("", encoding="utf-8")
    (root / ".gbc/app/interface.pyi").write_text("", encoding="utf-8")
    g = Guarantee(desc="DIRECT_PROMISE", test="tests/check.py::test_direct", executor="unused", disabled=True, dependents=["app/target.py", "app/second.py"])
    own = Guarantee(desc="OWN_PROMISE", test="tests/own.py::test_own", executor="unused", dependents=["consumer.py"])
    metas = {
        "app/target.py": FileMeta(provides={"run.own": own}, depends_on=[Dependency(symbol="provider.py:run", guarantees=["run.direct", "run.missing"])]),
        "app/second.py": FileMeta(depends_on=[Dependency(symbol="provider.py:run", guarantees=["run.direct"]), Dependency(symbol="free.py:call")]),
        "provider.py": FileMeta(provides={"run.direct": g}, depends_on=[Dependency(symbol="transitive.py:hidden")]),
        "consumer.py": FileMeta(depends_on=[Dependency(symbol="app/target.py:run")]),
        "outside.py": FileMeta(depends_on=[Dependency(symbol="app/deep/gap.py:use")]),
        "outside_gap.py": FileMeta(),
    }
    monkeypatch.setattr(base, "_iter_all_metas", lambda: iter(metas.items()))
    yield root
    set_lang(previous)


class TestScopedViews:
    def test_depth_and_folder_projection(self, view_project):
        output = base.render_tree(folder="app", depth=1)
        assert "TARGET_DESC" in output
        assert "DEEP_INTENT" in output and "DEEP_RULE" in output
        assert "[collapsed]" in output and "LEAF_DESC" not in output
        assert "OUTSIDE" not in output
        assert output.count("CHILD_INTENT") == 1
        folders = base.render_tree(folder="app", depth=1, folders_only=True)
        assert "TARGET_DESC" not in folders and "run.own" not in folders
        assert "DEEP_RULE" in folders and "FALLBACK_INTENT" in folders
        assert "[gbc.md missing]" in folders
        zero = base.render_tree(folder="app", depth=0)
        assert "CHILD_RULE" in zero and "TARGET_DESC" not in zero
        assert "interface.pyi" in base.render_tree(folder="app", depth=0, detail=True)
        assert "interface.pyi" not in base.render_tree(folder="app", detail=True, folders_only=True)

    def test_scoped_gaps_use_whole_graph_ignore_depth(self, view_project):
        output = base.render_tree(folder="app", depth=0, gaps=True)
        assert "app/deep/gap.py" in output
        assert "outside_gap.py" not in output
        assert "independent of depth" in output

    @pytest.mark.parametrize("kwargs", [{"folder": "../outside"}, {"folder": "app/target.py"}, {"folder": "absent"}, {"depth": -1}])
    def test_reject_invalid_inputs(self, view_project, kwargs):
        with pytest.raises(ValueError):
            base.render_tree(**kwargs)

    def test_legacy_and_localization(self, view_project):
        assert base.render_tree().startswith(base._TREE_LEGEND)
        set_lang("zh")
        assert "[已折叠]" in base.render_tree(folder="app", depth=0)


class TestDirectContext:
    def test_union_direct_contracts_and_missing_registration(self, view_project, monkeypatch):
        def forbidden(*args, **kwargs):
            raise AssertionError("Browsing must not execute tests")
        monkeypatch.setattr(base.gtee, "verify_guarantee", forbidden)
        output = base.render_tree_for(["app/target.py", "app/second.py", "app/target.py"])
        assert output.count("ROOT_INTENT") == 1 and output.count("CHILD_RULE") == 1
        assert output.count("DIRECT_PROMISE") == 1
        assert "app/target.py, app/second.py" in output
        assert "TARGET_DESC" in output and "OWN_PROMISE" in output
        assert "tests/check.py::test_direct" in output and "[DISABLED]" in output
        assert "consumer.py" in output and "[Named guarantee not registered]" in output
        assert "[Provider file entry not registered] free.py" in output
        assert "[Provider file metadata not registered] free.py" in output
        assert "transitive.py" not in output and "LEAF_DESC" not in output
        missing = base.render_tree_for(["plain.py"])
        assert "[File description not registered]" in missing
        assert "[No registered file metadata]" in missing

    @pytest.mark.parametrize("targets", [[], ["app"], ["../outside.py"], ["absent.py"]])
    def test_reject_invalid_targets(self, view_project, targets):
        with pytest.raises(ValueError):
            base.render_tree_for(targets)
