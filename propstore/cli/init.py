"""pks init — bootstrap a new propstore project."""
from __future__ import annotations

from pathlib import Path

import click

from propstore.artifacts.codecs import decode_yaml_mapping
from propstore.artifacts import FORM_FAMILY, FormRef
from propstore.repository import Repository


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


def _render_seed_form_files(
    repo: Repository,
    form_documents: list[tuple[FormRef, object]],
) -> dict[str, bytes]:
    """Render typed seed forms to repo-relative YAML blobs for one commit."""
    return {
        repo.artifacts.resolve(FORM_FAMILY, ref).relpath: repo.artifacts.render(document, FORM_FAMILY).encode("utf-8")
        for ref, document in form_documents
    }


@click.command()
@click.argument("directory", default="knowledge")
@click.pass_obj
def init(obj: dict, directory: str) -> None:
    """Initialize a new propstore project directory.

    Creates the standard knowledge tree (concepts/, claims/, contexts/,
    forms/, justifications/, predicates/, rules/, sidecar/, sources/,
    stances/, worldlines/) as a git-backed repository, and seeds the
    packaged default forms.
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

    if form_documents:
        if repo.git is None:
            raise click.ClickException("init requires a git-backed repository")
        repo.git.commit_files(
            _render_seed_form_files(repo, form_documents),
            "Seed default forms",
        )
        repo.snapshot.sync_worktree()

    click.echo(f"Initialized propstore project at {root}/")
    click.echo(f"  {root / 'concepts/'}")
    click.echo(f"  {root / 'claims/'}")
    click.echo(f"  {root / 'contexts/'}")
    click.echo(f"  {root / 'forms/'}")
    click.echo(f"  {root / 'justifications/'}")
    click.echo(f"  {root / 'predicates/'}")
    click.echo(f"  {root / 'rules/'}")
    click.echo(f"  {root / 'sidecar/'}")
    click.echo(f"  {root / 'sources/'}")
    click.echo(f"  {root / 'stances/'}")
    click.echo(f"  {root / 'worldlines/'}")
