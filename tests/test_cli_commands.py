# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# see the LICENSE file for the full text.

"""保证:入口分发器(gbc.entry)整合后的命令树承诺。

- 唯一入口暴露两子系统的表面 + 服务/辅助命令。
- gbc rules 输出双语规则文本,声明"非强制沙箱"。
- gbc doc 经 intent 子系统合规读意图。
- gbc setup 输出本地化接线指南，只给坐标(MCP 入口/skills 目录)。
- 根 --help 根据 --lang / GBC_LANG 输出对应语言文本。
"""
import importlib
import os
from pathlib import Path
import subprocess
import sys

from click.testing import CliRunner

from gbc.app.assets import SKILLS_DIR
from gbc.entry import get_wrapped_app

runner = CliRunner()


def test_command_tree_has_all_commands():
    """承诺:保证命令 + doc/mcp/editor/rules/setup 都在唯一入口下。"""
    result = runner.invoke(get_wrapped_app(), ["--help"])
    assert result.exit_code == 0
    for cmd in ("guarantee", "verify", "doc", "mcp", "editor", "rules", "setup"):
        assert cmd in result.output


_PROJECT_COMMAND_PATHS = (
    ("guarantee", "create"),
    ("guarantee", "update"),
    ("guarantee", "retire"),
    ("guarantee", "disable"),
    ("guarantee", "enable"),
    ("guarantee", "list"),
    ("dep", "add"),
    ("dep", "remove"),
    ("dep", "of"),
    ("dep", "who"),
    ("verify", "provider"),
    ("verify", "single"),
    ("refactor", "file"),
    ("refactor", "rename-id"),
    ("refactor", "func"),
    ("tree",),
    ("doctor", "check"),
    ("executor", "upsert"),
)


def test_all_guarantee_engine_project_leaves_expose_project_option():
    """承诺:每个保证引擎项目操作叶子都暴露后置 --project/-C。"""
    command = get_wrapped_app()
    for path in _PROJECT_COMMAND_PATHS:
        result = runner.invoke(command, [*path, "--help"])
        assert result.exit_code == 0, (path, result.output)
        assert "--project" in result.output, path
        assert "-C" in result.output, path


def test_doctor_project_option_overrides_unrelated_cwd(monkeypatch, tmp_path):
    """承诺:doctor 的后置 --project 可从无关嵌套 cwd 指向目标项目。"""
    from gbc.app.config import project as project_config

    original_project = project_config.get_current_project()
    target = tmp_path / "target"
    (target / ".gbc").mkdir(parents=True)
    unrelated = tmp_path / "unrelated" / "nested"
    unrelated.mkdir(parents=True)
    monkeypatch.chdir(unrelated)
    project_config.set_current_project(unrelated)
    try:
        result = runner.invoke(
            get_wrapped_app(), ["doctor", "check", "--project", str(target)]
        )
        assert result.exit_code == 0, result.output
        assert "consistent" in result.output
        assert project_config.get_current_project() == target.resolve()
    finally:
        project_config.set_current_project(original_project)


def test_doctor_missing_gbc_is_nonzero_and_not_consistent(tmp_path):
    """承诺:目标根缺少 .gbc 时 CLI 体检失败，不能假绿。"""
    from gbc.app.config import project as project_config

    original_project = project_config.get_current_project()
    missing = tmp_path / "missing"
    missing.mkdir()
    try:
        result = runner.invoke(
            get_wrapped_app(), ["doctor", "check", "--project", str(missing)]
        )
        assert result.exit_code != 0
        assert "consistent" not in result.output.lower()
    finally:
        project_config.set_current_project(original_project)


def test_doctor_uses_environment_project_and_trailing_option_overrides_it(
    monkeypatch, tmp_path
):
    """承诺:GBC_PROJECT_ROOT 是默认值，后置 --project 可显式覆盖。"""
    from gbc.app.config import project as project_config

    original_project = project_config.get_current_project()
    environment_project = tmp_path / "from-env"
    explicit_project = tmp_path / "explicit"
    (environment_project / ".gbc").mkdir(parents=True)
    (explicit_project / ".gbc").mkdir(parents=True)
    try:
        monkeypatch.setenv(project_config.GBC_PROJECT_ROOT, str(environment_project))
        importlib.reload(project_config)

        from_environment = runner.invoke(get_wrapped_app(), ["doctor", "check"])
        assert from_environment.exit_code == 0, from_environment.output
        assert "consistent" in from_environment.output
        assert project_config.get_current_project() == environment_project.resolve()

        # CliRunner reuses this process, so restore the expected default before
        # proving that the trailing explicit option replaces it.
        project_config.set_current_project(environment_project)
        explicit = runner.invoke(
            get_wrapped_app(),
            ["doctor", "check", "--project", str(explicit_project)],
        )
        assert explicit.exit_code == 0, explicit.output
        assert "consistent" in explicit.output
        assert project_config.get_current_project() == explicit_project.resolve()
    finally:
        project_config.set_current_project(original_project)


