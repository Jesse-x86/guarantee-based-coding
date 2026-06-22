"""Parse / serialize a single GBC `gbc.md` file.

Format (observed from real .gbc trees):

    # 意图
    <intent text, may span multiple paragraphs>

    # 内部约束            <- optional H1 block
    <constraints text>

    ## app/               <- H2 entry; trailing "/" => subfolder
    <desc>                   (a subfolder's desc == that subfolder's own `# 意图`)

    ## main.py            <- H2 entry without "/" => plain file
    <desc>

Two "大标题 (H1)" blocks: 意图 (intent) + optional 内部约束 (constraints).
"二号标题 (H2)" blocks: one per child (file or subfolder) under this path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

INTENT_HEADING = "意图"
CONSTRAINTS_HEADING = "内部约束"

_HEADING_RE = re.compile(r"^(#{1,2})\s+(.*?)\s*$")


@dataclass
class Entry:
    """An H2 (`##`) child entry: a file or a subfolder."""
    name: str            # e.g. "main.py" or "app/" (trailing slash kept for dirs)
    is_dir: bool
    desc: str = ""       # for files, the only source; for dirs, mirrors child intent


@dataclass
class ParsedDoc:
    intent: str = ""
    constraints: str = ""
    entries: list[Entry] = field(default_factory=list)


def parse(text: str) -> ParsedDoc:
    """Parse gbc.md text into intent / constraints / ordered entries."""
    doc = ParsedDoc()
    # current sink: ("intent" | "constraints" | entry-index) -> collect body lines
    body: list[str] = []
    sink: str | int | None = None

    def flush() -> None:
        content = "\n".join(body).strip()
        if sink == "intent":
            doc.intent = content
        elif sink == "constraints":
            doc.constraints = content
        elif isinstance(sink, int):
            doc.entries[sink].desc = content

    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if not m:
            body.append(line)
            continue
        # heading boundary: flush the previous block first
        flush()
        body = []
        level, title = len(m.group(1)), m.group(2).strip()
        if level == 1:
            sink = "constraints" if title == CONSTRAINTS_HEADING else "intent"
        else:  # level 2 -> child entry
            is_dir = title.endswith("/")
            doc.entries.append(Entry(name=title, is_dir=is_dir))
            sink = len(doc.entries) - 1
    flush()
    return doc


def serialize(intent: str, constraints: str, entries: list[Entry]) -> str:
    """Render intent / constraints / entries back into gbc.md text."""
    blocks: list[str] = []
    blocks.append(f"# {INTENT_HEADING}\n{intent.strip()}".rstrip())
    if constraints.strip():
        blocks.append(f"# {CONSTRAINTS_HEADING}\n{constraints.strip()}".rstrip())
    for e in entries:
        blocks.append(f"## {e.name}\n{e.desc.strip()}".rstrip())
    return "\n\n".join(blocks) + "\n"
