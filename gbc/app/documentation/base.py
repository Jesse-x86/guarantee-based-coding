# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Read the packaged manual independently of any target project."""

from gbc.app.assets import DOCS_DIR
from gbc.app.i18n import resolve_lang, t
from gbc.app.i18n.lang import normalize
from gbc.app.models.errors import GBCError

TOPICS = ("quick-start", "concepts", "workflow", "reference", "onboarding-agent")
LANGUAGES = ("en", "zh")
MAX_SNIPPET_LENGTH = 240


class DocumentationError(GBCError):
    """A manual query error localized without changing process language."""

    def __init__(self, key: str, language: str, **params):
        self.key = key
        self.language = language
        self.params = params
        super().__init__(key)

    def __str__(self):
        return t(self.key, lang=self.language, **self.params)


def _language(lang: str | None) -> str:
    if lang is None:
        language = resolve_lang()
        return language if language in LANGUAGES else "en"
    language = normalize(lang) if isinstance(lang, str) else None
    if language not in LANGUAGES:
        raise DocumentationError("exc.manual_language", resolve_lang(), value=lang)
    return language


def _read(topic: str, language: str) -> str:
    if topic not in TOPICS:
        raise DocumentationError("exc.manual_topic", language, topic=topic)
    try:
        return (DOCS_DIR / language / f"{topic}.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocumentationError("exc.manual_resource", language, topic=topic) from exc


def list_topics(lang: str | None = None) -> dict:
    """List the fixed topic IDs and their localized Markdown titles."""
    language = _language(lang)
    topics = []
    for topic in TOPICS:
        markdown = _read(topic, language)
        title = next((line[2:].strip() for line in markdown.splitlines()
                      if line.startswith("# ")), topic)
        topics.append({"id": topic, "title": title})
    return {"language": language, "topics": topics}


def read_topic(topic: str, lang: str | None = None) -> str:
    """Return one complete Markdown topic; topic is an ID, never a path."""
    return _read(topic, _language(lang))


def _snippet(line: str, folded_start: int, folded_length: int) -> str:
    """Center a Unicode-character-bounded excerpt around a casefold match."""
    if len(line) <= MAX_SNIPPET_LENGTH:
        return line
    offset = 0
    start = 0
    end = len(line)
    for index, char in enumerate(line):
        next_offset = offset + len(char.casefold())
        if offset <= folded_start < next_offset:
            start = index
        if next_offset >= folded_start + folded_length:
            end = index + 1
            break
        offset = next_offset
    center = start + min(end - start, MAX_SNIPPET_LENGTH) // 2
    left = max(0, min(center - MAX_SNIPPET_LENGTH // 2,
                      len(line) - MAX_SNIPPET_LENGTH))
    return line[left:left + MAX_SNIPPET_LENGTH]


def search_docs(query: str, lang: str | None = None, limit: int = 20) -> dict:
    """Find literal, case-insensitive matching lines in stable topic order.

    Each matching line contributes one result with a one-based line number.
    ``truncated`` is true only if another matching line exceeds the limit.
    """
    language = _language(lang)
    if not isinstance(query, str) or not query.strip():
        raise DocumentationError("exc.manual_query", language)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise DocumentationError("exc.manual_limit", language)
    matches = []
    needle = query.casefold()
    for topic in TOPICS:
        for number, line in enumerate(_read(topic, language).splitlines(), 1):
            position = line.casefold().find(needle)
            if position < 0:
                continue
            if len(matches) == limit:
                return {"language": language, "query": query,
                        "matches": matches, "truncated": True}
            matches.append({"topic": topic, "line": number,
                            "text": _snippet(line, position, len(needle))})
    return {"language": language, "query": query,
            "matches": matches, "truncated": False}
