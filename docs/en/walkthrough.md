# GBC in two examples

[中文](../zh/walkthrough.md) · [Back to README](README.md) · [Quick start](quick-start.md)

An AI edit can put a responsibility in the wrong place or break behavior another module relies on.
These examples show how GBC's intent and guarantee layers help with each problem.
No installation or old demo runner is needed. These are standalone teaching examples, not a
transcript of an observed agent run.

## Example one: the feature works, but responsibilities drift

The request is simple: **let the model client use an API key to make requests.**

The project already has these boundaries:

| Location | Current responsibilities and constraints |
|---|---|
| `config/` | Load and validate configuration, including secrets; make no model calls |
| `llm_client/` | Make model requests; receive the key from the caller, without reading configuration |
| Caller | Wire configuration and client together to perform the business operation |

Adding this code directly to the client might make the feature work:

```python
# llm_client/client.py — an edit that violates the agreed boundary
import os

def chat(prompt):
    api_key = os.environ["MODEL_API_KEY"]
    return send_request(prompt, api_key=api_key)
```

`send_request` stands for the project's existing request function. Reading an environment variable
isn't inherently wrong; placing configuration loading inside a request-only module violates this
project's design. A test that only checks successful requests may miss that drift.

### Inspect the responsibilities before editing

In GBC, those boundaries live in the corresponding directories' intent documents, maintained
through `gbc intent`. An agent can query context around the files it plans to change:

```bash
gbc tree for llm_client/client.py config/settings.py
```

This query returns ancestor intent, file roles, direct dependencies, and guarantee context for the
target files. It does not run tests. Documentation is organized by code location, so a local task
can read the relevant parts.

An edit that follows the existing design loads the key in configuration, passes it into the
client, and connects the two at the caller:

```python
# config/settings.py
import os

def load_api_key():
    return os.environ["MODEL_API_KEY"]

# llm_client/client.py
def chat(prompt, api_key):
    return send_request(prompt, api_key=api_key)
```

These fragments show responsibility placement, omitting project-specific validation and request
implementation. Finish the caller wiring and relevant tests, then verify the guarantees affected
by the change. One agent or several can do the work; delegation does not change the contracts.

**GBC supplies queryable design context before the edit.** Intent records current responsibilities
and constraints; an ADR can record why that design was chosen. Natural-language intent does not
automatically block incorrect code, and an intent consistency check cannot prove the code follows
it. If responsibilities need to change, coordinate that decision and update the current contract
through the intent tools.

## Example two: one simplification breaks another module

Now consider a concrete behavioral dependency. The configuration module promises:
**missing keys return an empty string; existing keys preserve their configured string values.**

```python
# config_loader.py
def get_config(config, key):
    return config.get(key, "")
```

The display module relies on this behavior to trim an optional title:

```python
# display.py
from config_loader import get_config

def display_title(config):
    return get_config(config, "title").strip() or "Untitled"
```

With empty configuration, `get_config({}, "title")` returns `""` and the display uses `"Untitled"`.
The dependency is on how missing configuration is handled, not just the function name or signature.

### Connect the promise, consumer, and check

The project protects that behavior with its own test:

```python
# tests/test_config.py
from config_loader import get_config

def test_string_values_and_missing_default():
    assert get_config({"title": "  Hello  "}, "title") == "  Hello  "
    assert get_config({}, "title") == ""
```

Exact values are part of this contract, so the assertions check them. Assuming you configured an
executor called `pytest-example` for this example project using the [Quick start](quick-start.md),
register it through the CLI (equivalent MCP tools are available):

```bash
gbc guarantee create config_loader.py get_config.string_values_and_missing_default tests/test_config.py::test_string_values_and_missing_default pytest-example "Preserve configured strings; return an empty string for missing keys."
gbc dep add display.py config_loader.py get_config -g get_config.string_values_and_missing_default
```

The first command runs the test immediately and registers the guarantee only if it passes.
The second records that `display.py` relies on it. Context queries for `config_loader.py` can now
show its promise and registered consumer. Other consumers can share the same guarantee instead
of registering duplicate promises.

### One edit, two observable effects

Now the agent removes the default to "simplify" the code:

```diff
- return config.get(key, "")
+ return config.get(key)
```

Existing titles still load, but missing titles now produce `None`:

| Check | Before | After |
|---|---|---|
| `get_config({}, "title")` | `""` | `None` |
| `display_title({})` | `"Untitled"` | `.strip()` raises `AttributeError` |
| Missing-key assertion | Passes | Fails |

The agent runs this inside its current task:

```bash
gbc verify provider config_loader.py
```

The registered test fails on its second assertion. GBC supplies the failed guarantee and test
result and maintains queryable consumer relationships. The agent restores the contract, or
coordinates a change to the relied-on behavior, then verifies again. These results come from
explicit queries and execution, not background monitoring or GBC repairing code itself.

### What if the test only checked existing keys?

Suppose the registered test had been:

```python
def test_existing_key_only():
    assert get_config({"title": "Hello"}, "title") == "Hello"
```

After the same edit, it still passes while `display_title({})` still crashes. The test checks
existing keys but cannot support the missing-key promise. GBC does not infer absent assertions
from a guarantee's description. Test and contract changes need review.

### What does checking at registration establish?

If a test instead expects `get_config({}, "title") == "default"`, the original implementation
already fails it. Creating a normally enabled guarantee is refused. This is "born-green":
do not register currently failing checks as guarantees others can rely on.

It does not prove the test's expectations are correct or sufficient. During development, you can
still write a failing test, implement to green, then register it. No disabled placeholder is needed
for that development feedback.

## Bring it to your project

Start with a real change: inspect existing responsibilities, identify behavior other code relies
on, reuse or register the relevant guarantees, and verify and correct during the edit. Whether
failures block commits or merges depends on the project's integration and permissions.

- [Quick start](quick-start.md): install, connect your agent, and run a smoke check.
- [Core concepts](concepts.md): relationships, ADR / AGENTS.md / CI comparisons, and limitations.
- [Workflow](workflow.md): maintain intent, design focused tests, and complete acceptance.

This page adapts ideas from the retired demo, fixes the original configuration example's consumer
path, and drops the playback procedure. Old scripts and scenarios remain historical material,
not the current onboarding route. This walkthrough is a repository document; `gbc doc` continues
to offer five offline topics: quick-start, concepts, workflow, reference, and onboarding-agent.
