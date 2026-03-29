"""Semantic merge classification at claim granularity.

Three-way diff between two branches using their merge-base as the common
ancestor. Each claim is classified into one of six categories.

Literature grounding:
- Coste-Marquis et al. 2007, Def 9: PAF three-valued attack relation
  maps to CONFLICT (attack), COMPATIBLE (non-attack), PHI_NODE (ignorance).
- Konieczny & Pino Perez 2002, IC3: classification is syntax-independent
  (keyed by claim ID, not filename or YAML order).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from propstore.repo.branch import branch_head, merge_base

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


class MergeClassification(Enum):
    """Six-valued merge classification per semantic-merge-spec Phase 2."""
    IDENTICAL = "identical"
    COMPATIBLE = "compatible"
    PHI_NODE = "phi_node"
    CONFLICT = "conflict"
    NOVEL_LEFT = "novel_left"
    NOVEL_RIGHT = "novel_right"


@dataclass(frozen=True)
class MergeItem:
    """A single claim's merge classification with three-way values.

    Carries the claim identity, concept identity, values from all three
    versions (base, left, right), and branch provenance.
    """
    classification: MergeClassification
    claim_id: str
    concept_id: str
    left_value: Any | None
    right_value: Any | None
    base_value: Any | None
    left_branch: str
    right_branch: str


def _extract_concept(claim: dict) -> str:
    """Extract the primary concept ID from a claim dict.

    Parameter/measurement types use ``concept``; observation types use
    the first entry in ``concepts``.
    """
    c = claim.get("concept")
    if c:
        return c
    concepts = claim.get("concepts", [])
    if concepts:
        return concepts[0]
    return ""


def _claim_semantic_key(claim: dict) -> dict:
    """Extract the semantically meaningful fields from a claim for comparison.

    Excludes provenance metadata and ordering artifacts so that IC3
    (syntax independence) is satisfied.
    """
    # Include all fields except provenance — provenance doesn't affect semantics
    skip = {"provenance"}
    return {k: v for k, v in claim.items() if k not in skip}


def _claims_equal(a: dict, b: dict) -> bool:
    """Compare two claims by their semantic content (IC3 compliance)."""
    return _claim_semantic_key(a) == _claim_semantic_key(b)


def _index_claims(claim_files) -> dict[str, dict]:
    """Build a dict mapping claim ID -> claim dict from LoadedClaimFile list."""
    index: dict[str, dict] = {}
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            cid = claim.get("id")
            if cid:
                index[cid] = claim
    return index


def _classify_modified_both(
    left_claim: dict,
    right_claim: dict,
    left_branch: str,
    right_branch: str,
) -> MergeClassification:
    """Classify a claim modified on both branches.

    Uses the conflict detector to distinguish PHI_NODE (mutually exclusive
    conditions) from CONFLICT (genuine overlap).
    """
    from propstore.validate_claims import LoadedClaimFile
    from propstore.conflict_detector import detect_conflicts, ConflictClass

    # Build synthetic LoadedClaimFiles for the two versions
    left_file = LoadedClaimFile(
        filename="_left",
        filepath=None,
        data={
            "source": {"paper": "merge_left", "extraction_model": "merge", "extraction_date": "2026-01-01"},
            "claims": [left_claim],
        },
    )
    right_file = LoadedClaimFile(
        filename="_right",
        filepath=None,
        data={
            "source": {"paper": "merge_right", "extraction_model": "merge", "extraction_date": "2026-01-01"},
            "claims": [right_claim],
        },
    )

    records = detect_conflicts([left_file, right_file], concept_registry={})

    # If any record is a genuine CONFLICT or OVERLAP, classify as CONFLICT
    for r in records:
        if r.warning_class in (ConflictClass.CONFLICT, ConflictClass.OVERLAP, ConflictClass.PARAM_CONFLICT):
            return MergeClassification.CONFLICT

    # If we got PHI_NODE or CONTEXT_PHI_NODE, that's a phi node
    for r in records:
        if r.warning_class in (ConflictClass.PHI_NODE, ConflictClass.CONTEXT_PHI_NODE):
            return MergeClassification.PHI_NODE

    # If no conflict records at all but claims differ, the conflict detector
    # may not cover this claim type (e.g. observations). Claims that differ
    # but don't trigger the conflict detector are conflicts by default —
    # the claims are semantically different with no condition-based excuse.
    # However, if concepts differ, they're compatible (different topics).
    left_concept = _extract_concept(left_claim)
    right_concept = _extract_concept(right_claim)
    if left_concept != right_concept:
        return MergeClassification.COMPATIBLE

    return MergeClassification.CONFLICT


def classify_merge(
    kr: KnowledgeRepo,
    branch_a: str,
    branch_b: str,
) -> list[MergeItem]:
    """Three-way diff at claim granularity.

    Per Coste-Marquis 2007 Definition 9: classification maps to
    PAF three-valued relation (attack/non-attack/ignorance).

    Algorithm:
    1. Find merge-base
    2. Load claims from all three commits via GitTreeReader
    3. Index claims by ID
    4. Classify each claim in the union
    """
    from propstore.tree_reader import GitTreeReader
    from propstore.validate_claims import load_claim_files

    # Step 1: find merge base
    base_sha = merge_base(kr, branch_a, branch_b)
    left_sha = branch_head(kr, branch_a)
    right_sha = branch_head(kr, branch_b)

    # Step 2: load claims from all three commits
    base_reader = GitTreeReader(kr, commit=base_sha)
    left_reader = GitTreeReader(kr, commit=left_sha)
    right_reader = GitTreeReader(kr, commit=right_sha)

    base_claims_files = load_claim_files(None, reader=base_reader)
    left_claims_files = load_claim_files(None, reader=left_reader)
    right_claims_files = load_claim_files(None, reader=right_reader)

    # Step 3: index by claim ID
    base_idx = _index_claims(base_claims_files)
    left_idx = _index_claims(left_claims_files)
    right_idx = _index_claims(right_claims_files)

    # Step 4: classify each claim ID in the union
    all_ids = set(base_idx) | set(left_idx) | set(right_idx)
    items: list[MergeItem] = []

    # Determine whether each branch diverged from base (has any changes).
    # When both branches diverged, new claims on one side are COMPATIBLE
    # (both branches contributed). When only one branch diverged, new
    # claims are NOVEL_LEFT or NOVEL_RIGHT.
    left_diverged = left_idx != base_idx
    right_diverged = right_idx != base_idx
    both_diverged = left_diverged and right_diverged

    for cid in sorted(all_ids):
        in_base = cid in base_idx
        in_left = cid in left_idx
        in_right = cid in right_idx

        base_claim = base_idx.get(cid)
        left_claim = left_idx.get(cid)
        right_claim = right_idx.get(cid)

        # Determine concept from whichever version exists
        concept = ""
        for c in (left_claim, right_claim, base_claim):
            if c is not None:
                concept = _extract_concept(c)
                break

        # Classification logic
        if in_left and in_right and in_base:
            # All three present
            left_eq_base = _claims_equal(left_claim, base_claim)
            right_eq_base = _claims_equal(right_claim, base_claim)
            left_eq_right = _claims_equal(left_claim, right_claim)

            if left_eq_base and right_eq_base:
                classification = MergeClassification.IDENTICAL
            elif left_eq_base and not right_eq_base:
                # Only right modified — compatible one-sided change
                classification = MergeClassification.COMPATIBLE
            elif right_eq_base and not left_eq_base:
                # Only left modified — compatible one-sided change
                classification = MergeClassification.COMPATIBLE
            elif left_eq_right:
                # Both modified identically — identical result
                classification = MergeClassification.IDENTICAL
            else:
                # Both modified differently — check conflict detector
                classification = _classify_modified_both(
                    left_claim, right_claim, branch_a, branch_b
                )
        elif in_left and in_right and not in_base:
            # Added on both sides (not in base)
            if _claims_equal(left_claim, right_claim):
                classification = MergeClassification.IDENTICAL
            else:
                classification = _classify_modified_both(
                    left_claim, right_claim, branch_a, branch_b
                )
        elif in_left and not in_right and not in_base:
            # Added only on left
            classification = (
                MergeClassification.COMPATIBLE if both_diverged
                else MergeClassification.NOVEL_LEFT
            )
        elif not in_left and in_right and not in_base:
            # Added only on right
            classification = (
                MergeClassification.COMPATIBLE if both_diverged
                else MergeClassification.NOVEL_RIGHT
            )
        elif in_left and not in_right and in_base:
            # Deleted on right, present on left
            left_eq_base = _claims_equal(left_claim, base_claim)
            if left_eq_base:
                # Right deleted, left unchanged — novel deletion
                classification = MergeClassification.NOVEL_RIGHT
            else:
                # Left modified, right deleted — conflict
                classification = MergeClassification.CONFLICT
        elif not in_left and in_right and in_base:
            # Deleted on left, present on right
            right_eq_base = _claims_equal(right_claim, base_claim)
            if right_eq_base:
                # Left deleted, right unchanged — novel deletion
                classification = MergeClassification.NOVEL_LEFT
            else:
                # Right modified, left deleted — conflict
                classification = MergeClassification.CONFLICT
        elif not in_left and not in_right and in_base:
            # Deleted on both sides
            classification = MergeClassification.IDENTICAL
        elif in_left and in_right:
            # Both present, base ambiguous — treat as compatible
            classification = MergeClassification.COMPATIBLE
        else:
            # Shouldn't happen (claim in union but not in any set)
            continue

        items.append(MergeItem(
            classification=classification,
            claim_id=cid,
            concept_id=concept,
            left_value=left_claim,
            right_value=right_claim,
            base_value=base_claim,
            left_branch=branch_a,
            right_branch=branch_b,
        ))

    return items
