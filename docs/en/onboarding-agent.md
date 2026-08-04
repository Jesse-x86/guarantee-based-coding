# Onboarding Instructions for Agents

> Language: [简体中文](../zh/onboarding-agent.md) | **English**

Hi. If you're reading this, you're working inside a project and your human wants to use GBC — glad
you're here to wire it up. It's not much: confirm the tool is ready, wire it into the current
project, then work by the recommended workflow.

Two roles throughout:

- **The working project** — the project you're in right now; GBC gets wired in here.
- **The GBC tool** — a standalone tool already installed as the `gbc` command. You call it and
  point it at the working project.

---

## ① Confirm the tool is ready

GBC ships as a standalone command-line tool. Confirm it's installed:

```bash
gbc --help
```

If not, have your human install it (or install it yourself when authorized):
`pipx install guarantee-based-coding`. Once installed, the `gbc` command is on PATH and the same
install is reused across projects.

> For a localized wiring guide (where the endpoints / skill files are), run `gbc setup` any time.

---

## ② Wire GBC into the current project

GBC's abilities reach you through two paths — use whichever you support (or both):

### Path A — MCP (recommended)

Register GBC's MCP server for yourself, pointed at the working project. Start command:

```
gbc mcp up <absolute path to the working project root>
```

Register it however your framework adds MCP servers (for Claude Code, a `.mcp.json` in the project
root). Reconnect / restart afterward and the tools appear. MCP exposes **both subsystems**: the
guarantee engine + intent documents (`doc_*` tools).

### Path B — Skills

Run `gbc setup`; it prints the absolute path to the bundled skill files. Copy them into wherever
your framework discovers skills (GBC materializes the files, you place them). The `gbc-cli` skill
teaches you to use every `gbc` command.

### Once per project

GBC points at the working project, and the test executor follows that project's environment and
language — switch projects and it naturally needs reconfiguring. So re-run this wiring once per new
project (a few minutes).

---

## ③ Register an executor + smoke test

- Register a test executor (how to run tests): see [reference.md](./reference.md#executor-config).
  Give it a **project-scoped name** (`pytest-<project>`), since executors are shared across
  projects by name.
- Smoke test: run `gbc tree` or `gbc doctor check` (over MCP, call `tree` / `check_consistency`).
  If it returns, you're wired.

---

## ④ Before you touch code: don't let guarantees rot into fake safety

Wiring only connects the tools — it can't stop you from making them lie. A guarantee only protects
what it can actually catch, and a handful of moves quietly turn it into theater. These three are
worth carrying from day one, because they fail **silently** (full trap list in
[workflow.md](./workflow.md#a-few-traps-that-fail-silently)):

- **A guarantee test must be able to go red**: a fixture that only walks the happy path stays green
  even after the behavior breaks = guarding nothing.
- **Promote the behavior you actually depend on**: non-null / non-empty / raises-on-X / ordering /
  idempotence are behavior, not signature, and a free symbol dependency has no test guarding them.
- **When a guarantee goes red, restore it or announce it — never loosen the test**: relaxing /
  retiring a test to turn green silently downgrades a real guarantee into fake safety.

Every time you register a dependency or a guarantee, ask: **"If the behavior I care about broke
right now, would a test actually go red?"** If no, fix that first.

---

## ⑤ Hierarchy and authority: stay within your scope

- **Top-level agent (architect / lead)**: you lead the intent. Draft `gbc.md` changes through
  `gbc doc` (MCP doc tools / CLI) — never hand-edit — bound each subtask, review the local
  contracts it registers, and do the final integration check after subtasks return.
- **Subagent (task worker)**: a focused implementer. It reads `gbc.md` without changing intent,
  maintains any interface artifact required by that language/project (a Python project may use
  `.pyi`) with the code, and owns the local GBC contracts introduced by its implementation:
  query/reuse guarantees, register actual dependencies, and when a needed
  guarantee is missing, write a narrow test that can genuinely go red and create it. Then self-prove with `verify_provider` /
  `verify_guarantee`. An unregistered behavioral dependency means the task is not done.
- **Guardrails**: if your framework supports hooks (e.g. Claude Code's `pre-tool-use`), block every
  agent from hand-editing GBC-managed files, and block subagents from changing intent or performing
  unauthorized cross-scope operations such as retiring/disabling guarantees or refactoring other
  files. **Do not blanket-block dependency registration, guarantee creation, or verification for
  subagents.** Enforcement comes from the framework, independent of MCP vs CLI.

---

The full "working safely under GBC" is in [workflow.md](./workflow.md); a command / tool cheat sheet
is in [reference.md](./reference.md); core concepts are in [concepts.md](./concepts.md).
