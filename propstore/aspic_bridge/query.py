"""Goal-directed querying on top of the shared ASPIC bridge pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from argumentation.aspic import (
    Argument,
    Attack,
    ContrarinessFn,
    GroundAtom,
    Literal,
    build_arguments_for,
    conc,
    compute_attacks,
    compute_defeats,
)
from propstore.core.active_claims import ActiveClaimInput
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import LiteralKey, claim_key, ground_key
from propstore.core.row_types import StanceRowInput
from propstore.grounding.bundle import GroundedRulesBundle

from .build import _filter_preference_sensitive_stance_attacks, compile_bridge_context
from .translate import preference_sensitive_stance_pairs


@dataclass(frozen=True)
class ClaimQueryResult:
    """Focused argumentation result for one goal literal."""

    claim_id: str | GroundAtom | LiteralKey
    goal: Literal
    arguments_for: frozenset[Argument]
    arguments_against: frozenset[Argument]
    attacks: frozenset[Attack]
    defeats: frozenset[tuple[Argument, Argument]]


def _query_goal_key(goal_ref: str | GroundAtom | LiteralKey) -> LiteralKey:
    """Convert a query boundary input to the internal typed literal-key surface."""

    if isinstance(goal_ref, str):
        return claim_key(goal_ref)
    if isinstance(goal_ref, GroundAtom):
        return ground_key(goal_ref, False)
    return goal_ref


def _goal_contraries(
    literal: Literal,
    contrariness: ContrarinessFn,
    language: frozenset[Literal],
) -> frozenset[Literal]:
    """Return every language literal that conflicts with ``literal``."""

    return frozenset(
        other
        for other in language
        if contrariness.is_contradictory(other, literal)
        or contrariness.is_contrary(other, literal)
    )


def query_claim(
    claim_id: str | GroundAtom | LiteralKey,
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceRowInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
    max_depth: int = 10,
) -> ClaimQueryResult:
    """Build only the arguments relevant to one goal and its attackers."""

    compiled = compile_bridge_context(
        active_claims,
        justifications,
        stances,
        bundle=bundle,
        comparison=comparison,
        link=link,
    )

    goal_key = _query_goal_key(claim_id)
    if goal_key not in compiled.literals:
        raise KeyError(claim_id)
    goal = compiled.literals[goal_key]

    arguments = build_arguments_for(
        compiled.system,
        compiled.kb,
        goal,
        include_attackers=True,
        max_depth=max_depth,
    )
    attacks = compute_attacks(arguments, compiled.system)
    attacks = _filter_preference_sensitive_stance_attacks(
        attacks,
        preference_sensitive_stance_pairs(stances, compiled.literals),
    )
    defeat_attacks = compute_defeats(
        attacks,
        arguments,
        compiled.system,
        compiled.kb,
        compiled.pref,
    )
    defeat_pairs = frozenset((attack.attacker, attack.target) for attack in defeat_attacks)

    arguments_for = frozenset(argument for argument in arguments if conc(argument) == goal)
    against_literals = _goal_contraries(
        goal,
        compiled.system.contrariness,
        compiled.system.language,
    )
    arguments_against = frozenset(
        argument for argument in arguments if conc(argument) in against_literals
    )

    return ClaimQueryResult(
        claim_id=claim_id,
        goal=goal,
        arguments_for=arguments_for,
        arguments_against=arguments_against,
        attacks=attacks,
        defeats=defeat_pairs,
    )


__all__ = [
    "ClaimQueryResult",
    "query_claim",
]
