"""pks source - source lifecycle commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.repository import Repository
from propstore.core.source_types import (
    coerce_source_kind,
    coerce_source_origin_type,
)
from propstore.provenance import stamp_file
from propstore.source_documents import SourceConceptFormParametersDocument
from propstore.source import (
    commit_source_claim_proposal,
    commit_source_claims_batch,
    commit_source_concept_proposal,
    commit_source_concepts_batch,
    commit_source_justification_proposal,
    commit_source_justifications_batch,
    commit_source_metadata,
    commit_source_notes,
    commit_source_stance_proposal,
    commit_source_stances_batch,
    finalize_source_branch,
    init_source_branch,
    promote_source_branch,
    sync_source_branch,
    source_branch_name,
)


@click.group()
def source() -> None:
    """Manage source branches and source-local artifacts."""


def _auto_finalize_source_branch(repo: Repository, name: str) -> None:
    try:
        finalize_source_branch(repo, name)
    except Exception as exc:
        click.echo(f"Finalize note: {exc}", err=True)
        return
    click.echo(f"Auto-finalized {source_branch_name(name)}")


@source.command("init")
@click.argument("name")
@click.option("--kind", "kind_name", required=True)
@click.option("--origin-type", required=True)
@click.option("--origin-value", required=True)
@click.option("--content-file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def source_init(
    obj: dict,
    name: str,
    kind_name: str,
    origin_type: str,
    origin_value: str,
    content_file: Path | None,
) -> None:
    repo: Repository = obj["repo"]
    try:
        source_kind = coerce_source_kind(kind_name)
        source_origin_type = coerce_source_origin_type(origin_type)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    branch = init_source_branch(
        repo,
        name,
        kind=source_kind,
        origin_type=source_origin_type,
        origin_value=origin_value,
        content_file=content_file,
    )
    click.echo(f"Initialized {branch}")


@source.command("write-notes")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_notes(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    commit_source_notes(repo, name, file_path)
    click.echo(f"Wrote notes to {source_branch_name(name)}")


@source.command("write-metadata")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def write_metadata(obj: dict, name: str, file_path: Path) -> None:
    repo: Repository = obj["repo"]
    commit_source_metadata(repo, name, file_path)
    click.echo(f"Wrote metadata to {source_branch_name(name)}")


@source.command("propose-concept")
@click.argument("name")
@click.option("--name", "concept_name", required=True)
@click.option("--definition", required=True)
@click.option("--form", "form_name", required=True)
@click.option("--values", default=None, help="Comma-separated values (required for category concepts)")
@click.option("--closed", is_flag=True, default=False, help="Declare category value set as exhaustive (extensible: false)")
@click.pass_obj
def propose_concept(
    obj: dict,
    name: str,
    concept_name: str,
    definition: str,
    form_name: str,
    values: str | None,
    closed: bool,
) -> None:
    if closed and form_name != "category":
        raise click.ClickException("--closed is only valid with --form=category")
    if values is not None and form_name != "category":
        raise click.ClickException("--values is only valid with --form=category")
    repo: Repository = obj["repo"]
    try:
        form_parameters: SourceConceptFormParametersDocument | None = None
        if values is not None:
            value_list = tuple(v.strip() for v in values.split(",") if v.strip())
            form_parameters = SourceConceptFormParametersDocument(
                values=value_list,
                extensible=False if closed else None,
            )
        elif closed:
            form_parameters = SourceConceptFormParametersDocument(extensible=False)
        info = commit_source_concept_proposal(
            repo,
            name,
            local_name=concept_name,
            definition=definition,
            form=form_name,
            form_parameters=form_parameters,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    status = info.status or "proposed"
    if status == "linked":
        match = info.registry_match
        canonical = concept_name if match is None or match.canonical_name is None else match.canonical_name
        artifact_id = "" if match is None else match.artifact_id
        click.echo(f"Linked '{concept_name}' \u2192 existing '{canonical}' ({artifact_id})")
    else:
        click.echo(f"Proposed new concept '{concept_name}' (form: {info.form or form_name})")


@source.command("propose-claim")
@click.argument("name")
@click.option("--id", "claim_id", required=True)
@click.option("--type", "claim_type", required=True)
@click.option("--statement", required=False)
@click.option("--concept", required=False)
@click.option("--value", type=float, required=False)
@click.option("--unit", required=False)
@click.option("--page", type=int, required=False)
@click.pass_obj
def propose_claim(
    obj: dict,
    name: str,
    claim_id: str,
    claim_type: str,
    statement: str | None,
    concept: str | None,
    value: float | None,
    unit: str | None,
    page: int | None,
) -> None:
    repo: Repository = obj["repo"]
    try:
        entry = commit_source_claim_proposal(
            repo,
            name,
            claim_id=claim_id,
            claim_type=claim_type,
            statement=statement,
            concept=concept,
            value=value,
            unit=unit,
            page=page,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    artifact_id = "" if entry.artifact_id is None else entry.artifact_id
    click.echo(f"Proposed claim '{claim_id}' (type: {claim_type}, artifact: {artifact_id})")


@source.command("propose-justification")
@click.argument("name")
@click.option("--id", "just_id", required=True)
@click.option("--conclusion", required=True)
@click.option("--premises", required=True)
@click.option("--rule-kind", required=True)
@click.option("--page", type=int, required=False)
@click.pass_obj
def propose_justification(
    obj: dict,
    name: str,
    just_id: str,
    conclusion: str,
    premises: str,
    rule_kind: str,
    page: int | None,
) -> None:
    repo: Repository = obj["repo"]
    premises_list = [p.strip() for p in premises.split(",") if p.strip()]
    try:
        entry = commit_source_justification_proposal(
            repo,
            name,
            just_id=just_id,
            conclusion=conclusion,
            premises=premises_list,
            rule_kind=rule_kind,
            page=page,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    resolved_premises = ", ".join(entry.premises or tuple(premises_list))
    resolved_conclusion = entry.conclusion or conclusion
    click.echo(f"Proposed justification '{just_id}' ({rule_kind}: {resolved_premises} \u2192 {resolved_conclusion})")


@source.command("propose-stance")
@click.argument("name")
@click.option("--source-claim", required=True)
@click.option("--target", required=True)
@click.option("--type", "stance_type", required=True)
@click.option("--strength", required=False)
@click.option("--note", required=False)
@click.pass_obj
def propose_stance(
    obj: dict,
    name: str,
    source_claim: str,
    target: str,
    stance_type: str,
    strength: str | None,
    note: str | None,
) -> None:
    repo: Repository = obj["repo"]
    try:
        entry = commit_source_stance_proposal(
            repo,
            name,
            source_claim=source_claim,
            target=target,
            stance_type=stance_type,
            strength=strength,
            note=note,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Proposed stance: '{source_claim}' {stance_type} '{target}'")


@source.command("add-concepts")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def add_concepts(obj: dict, name: str, batch_file: Path) -> None:
    repo: Repository = obj["repo"]
    try:
        commit_source_concepts_batch(repo, name, batch_file)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote concepts to {source_branch_name(name)}")
    _auto_finalize_source_branch(repo, name)


@source.command("add-claim")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these claims (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_claim(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        commit_source_claims_batch(repo, name, batch_file, reader=reader, method=method)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote claims to {source_branch_name(name)}")
    _auto_finalize_source_branch(repo, name)


@source.command("add-justification")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these justifications (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_justification(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        commit_source_justifications_batch(repo, name, batch_file, reader=reader, method=method)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote justifications to {source_branch_name(name)}")
    _auto_finalize_source_branch(repo, name)


@source.command("add-stance")
@click.argument("name")
@click.option("--batch", "batch_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--reader", required=False, help="Who extracted these stances (human name or model ID)")
@click.option("--method", required=False, help="Extraction method (skill name, 'manual', etc.)")
@click.pass_obj
def add_stance(obj: dict, name: str, batch_file: Path, reader: str | None, method: str | None) -> None:
    repo: Repository = obj["repo"]
    try:
        commit_source_stances_batch(repo, name, batch_file, reader=reader, method=method)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Wrote stances to {source_branch_name(name)}")
    _auto_finalize_source_branch(repo, name)


@source.command("finalize")
@click.argument("name")
@click.pass_obj
def finalize(obj: dict, name: str) -> None:
    repo: Repository = obj["repo"]
    try:
        finalize_source_branch(repo, name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Finalized {source_branch_name(name)}")


@source.command("promote")
@click.argument("name")
@click.pass_obj
def promote(obj: dict, name: str) -> None:
    repo: Repository = obj["repo"]
    try:
        promote_source_branch(repo, name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Promoted {source_branch_name(name)} to master")


@source.command("sync")
@click.argument("name")
@click.option("--output-dir", type=click.Path(file_okay=False, path_type=Path))
@click.pass_obj
def sync(obj: dict, name: str, output_dir: Path | None) -> None:
    repo: Repository = obj["repo"]
    try:
        destination = sync_source_branch(repo, name, output_dir=output_dir)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Synchronized {source_branch_name(name)} to {destination}")


@source.command("stamp-provenance")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--agent", required=True)
@click.option("--skill", "skill_name", required=True)
@click.option("--plugin-version", required=False)
def stamp_provenance(
    name: str,
    file_path: Path,
    agent: str,
    skill_name: str,
    plugin_version: str | None,
) -> None:
    """Stamp extraction provenance onto a pipeline artifact.

    DEPRECATED: Use --reader/--method flags on add-claim, add-justification,
    add-stance instead. Provenance is now stored on the source branch directly.
    """
    stamp_file(file_path, agent=agent, skill=skill_name, plugin_version=plugin_version)
    click.echo(f"Stamped provenance on {file_path}")
