"""``pks micropub`` — read projections over the micropublication family.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): ``list`` and ``show``
project directly over the
:class:`~propstore.families.micropublications.Micropublication` family store
(``repo.families.micropublication``). No bundle view or filtering logic lives here.

``micropub lift`` (reporting micropublication lifting decisions for a target
context) needs a Phase-10 ``inspect_micropub_lift`` owner facade that does not
exist in the rewrite, so it is deferred rather than fabricated here.
"""

from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table
from propstore.families.micropublications import Micropublication


@click.group()
def micropub() -> None:
    """Read views over micropublications."""


@micropub.command("list")
@click.pass_obj
def micropub_list(obj: CliContext) -> None:
    """List every stored micropublication."""

    repo = require_repo(obj)
    micropubs = sorted(
        (handle.document for handle in repo.families.micropublication.iter_handles()),
        key=lambda item: item.artifact_id,
    )
    if not micropubs:
        emit("No micropublications.")
        return
    emit_table(
        ("ARTIFACT ID", "CONTEXT", "SOURCE"),
        [(item.artifact_id, item.context_id, item.source or "") for item in micropubs],
    )


@micropub.command("show")
@click.argument("artifact_id")
@click.pass_obj
def micropub_show(obj: CliContext, artifact_id: str) -> None:
    """Show one micropublication's rendered YAML document."""

    repo = require_repo(obj)
    loaded = repo.families.micropublication.load(artifact_id)
    if not isinstance(loaded, Micropublication):
        fail(f"Micropublication '{artifact_id}' not found")
    emit(repo.families.micropublication.render(loaded))
