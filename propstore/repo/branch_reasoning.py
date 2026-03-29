"""Branch-aware reasoning: bridges merge classification to ATMS/ASPIC+.

Creates branch assumptions for ATMS, generates nogoods from merge conflicts,
and synthesizes cross-branch stances for ASPIC+ attack generation.

Per Mason & Johnson 1989: each agent's belief space maps to an assumption
set in the ATMS. Git branches are agents — their assumptions participate
in label computation identically to binding/context assumptions.

Per Coste-Marquis et al. 2007: conflicts between sources become attacks
in the merged argumentation framework. Only CONFLICT items produce stances;
PHI_NODE (ignorance) is NOT attack (Definition 9).
"""
from __future__ import annotations

from propstore.core.labels import AssumptionRef, EnvironmentKey, NogoodSet
from propstore.repo.merge_classifier import MergeClassification, MergeItem


def make_branch_assumption(branch_name: str) -> AssumptionRef:
    """Create an AssumptionRef for a branch.

    Per Mason & Johnson 1989: each agent's belief space maps to
    an assumption set in the ATMS. A git branch is an agent — its
    assumption ref carries kind='branch' and identifies the branch
    as source.

    Branch names are sanitized for use as assumption_id (slashes and
    hyphens become underscores) but the original name is preserved
    in the source field.
    """
    safe_id = branch_name.replace("/", "_").replace("-", "_")
    return AssumptionRef(
        assumption_id=f"branch:{safe_id}",
        kind="branch",
        source=branch_name,
        cel=f"branch == '{branch_name}'",
    )


def branch_nogoods_from_merge(items: list[MergeItem]) -> NogoodSet:
    """Generate ATMS nogoods from merge classification.

    Per Mason & Johnson 1989, claim 2: contradictions detected across
    agents become nogoods that limit context explosion.

    Only CONFLICT items generate nogoods. PHI_NODE, COMPATIBLE, etc. do not.
    Each CONFLICT creates a nogood containing both branch assumption IDs,
    meaning you cannot simultaneously accept both branches' values for
    that claim.
    """
    nogood_envs: list[EnvironmentKey] = []
    for item in items:
        if item.classification == MergeClassification.CONFLICT:
            left_ref = make_branch_assumption(item.left_branch)
            right_ref = make_branch_assumption(item.right_branch)
            nogood_envs.append(
                EnvironmentKey(
                    tuple(sorted([left_ref.assumption_id, right_ref.assumption_id]))
                )
            )
    return NogoodSet(tuple(nogood_envs))


def inject_branch_stances(items: list[MergeItem]) -> list[dict[str, str]]:
    """Synthesize cross-branch stances for ASPIC+ attack generation.

    Per Coste-Marquis et al. 2007: conflicts between sources become
    attacks in the merged AF. Only CONFLICT items produce stances
    (symmetric contradicts). PHI_NODE items produce no stances —
    per PAF Definition 9, ignorance is NOT attack.

    Returns stance dicts compatible with aspic_bridge.stances_to_contrariness().
    Each CONFLICT produces two symmetric stances (both attack directions).
    """
    stances: list[dict[str, str]] = []
    for item in items:
        if item.classification == MergeClassification.CONFLICT:
            # Extract claim IDs from the value dicts if available,
            # otherwise fall back to the merge item's claim_id
            left_claim_id = (
                item.left_value.get("id", item.claim_id)
                if isinstance(item.left_value, dict)
                else item.claim_id
            )
            right_claim_id = (
                item.right_value.get("id", item.claim_id)
                if isinstance(item.right_value, dict)
                else item.claim_id
            )
            # Symmetric contradicts — both directions
            stances.append({
                "claim_id": left_claim_id,
                "target_claim_id": right_claim_id,
                "stance_type": "contradicts",
            })
            stances.append({
                "claim_id": right_claim_id,
                "target_claim_id": left_claim_id,
                "stance_type": "contradicts",
            })
    return stances
