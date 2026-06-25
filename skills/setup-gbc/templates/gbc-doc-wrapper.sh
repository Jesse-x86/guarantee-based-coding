#!/usr/bin/env bash
# gbc-doc — the ONLY compliant entry for editing the gbc.md intent docs of the project it lives in.
# Wraps GBC's intent CLI (gbc_doc.py); pins the interpreter + project root so the agent
# only ever passes a command + args. gbc.md structure & parent/child consistency are
# deterministic constraints — NEVER hand-edit gbc.md; always go through this.
#
#   {{INTERPRETER}}  : interpreter that runs GBC (same one used in .mcp.json).
#   {{GBC_REPO}}     : absolute path to the guarantee-based-coding repo.
#   {{PROJECT_ROOT}} : absolute path to the TARGET project (Windows form if cross-platform).
exec {{INTERPRETER}} \
  {{GBC_REPO}}/tools/intent-editor/backend/gbc_doc.py \
  --root {{PROJECT_ROOT}} \
  "$@"
