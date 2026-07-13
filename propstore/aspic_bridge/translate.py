"""Claim-graph to ASPIC+ translation (Modgil & Prakken 2018).

These stages lower the propstore claim graph into the argumentation package's
ASPIC+ vocabulary, used directly (CLAUDE.md substrate boundary):

* T1 ``claims_to_literals`` — each claim becomes a positive ``ist(c, p)`` literal;
* T2 ``justifications_to_rules`` — justifications become strict/defeasible rules
  (a ``reported_claim`` contributes a premise, not a rule);
* T3 ``stances_to_contrariness`` — rebut/supersede/undermine/undercut stances
  become the contrariness function;
* T4 ``claims_to_kb`` — reported claims populate ``K_n`` (necessary) / ``K_p``;
* T5 ``build_preference_config`` — the metadata strength heuristic orders
  premises; an authored partial order orders defeasible rules.

Stances are read as plain mappings at this boundary (``claim_id`` /
``target_claim_id`` / ``stance_type`` / optional ``target_justification_id``);
the stance vocabulary is :class:`~propstore.stances.StanceType`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from argumentation.core.preference import strict_partial_order_closure
from argumentation.structured.aspic.aspic import (
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    Rule,
)
from argumentation.structured.aspic.datalog_grounding import GroundRuleOrigin

from propstore.core.active_claims import ActiveClaim
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import (
    REPOSITORY_ROOT_CONTEXT_ID,
    IstLiteralKey,
    LiteralKey,
    claim_key,
)
from propstore.preference import MetadataStrengthVector, metadata_strength_vector
from propstore.stances import StanceType, coerce_stance_type

StanceInput: TypeAlias = Mapping[str, Any]


def _claim_context_id(claim: ActiveClaim) -> str:
    if claim.context_id is None:
        return str(REPOSITORY_ROOT_CONTEXT_ID)
    return str(claim.context_id)


def _claim_literal_key(claim: ActiveClaim) -> IstLiteralKey:
    return claim_key(str(claim.claim_id), context_id=_claim_context_id(claim))


def _stance_field(stance: StanceInput, key: str) -> str | None:
    value = stance.get(key)
    return None if value is None else str(value)


def _stance_type(stance: StanceInput) -> StanceType | None:
    return coerce_stance_type(stance.get("stance_type"))


def _literal_key_for_proposition(
    proposition_id: str,
    literals: Mapping[LiteralKey, Literal],
) -> LiteralKey:
    matches = [
        key
        for key in literals
        if isinstance(key, IstLiteralKey) and str(key.proposition_id) == str(proposition_id)
    ]
    if not matches:
        return claim_key(str(proposition_id))
    if len(matches) > 1:
        contexts = ", ".join(sorted(str(key.context_id) for key in matches))
        raise ValueError(f"claim {proposition_id!r} is ambiguous across contexts: {contexts}")
    return matches[0]


def claims_to_literals(active_claims: Sequence[ActiveClaim]) -> dict[LiteralKey, Literal]:
    """Map each claim to a positive ASPIC+ ``ist(c, p)`` literal."""

    return {
        _claim_literal_key(claim): Literal(
            atom=GroundAtom("ist", (_claim_context_id(claim), str(claim.claim_id))),
            negated=False,
        )
        for claim in active_claims
    }


def justifications_to_rules(
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> tuple[frozenset[Rule], frozenset[Rule]]:
    """Translate justifications into ASPIC+ strict and defeasible rules."""

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

        conclusion_key = _literal_key_for_proposition(justification.conclusion_claim_id, literals)
        premise_keys = tuple(
            _literal_key_for_proposition(pid, literals)
            for pid in justification.premise_claim_ids
        )
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
                f"unknown premise in justification {justification.justification_id!r}: {missing}"
            )

        antecedents = tuple(literals[pid] for pid in premise_keys)
        consequent = literals[conclusion_key]
        if justification.rule_strength == "strict":
            strict.append(Rule(antecedents=antecedents, consequent=consequent, kind="strict", name=None))
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
    stances: Sequence[StanceInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
    *,
    rule_origins: Mapping[Rule, GroundRuleOrigin] | None = None,
) -> ContrarinessFn:
    """Build the ASPIC+ contrariness function from attack stances.

    Rebuts are symmetric contradictories (unless a reverse directional pair was
    authored). Supersedes/undermines are directional contraries. Undercuts make
    the attacker contrary to the *named defeasible rule* concluding the target.
    """

    contradictory_pairs: set[tuple[Literal, Literal]] = {
        (literal, literal.contrary) for literal in literals.values()
    }
    for rule in defeasible_rules:
        if rule.name is None:
            continue
        rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
        contradictory_pairs.add((rule_lit, rule_lit.contrary))

    contrary_pairs: set[tuple[Literal, Literal]] = set()
    origins: Mapping[Rule, GroundRuleOrigin] = {} if rule_origins is None else rule_origins

    authored_rebuts: set[tuple[Literal, Literal]] = set()
    authored_directional: set[tuple[Literal, Literal]] = set()

    for stance in stances:
        stance_type = _stance_type(stance)
        source_id = _stance_field(stance, "claim_id")
        target_id = _stance_field(stance, "target_claim_id")
        if source_id is None or target_id is None:
            continue
        src_key = _literal_key_for_proposition(source_id, literals)
        tgt_key = _literal_key_for_proposition(target_id, literals)
        if src_key not in literals or tgt_key not in literals:
            continue
        src = literals[src_key]
        tgt = literals[tgt_key]
        if src == tgt:
            continue

        if stance_type is StanceType.REBUTS:
            authored_rebuts.add((src, tgt))
        elif stance_type in (StanceType.SUPERSEDES, StanceType.UNDERMINES):
            authored_directional.add((src, tgt))
        elif stance_type is StanceType.UNDERCUTS:
            _add_undercut_contraries(
                stance,
                src,
                tgt,
                target_id,
                defeasible_rules,
                origins,
                contrary_pairs,
            )

    for src, tgt in authored_rebuts:
        if (tgt, src) not in authored_directional:
            contradictory_pairs.add((src, tgt))
    contrary_pairs.update(authored_directional)

    return ContrarinessFn(
        contradictories=frozenset(contradictory_pairs),
        contraries=frozenset(contrary_pairs),
    )


def _add_undercut_contraries(
    stance: StanceInput,
    src: Literal,
    tgt: Literal,
    target_id: str,
    defeasible_rules: frozenset[Rule],
    origins: Mapping[Rule, GroundRuleOrigin],
    contrary_pairs: set[tuple[Literal, Literal]],
) -> None:
    target_justification_id = _stance_field(stance, "target_justification_id")
    matching_rules = [
        rule for rule in defeasible_rules if rule.consequent == tgt and rule.name is not None
    ]
    if target_justification_id is not None:
        exact_matches = [rule for rule in matching_rules if rule.name == target_justification_id]
        if exact_matches:
            matching_rules = exact_matches
        else:
            matching_rules = [
                rule
                for rule in matching_rules
                if (origin := origins.get(rule)) is not None
                and origin.role == "ground"
                and origin.source_rule_id == target_justification_id
            ]
        if not matching_rules:
            raise ValueError(
                f"undercut target_justification_id {target_justification_id!r} did not match a "
                f"defeasible justification for target claim {target_id!r}"
            )
    elif len(matching_rules) > 1:
        rule_names = ", ".join(
            sorted(rule.name for rule in matching_rules if rule.name is not None)
        )
        raise ValueError(
            f"undercut against target claim {target_id!r} is ambiguous: "
            f"{len(matching_rules)} defeasible rules conclude this claim. "
            f"Set target_justification_id on the stance to one of: {rule_names}."
        )

    for rule in matching_rules:
        if rule.name is None:
            continue
        rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
        if src != rule_lit:
            contrary_pairs.add((src, rule_lit))


def preference_sensitive_stance_pairs(
    stances: Sequence[StanceInput],
    literals: dict[LiteralKey, Literal],
) -> frozenset[tuple[Literal, Literal]]:
    """The directional ``(attacker, target)`` literal pairs from supersede/undermine."""

    pairs: set[tuple[Literal, Literal]] = set()
    for stance in stances:
        if _stance_type(stance) not in (StanceType.SUPERSEDES, StanceType.UNDERMINES):
            continue
        source_id = _stance_field(stance, "claim_id")
        target_id = _stance_field(stance, "target_claim_id")
        if source_id is None or target_id is None:
            continue
        src_key = _literal_key_for_proposition(source_id, literals)
        tgt_key = _literal_key_for_proposition(target_id, literals)
        if src_key not in literals or tgt_key not in literals:
            continue
        src = literals[src_key]
        tgt = literals[tgt_key]
        if src != tgt:
            pairs.add((src, tgt))
    return frozenset(pairs)


def claims_to_kb(
    active_claims: Sequence[ActiveClaim],
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> KnowledgeBase:
    """Build ``K_n`` (necessary) and ``K_p`` (ordinary) from reported claims."""

    reported_claim_ids = {
        justification.conclusion_claim_id
        for justification in justifications
        if justification.rule_kind == "reported_claim"
    }
    claim_by_id = {str(claim.claim_id): claim for claim in active_claims}
    axioms: set[Literal] = set()
    premises: set[Literal] = set()

    for claim_id in reported_claim_ids:
        claim = claim_by_id.get(claim_id)
        if claim is None:
            continue
        literal_key = _claim_literal_key(claim)
        if literal_key not in literals:
            continue
        literal = literals[literal_key]
        if claim.premise_kind == "necessary":
            axioms.add(literal)
        else:
            premises.add(literal)

    return KnowledgeBase(axioms=frozenset(axioms), premises=frozenset(premises))


def _dominates(a: MetadataStrengthVector, b: MetadataStrengthVector) -> bool:
    """True when ``a`` is strictly weaker than ``b`` under Pareto domination."""

    if a.is_vacuous or b.is_vacuous or len(a.dimensions) != len(b.dimensions):
        return False
    return all(ai <= bi for ai, bi in zip(a.dimensions, b.dimensions)) and any(
        ai < bi for ai, bi in zip(a.dimensions, b.dimensions)
    )


def build_preference_config(
    active_claims: Sequence[ActiveClaim],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
    *,
    rule_order: frozenset[tuple[Rule, Rule]] = frozenset(),
    comparison: str = "elitist",
    link: str = "last",
) -> PreferenceConfig:
    """Build the ASPIC+ preference configuration.

    Premise ordering is the metadata strength heuristic (Pareto under elitist,
    summed score under democratic). Rule ordering is an explicit authored strict
    partial order over defeasible rules, oriented ``(weaker, stronger)``.
    """

    normalized_claims = tuple(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    premise_order: set[tuple[Literal, Literal]] = set()

    if any(
        weaker not in defeasible_rules or stronger not in defeasible_rules
        for weaker, stronger in rule_order
    ):
        raise ValueError("rule_order contains rules outside defeasible_rules")

    claim_keys = [
        _claim_literal_key(claim)
        for claim in normalized_claims
        if _claim_literal_key(claim) in literals
    ]
    for index, key_a in enumerate(claim_keys):
        for key_b in claim_keys[index + 1 :]:
            vec_a = metadata_strength_vector(claim_by_id[str(key_a.proposition_id)])
            vec_b = metadata_strength_vector(claim_by_id[str(key_b.proposition_id)])
            lit_a = literals[key_a]
            lit_b = literals[key_b]
            if _dominates(vec_a, vec_b):
                premise_order.add((lit_a, lit_b))
            elif _dominates(vec_b, vec_a):
                premise_order.add((lit_b, lit_a))
            elif comparison == "democratic" and not vec_a.is_vacuous and not vec_b.is_vacuous:
                score_a = sum(vec_a.dimensions)
                score_b = sum(vec_b.dimensions)
                if score_a < score_b:
                    premise_order.add((lit_a, lit_b))
                elif score_b < score_a:
                    premise_order.add((lit_b, lit_a))

    return PreferenceConfig(
        rule_order=strict_partial_order_closure(rule_order),
        premise_order=strict_partial_order_closure(premise_order),
        comparison=comparison,
        link=link,
    )


__all__ = [
    "StanceInput",
    "build_preference_config",
    "claims_to_kb",
    "claims_to_literals",
    "justifications_to_rules",
    "preference_sensitive_stance_pairs",
    "stances_to_contrariness",
]
