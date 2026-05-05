"""Source proposal commands."""

from __future__ import annotations

import click

from propstore.cli.output import emit_success

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


def _parse_comma_values(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    return tuple(value.strip() for value in raw.split(",") if value.strip())


@source.command("propose-concept")
@click.argument("source_name", metavar="SOURCE_NAME")
@click.option("--concept-name", required=True)
@click.option("--definition", required=True)
@click.option("--form", "form_name", required=True)
@click.option("--values", default=None, help="Comma-separated values (required for category concepts)")
@click.option("--closed", is_flag=True, default=False, help="Declare category value set as exhaustive (extensible: false)")
@click.pass_obj
def propose_concept(
    obj: dict,
    source_name: str,
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
                source_name=source_name,
                concept_name=concept_name,
                definition=definition,
                form_name=form_name,
                values=_parse_comma_values(values),
                closed=closed,
            ),
        )
    except (SourceAppError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if report.status == "linked":
        canonical = report.linked_canonical_name or concept_name
        artifact_id = report.linked_artifact_id or ""
        emit_success(f"Linked '{concept_name}' \u2192 existing '{canonical}' ({artifact_id})")
    else:
        emit_success(f"Proposed new concept '{concept_name}' (form: {report.form_name})")


@source.command("propose-claim")
@click.argument("name")
@click.option("--id", "claim_id", required=True)
@click.option("--type", "claim_type", required=True)
@click.option("--statement", required=False)
@click.option("--concept", required=False)
@click.option("--concept-ref", "concept_refs", multiple=True)
@click.option("--condition", "conditions", multiple=True)
@click.option("--value", type=float, required=False)
@click.option("--lower-bound", type=float, required=False)
@click.option("--upper-bound", type=float, required=False)
@click.option("--unit", required=False)
@click.option("--context", required=True)
@click.option("--notes", required=False)
@click.option("--uncertainty", type=float, required=False)
@click.option("--uncertainty-type", required=False)
@click.option("--page", type=int, required=False)
@click.option("--section", required=False)
@click.option("--quote-fragment", required=False)
@click.option("--table", required=False)
@click.option("--figure", required=False)
@click.pass_obj
def propose_claim(
    obj: dict,
    name: str,
    claim_id: str,
    claim_type: str,
    statement: str | None,
    concept: str | None,
    concept_refs: tuple[str, ...],
    conditions: tuple[str, ...],
    value: float | None,
    lower_bound: float | None,
    upper_bound: float | None,
    unit: str | None,
    context: str,
    notes: str | None,
    uncertainty: float | None,
    uncertainty_type: str | None,
    page: int | None,
    section: str | None,
    quote_fragment: str | None,
    table: str | None,
    figure: str | None,
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
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                unit=unit,
                context=context,
                concepts=concept_refs,
                conditions=conditions,
                notes=notes,
                uncertainty=uncertainty,
                uncertainty_type=uncertainty_type,
                page=page,
                section=section,
                quote_fragment=quote_fragment,
                table=table,
                figure=figure,
            ),
        )
    except (SourceAppError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    emit_success(
        f"Proposed claim '{claim_id}' (type: {report.claim_type}, artifact: {report.artifact_id})"
    )


@source.command("propose-justification")
@click.argument("name")
@click.option("--id", "just_id", required=True)
@click.option("--conclusion", required=True)
@click.option("--premises", required=True)
@click.option("--rule-kind", required=True)
@click.option("--rule-strength", required=False)
@click.option("--page", type=int, required=False)
@click.option("--section", required=False)
@click.option("--quote-fragment", required=False)
@click.option("--table", required=False)
@click.option("--figure", required=False)
@click.option("--attack-target-claim", required=False)
@click.option("--attack-target-justification-id", required=False)
@click.option("--attack-target-premise-index", type=int, required=False)
@click.pass_obj
def propose_justification(
    obj: dict,
    name: str,
    just_id: str,
    conclusion: str,
    premises: str,
    rule_kind: str,
    rule_strength: str | None,
    page: int | None,
    section: str | None,
    quote_fragment: str | None,
    table: str | None,
    figure: str | None,
    attack_target_claim: str | None,
    attack_target_justification_id: str | None,
    attack_target_premise_index: int | None,
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
                rule_strength=rule_strength,
                page=page,
                section=section,
                quote_fragment=quote_fragment,
                table=table,
                figure=figure,
                attack_target_claim=attack_target_claim,
                attack_target_justification_id=attack_target_justification_id,
                attack_target_premise_index=attack_target_premise_index,
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    resolved_premises = ", ".join(report.premises)
    emit_success(
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
    emit_success(
        f"Proposed stance: '{source_claim}' {report.stance_type} '{report.target}'"
    )
