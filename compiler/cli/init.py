"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

import shutil
from pathlib import Path

import click


_FALLBACK_FORMS = (
    "amplitude_ratio",
    "category",
    "dimensionless_compound",
    "duration_ratio",
    "flow",
    "flow_derivative",
    "frequency",
    "level",
    "pressure",
    "structural",
    "time",
)


def _seed_forms(forms_dir: Path) -> None:
    """Populate forms/ for a freshly initialized project."""
    package_forms_dir = Path(__file__).resolve().parents[2] / "forms"
    if package_forms_dir.is_dir():
        for form_path in sorted(package_forms_dir.glob("*.yaml")):
            shutil.copy2(form_path, forms_dir / form_path.name)
        return

    for form_name in _FALLBACK_FORMS:
        (forms_dir / f"{form_name}.yaml").write_text(f"name: {form_name}\n")


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
        root / "forms",
        root / "sidecar",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    _seed_forms(root / "forms")

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'concepts' / '.counters/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'forms/'}")
    click.echo(f"  {root / 'sidecar/'}")
