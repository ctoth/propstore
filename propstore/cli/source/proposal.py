"""Source proposal commands."""

from __future__ import annotations

import click

from propstore.artifacts.documents.sources import SourceConceptFormParametersDocument
from propstore.core.claim_types import coerce_claim_type
from propstore.repository import Repository
from propstore.stances import coerce_stance_type
from propstore.source import (
    commit_source_claim_proposal,
    commit_source_concept_proposal,
    commit_source_justification_proposal,
    commit_source_stance_proposal,
)
from propstore.cli.source import source


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
@click.option("--context", required=True)
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
    context: str,
    page: int | None,
) -> None:
    repo: Repository = obj["repo"]
    try:
        typed_claim_type = coerce_claim_type(claim_type)
        if typed_claim_type is None:
            raise ValueError("claim type is required")
        entry = commit_source_claim_proposal(
            repo,
            name,
            claim_id=claim_id,
            claim_type=typed_claim_type,
            statement=statement,
            concept=concept,
            value=value,
            unit=unit,
            context=context,
            page=page,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    artifact_id = "" if entry.artifact_id is None else entry.artifact_id
    click.echo(
        f"Proposed claim '{claim_id}' (type: {typed_claim_type.value}, artifact: {artifact_id})"
    )


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
        typed_stance_type = coerce_stance_type(stance_type)
        if typed_stance_type is None:
            raise ValueError("stance type is required")
        entry = commit_source_stance_proposal(
            repo,
            name,
            source_claim=source_claim,
            target=target,
            stance_type=typed_stance_type,
            strength=strength,
            note=note,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Proposed stance: '{source_claim}' {typed_stance_type.value} '{target}'")
