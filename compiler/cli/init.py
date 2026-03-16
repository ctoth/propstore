"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.argument("directory", default="knowledge")
def init(directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates the standard directory structure (concepts/, claims/, sidecar/)
    needed for pks to operate. If no DIRECTORY argument is given, creates
    a ``knowledge/`` directory in the current working directory.
    """
    root = Path(directory)

    # Already initialized?
    if (root / "concepts").is_dir():
        click.echo(f"Already initialized: {root}")
        return

    # Create the directory structure
    dirs = [
        root / "concepts" / ".counters",
        root / "claims",
        root / "sidecar",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'concepts' / '.counters/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'sidecar/'}")
