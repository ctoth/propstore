from __future__ import annotations

from propstore.core.active_claims import ActiveClaim
from propstore.core.id_types import AssumptionId, to_claim_id
from propstore.core.labels import SupportQuality

from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope


def _claim_atom_id(claim: ActiveClaim) -> str | None:
    logical_id = claim.primary_logical_id
    if isinstance(logical_id, str) and logical_id:
        return f"claim:{logical_id.split(':', 1)[1] if ':' in logical_id else logical_id}"

    for logical_id_entry in claim.logical_ids:
        if logical_id_entry.value:
            return f"claim:{logical_id_entry.value}"

    return f"claim:{claim.claim_id}"


def _claim_support_lookup_id(claim: ActiveClaim) -> str:
    return to_claim_id(claim.claim_id)


def project_belief_base(bound, *, include_assumptions: bool = True) -> BeliefBase:
    """Project a scoped BoundWorld into a minimal revision-facing belief base.

    V1 includes only claims with exact ATMS-reconstructible support.
    """
    atoms: list[BeliefAtom] = []
    supporting_assumption_ids: set[AssumptionId] = set()
    support_sets: dict[str, tuple[tuple[AssumptionId, ...], ...]] = {}
    essential_support: dict[str, tuple[AssumptionId, ...]] = {}
    for claim in sorted(bound.active_claims(None), key=lambda row: str(row.claim_id)):
        claim_id = str(claim.claim_id)
        label, quality = bound.claim_support(claim)
        if quality is not SupportQuality.EXACT:
            continue
        atom_id = _claim_atom_id(claim)
        if atom_id is None:
            continue
        if label is not None:
            for environment in label.environments:
                supporting_assumption_ids.update(environment.assumption_ids)
            support_sets[atom_id] = tuple(
                environment.assumption_ids
                for environment in label.environments
            )
        else:
            support_sets[atom_id] = ()
        support_lookup_id = _claim_support_lookup_id(claim)
        if support_lookup_id is None:
            continue
        essential = bound.claim_essential_support(support_lookup_id)
        essential_support[atom_id] = (
            essential.assumption_ids
            if essential is not None
            else ()
        )
        atoms.append(
            BeliefAtom(
                atom_id=atom_id,
                kind="claim",
                payload=claim.to_dict(),
                label=label,
            )
        )

    scope = RevisionScope(
        bindings=dict(bound._environment.bindings),
        context_id=bound._environment.context_id,
    )
    assumptions = (
        tuple(
            assumption
            for assumption in bound._environment.assumptions
            if assumption.assumption_id in supporting_assumption_ids
        )
        if include_assumptions
        else ()
    )
    return BeliefBase(
        scope=scope,
        atoms=tuple(atoms),
        assumptions=assumptions,
        support_sets=support_sets,
        essential_support=essential_support,
    )
