"""``pks context`` — read projections over the context family store.

Contexts (``ist(c, p)`` qualifiers) are immutable except through the source
subsystem, and the rewrite has no context read/mutation owner in the app layer, so
this module builds only the two read projections directly over the
:class:`~propstore.families.contexts.Context` family store
(``repo.families.context``): ``list`` and ``show``. These read the stored
documents and render them; they own no mutation logic. Authoring (add / remove /
lifting-rule) is deferred to the phase that lands a context owner — fabricating a
mutation command with no owner is out of scope (CLAUDE.md CLI-adapter discipline).
"""
from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit
from propstore.families.contexts import Context


@click.group()
def context() -> None:
    """Read views over contexts."""


@context.command("list")
@click.pass_obj
def context_list(obj: CliContext) -> None:
    """List every stored context."""

    repo = require_repo(obj)
    contexts = sorted(
        (handle.document for handle in repo.families.context.iter_handles()),
        key=lambda ctx: ctx.context_id,
    )
    if not contexts:
        emit("No contexts registered.")
        return
    for ctx in contexts:
        suffix = f" ({ctx.perspective})" if ctx.perspective else ""
        description = ctx.description or ctx.name
        emit(f"  {ctx.context_id}{suffix} — {description}")


@context.command("show")
@click.argument("name")
@click.pass_obj
def context_show(obj: CliContext, name: str) -> None:
    """Show one context's rendered YAML document."""

    repo = require_repo(obj)
    loaded = repo.families.context.load(name)
    if not isinstance(loaded, Context):
        fail(f"Context '{name}' not found")
    emit(repo.families.context.render(loaded))
