"""Claim-graph to ASPIC+ translation stages T1-T5."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from argumentation.aspic import (
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    Rule,
)
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import ClaimLiteralKey, LiteralKey, claim_key
from propstore.core.row_types import StanceRow, StanceRowInput, coerce_stance_row
from argumentation.preference import strict_partial_order_closure

from propstore.preference import MetadataStrengthVector, metadata_strength_vector


def _claim_attr(claim: ActiveClaim, key: str) -> Any:
    return getattr(claim, key, claim.attributes.get(key))


def _coerce_bridge_stance_row(row: StanceRowInput) -> StanceRow:
    """Coerce a bridge stance row through the shared typed stance boundary."""

    return coerce_stance_row(row)


def claims_to_literals(active_claims: Sequence[ActiveClaimInput]) -> dict[LiteralKey, Literal]:
    """Map each claim to a positive ASPIC+ literal."""

    normalized_claims = coerce_active_claims(active_claims)
    return {
        claim_key(str(claim.claim_id)): Literal(
            atom=GroundAtom(str(claim.claim_id)),
            negated=False,
        )
        for claim in normalized_claims
    }


def justifications_to_rules(
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> tuple[frozenset[Rule], frozenset[Rule]]:
    """Translate stored justifications into ASPIC+ strict and defeasible rules."""

    strict: list[Rule] = []
    defeasible: list[Rule] = []

    for justification in justifications:
        if justification.rule_kind == "reported_claim":
            continue
        if not justification.premise_claim_ids:
            raise ValueError(
                "empty-premise justification "
                f"{justification.justification_id!r} must be rejected or represented explicitly"
            )

        conclusion_key = claim_key(justification.conclusion_claim_id)
        premise_keys = tuple(claim_key(pid) for pid in justification.premise_claim_ids)
        if conclusion_key not in literals:
            continue
        unknown_premises = [
            premise_id
            for premise_id, premise_key in zip(justification.premise_claim_ids, premise_keys)
            if premise_key not in literals
        ]
        if unknown_premises:
            missing = ", ".join(repr(premise_id) for premise_id in unknown_premises)
            raise ValueError(
                "unknown premise in justification "
                f"{justification.justification_id!r}: {missing}"
            )

        antecedents = tuple(literals[pid] for pid in premise_keys)
        consequent = literals[conclusion_key]
        if justification.rule_strength == "strict":
            strict.append(
                Rule(
                    antecedents=antecedents,
                    consequent=consequent,
                    kind="strict",
                    name=None,
                )
            )
        else:
            defeasible.append(
                Rule(
                    antecedents=antecedents,
                    consequent=consequent,
                    kind="defeasible",
                    name=justification.justification_id,
                )
            )

    return frozenset(strict), frozenset(defeasible)


def stances_to_contrariness(
    stances: Sequence[StanceRowInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
) -> ContrarinessFn:
    """Build the ASPIC+ contrariness function from attack stances."""

    contradictory_pairs: set[tuple[Literal, Literal]] = {
        (literal, literal.contrary) for literal in literals.values()
    }
    for rule in defeasible_rules:
        if rule.name is None:
            continue
        rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
        contradictory_pairs.add((rule_lit, rule_lit.contrary))

    contrary_pairs: set[tuple[Literal, Literal]] = set()

    for stance_input in stances:
        stance = _coerce_bridge_stance_row(stance_input)
        src_key = claim_key(stance.claim_id)
        tgt_key = claim_key(stance.target_claim_id)
        if src_key not in literals or tgt_key not in literals:
            continue

        src = literals[src_key]
        tgt = literals[tgt_key]
        if src == tgt:
            continue

        if stance.stance_type == "rebuts":
            contradictory_pairs.add((src, tgt))
            contradictory_pairs.add((tgt, src))
        elif stance.stance_type in ("supersedes", "undermines"):
            contradictory_pairs.add((src, tgt))
        elif stance.stance_type == "undercuts":
            target_justification_id = stance.target_justification_id
            matching_rules = [
                rule
                for rule in defeasible_rules
                if rule.consequent == tgt and rule.name is not None
            ]
            if target_justification_id is not None:
                exact_matches = [
                    rule for rule in matching_rules if rule.name == target_justification_id
                ]
                if exact_matches:
                    matching_rules = exact_matches
                else:
                    matching_rules = [
                        rule
                        for rule in matching_rules
                        if rule.name is not None
                        and rule.name.partition("#")[0] == target_justification_id
                    ]
                if not matching_rules:
                    raise ValueError(
                        "undercut target_justification_id "
                        f"{target_justification_id!r} did not match a defeasible "
                        f"justification for target claim {stance.target_claim_id!r}"
                    )
            elif len(matching_rules) > 1:
                raise ValueError(
                    "undercut against target claim "
                    f"{stance.target_claim_id!r} is ambiguous across multiple defeasible "
                    "justifications; provide target_justification_id"
                )

            for rule in matching_rules:
                assert rule.name is not None
                rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
                if src != rule_lit:
                    contrary_pairs.add((src, rule_lit))

    return ContrarinessFn(
        contradictories=frozenset(contradictory_pairs),
        contraries=frozenset(contrary_pairs),
    )


def preference_sensitive_stance_pairs(
    stances: Sequence[StanceRowInput],
    literals: dict[LiteralKey, Literal],
) -> frozenset[tuple[Literal, Literal]]:
    pairs: set[tuple[Literal, Literal]] = set()
    for stance_input in stances:
        stance = _coerce_bridge_stance_row(stance_input)
        if stance.stance_type not in ("supersedes", "undermines"):
            continue
        src_key = claim_key(stance.claim_id)
        tgt_key = claim_key(stance.target_claim_id)
        if src_key not in literals or tgt_key not in literals:
            continue
        src = literals[src_key]
        tgt = literals[tgt_key]
        if src != tgt:
            pairs.add((src, tgt))
    return frozenset(pairs)


def claims_to_kb(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> KnowledgeBase:
    """Build ``K_n`` and ``K_p`` from reported claims."""

    reported_claim_ids = {
        justification.conclusion_claim_id
        for justification in justifications
        if justification.rule_kind == "reported_claim"
    }

    normalized_claims = coerce_active_claims(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    axioms: set[Literal] = set()
    premises: set[Literal] = set()

    for claim_id in reported_claim_ids:
        literal_key = claim_key(claim_id)
        if literal_key not in literals:
            continue
        claim = claim_by_id.get(claim_id)
        if claim is None:
            continue
        literal = literals[literal_key]
        if _claim_attr(claim, "premise_kind") == "necessary":
            axioms.add(literal)
        else:
            premises.add(literal)

    return KnowledgeBase(axioms=frozenset(axioms), premises=frozenset(premises))


def _component_wise_dominates(
    a: MetadataStrengthVector,
    b: MetadataStrengthVector,
) -> bool:
    """True when ``a`` is strictly weaker than ``b`` under Pareto domination."""

    if a.is_vacuous or b.is_vacuous:
        return False
    if len(a.dimensions) != len(b.dimensions):
        return False
    return all(ai <= bi for ai, bi in zip(a.dimensions, b.dimensions)) and any(
        ai < bi for ai, bi in zip(a.dimensions, b.dimensions)
    )


def build_preference_config(
    active_claims: Sequence[ActiveClaimInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
    *,
    rule_order: frozenset[tuple[Rule, Rule]] = frozenset(),
    comparison: str = "elitist",
    link: str = "last",
) -> PreferenceConfig:
    """Build ASPIC+ preference configuration.

    Premise ordering remains the existing metadata heuristic. Rule ordering
    is an explicit authored strict partial order over defeasible rules,
    oriented ``(weaker, stronger)``.
    """

    normalized_claims = coerce_active_claims(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    premise_order: set[tuple[Literal, Literal]] = set()

    unknown_rule_pairs = [
        (weaker, stronger)
        for weaker, stronger in rule_order
        if weaker not in defeasible_rules or stronger not in defeasible_rules
    ]
    if unknown_rule_pairs:
        raise ValueError("rule_order contains rules outside defeasible_rules")

    claim_ids = [
        key.claim_id
        for key in literals
        if isinstance(key, ClaimLiteralKey) and key.claim_id in claim_by_id
    ]
    for index, claim_id_a in enumerate(claim_ids):
        for claim_id_b in claim_ids[index + 1 :]:
            vec_a = metadata_strength_vector(claim_by_id[claim_id_a])
            vec_b = metadata_strength_vector(claim_by_id[claim_id_b])
            lit_a = literals[claim_key(claim_id_a)]
            lit_b = literals[claim_key(claim_id_b)]

            if _component_wise_dominates(vec_a, vec_b):
                premise_order.add((lit_a, lit_b))
            elif _component_wise_dominates(vec_b, vec_a):
                premise_order.add((lit_b, lit_a))

    return PreferenceConfig(
        rule_order=strict_partial_order_closure(rule_order),
        premise_order=strict_partial_order_closure(premise_order),
        comparison=comparison,
        link=link,
    )


__all__ = [
    "build_preference_config",
    "claims_to_kb",
    "claims_to_literals",
    "justifications_to_rules",
    "preference_sensitive_stance_pairs",
    "stances_to_contrariness",
]
