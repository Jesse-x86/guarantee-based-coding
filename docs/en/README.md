# Guarantee-Based Coding (GBC)

**Stop AI changes from breaking code elsewhere.**

Getting AI to change a feature is often quick. The trouble starts when that change breaks
something elsewhere.

You can wait for tests or CI to catch it and send the agent back to fix it. But some of that
back-and-forth is avoidable: another module already depended on that behavior—the agent just
didn't know it when making the change.

GBC records those expectations: what a module is responsible for, which parts of the code rely
on it, what behavior needs to stay intact, and which tests to run. The agent has something to
consult before editing and checks to run afterward.

[中文](../../README.md) · [GBC in two examples](walkthrough.md) · [Quick start](quick-start.md)

## How does one line break code you never touched?

You ask an agent to simplify configuration loading. It removes a default:

```diff
- return config.get(key, "")
+ return config.get(key)
```

Existing keys still work. But another module relies on missing keys returning an empty string
and calls `.strip()` on the result. Now it receives `None` and crashes—even though that module
isn't in the diff.

In GBC, that behavior is a named, test-backed **guarantee**, and the module using it is registered
as a consumer. The agent can inspect this dependency before editing. After the change, running
the guarantee catches the regression if its test covers the missing-key case.

**Who promises what → who relies on it → which check protects it.** GBC maintains these
relationships so local changes have explicit checks and failures point to a relied-on promise.

Architecture has a related problem: a feature can work while its responsibilities drift.
GBC's intent documents describe current responsibilities, internal constraints, and file roles
by directory. They guide the agent's changes; guarantee tests verify specific behavior.

→ **[Read the full examples: preserve responsibilities and catch behavioral regressions](walkthrough.md)**

## Inside one code change

1. **Inspect relevant context.** Look up the target files' architectural intent, direct dependencies,
   and behavioral promises without loading all the project's documentation at once.
2. **Implement within those boundaries.** Preserve existing contracts; coordinate changes when
   responsibilities or relied-on behavior need to change.
3. **Verify and correct.** Run related guarantees during development, feed failures back to the
   agent, and verify again after fixing them.

GBC works with your existing agent through CLI or MCP and runs your project's own tests.
It supplies context and results; the agent interprets and fixes issues. Whether a failed check
blocks a commit or merge depends on your integration and permissions.

## Already using ADRs, AGENTS.md, and CI?

They work together. GBC focuses on **what this change must preserve, which code relies on it,
and how to check that the promises still hold.**

| Existing tool or document | Main question | What GBC adds |
|---|---|---|
| ADR | Why did we make this architectural decision? | Current responsibilities and constraints organized by code location, with links to decision history when needed |
| AGENTS.md | How should an agent work in this project? | Queryable, tool-maintained intent structure and behavioral dependencies; AGENTS.md can direct agents to use GBC |
| Tests | Does this check pass now? | Named promises, their providers and consumers, and the checks that back them |
| CI/CD | When and where do builds, checks, and delivery run? | Contract verification that can run inside an agent's editing process or in CI |

ADRs and AGENTS.md can both be organized by module; CI can give rapid feedback too. GBC connects
relevant context, behavioral dependencies, and executable checks. Splitting documents or running
tests earlier is only part of that. See [Core concepts](concepts.md#how-it-differs-from-existing-ideas)
for the fuller comparison.

## Quick start

```bash
pipx install guarantee-based-coding
gbc setup
```

`gbc setup` prints the agent integration guide. Follow the [Quick start](quick-start.md) for
installation, integration, and a smoke check. You can also hand the
[Agent onboarding guide](onboarding-agent.md) to your agent for help getting connected.

## Read more

| What you want to understand | Read |
|---|---|
| What GBC contributes to an actual change | [Walkthrough](walkthrough.md) |
| How intent, guarantees, and consumers fit together | [Core concepts](concepts.md) |
| Maintaining contracts, writing tests, and accepting changes | [Workflow](workflow.md) |
| CLI, MCP tools, and test execution configuration | [Reference](reference.md) |
| Version changes and migration notes | [Changelog](../../CHANGELOG.md) |

GBC uses this method to maintain its own project. It supports CLI and MCP, and connects to test
languages and frameworks through executor configuration. Project metadata lives in `.gbc/`;
business code needs no GBC-specific annotations.

**Protection depends on registered contracts and their tests.** Dependencies need active maintenance;
uncovered behavior is not automatically protected. Intent guides changes, but natural-language
constraints do not automatically become executable checks. Test and contract changes still need
review. GREEN means no executed check failed; acceptance also requires the needed checks to run.
See [Limitations](concepts.md#limitations-stated-honestly).

## License and contact

[Apache-2.0](../../LICENSE). Issues with questions, feedback, and experience reports are welcome.
