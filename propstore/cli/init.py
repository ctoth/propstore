"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

import shutil
from pathlib import Path

import click

from propstore.cli.repository import Repository


_FALLBACK_FORMS = (
    "category",
    "boolean",
    "structural",
)


def _seed_forms(forms_dir: Path) -> None:
    """Populate forms/ for a freshly initialized project."""
    package_forms_dir = Path(__file__).resolve().parents[2] / "forms"
    if package_forms_dir.is_dir():
        for form_path in sorted(package_forms_dir.glob("*.yaml")):
            shutil.copy2(form_path, forms_dir / form_path.name)
        return

    for form_name in _FALLBACK_FORMS:
        stub = f"name: {form_name}\nkind: {form_name}\ndimensionless: false\n"
        (forms_dir / f"{form_name}.yaml").write_text(stub)


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: dict, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates the standard directory structure (concepts/, claims/, sidecar/)
    needed for pks to operate. If no DIRECTORY argument is given, creates
    a ``knowledge/`` directory in the current working directory.
    """
    start = (obj or {}).get("start")
    if start is not None:
        root = start / directory
    else:
        root = Path(directory)

    # Already initialized?
    if (root / "concepts").is_dir():
        click.echo(f"Already initialized: {root}")
        return

    repo = Repository.init(root)

    _seed_forms(repo.forms_dir)

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'concepts' / '.counters/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'forms/'}")
    click.echo(f"  {root / 'sidecar/'}")
