"""Claim ingestion and grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from eq_equiv import BoundEquation, EquationSymbolBinding, equation_signature

from propstore.claim_equations import bound_equation
from propstore.families.claims import ClaimType

from .models import ConflictClaim


def equation_bound_for_claim(claim: ConflictClaim) -> BoundEquation:
    """Lower an EQUATION claim into eq-equiv's ``BoundEquation`` for comparison."""

    expression = claim.expression or claim.sympy or ""
    bindings = tuple(
        EquationSymbolBinding(
            symbol=variable.symbol,
            concept_id=variable.concept,
            role=variable.role,
        )
        for variable in claim.variables
        if variable.symbol
    )
    return bound_equation(expression, bindings)


def collect_measurement_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, str], list[ConflictClaim]]:
    by_key: dict[tuple[str, str], list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if (
            claim.claim_type is ClaimType.MEASUREMENT
            and claim.target_concept_id
            and claim.measure
        ):
            by_key[(claim.target_concept_id, claim.measure)].append(claim)
    return dict(by_key)


def collect_parameter_claims(
    claims: Sequence[ConflictClaim],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type is ClaimType.PARAMETER and claim.output_concept_id:
            by_concept[claim.output_concept_id].append(claim)
    return dict(by_concept)


def collect_equation_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, tuple[str, ...]], list[ConflictClaim]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[ConflictClaim]] = defaultdict(
        list
    )
    for claim in claims:
        if claim.claim_type is not ClaimType.EQUATION:
            continue
        signature = equation_signature(equation_bound_for_claim(claim))
        if signature is None:
            continue
        by_signature[signature].append(claim)
    return dict(by_signature)


def collect_algorithm_claims(
    claims: Sequence[ConflictClaim],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type is not ClaimType.ALGORITHM:
            continue
        if claim.output_concept_id is not None:
            by_concept[claim.output_concept_id].append(claim)
            continue
        first_concept = next((variable.concept for variable in claim.variables), None)
        if first_concept is not None:
            by_concept[first_concept].append(claim)
    return dict(by_concept)
