"""MaxSMT-based conflict resolution.

Uses z3.Optimize with soft constraints to find the maximally consistent
subset of claims, weighted by claim_strength.
"""
from __future__ import annotations

import z3


def resolve_conflicts(
    conflicts: list[tuple[str, str]],
    claim_strengths: dict[str, float],
) -> frozenset[str]:
    """Find maximally consistent claim subset.

    Args:
        conflicts: pairs of claim IDs that conflict
        claim_strengths: mapping from claim ID to strength (higher = more reliable)

    Returns:
        frozenset of claim IDs to keep
    """
    if not claim_strengths:
        return frozenset()

    optimizer = z3.Optimize()

    # One Boolean variable per claim
    keep_vars = {cid: z3.Bool(f"keep_{cid}") for cid in claim_strengths}

    # Hard constraints: conflicting claims can't both be kept
    for a, b in conflicts:
        if a in keep_vars and b in keep_vars:
            optimizer.add(z3.Not(z3.And(keep_vars[a], keep_vars[b])))

    # Soft constraints: prefer to keep each claim, weighted by strength
    for cid, strength in claim_strengths.items():
        optimizer.add_soft(keep_vars[cid], weight=str(strength))

    if optimizer.check() == z3.sat:
        model = optimizer.model()
        return frozenset(
            cid for cid, var in keep_vars.items()
            if model.evaluate(var, model_completion=True)
        )

    return frozenset()  # Should never happen with soft constraints
