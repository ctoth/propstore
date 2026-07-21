"""Source-branch single-artifact proposal commands.

``propose-concept`` / ``propose-claim`` / ``propose-justification`` /
``propose-stance`` author one artifact at a time onto a source branch, each a thin
adapter over the matching ``commit_source_*_proposal`` owner.
"""

from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit_success
from propstore.cli.source import source
from propstore.families.sources import SourceConceptFormParametersDocument
from propstore.source.claims import coerce_claim_type, commit_source_claim_proposal
from propstore.source.concepts import commit_source_concept_proposal
from propstore.source.relations import (
    commit_source_justification_proposal,
    commit_source_stance_proposal,
)
from propstore.stances import coerce_stance_type


def _parse_comma_values(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    return tuple(value.strip() for value in raw.split(",") if value.strip())


@source.command("propose-concept")
@click.argument("name")
@click.option(
    "--concept-name", "concept_name", required=True, help="Source-local concept handle."
)
@click.option("--definition", required=True, help="Concept definition.")
@click.option(
    "--form", "form_name", required=True, help="Concept form (must be a known form)."
)
@click.option("--values", default=None, help="Comma-separated category values.")
@click.option(
    "--closed",
    is_flag=True,
    default=False,
    help="Mark the value set exhaustive (extensible: false).",
)
@click.pass_obj
def propose_concept(
    obj: CliContext,
    name: str,
    concept_name: str,
    definition: str,
    form_name: str,
    values: str | None,
    closed: bool,
) -> None:
    """Propose one concept onto a source branch."""
    repo = require_repo(obj)
    form_parameters: SourceConceptFormParametersDocument | None = None
    parsed_values = _parse_comma_values(values)
    if parsed_values or closed:
        form_parameters = SourceConceptFormParametersDocument(
            values=parsed_values or None,
            extensible=False if closed else None,
        )
    entry = commit_source_concept_proposal(
        repo,
        name,
        local_name=concept_name,
        definition=definition,
        form=form_name,
        form_parameters=form_parameters,
    )
    if entry.status == "linked" and entry.registry_match is not None:
        canonical = entry.registry_match.canonical_name or concept_name
        emit_success(
            f"Linked '{concept_name}' -> existing '{canonical}' "
            f"({entry.registry_match.artifact_id})"
        )
    else:
        emit_success(f"Proposed new concept '{concept_name}' (form: {entry.form})")


@source.command("propose-claim")
@click.argument("name")
@click.option("--id", "claim_id", required=True, help="Source-local claim handle.")
@click.option(
    "--type", "claim_type", required=True, help="Claim type (observation/parameter/…)."
)
@click.option("--context", required=True, help="Context id the claim is asserted in.")
@click.option("--statement", default=None)
@click.option(
    "--concept",
    default=None,
    help="Single concept handle (parameter/measurement subject).",
)
@click.option(
    "--concept-ref", "concept_refs", multiple=True, help="Additional concept handle(s)."
)
@click.option("--condition", "conditions", multiple=True, help="CEL condition(s).")
@click.option("--value", type=float, default=None)
@click.option("--lower-bound", type=float, default=None)
@click.option("--upper-bound", type=float, default=None)
@click.option("--unit", default=None)
@click.option("--notes", default=None)
@click.option("--uncertainty", type=float, default=None)
@click.option("--uncertainty-type", default=None)
@click.option("--page", type=int, default=None)
@click.option("--section", default=None)
@click.option("--quote-fragment", default=None)
@click.option("--table", default=None)
@click.option("--figure", default=None)
@click.pass_obj
def propose_claim(
    obj: CliContext,
    name: str,
    claim_id: str,
    claim_type: str,
    context: str,
    statement: str | None,
    concept: str | None,
    concept_refs: tuple[str, ...],
    conditions: tuple[str, ...],
    value: float | None,
    lower_bound: float | None,
    upper_bound: float | None,
    unit: str | None,
    notes: str | None,
    uncertainty: float | None,
    uncertainty_type: str | None,
    page: int | None,
    section: str | None,
    quote_fragment: str | None,
    table: str | None,
    figure: str | None,
) -> None:
    """Propose one claim onto a source branch."""
    repo = require_repo(obj)
    claim = commit_source_claim_proposal(
        repo,
        name,
        claim_id=claim_id,
        claim_type=coerce_claim_type(claim_type),
        context=context,
        statement=statement,
        concept=concept,
        concepts=concept_refs,
        conditions=conditions,
        value=value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        unit=unit,
        notes=notes,
        uncertainty=uncertainty,
        uncertainty_type=uncertainty_type,
        page=page,
        section=section,
        quote_fragment=quote_fragment,
        table=table,
        figure=figure,
    )
    type_label = claim.type.value if claim.type is not None else "?"
    emit_success(
        f"Proposed claim '{claim_id}' (type: {type_label}, artifact: {claim.artifact_id})"
    )


@source.command("propose-justification")
@click.argument("name")
@click.option(
    "--id", "just_id", required=True, help="Source-local justification handle."
)
@click.option("--conclusion", required=True, help="Conclusion claim handle.")
@click.option(
    "--premises", required=True, help="Comma-separated premise claim handle(s)."
)
@click.option("--rule-kind", required=True)
@click.option("--rule-strength", default=None, help="strict or defeasible.")
@click.option("--page", type=int, default=None)
@click.option("--section", default=None)
@click.option("--quote-fragment", default=None)
@click.option("--table", default=None)
@click.option("--figure", default=None)
@click.option("--attack-target-claim", default=None)
@click.option("--attack-target-justification-id", default=None)
@click.option("--attack-target-premise-index", type=int, default=None)
@click.pass_obj
def propose_justification(
    obj: CliContext,
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
    """Propose one justification onto a source branch."""
    repo = require_repo(obj)
    justification = commit_source_justification_proposal(
        repo,
        name,
        just_id=just_id,
        conclusion=conclusion,
        premises=_parse_comma_values(premises),
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
    )
    emit_success(f"Proposed justification '{just_id}' ({justification.rule_kind})")


@source.command("propose-stance")
@click.argument("name")
@click.option("--source-claim", required=True, help="Asserting claim handle.")
@click.option("--target", required=True, help="Target claim handle.")
@click.option(
    "--type", "stance_type", required=True, help="Stance type (supports/rebuts/…)."
)
@click.option("--strength", default=None)
@click.option("--note", default=None)
@click.pass_obj
def propose_stance(
    obj: CliContext,
    name: str,
    source_claim: str,
    target: str,
    stance_type: str,
    strength: str | None,
    note: str | None,
) -> None:
    """Propose one stance onto a source branch."""
    repo = require_repo(obj)
    coerced = coerce_stance_type(stance_type)
    if coerced is None:
        fail(f"Unknown stance type {stance_type!r}.")
    stance = commit_source_stance_proposal(
        repo,
        name,
        source_claim=source_claim,
        target=target,
        stance_type=coerced,
        strength=strength,
        note=note,
    )
    type_label = stance.type.value if stance.type is not None else stance_type
    emit_success(f"Proposed stance '{source_claim}' -> '{target}' ({type_label})")
