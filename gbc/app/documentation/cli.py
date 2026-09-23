# Copyright 2026 Jesse-x86
# Licensed under the Apache License, Version 2.0; see LICENSE.
"""Thin command-line surface for the packaged offline manual."""

import json
from typing import Optional

import typer

from gbc.app.documentation import base
from gbc.app.i18n import current_lang

doc_app = typer.Typer(help="cli.doc.help", invoke_without_command=True)


@doc_app.callback()
def doc_help(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _emit(operation, *args, **kwargs):
    try:
        result = operation(*args, **kwargs)
    except base.DocumentationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(result if isinstance(result, str)
               else json.dumps(result, ensure_ascii=False, indent=2))


@doc_app.command("list", help="cli.doc.list.help")
def doc_list(
    lang: Optional[str] = typer.Option(None, "--lang", help="cli.option.lang.help"),
):
    _emit(base.list_topics, lang=lang if lang is not None else current_lang())


@doc_app.command("read", help="cli.doc.read.help")
def doc_read(
    topic: str = typer.Argument(..., help="cli.doc.topic.help"),
    lang: Optional[str] = typer.Option(None, "--lang", help="cli.option.lang.help"),
):
    _emit(base.read_topic, topic, lang=lang if lang is not None else current_lang())


@doc_app.command("search", help="cli.doc.search.help")
def doc_search(
    query: str = typer.Argument(..., help="cli.doc.query.help"),
    lang: Optional[str] = typer.Option(None, "--lang", help="cli.option.lang.help"),
    limit: int = typer.Option(20, "--limit", help="cli.doc.limit.help"),
):
    _emit(base.search_docs, query, lang=lang if lang is not None else current_lang(),
          limit=limit)
