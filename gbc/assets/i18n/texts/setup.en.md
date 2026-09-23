# Wiring GBC into your agent

This guide is for AI agents: when the user says “install GBC for this project”,
follow these steps to connect and verify it. `gbc setup` only prints instructions;
it does not install or configure anything. If it already runs, GBC is usually
installed; the remaining work is connecting this agent to this project. Initial
AI discovery still needs an available command, document, or skill entry point;
this output does not make clients discover GBC automatically.

## 1. Confirm the project and runtime

Confirm the intended project's absolute path, the agent client and its MCP
configuration mechanism, and the OS, interpreter, and PATH used to launch its
processes. Check whether the existing GBC command runs in that environment; do
not mix Windows and WSL paths. If it is missing, install from a trusted source
in the project documentation or supplied by the user; do not invent a pip package
name. One GBC installation can serve multiple projects, but each project's MCP
configuration must explicitly bind its own absolute path.

## 2. Persist MCP configuration for this project

Check the client's supported project-level MCP configuration location and format,
then inspect existing settings. Add or check the GBC stdio entry in the current
project, preserving other servers and user settings; reuse a correct existing
entry. This is a persistent project-level binding, not an in-session switch.
Do not hard-code the current project in global MCP configuration.

Start with `gbc mcp up <ABSOLUTE_PATH_TO_YOUR_PROJECT>`. Replace the example paths
below and place the entry according to the client's schema; these are generic
entry templates, not complete configuration files for every client:

```json
{{
  "command": "gbc",
  "args": ["mcp", "up", "/abs/path/to/your/project"]
}}
```

If the client cannot find `gbc` on PATH, use the verified interpreter's absolute path:

```json
{{
  "command": "/abs/path/to/python",
  "args": ["-m", "gbc.entry", "mcp", "up", "/abs/path/to/your/project"]
}}
```

Windows paths can use forward slashes in JSON; keep a path containing spaces as
one argument. Project state lives under its `.gbc/`, created on first write;
do not generate architectural content just to connect. If the client does not
support project-level MCP, report the limitation and use CLI below instead of
pinning this project globally.

## 3. Reconnect and verify the actual target

Reload / reconnect MCP using the client's mechanism. Check the effective launch
command, arguments, or startup logs shown by the client against the intended
project's absolute path, then make a read-only call such as MCP `tree`.
For an existing project, compare the result with known content in that project.
An empty tree only proves that the call succeeded; it does not by itself prove
correct binding. If the client exposes no effective arguments and the project
has no distinguishable content, report that target binding remains unverified;
do not write test data and call that read-only verification.

## 4. Use CLI / skills without MCP

CLI exposes the same abilities. Learn the commands directly from the bundled skills:

```
{skills_dir}
```

Read the relevant `SKILL.md` first. Integrate it at project level only if the client
needs that; do not automatically create global skills or memory. Run CLI in the
project directory, or explicitly select the target with `--project` / `-C` after
the leaf command, for example this read-only view:

```
gbc tree show --project "/abs/path/to/your/project"
```

## Read the offline manual

`gbc doc list --lang en` lists the five bundled topics. Use
`gbc doc read onboarding-agent --lang en` for onboarding, or
`gbc doc search "guarantee" --lang en` to search. These commands work without a project or
network connection; `--help` remains the short syntax reference. MCP equivalents are
`doc_list`, `doc_read`, and `doc_search`. Project architecture uses `gbc intent` / `intent_*`;
the former intent `doc` names were removed in 0.3.0.

## Three things to remember before you start

- **`gbc.md` is a snapshot of the current state, not a sacred text.** It guards against
  architectural drift, not evolution — to change it, draft → human sign-off → commit via
  gbc intent; that's legitimate evolution, not a violation. Don't pile responsibilities into
  an existing file just because you can't hand-edit it — a god file is the drift-guard
  mechanism turned upside down.
- **A guarantee is NOT full test coverage.** Each guarantee is a named behavioral promise
  guarded by a narrow test; register only behaviors you care about and that are depended
  on, reuse what exists first; a guarantee nobody cares about is a liability.
- **Communicate with the human often.** Report the completed connection, verification
  evidence, and actual blockers; do not report unverified target binding as success.

## Connection boundaries

GBC provides abilities, not an enforced sandbox. `gbc rules` describes the rules;
enforcement requires separate integration with agent framework hooks or similar
mechanisms. “Install GBC” does not authorize automatically deploying enforcement
hooks, generating project architecture, or creating global skills / memory.
Complete the authorized connection; align separately on additional actions.
