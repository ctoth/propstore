"""propstore CLI entry point (``pks``).

Phase-0 skeleton: a bare Click group so ``pks --help`` works on the fresh tree.
The lazy command registry and the command families (claim/concept/world/source/…)
are authored per slice — registered through the lazy registry here, never via eager
imports of unrelated command families (see CLAUDE.md "CLI adapter discipline").
"""

from __future__ import annotations

import click


@click.group()
@click.version_option(package_name="propstore")
def cli() -> None:
    """Propositional Knowledge Store CLI."""
