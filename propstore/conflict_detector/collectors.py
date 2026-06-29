"""Claim ingestion and grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from eq_equiv import BoundEquation, EquationSymbolBinding, equation_signature

from propstore.claim_equations import bound_equation

from .models import ConflictClaim


def conflict_claim_from_payload(
    payload: Mapping[str, Any],
    *,
    source_paper: str | None = None,
) -> ConflictClaim | None:
    """Parse a stored claim payload into a :class:`ConflictClaim`.

    A payload-supplied ``source_paper`` only fills in when the claim does not
    already carry one; the source provenance is then folded into the claim's
    conditions so the solver treats different papers as disjoint enum values.
    """

    claim = ConflictClaim.from_payload(payload)
    if claim is None:
        return None
    if claim.source_paper is None and source_paper:
        claim = replace(claim, source_paper=source_paper)
    return claim.with_source_condition()


def equation_bound_for_claim(claim: ConflictClaim) -> BoundEquation:
    """Lower an EQUATION claim into eq-equiv's ``BoundEquation`` for comparison."""

    expression = claim.expression or claim.sympy or ""
    bindings = tuple(
        EquationSymbolBinding(
            symbol=variable.symbol,
            concept_id=variable.concept_id,
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
            claim.claim_type == "measurement"
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
        if claim.claim_type == "parameter" and claim.output_concept_id:
            by_concept[claim.output_concept_id].append(claim)
    return dict(by_concept)


def collect_equation_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, tuple[str, ...]], list[ConflictClaim]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[ConflictClaim]] = defaultdict(
        list
    )
    for claim in claims:
        if claim.claim_type != "equation":
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
