"""pks source - source-branch authoring command family.

Thin Click adapters over the :mod:`propstore.source` subsystem (CLAUDE.md "CLI
adapter discipline"): each command parses flags into the owner function's typed
arguments, calls the owner, and renders the typed result. No lifecycle, finalize,
promote, or mutation semantics live here — those belong to ``propstore.source``.

This package ``__init__`` owns the ``source`` Click group; the command families
live in sibling modules imported at the bottom (so registering the group does not
require the submodules until the group is actually built).
"""

from __future__ import annotations

import click


@click.group()
def source() -> None:
    """Manage source branches and source-local authoring state."""


# Import the split command modules last so each can attach its subcommands to the
# ``source`` group; re-exported via ``__all__`` so the side-effect imports read as
# the package's public command surface rather than unused imports.
from propstore.cli.source import authoring, batch, lifecycle, proposal  # noqa: E402

__all__ = [
    "authoring",
    "batch",
    "lifecycle",
    "proposal",
    "source",
]
