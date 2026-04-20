"""Source proposal commands."""

from __future__ import annotations

import click

from propstore.cli.output import emit

from propstore.app.sources import (
    SourceAppError,
    SourceClaimProposalRequest,
    SourceConceptProposalRequest,
    SourceJustificationProposalRequest,
    SourceStanceProposalRequest,
    propose_source_claim,
    propose_source_concept,
    propose_source_justification,
    propose_source_stance,
)
from propstore.repository import Repository
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
    repo: Repository = obj["repo"]
    try:
        report = propose_source_concept(
            repo,
            SourceConceptProposalRequest(
                source_name=name,
                concept_name=concept_name,
                definition=definition,
                form_name=form_name,
                values=values,
                closed=closed,
            ),
        )
    except (SourceAppError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if report.status == "linked":
        canonical = report.linked_canonical_name or concept_name
        artifact_id = report.linked_artifact_id or ""
        emit(f"Linked '{concept_name}' \u2192 existing '{canonical}' ({artifact_id})")
    else:
        emit(f"Proposed new concept '{concept_name}' (form: {report.form_name})")


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
        report = propose_source_claim(
            repo,
            SourceClaimProposalRequest(
                source_name=name,
                claim_id=claim_id,
                claim_type=claim_type,
                statement=statement,
                concept=concept,
                value=value,
                unit=unit,
                context=context,
                page=page,
            ),
        )
    except (SourceAppError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    emit(
        f"Proposed claim '{claim_id}' (type: {report.claim_type}, artifact: {report.artifact_id})"
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
    try:
        report = propose_source_justification(
            repo,
            SourceJustificationProposalRequest(
                source_name=name,
                justification_id=just_id,
                conclusion=conclusion,
                premises=premises,
                rule_kind=rule_kind,
                page=page,
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    resolved_premises = ", ".join(report.premises)
    emit(
        f"Proposed justification '{just_id}' "
        f"({report.rule_kind}: {resolved_premises} \u2192 {report.conclusion})"
    )


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
        report = propose_source_stance(
            repo,
            SourceStanceProposalRequest(
                source_name=name,
                source_claim=source_claim,
                target=target,
                stance_type=stance_type,
                strength=strength,
                note=note,
            ),
        )
    except (SourceAppError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    emit(
        f"Proposed stance: '{source_claim}' {report.stance_type} '{report.target}'"
    )
