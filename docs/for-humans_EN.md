# Using GBC (for humans)

**中文版: [for-humans.md](./for-humans.md)**

Welcome to GBC. It turns "will this change quietly break something elsewhere?" from a worry into a fact you can verify on the spot: the behaviors you care about get registered as individual, test-backed **guarantees**, and every time you finish a change you run them once — all green means peace of mind, a red one tells you precisely what you broke and who depends on it.

And the best news is: **once GBC is wired in, you barely have to do anything yourself.** Just leave it to your coding agent.

## Getting started

1. Have your agent **install and run GBC's `setup-gbc` skill**.
   - If your agent supports the `.agents/skills` standard, you can copy it over: `cp -r <gbc-path>/skills/setup-gbc .agents/skills/`
   - Or simply paste the content of `skills/setup-gbc/SKILL.md` to your agent.
2. It will ask you a few questions along the way — which Python environment to run GBC in, how your project runs its tests, which file the rules should be written into — just answer honestly, and if something is unclear it will explain first.
3. Once you're done answering, it has wired GBC into the project you're working on. Restart the agent once, and you're ready to go.

## Do this once per project

GBC travels with the project; it's not a one-time install-and-forget: how tests run and which environment is used may differ from project to project. So **every time you start a new project, just have the agent run `setup-gbc` again** — again, a matter of a few minutes.

## Want to know more

- Curious what exactly your agent is doing on its side → [for-agents.md](./for-agents.md)
- Want to do it by hand, or understand the ins and outs of every step → [manual_EN.md](./manual_EN.md) (manual / detailed docs)
