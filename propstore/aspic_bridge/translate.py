"""Claim-graph to ASPIC+ translation stages T1-T5."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from propstore.aspic import (
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
from propstore.preference import metadata_strength_vector


def _claim_attr(claim: ActiveClaim, key: str) -> Any:
    return getattr(claim, key, claim.attributes.get(key))


def _coerce_bridge_stance_row(row: StanceRowInput) -> StanceRow:
    """Coerce a bridge stance row, accepting bridge-local ``contradicts``."""

    if isinstance(row, StanceRow):
        return row
    row_map = dict(row)
    if row_map.get("stance_type") == "contradicts":
        row_map["stance_type"] = "rebuts"
    return coerce_stance_row(row_map)


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
        if any(pid not in literals for pid in premise_keys):
            continue

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

        if stance.stance_type in ("rebuts", "contradicts"):
            contradictory_pairs.add((src, tgt))
            contradictory_pairs.add((tgt, src))
        elif stance.stance_type in ("supersedes", "undermines"):
            contrary_pairs.add((src, tgt))
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


def _component_wise_dominates(a: list[float], b: list[float]) -> bool:
    """True when ``a`` is strictly weaker than ``b`` under Pareto domination."""

    if len(a) != len(b):
        return False
    return all(ai <= bi for ai, bi in zip(a, b)) and any(ai < bi for ai, bi in zip(a, b))


def _transitive_closure(
    pairs: set[tuple[Literal, Literal]],
) -> frozenset[tuple[Literal, Literal]]:
    """Compute the transitive closure of a binary relation over literals."""

    closure = set(pairs)
    changed = True
    while changed:
        changed = False
        new_pairs: set[tuple[Literal, Literal]] = set()
        for left, mid in closure:
            for source, right in closure:
                if mid == source and (left, right) not in closure:
                    new_pairs.add((left, right))
        if new_pairs:
            closure |= new_pairs
            changed = True
    return frozenset(closure)


def build_preference_config(
    active_claims: Sequence[ActiveClaimInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
    *,
    comparison: str = "elitist",
    link: str = "last",
) -> PreferenceConfig:
    """Build premise ordering from claim metadata and leave rules incomparable."""

    del defeasible_rules

    normalized_claims = coerce_active_claims(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    premise_order: set[tuple[Literal, Literal]] = set()

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
        rule_order=frozenset(),
        premise_order=_transitive_closure(premise_order),
        comparison=comparison,
        link=link,
    )


__all__ = [
    "build_preference_config",
    "claims_to_kb",
    "claims_to_literals",
    "justifications_to_rules",
    "stances_to_contrariness",
]
