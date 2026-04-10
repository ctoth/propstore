"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from propstore.claim_documents import LoadedClaimFile
from propstore.equation_comparison import equation_signature


def _ensure_claim_id_alias(claim: dict) -> dict:
    """Ensure downstream conflict detectors see a stable claim ``id`` key."""
    if "id" in claim:
        return claim
    artifact_id = claim.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        aliased = dict(claim)
        aliased["id"] = artifact_id
        return aliased
    return claim


def _inject_source_condition(claim: dict, cf: LoadedClaimFile) -> dict:
    """Add a synthetic ``source == '<paper>'`` condition to a claim.

    Every claim is inherently parameterized by its source paper.  Without
    this, claims from different papers that happen to share a concept
    (e.g. sample_size) are flagged as OVERLAP even though they describe
    different studies.  Injecting the source as a condition lets Z3
    recognize them as disjoint.
    """
    source_paper = cf.source_paper or cf.filename
    if not source_paper:
        return claim
    source_cond = f"source == '{source_paper}'"
    existing = claim.get("conditions") or []
    if source_cond in existing:
        return claim
    enriched = dict(claim)
    enriched["conditions"] = [*existing, source_cond]
    return enriched


def _collect_measurement_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[tuple[str, str], list[dict]]:
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim_document in cf.claims:
            claim = claim_document.to_payload()
            if (
                claim.get("type") == "measurement"
                and claim.get("target_concept")
                and claim.get("measure")
            ):
                claim = _ensure_claim_id_alias(claim)
                claim = _inject_source_condition(claim, cf)
                key = (claim["target_concept"], claim["measure"])
                by_key[key].append(claim)
    return dict(by_key)


def _collect_parameter_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[str, list[dict]]:
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim_document in cf.claims:
            claim = claim_document.to_payload()
            if claim.get("type") == "parameter" and claim.get("concept"):
                claim = _ensure_claim_id_alias(claim)
                claim = _inject_source_condition(claim, cf)
                by_concept[claim["concept"]].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[tuple[str, tuple[str, ...]], list[dict]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim_document in cf.claims:
            claim = claim_document.to_payload()
            if claim.get("type") != "equation":
                continue
            claim = _ensure_claim_id_alias(claim)
            claim = _inject_source_condition(claim, cf)
            signature = equation_signature(claim)
            if signature is None:
                continue
            by_signature[signature].append(claim)
    return dict(by_signature)


def _collect_algorithm_claims(
    claim_files: Sequence[LoadedClaimFile],
) -> dict[str, list[dict]]:
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim_document in cf.claims:
            claim = claim_document.to_payload()
            if claim.get("type") != "algorithm":
                continue
            claim = _ensure_claim_id_alias(claim)
            claim = _inject_source_condition(claim, cf)
            declared_concept = claim.get("concept")
            if isinstance(declared_concept, str) and declared_concept:
                by_concept[declared_concept].append(claim)
                continue
            variables = claim.get("variables")
            if not isinstance(variables, list) or not variables:
                continue
            first_concept = None
            for var in variables:
                if isinstance(var, dict):
                    concept = var.get("concept")
                    if isinstance(concept, str) and concept:
                        first_concept = concept
                        break
            if first_concept is not None:
                by_concept[first_concept].append(claim)
    return dict(by_concept)
