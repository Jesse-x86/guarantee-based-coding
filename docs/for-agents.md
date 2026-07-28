# Wiring GBC in (for Agents)

Hi. If you're reading this, you're working inside a project and your human wants to use GBC — glad
you're here to wire it up for them. It's not much: first get the GBC tool ready, then onboard each
project once.

Two roles you'll use throughout:

- **The working project** — the project you're in right now, where GBC gets wired in.
- **The GBC tool repo** — the `guarantee-based-coding` repo itself; `serve.py`, the templates, and
  the `setup-gbc` skill all live here. You read from it and point at it.

## ① First time: get the GBC tool ready

Do this once; every project reuses it. This step only touches the **GBC tool repo**.

1. **Find the GBC tool repo.** If you're not sure where it is, follow your human's autonomy preference: if they run you autonomous (or their rules say not to keep asking), search the obvious places yourself; if they prefer you ask before acting, ask them for the path.
2. **Install its dependencies.** It ships a `requirements.txt` — install it into a suitable Python
   environment. Which environment and how is up to you and your human's conventions.
3. **Install the `setup-gbc` skill.** It's under the GBC tool repo's `skills/setup-gbc/`; install it
   the way you install skills. You'll use it every time you onboard a project.
4. **Know how `setup-gbc` remembers the repo.** It caches the GBC repo path and the interpreter in
   `gbc.config.json` next to its `SKILL.md` (`{"gbc_repo": "...", "gbc_interpreter": "..."}`).
   Rule: file exists and the paths work → use them; file missing or a path stale/wrong → write them
   back in (one-time burn-in that re-heals whenever it goes stale). So the first time you run
   `setup-gbc` after installing, it burns the paths in — nothing to do by hand at install, just be
   aware that's where the path lives.

Once done, these four are good for all projects.

## ② Each project: run setup-gbc to onboard

Run the `setup-gbc` skill inside the **working project** and it walks you through wiring GBC in —
usually within one session. It registers the gbc MCP server, a test executor, a `gbc-doc` intent
skill, and drops GBC's operating rules into the project's instruction file.

Those rules assume **you are the top-level agent**: preferred default is plan → align intent
(default install **requires explicit human approval** before landing gbc.md; if your human asks
you to delete that line from the instruction file, the rule simply disappears from your context
and autonomy goes up — drift risk too) → dispatch subagents (brief = sliced intent **and**
internal constraints, **writable target file(s)**, everything else **read-only**) → subagent
self-verifies and registers guarantees for new behavior → **you** final-gate via GBC tools (MCP
by default — never hand-run the underlying test runner). Planning and implementation in one agent
is allowed for small changes; day-to-day coding is not the default role of the top-level agent.
After onboarding, treat the block in the instruction file as the living workflow — including
`[[ ]]` references, refactor tools, and how to move/rename safely.

> Why once per project? GBC points at the working project, and the test executor follows that
> project's environment and language — switch projects and it naturally needs reconfiguring. That's
> why it's a re-runnable skill rather than a one-time install.

## ③ Before you touch code: don't let guarantees rot into fake safety

Setup wires the tools in — it can't stop you from making them lie. A guarantee only
protects what it can actually catch, and a handful of moves quietly turn it into theater.
The full trap list is in [manual.md §7–8](./manual_EN.md), and [demo/EXAMPLE.md](../demo/EXAMPLE.md)
walks a runnable version of exactly this — its *strong* vs *weak* scenarios show one guarantee
catching, then silently missing, the same non-null→null break. These three are worth carrying
in your head from day one, because they're the ones that fail *silently*:

- **A guarantee test must be able to go red.** The deadliest failure isn't a missing test —
  it's a test whose fixture only ever walks the happy path, so it stays green even after the
  behavior breaks. A "non-empty" guarantee whose fixture can never produce empty is guarding
  nothing. Give the fixture a way to produce the bad value (empty / None / exception /
  duplicate) and confirm the test actually goes red when the promise is violated. Narrow ≠ soft.
- **Promote the behavior you actually depend on.** Non-null, non-empty, raises-on-X, ordering,
  idempotence — these are behavior, not signature, and a free symbol dependency has no test
  guarding them. The classic silent crash: an upstream weakens "non-null" to "maybe null" and a
  downstream hits a NoneType — because non-null was never named. (Still default to free symbol
  deps; just don't leave a *behavioral* one unnamed.)
- **When a guarantee goes red, restore it or announce it — never loosen the test.** Relaxing or
  retiring a test to turn red green silently downgrades a real guarantee into fake safety.
  Breaking is allowed; breaking quietly is not — a red means either put the behavior back, or
  make every dependent adapt.

Smell test, every time you register a dependency or a guarantee: *"If the behavior I care about
broke right now, would a test actually go red?"* If no, you have a symbol dependency pretending
to be a guarantee, or a happy-path fixture pretending to be a test. Fix that first.

Once onboarded, [manual.md](./manual_EN.md) covers how to change code safely under GBC in full.
