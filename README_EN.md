# Guarantee-Based Coding (GBC)

**Instead of making AI smarter at understanding code, make code safe to modify even without full understanding.**

**中文版: [README.md](./README.md)**

## 🚀 Want your agent to use GBC?

Hand **[docs/teach-your-agent.md](./docs/teach-your-agent.md)** to your coding agent — it can follow that to install GBC into your project, wire up the tools, and start using it. More docs in [docs/](./docs/).

## The Problem

The core failure mode of coding agents (Cursor, Aider, Devin, etc.) isn't writing wrong code — wrong code can be retried. The real problem is **silently breaking implicit assumptions in existing code**.

When an agent modifies a function's return format, another module 12 directories away might depend on that format. Nothing tells the agent this dependency exists, and nothing prevents the breakage from happening.

Existing coding agents optimize for context retrieval and token efficiency. But they don't address a more fundamental question:

> **When modifying code, how do you know what must not break?**

## Core Idea

Dependencies between code modules are essentially a set of **guarantees**. Module A depends on Module B not because of B's implementation details, but because of B's behavioral promises — return types, formats, semantics.

If we make these guarantees **explicit, executable, and verifiable**, then:

- Every modification automatically checks whether all guarantees still hold
- If a guarantee breaks, you know exactly which one and who depends on it
- **Correctness shifts from "the AI thinks it got it right" to "all guarantees still pass"** — a mechanically verifiable boolean condition

## How It Works

### Design Principles

1. **Zero intrusion**: All metadata lives in a `.gbc/` directory; your codebase stays clean
2. **User-managed test files**: GBC does not generate, store, or manage test files. You organize your test files however you like in your own project. GBC only **records which test files correspond to which guarantees, runs them, and aggregates results**
3. **Language-agnostic**: Supports any language and test framework through executor configuration

### Directory Structure

```
my-project/
├── src/                                    # Your code
│   ├── llm_client/
│   │   └── client.py
│   └── conversation/
│       └── manager.py
│
├── tests/                                  # Your test files, managed by you
│   ├── test_client_returns_dict.py
│   ├── test_client_content_is_str.py
│   └── ...
│
└── .gbc/                                   # GBC metadata directory (auto-generated)
    └── src/
        └── llm_client/
            └── gbc.client.py.json          # Guarantee registry for client.py
```

### Core Concepts

- **Provider**: The source file that provides guarantees (e.g., `src/llm_client/client.py`)
- **Consumer / Dependent**: The file that depends on a guarantee (e.g., `src/conversation/manager.py`)
- **Guarantee**: A **named** (globally-unique id) behavioral promise, mapped to a test + a description; **multiple consumers can share one guarantee**
- **Executor**: Configuration defining how to run tests (command template, working directory, environment variables, etc.)

Dependency edges come in two levels: a free **symbol dependency** (on a signature/symbol existing) and a **named-guarantee dependency** (on a specific behavior). The latter is **registered bidirectionally** — the provider's `provides[id].dependents` ⇄ the consumer's `depends_on[].guarantees`, kept in sync by the tools.

### Meta File Example

Each source file may have a sibling `.json` recording two things: what guarantees it **provides** (`provides`) and what it **depends on** (`depends_on`).

`client.py` (provider) at `.gbc/src/llm_client/gbc.client.py.json`:

```json
{
    "provides": {
        "llm_client.client.chat.content_is_str": {
            "desc": "chat() returns result['content'] as str; manager uses it directly to build conversation history",
            "test": "tests/test_client_content_is_str.py::test_content_is_str",
            "executor": "pytest",
            "heavy": 0,
            "dependents": ["src/conversation/manager.py"]
        }
    }
}
```

`manager.py` (consumer) at `.gbc/src/conversation/gbc.manager.py.json` registers the reverse edge:

```json
{
    "depends_on": [
        {
            "symbol": "src/llm_client/client.py:chat",
            "guarantees": ["llm_client.client.chat.content_is_str"]
        }
    ]
}
```

