"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING, Any, cast

from eq_equiv import equation_signature
from quire.documents import document_to_payload

from propstore.claims import (
    LoadedClaimsFile,
    claim_file_claims,
    claim_file_source_paper,
)

from .equation_inputs import bound_equation_from_conflict_claim
from .models import ConflictClaim, ConflictClaimVariable

if TYPE_CHECKING:
    from propstore.families.claims.declaration import Claim


def conflict_claim_from_payload(
    payload: Mapping[str, Any],
    *,
    source_paper: str | None = None,
) -> ConflictClaim | None:
    claim = ConflictClaim.from_payload(dict(payload))
    if claim is None:
        return None
    if claim.source_paper is None and source_paper:
        claim = replace(claim, source_paper=source_paper)
    return claim.with_source_condition()


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


def conflict_claims_from_claim_files(
    claim_files: Sequence[LoadedClaimsFile],
) -> list[ConflictClaim]:
    claims: list[ConflictClaim] = []
    for claim_file in claim_files:
        source_paper = claim_file_source_paper(claim_file)
        for claim_document in claim_file_claims(claim_file):
            claim = conflict_claim_from_payload(
                cast(Mapping[str, Any], document_to_payload(claim_document)),
                source_paper=source_paper,
            )
            if claim is None:
                continue
            claims.append(claim)
    return claims


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