def test_rules_outputs_bilingual_and_non_sandbox():
    """承诺:rules 双语可出,且都强调不是强制沙箱。"""
    zh = runner.invoke(get_wrapped_app(), ["rules", "--lang", "zh"])
    en = runner.invoke(get_wrapped_app(), ["rules", "--lang", "en"])
    assert zh.exit_code == 0 and en.exit_code == 0
    assert "强制" in zh.output
    assert "sandbox" in en.output.lower()


def test_mcp_up_is_a_command():
    """承诺:mcp up 子命令存在。"""
    result = runner.invoke(get_wrapped_app(), ["mcp", "--help"])
    assert result.exit_code == 0
    assert "up" in result.output


def test_setup_prints_wiring_guide():
    """承诺:setup 输出接线指南，含 MCP 入口与 skills 目录坐标，且双语可出。"""
    zh = runner.invoke(get_wrapped_app(), ["setup", "--lang", "zh"])
    en = runner.invoke(get_wrapped_app(), ["setup", "--lang", "en"])
    assert zh.exit_code == 0 and en.exit_code == 0
    # 只给坐标：MCP 启动入口 + skills 目录路径(占位符已填充)。
    for out in (zh.output, en.output):
        assert "gbc mcp up" in out
        assert str(SKILLS_DIR) in out


