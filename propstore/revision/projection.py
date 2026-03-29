from __future__ import annotations

from propstore.world.labelled import SupportQuality

from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope


def project_belief_base(bound, *, include_assumptions: bool = True) -> BeliefBase:
    """Project a scoped BoundWorld into a minimal revision-facing belief base.

    V1 includes only claims with exact ATMS-reconstructible support.
    """
    atoms: list[BeliefAtom] = []
    for claim in sorted(bound.active_claims(None), key=lambda row: str(row.get("id") or "")):
        claim_id = claim.get("id")
        if not claim_id:
            continue
        label, quality = bound.claim_support(claim)
        if quality is not SupportQuality.EXACT:
            continue
        atoms.append(
            BeliefAtom(
                atom_id=f"claim:{claim_id}",
                kind="claim",
                payload=dict(claim),
                label=label,
            )
        )

    scope = RevisionScope(
        bindings=dict(bound._environment.bindings),
        context_id=bound._environment.context_id,
    )
    assumptions = (
        tuple(bound._environment.assumptions)
        if include_assumptions
        else ()
    )
    return BeliefBase(
        scope=scope,
        atoms=tuple(atoms),
        assumptions=assumptions,
    )
