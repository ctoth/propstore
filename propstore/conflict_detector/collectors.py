"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from eq_equiv import equation_signature


from .equation_inputs import bound_equation_from_conflict_claim
from .models import ConflictClaim


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