def test_doc_show_reads_intent(tmp_path):
    """承诺:doc show 经 intent 子系统读出意图(用 --project 显式指定)。"""
    from gbc.app.intent import base
    gbc_root, _ = base.resolve_gbc(str(tmp_path))
    base.set_intent(gbc_root, "sub", "hello intent")

    result = runner.invoke(get_wrapped_app(), ["doc", "show", "sub", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert "hello intent" in result.output


# ============================================================================
# Help i18n — CliRunner（等价于进程内调用，覆盖 i18n_wrap_click_tree 路径）
# ============================================================================


def test_root_help_defaults_to_en(monkeypatch):
    """承诺:无 env/--lang 时根 --help 默认输出英文。"""
    monkeypatch.delenv("GBC_LANG", raising=False)
    result = runner.invoke(get_wrapped_app(), ["--help"])
    assert result.exit_code == 0
    # 英文关键词
    assert "Guarantee-Based Coding CLI tool" in result.output
    assert "Guarantee CRUD" in result.output
    assert "Consistency check" in result.output
    # 不存在中文关键词
    assert "命令行工具" not in result.output
    assert "增删改查" not in result.output


def test_root_help_zh_via_env(monkeypatch):
    """承诺:GBC_LANG=zh 环境下根 --help 输出中文。"""
    monkeypatch.setenv("GBC_LANG", "zh")
    result = runner.invoke(get_wrapped_app(), ["--help"])
    assert result.exit_code == 0
    # 中文关键词
    assert "命令行工具" in result.output
    assert "增删改查" in result.output
    assert "一致性体检" in result.output


def test_root_help_explicit_lang_overrides_env(monkeypatch):
    """承诺:显式 --lang zh 压过环境变量 GBC_LANG=en。

    通过 monkeypatch sys.argv 模拟 CLI 调用中 _lang_from_argv() 的解析路径，
    然后再经 CliRunner 调用已包装的 Click group。
    """
    monkeypatch.setenv("GBC_LANG", "en")
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang", "zh", "--help"])
    result = runner.invoke(get_wrapped_app(), ["--help"])
    assert result.exit_code == 0
    # 中文关键词——显式 --lang zh 压过 env en
    assert "命令行工具" in result.output
    assert "增删改查" in result.output


def test_root_help_lang_equals_syntax(monkeypatch):
    """承诺:--lang=zh 等号语法也被正确解析（CLI 常见语法）。"""
    monkeypatch.setenv("GBC_LANG", "en")
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang=zh", "--help"])
    result = runner.invoke(get_wrapped_app(), ["--help"])
    assert result.exit_code == 0
    # 中文关键词——等号语法 --lang=zh 压过 env en
    assert "命令行工具" in result.output
    assert "增删改查" in result.output


def test_subcommand_help_en(monkeypatch):
    """承诺:子命令 --help 在英文环境下显示英文描述。"""
    monkeypatch.delenv("GBC_LANG", raising=False)
    result = runner.invoke(get_wrapped_app(), ["guarantee", "--help"])
    assert result.exit_code == 0
    assert "Guarantee CRUD" in result.output


def test_subcommand_help_zh(monkeypatch):
    """承诺:子命令 --help 在中文环境下显示中文描述。"""
    monkeypatch.setenv("GBC_LANG", "zh")
    result = runner.invoke(get_wrapped_app(), ["guarantee", "--help"])
    assert result.exit_code == 0
    assert "增删改查" in result.output


def test_rules_setup_help_i18n(monkeypatch):
    """承诺:rules/setup 的 --help 描述支持中英双语。"""
    # en
    monkeypatch.setenv("GBC_LANG", "en")
    en = runner.invoke(get_wrapped_app(), ["--help"])
    assert en.exit_code == 0
    assert "guardrail" in en.output.lower()
    assert "wiring guide" in en.output.lower()
    # zh
    monkeypatch.setenv("GBC_LANG", "zh")
    zh = runner.invoke(get_wrapped_app(), ["--help"])
    assert zh.exit_code == 0
    assert "围栏" in zh.output
    assert "接线指南" in zh.output


def test_lang_from_argv_rejects_flags(monkeypatch):
    """承诺：_lang_from_argv 拒绝以 - 开头的值，防把 --help 等 option 当语言码。"""
    from gbc.app.interface.cli import _lang_from_argv
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang", "--help"])
    assert _lang_from_argv() is None, "--help 不应被当语言码"
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang=--help"])
    assert _lang_from_argv() is None, "--help（等号语法）不应被当语言码"
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang=zh"])
    assert _lang_from_argv() == "zh", "正常 lang 值应正确解析"
    monkeypatch.setattr(sys, "argv", ["gbc", "--lang", "zh"])
    assert _lang_from_argv() == "zh", "正常 lang 值(两 token)应正确解析"


# ============================================================================
# Help i18n — 真实子进程端到端（覆盖 main() → get_wrapped_app() → Click 完整路径）
# ============================================================================

_PYTHON = sys.executable
_ENTRY_MOD = "gbc.entry"


def _child_env(overrides=None):
    """构建隔离语言设置且固定 UTF-8 的子 Python 环境。"""
    env = {k: v for k, v in os.environ.items() if k != "GBC_LANG"}
    env.update(overrides or {})
    env["PYTHONUTF8"] = "1"
    return env


def _gbc(*args, env=None):
    """运行 `python -m gbc.entry ...` 子进程，返回 CompletedProcess。

    默认剥离外部 GBC_LANG，避免开发者环境泄漏到测试。
    """
    return subprocess.run(
        [_PYTHON, "-m", _ENTRY_MOD, *args],
        capture_output=True, text=True, timeout=30, env=_child_env(env),
    )


def test_e2e_default_en():
    """承诺:真实子进程，无 env/--lang 时根 --help 输出英文。"""
    p = _gbc("--help")
    assert p.returncode == 0
    assert "Guarantee-Based Coding CLI tool" in p.stdout
    assert "Guarantee CRUD" in p.stdout
    assert "命令行工具" not in p.stdout


def test_e2e_env_zh():
    """承诺:真实子进程，GBC_LANG=zh 时根 --help 输出中文。"""
    p = _gbc("--help", env={"GBC_LANG": "zh"})
    assert p.returncode == 0
    assert "命令行工具" in p.stdout
    assert "增删改查" in p.stdout
    assert "Guarantee CRUD" not in p.stdout


def test_e2e_explicit_overrides_env():
    """承诺:真实子进程，显式 --lang zh 压过 GBC_LANG=en。"""
    p = _gbc("--lang", "zh", "--help", env={"GBC_LANG": "en"})
    assert p.returncode == 0
    assert "命令行工具" in p.stdout
    assert "增删改查" in p.stdout


def test_e2e_lang_equals_syntax():
    """承诺:真实子进程，--lang=zh 等号语法正确解析。"""
    p = _gbc("--lang=zh", "--help", env={"GBC_LANG": "en"})
    assert p.returncode == 0
    assert "命令行工具" in p.stdout
    assert "增删改查" in p.stdout


def test_e2e_lang_bad_value_no_i18n_leak():
    """承诺：--lang 接非法值（如空串、--）时不会泄漏裸 i18n key。

    _lang_from_argv guard 拒绝无效值，resolve_lang 回退到 en。
    不与 --help 组合（Click 会把 --help 当 lang 参数值消费，是 Click 自身行为）。
    """
    # 给一个无效但非 option 的值，让 Click 正常路由到 "Missing command"
    p = _gbc("--lang", "xx-invalid-xx", "nonexistent_cmd")
    assert p.returncode != 0
    # 错误输出不应泄漏裸 i18n key
    combined = p.stdout + p.stderr
    assert "cli.app.help" not in combined
    assert "cli.guarantee.help" not in combined


# ============================================================================
# console_scripts 入口路径（模拟 pipx 安装后的真实 gbc 命令）
# ============================================================================


def test_pyproject_scripts_is_main_cli():
    """承诺：pyproject.toml [project.scripts] gbc 指向 main_cli（i18n 包装后入口），不是裸 app。

    pipx/setuptools 生成的 wrapper 脚本调用该符号；若指向裸 Typer app，
    则 --help 绕过了 i18n_wrap_click_tree，显示裸 i18n key。

    用文本级解析（regex 限定 section），兼容 Python 3.10。
    """
    import re

    root = Path(__file__).resolve().parent.parent
    text = (root / "pyproject.toml").read_text(encoding="utf-8")

    # 定位 [project.scripts] section：从该行到下一个 [section] 或 EOF
    sec = re.search(r"^\[project\.scripts\]", text, re.MULTILINE)
    assert sec is not None, "未找到 [project.scripts] section"
    section_text = text[sec.start():]
    # 截断到下一个以 [ 开头的行（排除自身）
    next_sec = re.search(r"\n\[", section_text[1:])
    if next_sec:
        section_text = section_text[:next_sec.start() + 1]

    # 在 section 内匹配 gbc = "..."，^ 锚定行首防注释误命中
    m = re.search(r"^gbc\s*=\s*\"([^\"]+)\"", section_text, re.MULTILINE)
    assert m is not None, "未在 [project.scripts] 中找到 gbc = \"...\" 条目"
    entry = m.group(1)
    assert entry == "gbc.entry:main_cli", (
        f"[project.scripts] gbc = '{entry}'，"
        f"应指向 'gbc.entry:main_cli'（i18n 包装后入口）"
    )


def test_e2e_main_cli_path_is_i18n():
    """承诺：通过 main_cli（console_scripts 入口路径）的 --help 输出已翻译文本。

    模拟 pipx 安装后 `gbc --help` 的真实调用路径——设置 sys.argv 后直接调 main_cli，
    不走 python -m 旁路。
    """
    code = f"""
import sys
sys.argv = ["gbc", "--help"]
from gbc.entry import main_cli
main_cli()
"""
    p = subprocess.run(
        [_PYTHON, "-c", code],
        capture_output=True, text=True, timeout=30,
        env=_child_env(),
    )
    assert p.returncode == 0
    # 英文翻译（默认）出现在输出中
    assert "Guarantee-Based Coding CLI tool" in p.stdout
    assert "Guarantee CRUD" in p.stdout
    # 不应出现裸 i18n key（绕过了包装）
    assert "cli.app.help" not in p.stdout
    assert "cli.guarantee.help" not in p.stdout


def test_e2e_main_cli_path_zh():
    """承诺：main_cli 路径下 --lang zh 输出中文。"""
    code = f"""
import sys
sys.argv = ["gbc", "--lang", "zh", "--help"]
from gbc.entry import main_cli
main_cli()
"""
    p = subprocess.run(
        [_PYTHON, "-c", code],
        capture_output=True, text=True, timeout=30,
        env=_child_env(),
    )
    assert p.returncode == 0
    assert "命令行工具" in p.stdout
    assert "增删改查" in p.stdout


def test_e2e_main_cli_returns_nonzero_on_error():
    """承诺：main_cli 路径下非法命令返回非零退出码（保持 Click/Typer 语义）。"""
    code = f"""
import sys
sys.argv = ["gbc", "nonexistent_cmd"]
from gbc.entry import main_cli
main_cli()
"""
    p = subprocess.run(
        [_PYTHON, "-c", code],
        capture_output=True, text=True, timeout=30,
        env=_child_env(),
    )
    assert p.returncode != 0