Guarantee ids are globally unique (`<dotted.path>.<symbol>.<behavior>`); both directions are written by the tools (CLI/MCP) — you don't hand-edit them.

### Executor Configuration Example

Executors define how tests are run. `{file}` is a placeholder replaced at runtime with the guarantee's test file path:

```json
{
    "executors": {
        "pytest": {
            "command": ["python", "-m", "pytest", "{file}", "-x", "-q"],
            "cwd": "/path/to/my-project",
            "timeout": 30,
            "env_ops": [
                {"key": "PYTHONPATH", "action": "prepend", "value": "/path/to/my-project/src"}
            ]
        },
        "jest": {
            "command": ["npx", "jest", "{file}"],
            "cwd": "/path/to/my-project",
            "timeout": 30,
            "env_ops": null
        }
    }
}
```

Supported environment variable operations: `set`, `append`, `prepend`, `remove`.

### Workflow

```
Modify client.py
       │
       ▼
verify_provider(src/llm_client/client.py)
       │
       ├── Run tests/test_client_content_is_str.py  (for manager.py)
       ├── Run tests/test_client_returns_dict.py     (for handler.py)
       │
       ▼
  All pass  → Modification is safe
  Failure   → Precise report: which guarantee failed, who depends on it, why
```

### Integration with Coding Agents

GBC provides two sets of integration points, available via both CLI and MCP:

- **Before modification**: `list_provides` / `list_depends_on` / `who_depends_on` — the agent learns what guarantees a file has, what it depends on, and who depends on it
- **Registration**: `add_dependency` / `create_guarantee` — explicitly record "I depend on this behavior of yours" (a named guarantee is run-on-birth)
- **After modification**: `verify_provider` / `verify_guarantee` — run guarantees to gate whether the change is acceptable

Context size depends on the number of guarantees for the current file, **not on overall project size**.

GBC offers **both CLI and MCP** interfaces, plus a **recommended agent workflow** — just hand [docs/teach-your-agent.md](./docs/teach-your-agent.md) to your agent to get started.

## Comparison with Existing Approaches

| | Context Optimization (Cursor, Aider) | Full Agent (Devin, OpenHands) | GBC |
|---|---|---|---|
| Core strategy | Better code retrieval | End-to-end automation | Constraints eliminate the need for understanding |
| Correctness guarantee | None | Agent self-verification | Guarantee gating |
| Modification impact awareness | None | Agent reasoning (unreliable) | Explicit registration + automatic detection |
| Context growth | Grows with project size | Grows with project size | Grows with per-file guarantee count, independent of project size |
| Codebase intrusion | Low | Medium | **Zero** |
| Language binding | Usually bound | Usually bound | Language-agnostic |

## How This Differs from Existing Concepts

**"Isn't this just Design by Contract?"**

Traditional DbC (Eiffel-style preconditions/postconditions) has modules declare their **own** contracts. GBC differs in key ways:

- **Guarantees are registered by the dependent**, not the provider — "what behavior I depend on" comes from the consumer, not the author
- **Attribution is built in** — you know who registered it and why; breakage can be precisely traced
- **Designed for AI agents** — provides modification boundaries for coding agents, not runtime checks for human programmers

**"Isn't this just testing?"**

Technically, guarantees are test files. The conceptual differences:

- **Attribution**: Each guarantee records who registered it and what cross-module dependency it protects
- **Real-time gating**: Not a post-hoc CI check, but a precondition enforced at modification time
- **User-managed**: GBC doesn't manage the test files themselves, only metadata and execution

## Current Status

🚧 **Early development**

- [x] Core guarantee register / verify / update / unregister mechanism (named guarantee ids, many-to-one, retire protection, reverse lookup)
- [x] Multi-language executor configuration
- [x] Atomic file writing with backup rotation
- [x] CLI interface
- [x] MCP interface
- [x] Example project (dogfood: AIGameGen, in progress)
- [x] Usage docs ([docs/](./docs/))
- [ ] Actually test the CLI interface and core code
- [ ] Full test coverage
- [ ] PyPI release

## Contact

If you're interested in this direction, feel free to star, open an issue, or reach out directly.