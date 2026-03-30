"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.repository import Repository


_FALLBACK_FORMS = (
    "category",
    "boolean",
    "structural",
    "count",
    "rate",
    "score",
    "ratio",
)


def _seed_form_files() -> dict[str, bytes]:
    """Return default form files keyed by repo-relative path."""
    form_files: dict[str, bytes] = {}
    package_forms_dir = Path(__file__).resolve().parent.parent / "_resources" / "forms"
    if package_forms_dir.is_dir():
        for form_path in sorted(package_forms_dir.glob("*.yaml")):
            form_files[f"forms/{form_path.name}"] = form_path.read_bytes()
        return form_files

    for form_name in _FALLBACK_FORMS:
        stub = f"name: {form_name}\nkind: {form_name}\ndimensionless: false\n"
        form_files[f"forms/{form_name}.yaml"] = stub.encode("utf-8")
    return form_files


def _materialize_seed_forms(forms_dir: Path, form_files: dict[str, bytes]) -> None:
    """Write default form files to disk for non-git repos."""
    forms_dir.mkdir(parents=True, exist_ok=True)
    for rel_path, content in sorted(form_files.items()):
        if not rel_path.startswith("forms/"):
            continue
        (forms_dir / rel_path.removeprefix("forms/")).write_bytes(content)


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

    form_files = _seed_form_files()

    # Commit seeded forms to git
    git = repo.git
    if git is not None:
        if form_files:
            git.commit_files(form_files, "Seed default forms")
            git.sync_worktree()
    else:
        _materialize_seed_forms(repo.forms_dir, form_files)

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'forms/'}")
    click.echo(f"  {root / 'sidecar/'}")
    click.echo(f"  {root / 'stances/'}")
