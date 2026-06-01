"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from eq_equiv import equation_signature


from .equation_inputs import bound_equation_from_conflict_claim
from .models import ConflictClaim, ConflictClaimVariable

if TYPE_CHECKING:
    from propstore.families.claims.declaration import Claim


def conflict_claim_from_claim(claim: Claim) -> ConflictClaim | None:
    numeric_payload = claim.numeric_payload
    text_payload = claim.text_payload
    algorithm_payload = claim.algorithm_payload
    output_concept_id = claim.output_concept_id
    target_concept_id = claim.target_concept
    claim_type = str(getattr(claim.type, "value", claim.type))
    if (
        claim_type == "measurement"
        and output_concept_id is not None
        and target_concept_id is None
    ):
        target_concept_id = output_concept_id
    variables = tuple(
        ConflictClaimVariable(
            concept_id=str(variable.concept_id),
            symbol=None if variable.symbol is None else str(variable.symbol),
            role=None if variable.role is None else str(variable.role),
            name=None if variable.name is None else str(variable.name),
        )
        for variable in claim.variables
        if variable.concept_id is not None
    )
    return ConflictClaim(
        claim_id=str(claim.id),
        claim_type=claim_type,
        output_concept_id=(
            output_concept_id if claim_type in {"parameter", "algorithm"} else None
        ),
        target_concept_id=target_concept_id,
        measure=None if text_payload is None else text_payload.measure,
        value=None if numeric_payload is None else numeric_payload.value,
        lower_bound=None if numeric_payload is None else numeric_payload.lower_bound,
        upper_bound=None if numeric_payload is None else numeric_payload.upper_bound,
        unit=None if numeric_payload is None else numeric_payload.unit,
        expression=None if text_payload is None else text_payload.expression,
        sympy=None if text_payload is None else text_payload.sympy_generated,
        body=None if algorithm_payload is None else algorithm_payload.body,
        listener_population=(
            None if text_payload is None else text_payload.listener_population
        ),
        source_paper=claim.source_paper,
        context_id=claim.context_id,
        conditions=claim.conditions,
        variables=variables,
    ).with_source_condition()


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
