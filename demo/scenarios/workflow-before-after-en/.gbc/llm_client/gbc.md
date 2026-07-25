# Intent

This folder is **LLM calls only** (build prompts, call the model, parse model output).
It does not load config files, env vars, or secrets.

# Internal constraints

- No new config I/O here (yaml/json/env for keys, etc.)
- Settings and secrets are injected from `config/`; callers pass them in

# Files

- `client.py`: public `chat(prompt) -> str`
