# Guarantee-Based Coding

**Instead of making AI smarter at understanding code, make code safe to modify even by a dumb AI.**

**中文版: [README.md](./README.md)**

## The Problem

The core failure mode of coding agents (Cursor, Aider, Devin, etc.) is not writing incorrect code — that can be fixed with retries. The real problem is **silently breaking implicit assumptions in existing code**.

When Agent A changes a function's return format, a module 12 folders away might depend on that exact format. Nothing tells Agent A that dependency exists. Nothing prevents the breakage from happening.

Current coding agents focus on **context retrieval and token efficiency** — how to understand codebases faster and more accurately. But they don't solve a more fundamental problem:

> **When modifying code, how do you know what must not break?**

## Core Idea

Dependencies between code modules are essentially a set of **guarantees**. Module A depends on Module B not because of B's implementation details, but because of B's behavioral promises — the type, format, and semantics of its return values.

If we make these guarantees **explicit, executable, and attributed**, then:

- Every modification automatically verifies whether all guarantees still hold
- If a guarantee is broken, we know exactly which one and who depends on it
- The modifier must explicitly declare "I know what I'm breaking" to proceed

**Correctness shifts from "the AI thinks it got it right" to "all guarantees still pass."** This is a mechanically verifiable boolean condition, independent of AI judgment.

## How It Works

### Core Principle: Zero Intrusion

All framework files live in an isolated `.gbc/` directory. Your codebase stays completely clean:

```
my-project/
├── src/                          # your code, completely untouched
│   ├── llm_client/
│   │   └── client.py
│   └── conversation/
│       └── manager.py
│
└── .gbc/                         # framework directory, mirrors code structure
    └── src/
        ├── llm_client/
        │   ├── design.client.py.md          # design doc: signatures + behavioral intent
        │   ├── meta.client.py.yaml          # metadata: dependencies, dependents
        │   ├── guarantee.init.client.py     # test initialization (fixtures, etc.)
        │   ├── guarantee.root.client.py     # self-correctness guarantees
        │   └── guarantee.1ef0a.client.py    # externally registered guarantee (hash identifies source)
        └── conversation/
            ├── design.manager.py.md
            ├── meta.manager.py.yaml
            ├── guarantee.init.manager.py
            ├── guarantee.root.manager.py
            └── guarantee.a3b72.manager.py
```

- `.gbc/` directory structure **mirrors** `src/`
- Each source file maps to a set of framework files, linked by filename suffix
- Guarantee files are standard **pytest** test files — no new tools to learn

### Design File Example

```markdown
# design.client.py.md

## chat(messages: list[dict]) -> dict

Send a conversation request to the LLM and return the model's response.

**Parameters:**
- messages: OpenAI-format message list, each containing role and content

**Returns:**
- dict in the format {"role": "assistant", "content": str}

**Exceptions:**
- LLMTimeoutError: raised on request timeout
- LLMAuthError: raised on authentication failure

**Design Constraints:**
- Return format is consistent regardless of the underlying model
- No conversation history management; responsible for single requests only
```

### Guarantee Examples

Self-correctness guarantee:

```python
# guarantee.root.client.py

"""Self-correctness guarantee: basic behavioral contract for client.py"""

from llm_client.client import chat
import pytest

def test_returns_dict():
    result = chat([{"role": "user", "content": "hello"}])
    assert isinstance(result, dict)

def test_returns_required_keys():
    result = chat([{"role": "user", "content": "hello"}])
    assert "role" in result
    assert "content" in result

def test_timeout_raises():
    with pytest.raises(LLMTimeoutError):
        chat([{"role": "user", "content": "hello"}], timeout=0.001)
```

Externally registered guarantee:

```python
# guarantee.1ef0a.client.py

"""
External guarantee, source: conversation/manager.py
Reason: manager uses result["content"] directly to build conversation history,
        depends on the content field being of type str
"""

from llm_client.client import chat

def test_content_is_string():
    result = chat([{"role": "user", "content": "hello"}])
    assert isinstance(result["content"], str), \
        "content must be str — conversation.manager depends on this behavior"
```

These are just ordinary pytest files. Running guarantees is just `pytest .gbc/` — nothing new to learn.

### Coding Agent Workflow

When a coding agent needs to modify `src/llm_client/client.py`, its context consists of:

```
1. src/llm_client/client.py                  ← code to modify
2. .gbc/src/llm_client/design.client.py.md   ← design intent and constraints
3. dependents' design.*.md                    ← interface info (no implementation)
4. if retrying: error message from last attempt
```

After modification:

```
1. Automatically run .gbc/src/llm_client/guarantee.*.client.py
2. All pass → modification accepted
3. Any failure →
   a) Agent attempts to fix without breaking the guarantee
   b) If a guarantee must be broken → explicit declaration, notify the registrant to adapt
```

**Context size depends on the complexity of the current file, not the overall project size.** A 10-file project and a 100-file project require the same amount of context when modifying the same file.

## Comparison with Existing Approaches

| | Context-Optimization (Cursor, Aider) | Full-Agent (Devin, OpenHands) | Guarantee-Based Coding |
|---|---|---|---|
| Core strategy | Better retrieval of relevant code | End-to-end automation | Use constraints to eliminate dependence on understanding |
| Correctness guarantee | None | Agent self-verification | Guarantee gating |
| Modification impact awareness | None | Agent reasoning (unreliable) | Explicit registration + automatic detection |
| Context growth | Grows with project | Grows with project | Grows with single-file complexity, independent of project size |
| Codebase intrusion | Low | Medium | **Zero** (all framework files under `.gbc/`) |

## How This Differs from Existing Concepts

**"Isn't this just Design by Contract?"**

Traditional Design by Contract (Eiffel-style preconditions/postconditions) has modules declare their **own** contracts. The key differences in Guarantee-Based Coding:

- **Guarantees are registered by dependents**, not written by the provider. "What behavior I depend on" comes from the consumer, not the author's good intentions.
- **Guarantees carry attribution** — we know who registered them and why. When broken, we can precisely notify the affected parties.
- **Designed for AI agents** — the goal is to give coding agents explicit modification boundaries, not to give human programmers runtime checks.

**"Isn't this just testing?"**

How guarantees differ from regular tests:

- **Attributed**: each guarantee knows who registered it and what cross-module dependency it protects
- **Gating on modification**: not run after the fact in CI, but triggered **in real-time** as a precondition when an agent modifies code
- **Semantically specific**: each guarantee verifies one concrete behavioral promise, not a vague "this feature works"

Technically, guarantees are pytest tests. Conceptually, they are an **attributed, real-time-gated behavioral contract system designed for AI agents**.

## Current Status

🚧 **Early stage** — Core architecture under design. Full implementation coming soon.

- [ ] Core architecture design document
- [ ] Guarantee registration and execution mechanism
- [ ] Design file generation tooling
- [ ] Coding agent integration (interfacing with existing agents)
- [ ] Example project: LLM Chatbot
- [ ] Benchmarks and evaluation

## Contact

If you're interested in this direction, feel free to star, open an issue, or reach out directly.
