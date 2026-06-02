"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from eq_equiv import equation_signature


from .equation_inputs import bound_equation_from_conflict_claim
from .models import ConflictClaim, ConflictClaimVariable

if TYPE_CHECKING:
    from propstore.families.claims.declaration import ClaimDocument


def conflict_claim_from_claim_document(
    claim: ClaimDocument,
) -> ConflictClaim | None:
    claim_id = claim.artifact_id or claim.primary_logical_id or claim.id
    if claim_id is None:
        return None

    claim_type = None if claim.type is None else str(getattr(claim.type, "value", claim.type))
    target_concept_id = claim.target_concept
    if (
        claim_type == "measurement"
        and claim.output_concept is not None
        and target_concept_id is None
    ):
        target_concept_id = claim.output_concept

    variables = tuple(
        ConflictClaimVariable(
            concept_id=str(variable.concept),
            symbol=None if variable.symbol is None else str(variable.symbol),
            role=None if variable.role is None else str(variable.role),
            name=None if variable.name is None else str(variable.name),
        )
        for variable in claim.variables
        if variable.concept is not None
    )
    source_paper = None
    if claim.source is not None:
        source_paper = claim.source.paper
    elif claim.provenance is not None:
        source_paper = claim.provenance.paper

    return ConflictClaim(
        claim_id=str(claim_id),
        claim_type=claim_type,
        artifact_id=claim.artifact_id,
        output_concept_id=(
            claim.output_concept if claim_type in {"parameter", "algorithm"} else None
        ),
        target_concept_id=target_concept_id,
        measure=claim.measure,
        value=claim.value,
        lower_bound=claim.lower_bound,
        upper_bound=claim.upper_bound,
        unit=claim.unit,
        expression=claim.expression,
        sympy=claim.sympy,
        body=claim.body,
        listener_population=claim.listener_population,
        source_paper=source_paper,
        context_id=str(claim.context.id) if claim.context is not None else None,
        conditions=claim.conditions,
        variables=variables,
    ).with_source_condition()


def conflict_claims_from_claim_documents(
    claims: Sequence[ClaimDocument],
) -> list[ConflictClaim]:
    conflict_claims: list[ConflictClaim] = []
    for claim in claims:
        conflict_claim = conflict_claim_from_claim_document(claim)
        if conflict_claim is not None:
            conflict_claims.append(conflict_claim)
    return conflict_claims


def _collect_measurement_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, str], list[ConflictClaim]]:
    by_key: dict[tuple[str, str], list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if (
            claim.claim_type == "measurement"
            and claim.target_concept_id
            and claim.measure
        ):
            by_key[(claim.target_concept_id, claim.measure)].append(claim)
    return dict(by_key)


def _collect_parameter_claims(
    claims: Sequence[ConflictClaim],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type == "parameter" and claim.output_concept_id:
            by_concept[claim.output_concept_id].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, tuple[str, ...]], list[ConflictClaim]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[ConflictClaim]] = defaultdict(
        list
    )
    for claim in claims:
        if claim.claim_type != "equation":
            continue
        signature = equation_signature(bound_equation_from_conflict_claim(claim))
        if signature is None:
            continue
        by_signature[signature].append(claim)
    return dict(by_signature)


def _collect_algorithm_claims(
    claims: Sequence[ConflictClaim],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type != "algorithm":
            continue
        if claim.output_concept_id is not None:
            by_concept[claim.output_concept_id].append(claim)
            continue
        first_concept = next(
            (variable.concept_id for variable in claim.variables), None
        )
        if first_concept is not None:
            by_concept[first_concept].append(claim)
    return dict(by_concept)
