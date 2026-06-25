"""Thin shim — the canonical gbc.md parser now lives in the main lib.

This backend was originally standalone (the agent that wrote it had no main-lib
checkout), so it carried its own copy of the gbc.md parser. The single source of
truth is now ``app/utils/gbc_md.py``; this module re-exports it so the intent-editor
and the engine never drift on the gbc.md format.

We put ``app/utils`` on sys.path and import the module directly rather than
``from app.utils.gbc_md import ...``: this backend has its own ``app.py`` that
shadows the main-lib ``app`` package by name, so the package path is unreachable
here. ``gbc_md`` is pure-stdlib and self-contained, so importing it standalone is safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

_utils_dir = Path(__file__).resolve().parents[3] / "app" / "utils"
if str(_utils_dir) not in sys.path:
    sys.path.insert(0, str(_utils_dir))

from gbc_md import (  # noqa: E402
    parse, serialize, ParsedDoc, Entry,
    INTENT_HEADING, CONSTRAINTS_HEADING, FILES_HEADING,
)
