"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from propstore.claims import LoadedClaimsFile, claim_file_claims, claim_file_source_paper
from propstore.equation_comparison import equation_signature

from .models import ConflictClaim


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


def conflict_claims_from_claim_files(
    claim_files: Sequence[LoadedClaimsFile],
) -> list[ConflictClaim]:
    claims: list[ConflictClaim] = []
    for claim_file in claim_files:
        source_paper = claim_file_source_paper(claim_file)
        for claim_document in claim_file_claims(claim_file):
            claim = conflict_claim_from_payload(
                claim_document.to_payload(),
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
        if claim.claim_type == "measurement" and claim.target_concept_id and claim.measure:
            by_key[(claim.target_concept_id, claim.measure)].append(claim)
    return dict(by_key)


def _collect_parameter_claims(
    claims: Sequence[ConflictClaim],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type == "parameter" and claim.concept_id:
            by_concept[claim.concept_id].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claims: Sequence[ConflictClaim],
) -> dict[tuple[str, tuple[str, ...]], list[ConflictClaim]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[ConflictClaim]] = defaultdict(list)
    for claim in claims:
        if claim.claim_type != "equation":
            continue
        signature = equation_signature(claim)
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
        if claim.concept_id is not None:
            by_concept[claim.concept_id].append(claim)
            continue
        first_concept = next((variable.concept_id for variable in claim.variables), None)
        if first_concept is not None:
            by_concept[first_concept].append(claim)
    return dict(by_concept)
