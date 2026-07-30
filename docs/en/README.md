# Guarantee-Based Coding (GBC)

**Instead of hoping the AI gets smarter, make it so even a dumb agent can't break your code.**

**中文版本: [README.md](../../README.md)**

GBC turns "will this change quietly break something elsewhere?" from a worry into a fact you can
verify on the spot: the behaviors you care about are registered as test-backed **guarantees**. Run
them after every change — all green means safe; a red tells you exactly what you broke and who
depends on it.

---

## 🚀 Quick start

```bash
pipx install guarantee-based-coding
gbc setup        # prints a localized wiring guide: how to connect MCP / skills to your agent
```

The `gbc` command is now on your PATH. Full onboarding (install → wire into your agent → smoke
test) is in **[docs/en/quick-start.md](quick-start.md)**.

Want your agent to wire it in for you? Hand it
**[docs/en/onboarding-agent.md](onboarding-agent.md)**.

---

> 🚧 **Interactive demo under construction**: the old demo suite is deprecated and a new interactive demo is in the works. For now, start directly from the docs.

---

## 📚 Documentation

| You want to | Go here |
|-------------|---------|
| Install and get running | [Quick Start](quick-start.md) |
| Understand what GBC protects | [Core Concepts](concepts.md) |
| Change code safely under GBC | [Working under GBC](workflow.md) |
| Look up a command / tool / executor | [Reference](reference.md) |
| You're an agent asked to wire GBC in | [Agent Onboarding](onboarding-agent.md) |

Chinese docs: [docs/zh/](../zh/).

---

## The core idea

Dependencies between code are essentially a set of **guarantees**. Module A depends on module B not
on its implementation details, but on some of its behavioral promises — the type, format, semantics
of return values. Make those guarantees **explicit, executable, and verifiable**, and correctness
shifts from "the AI thinks it got it right" to "every depended-on guarantee still passes" — a
mechanically verifiable boolean.

![Without GBC vs with GBC](../assets/workflow-comparison_en.svg)

GBC is **not** another AI coding assistant challenging Cursor / Aider — it fills the piece they lack
in large projects: a **machine-verifiable boundary for change**. It works *with* those agents
(check the dependency tree before, pass all relevant guarantees after) and differs from CI (CI is
after-the-fact; GBC is an admission gate that catches errors before they land, inside the agent's
context).

Full concepts, architecture diagram, and how it differs from existing ideas (Design by Contract /
testing) are in [Core Concepts](concepts.md).

---

## Current status

GBC is a working Python distribution package (`pipx install guarantee-based-coding`), and it manages
its own `.gbc/` with GBC (dogfooding):

- ✅ Core guarantee mechanism (named ids, many-to-one, born-green, retirement protection, reverse
  lookup)
- ✅ Language-agnostic executor config
- ✅ CLI + MCP dual interface (intent docs `gbc doc` fully exposed over MCP)
- ✅ Intent-document subsystem (`gbc doc` / web editor)
- ✅ Bundled wiring guide (`gbc setup`) and a skill pack for CLI-only agents
- ✅ Atomic file writes + backups


**Honest limitations**: protection ceiling = test quality (happy-path-only tests are a false sense
of safety); dependencies must be registered actively, and coverage takes ongoing investment as the
project grows; every verification really runs tests, so there's some latency. See
[Core Concepts · Limitations](concepts.md#limitations-stated-honestly).

---

## License

This project is licensed under [Apache-2.0](../../LICENSE).

## Contact

If this direction interests you, stars, issues, or reaching out directly are all welcome.
