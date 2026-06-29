"""Goal-directed querying on top of the shared ASPIC+ bridge pipeline.

:func:`query_claim` builds only the arguments relevant to one goal literal and
its attackers (``build_arguments_for``), then reports the arguments *for* the
goal, the arguments *against* it (concluding a contrary, or attacking a
sub-argument of the goal), and the surviving attacks/defeats.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from argumentation.structured.aspic.aspic import (
    Argument,
    Attack,
    GroundAtom,
    Literal,
    build_arguments_for,
    compute_attacks,
    compute_defeats,
    conc,
    contraries_of,
    sub,
)

from propstore.aspic_bridge.build import (
    compile_bridge_context,
    filter_preference_sensitive_stance_attacks,
    filter_preference_sensitive_stance_defeats,
)
from propstore.aspic_bridge.translate import StanceInput, preference_sensitive_stance_pairs
from propstore.core.active_claims import ActiveClaimInput
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import IstLiteralKey, LiteralKey, claim_key, ground_key
from propstore.grounding.bundle import GroundedRulesBundle


@dataclass(frozen=True)
class ClaimQueryResult:
    """Focused argumentation result for one goal literal."""

    claim_id: str | GroundAtom | LiteralKey
    goal: Literal
    arguments_for: frozenset[Argument]
    arguments_against: frozenset[Argument]
    attacks: frozenset[Attack]
    defeats: frozenset[tuple[Argument, Argument]]


def _query_goal_key(
    goal_ref: str | GroundAtom | LiteralKey,
    literals: Mapping[LiteralKey, Literal],
) -> LiteralKey:
    if isinstance(goal_ref, str):
        matches = [
            key
            for key in literals
            if isinstance(key, IstLiteralKey) and str(key.proposition_id) == goal_ref
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            contexts = ", ".join(sorted(str(key.context_id) for key in matches))
            raise ValueError(f"claim {goal_ref!r} is ambiguous across contexts: {contexts}")
        return claim_key(goal_ref)
    if isinstance(goal_ref, GroundAtom):
        return ground_key(goal_ref, False)
    return goal_ref


def query_claim(
    claim_id: str | GroundAtom | LiteralKey,
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
    max_depth: int = 10,
) -> ClaimQueryResult:
    """Build only the arguments relevant to one goal and its attackers."""

    compiled = compile_bridge_context(
        active_claims, justifications, stances, bundle=bundle, comparison=comparison, link=link
    )

    goal_key = _query_goal_key(claim_id, compiled.literals)
    if goal_key not in compiled.literals:
        raise KeyError(claim_id)
    goal = compiled.literals[goal_key]

    arguments = build_arguments_for(
        compiled.system, compiled.kb, goal, include_attackers=True, max_depth=max_depth
    )
    arguments = frozenset(
        sub_argument for argument in arguments for sub_argument in sub(argument)
    )
    attacks = compute_attacks(arguments, compiled.system)
    directed_pairs = preference_sensitive_stance_pairs(stances, compiled.literals)
    attacks = filter_preference_sensitive_stance_attacks(attacks, directed_pairs)
    defeat_attacks = compute_defeats(attacks, arguments, compiled.system, compiled.kb, compiled.pref)
    defeat_attacks = filter_preference_sensitive_stance_defeats(
        defeat_attacks,
        arguments=arguments,
        system=compiled.system,
        kb=compiled.kb,
        pref=compiled.pref,
        directed_pairs=directed_pairs,
    )
    defeat_pairs = frozenset((attack.attacker, attack.target) for attack in defeat_attacks)

    arguments_for = frozenset(argument for argument in arguments if conc(argument) == goal)
    against_literals = contraries_of(goal, compiled.system.contrariness, compiled.system.language)
    conclusion_attackers = {
        argument for argument in arguments if conc(argument) in against_literals
    }
    goal_subarguments = frozenset(
        sub_argument for argument in arguments_for for sub_argument in sub(argument)
    )
    attacked_goal_arguments = {
        attack.attacker for attack in attacks if attack.target_sub in goal_subarguments
    }
    arguments_against = frozenset(conclusion_attackers | attacked_goal_arguments)

    return ClaimQueryResult(
        claim_id=claim_id,
        goal=goal,
        arguments_for=arguments_for,
        arguments_against=arguments_against,
        attacks=attacks,
        defeats=defeat_pairs,
    )


__all__ = ["ClaimQueryResult", "query_claim"]
