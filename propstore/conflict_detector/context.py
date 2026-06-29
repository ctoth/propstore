"""Shared context-aware conflict classification helpers.

Two claims in different ``ist(c, p)`` contexts only conflict if one context's
proposition lifts into the other. A pair with no authored lifting bridge is a
:attr:`ConflictClass.CONTEXT_PHI_NODE` (rival, context-separated readings kept
side by side), decided through the context-lifting algebra — never collapsed.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from condition_ir import CelExpr

from propstore.families.contexts import LiftingDecisionStatus

from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingDecision, LiftingSystem


def _has_lift(decisions: Sequence[LiftingDecision]) -> bool:
    return any(
        decision.status is LiftingDecisionStatus.LIFTED for decision in decisions
    )


def _classify_pair_context(
    context_a: str | None,
    context_b: str | None,
    lifting_system: LiftingSystem | None,
    *,
    claim_a_id: str | None = None,
    claim_b_id: str | None = None,
) -> ConflictClass | None:
    """Return ``CONTEXT_PHI_NODE`` if the contexts make the pair non-conflicting."""

    if lifting_system is None:
        return None
    if context_a is None or context_b is None:
        return None
    if context_a == context_b:
        return None
    if claim_a_id is not None and _has_lift(
        lifting_system.lift_decisions_between(context_a, context_b, claim_a_id)
    ):
        return None
    if claim_b_id is not None and _has_lift(
        lifting_system.lift_decisions_between(context_b, context_a, claim_b_id)
    ):
        return None
    return ConflictClass.CONTEXT_PHI_NODE


def claim_context(claim: ConflictClaim) -> str | None:
    return claim.context_id


def append_context_classified_record(
    records: list[ConflictRecord],
    *,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    conditions_a: list[CelExpr],
    conditions_b: list[CelExpr],
    value_a: str,
    value_b: str,
    context_a: str | None,
    context_b: str | None,
    lifting_system: LiftingSystem | None,
    derivation_chain: str | None = None,
) -> bool:
    context_class = _classify_pair_context(
        context_a,
        context_b,
        lifting_system,
        claim_a_id=claim_a_id,
        claim_b_id=claim_b_id,
    )
    if context_class is None:
        return False
    records.append(
        ConflictRecord(
            concept_id=concept_id,
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            warning_class=context_class,
            conditions_a=conditions_a,
            conditions_b=conditions_b,
            value_a=value_a,
            value_b=value_b,
            derivation_chain=derivation_chain,
        )
    )
    return True
