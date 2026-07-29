# Guarantee-Based Coding (GBC)

**Instead of hoping the AI gets smarter, make it so even a dumb agent can't break your code.**

**中文版本: [README.md](./README.md)**

GBC turns "will this change quietly break something elsewhere?" from a worry into a fact you can
verify on the spot: the behaviors you care about are registered as test-backed **guarantees**. Run
them after every change — all green means safe; a red tells you exactly what you broke and who
depends on it.

---

## 🚀 Quick start

```bash
pip install guarantee-based-coding
gbc setup        # prints a localized wiring guide: how to connect MCP / skills to your agent
```

The `gbc` command is now on your PATH. Full onboarding (install → wire into your agent → smoke
test) is in **[docs/en/quick-start.md](./docs/en/quick-start.md)**.

Want your agent to wire it in for you? Hand it
**[docs/en/onboarding-agent.md](./docs/en/onboarding-agent.md)**.

---

## 🎬 See the demo

See what GBC looks like when it catches a break — pinpointing which guarantee failed and why.

```text
RED  passed=0 failed=1 skipped=0
failed: config_loader.get_config.never_none

── config_loader.get_config.never_none ──
E       AssertionError: assert None is not None
E        +  where None = get_config()
tests/test_never_none.py:12: AssertionError
1 failed in 0.08s
```

Near-zero config to run; the menu has both English and Chinese scenarios:

```bash
pip install -r demo/requirements.txt
python demo/run_demo.py
```

| Scenario | What it shows |
|----------|---------------|
| `config-service-strong` / `*-en` | **Caught** — a strong test covers the edge path, so breaking code triggers a RED block |
| `config-service-weak` / `*-en` | **Missed** — a weak test only covers the happy path, so the break stays GREEN |
| `config-service-bad-test` / `*-en` | **Born-green** — the test itself is buggy and registration is refused on the spot |
| `workflow-before-after` / `*-en` | **Workflow contrast** — how development logic evolves before/after adopting GBC |

> **Hand it to an agent**: [demo/EXAMPLE_EN.md](./demo/EXAMPLE_EN.md) (EN) / [demo/EXAMPLE.md](./demo/EXAMPLE.md) (ZH) — tell it "walk me through this." More in [demo/](./demo/).

---

## 📚 Documentation

| You want to | Go here |
|-------------|---------|
| Install and get running | [Quick Start](./docs/en/quick-start.md) |
| Understand what GBC protects | [Core Concepts](./docs/en/concepts.md) |
| Change code safely under GBC | [Working under GBC](./docs/en/workflow.md) |
| Look up a command / tool / executor | [Reference](./docs/en/reference.md) |
| You're an agent asked to wire GBC in | [Agent Onboarding](./docs/en/onboarding-agent.md) |

Chinese docs: [docs/zh/](./docs/zh/).

---

## The core idea

Dependencies between code are essentially a set of **guarantees**. Module A depends on module B not
on its implementation details, but on some of its behavioral promises — the type, format, semantics
of return values. Make those guarantees **explicit, executable, and verifiable**, and correctness
shifts from "the AI thinks it got it right" to "every depended-on guarantee still passes" — a
mechanically verifiable boolean.

![Without GBC vs with GBC](docs/assets/workflow-comparison_en.svg)

GBC is **not** another AI coding assistant challenging Cursor / Aider — it fills the piece they lack
in large projects: a **machine-verifiable boundary for change**. It works *with* those agents
(check the dependency tree before, pass all relevant guarantees after) and differs from CI (CI is
after-the-fact; GBC is an admission gate that catches errors before they land, inside the agent's
context).

Full concepts, architecture diagram, and how it differs from existing ideas (Design by Contract /
testing) are in [Core Concepts](./docs/en/concepts.md).

---

## Current status

GBC is a working Python distribution package (`pip install guarantee-based-coding`), and it manages
its own `.gbc/` with GBC (dogfooding):

- ✅ Core guarantee mechanism (named ids, many-to-one, born-green, retirement protection, reverse
  lookup)
- ✅ Language-agnostic executor config
- ✅ CLI + MCP dual interface (intent docs `gbc doc` fully exposed over MCP)
- ✅ Intent-document subsystem (`gbc doc` / web editor)
- ✅ Bundled wiring guide (`gbc setup`) and a skill pack for CLI-only agents
- ✅ Atomic file writes + backups
- ✅ Interactive Demo Runner (weak vs strong test gate contrast)

**Honest limitations**: protection ceiling = test quality (happy-path-only tests are a false sense
of safety); dependencies must be registered actively, and coverage takes ongoing investment as the
project grows; every verification really runs tests, so there's some latency. See
[Core Concepts · Limitations](./docs/en/concepts.md#limitations-stated-honestly).

---

## License

This project is licensed under [Apache-2.0](./LICENSE).

## Contact

If this direction interests you, stars, issues, or reaching out directly are all welcome.
