"""Claim grouping helpers for conflict detection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from propstore.equation_comparison import equation_signature
from propstore.loaded import LoadedEntry


def _collect_measurement_claims(
    claim_files: Sequence[LoadedEntry],
) -> dict[tuple[str, str], list[dict]]:
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if (
                claim.get("type") == "measurement"
                and claim.get("target_concept")
                and claim.get("measure")
            ):
                key = (claim["target_concept"], claim["measure"])
                by_key[key].append(claim)
    return dict(by_key)


def _collect_parameter_claims(
    claim_files: Sequence[LoadedEntry],
) -> dict[str, list[dict]]:
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") == "parameter" and claim.get("concept"):
                by_concept[claim["concept"]].append(claim)
    return dict(by_concept)


def _collect_equation_claims(
    claim_files: Sequence[LoadedEntry],
) -> dict[tuple[str, tuple[str, ...]], list[dict]]:
    by_signature: dict[tuple[str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") != "equation":
                continue
            signature = equation_signature(claim)
            if signature is None:
                continue
            by_signature[signature].append(claim)
    return dict(by_signature)


def _collect_algorithm_claims(
    claim_files: Sequence[LoadedEntry],
) -> dict[str, list[dict]]:
    by_concept: dict[str, list[dict]] = defaultdict(list)
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            if claim.get("type") != "algorithm":
                continue
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
