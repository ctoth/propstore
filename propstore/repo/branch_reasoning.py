"""Branch-aware reasoning over the formal repository merge object."""
from __future__ import annotations

from propstore.core.labels import AssumptionRef, EnvironmentKey, NogoodSet
from propstore.repo.merge_classifier import RepoMergeFramework


def make_branch_assumption(branch_name: str) -> AssumptionRef:
    safe_id = branch_name.replace("/", "_").replace("-", "_")
    return AssumptionRef(
        assumption_id=f"branch:{safe_id}",
        kind="branch",
        source=branch_name,
        cel=f"branch == '{branch_name}'",
    )


def branch_nogoods_from_merge(merge: RepoMergeFramework) -> NogoodSet:
    """Generate branch nogoods from mutually attacking merge alternatives."""
    argument_index = merge.argument_index()
    nogood_envs: set[EnvironmentKey] = set()

    for attacker_id, target_id in merge.framework.attacks:
        if (target_id, attacker_id) not in merge.framework.attacks:
            continue
        attacker = argument_index[attacker_id]
        target = argument_index[target_id]
        if len(attacker.branch_origins) != 1 or len(target.branch_origins) != 1:
            continue
        left_ref = make_branch_assumption(attacker.branch_origins[0])
        right_ref = make_branch_assumption(target.branch_origins[0])
        nogood_envs.add(
            EnvironmentKey(
                tuple(sorted([left_ref.assumption_id, right_ref.assumption_id]))
            )
        )

    return NogoodSet(tuple(sorted(nogood_envs)))


def inject_branch_stances(merge: RepoMergeFramework) -> list[dict[str, str]]:
    """Expose merge attacks as contradiction stances for current consumers."""
    stances: list[dict[str, str]] = []
    for attacker_id, target_id in sorted(merge.framework.attacks):
        stances.append(
            {
                "claim_id": attacker_id,
                "target_claim_id": target_id,
                "stance_type": "contradicts",
            }
        )
    return stances
