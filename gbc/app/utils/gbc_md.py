# Copyright 2026 Jesse-x86
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Parse / serialize a single GBC `gbc.md` file — the canonical parser.

This is the single authoritative parser/serializer for the `gbc.md` format. Both
`interface.base.render_tree` (engine side) and the standalone intent-editor tool
build on it; neither re-implements the format. Pure text handling, no IO.

Format:

    # 意图
    <intent text, may span multiple paragraphs>

    # 内部约束            <- optional H1 block
    <constraints text>

    # 文件                <- container for child entries (only emitted if any)
    ## game.py            <- H2 entry; no trailing "/" => plain file
    <desc>

    ## maker/             <- trailing "/" => subfolder
    <desc>                   (a subfolder's desc == that subfolder's own `# 意图`)

H1 blocks: 意图 (intent) + optional 内部约束 (constraints) + 文件 (files container).
The `# 文件` heading exists so child entries no longer visually nest under 内部约束.
H2 blocks (the `# 文件` children): one per child file or subfolder under this path.

Parsing is lenient: any H2 is treated as a child entry regardless of whether a
`# 文件` heading precedes it, so old-format docs (entries with no `# 文件` section)
still parse — re-serializing them upgrades them to the new format.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

INTENT_HEADING = "意图"
CONSTRAINTS_HEADING = "内部约束"
FILES_HEADING = "文件"

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
    # current sink: "intent" | "constraints" | entry-index | None (discard)
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
            if title == CONSTRAINTS_HEADING:
                sink = "constraints"
            elif title == FILES_HEADING:
                sink = None  # the 文件 container heading has no body; its H2s are entries
            else:
                sink = "intent"
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
    if entries:
        blocks.append(f"# {FILES_HEADING}")
        for e in entries:
            blocks.append(f"## {e.name}\n{e.desc.strip()}".rstrip())
    return "\n\n".join(blocks) + "\n"
