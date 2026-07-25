"""Simulated LLM tools: say / edit (with diff) / gbc (via MCP)."""

import json
from pathlib import Path
from typing import Any

from .display import (
    say_bubble,
    render_diff,
    render_gbc_start,
    render_gbc_result,
    render_file,
)
from .mcp_client import McpClient


def tool_say(text: str) -> None:
    """Simulated LLM speech."""
    say_bubble(text)


def tool_show(workspace: Path, file: str, desc: str, *, highlight: str | None = None) -> None:
    """Show a file with syntax highlighting.

    highlight: optional line/keyword note for the panel title (not a real highlight).
    """
    path = workspace / file
    if not path.exists():
        from rich.console import Console
        Console().print(f"[dim]({file} missing)[/dim]")
        return
    content = path.read_text(encoding="utf-8")
    lang = _guess_language(file)
    render_file(file, content, lang, desc, highlight=highlight)


def tool_edit(workspace: Path, file: str, edits: list[dict], desc: str) -> None:
    """Simulated precise edit (oldText → newText + unified diff)."""
    path = workspace / file
    if not path.exists():
        raise FileNotFoundError(f"edit target missing: {path}")

    original = path.read_text(encoding="utf-8")
    current = original

    for e in edits:
        old_text = e["oldText"]
        new_text = e["newText"]
        if old_text not in current:
            raise ValueError(
                f"oldText not found in {file}."
            )
        current = current.replace(old_text, new_text, 1)

    render_diff(
        file,
        original.splitlines(keepends=True),
        current.splitlines(keepends=True),
        desc,
    )
    path.write_text(current, encoding="utf-8")


def tool_gbc(
    mcp: McpClient,
    tool: str,
    args: dict[str, Any],
    desc: str,
) -> dict[str, Any]:
    """Call a GBC tool through MCP.

    Args:
        mcp: McpClient instance
        tool: MCP tool name (e.g. "create_guarantee", "verify_provider")
        args: keyword args for the tool
        desc: human-readable description

    Returns:
        {"returncode": int, "stdout": str, "stderr": str}
    """
    render_gbc_start([tool], desc)

    try:
        result_text = mcp.call_tool(tool, args)
        # Parse result — MCP tool text may be a JSON error
        try:
            parsed = json.loads(result_text)
            if isinstance(parsed, dict) and "error" in parsed:
                render_gbc_result(1, "", parsed["error"])
                return {"returncode": 1, "stdout": "", "stderr": str(parsed["error"])}
        except (json.JSONDecodeError, TypeError):
            pass

        # verify_provider returns a JSON object; extract green status + summary
        stdout = result_text
        if tool == "verify_provider":
            try:
                vdata = json.loads(result_text)
                passed = len(vdata.get("passed", []))
                failed = len(vdata.get("failed", []))
                skipped = len(vdata.get("skipped", []))
                green = vdata.get("green", failed == 0)
                stdout = (
                    f"{'GREEN' if green else 'RED'}  "
                    f"passed={passed} failed={failed} skipped={skipped}"
                )
                if failed:
                    stdout += f"\nfailed: {', '.join(vdata['failed'])}"
                    # show raw test output for failures
                    results = vdata.get("results", {})
                    for gid in vdata["failed"]:
                        r = results.get(gid, {})
                        detail = (r.get("stderr", "") + "\n" + r.get("stdout", "")).strip()
                        if detail:
                            # trim long output, keep the tail
                            lines = detail.splitlines()
                            if len(lines) > 15:
                                detail = "\n".join(lines[-12:])
                                detail = f"...({len(lines) - 12} lines omitted)\n{detail}"
                            stdout += f"\n\n── {gid} ──\n{detail}"
            except (json.JSONDecodeError, TypeError):
                pass

        returncode = 0
        if tool == "verify_provider" and "RED" in stdout:
            returncode = 1

        render_gbc_result(returncode, stdout, "")
        return {"returncode": returncode, "stdout": stdout, "stderr": ""}
    except Exception as e:
        render_gbc_result(1, "", str(e))
        return {"returncode": 1, "stdout": "", "stderr": str(e)}


def _guess_language(filename: str) -> str:
    """Guess language from extension for Rich Syntax."""
    ext = Path(filename).suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sh": "bash",
        ".sql": "sql",
    }.get(ext, "text")
