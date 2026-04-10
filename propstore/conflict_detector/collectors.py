"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace

from propstore.claim_documents import (
    ClaimFileInput,
    claim_file_claim_payloads,
    claim_payload_source_paper,
)
from propstore.equation_comparison import equation_signature

from .models import ConflictClaim


def _iter_conflict_claims(claim_files: Sequence[ClaimFileInput]) -> list[ConflictClaim]:
    claims: list[ConflictClaim] = []
    for claim_file in claim_files:
        for payload in claim_file_claim_payloads(claim_file):
            claim = ConflictClaim.from_payload(payload)
            if claim is None:
                continue
            source_paper = claim_payload_source_paper(payload, claim_file)
            if source_paper:
                claim = replace(claim, source_paper=source_paper)
            claims.append(claim.with_source_condition())
    return claims


def _collect_measurement_claims(
    claim_files: Sequence[ClaimFileInput],
) -> dict[tuple[str, str], list[ConflictClaim]]:
    by_key: dict[tuple[str, str], list[ConflictClaim]] = defaultdict(list)
    for claim in _iter_conflict_claims(claim_files):
        if claim.claim_type == "measurement" and claim.target_concept_id and claim.measure:
            by_key[(claim.target_concept_id, claim.measure)].append(claim)
    return dict(by_key)


def _collect_parameter_claims(
    claim_files: Sequence[ClaimFileInput],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in _iter_conflict_claims(claim_files):
        if claim.claim_type == "parameter" and claim.concept_id:
            by_concept[claim.concept_id].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claim_files: Sequence[ClaimFileInput],
) -> dict[tuple[str, tuple[str, ...]], list[ConflictClaim]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[ConflictClaim]] = defaultdict(list)
    for claim in _iter_conflict_claims(claim_files):
        if claim.claim_type != "equation":
            continue
        signature = equation_signature(claim)
        if signature is None:
            continue
        by_signature[signature].append(claim)
    return dict(by_signature)


def _collect_algorithm_claims(
    claim_files: Sequence[ClaimFileInput],
) -> dict[str, list[ConflictClaim]]:
    by_concept: dict[str, list[ConflictClaim]] = defaultdict(list)
    for claim in _iter_conflict_claims(claim_files):
        if claim.claim_type != "algorithm":
            continue
        if claim.concept_id is not None:
            by_concept[claim.concept_id].append(claim)
            continue
        first_concept = next((variable.concept_id for variable in claim.variables), None)
        if first_concept is not None:
            by_concept[first_concept].append(claim)
    return dict(by_concept)
