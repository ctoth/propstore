"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.artifacts.codecs import decode_yaml_mapping
from propstore.artifacts import FORM_FAMILY, FormRef
from propstore.cli.repository import Repository


def _seed_form_documents(repo: Repository) -> list[tuple[FormRef, object]]:
    """Return typed default forms ready for artifact-store persistence."""
    form_documents: list[tuple[FormRef, object]] = []
    package_forms_dir = Path(__file__).resolve().parent.parent / "_resources" / "forms"
    if not package_forms_dir.is_dir():
        raise click.ClickException(
            f"init requires packaged form resources at {package_forms_dir}"
        )
    for form_path in sorted(package_forms_dir.glob("*.yaml")):
        payload = decode_yaml_mapping(form_path.read_bytes(), source=str(form_path))
        form_documents.append(
            (
                FormRef(form_path.stem),
                repo.artifacts.coerce(FORM_FAMILY, payload, source=str(form_path)),
            )
        )
    return form_documents


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: dict, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates the standard knowledge tree (concepts/, claims/, contexts/,
    forms/, justifications/, sidecar/, sources/, stances/, worldlines/)
    as a git-backed repository, and seeds the packaged default forms.
    If no DIRECTORY argument is given, creates a ``knowledge/`` directory
    in the current working directory.
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

    form_documents = _seed_form_documents(repo)

    git = repo.git
    if git is None:
        raise click.ClickException("init requires a git-backed repository")
    if form_documents:
        with repo.artifacts.transact(message="Seed default forms") as transaction:
            for ref, document in form_documents:
                transaction.save(FORM_FAMILY, ref, document)
        git.sync_worktree()

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'forms/'}")
    click.echo(f"  {root / 'sidecar/'}")
    click.echo(f"  {root / 'stances/'}")
