"""Claims/justifications/stances → ASPIC+ translation and CSAF assembly.

These exercise the bridge over plain claim/justification/stance inputs and an
empty grounded bundle: literal interning, rule translation, contrariness from
stances, the K_n/K_p split, preference ordering, and the assembled CSAF's Dung
projection. The ASPIC+ kernel itself is the argumentation package's.
"""

from __future__ import annotations

import pytest
from argumentation.core.dung import grounded_extension
from argumentation.structured.aspic.aspic import GroundAtom, Literal, conc
from argumentation.structured.aspic.datalog_grounding import GroundRuleOrigin  # noqa: F401

from propstore.stances import StanceType
from propstore.aspic_bridge.translate import StanceInput
from propstore.aspic_bridge import (
    build_bridge_csaf,
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    query_claim,
    stances_to_contrariness,
)
from propstore.core.active_claims import ActiveClaim
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import claim_key
from propstore.grounding.bundle import GroundedRulesBundle


def _claim(claim_id: str, **extra) -> ActiveClaim:  # noqa: ANN003 - typed field kwargs
    return ActiveClaim(claim_id=claim_id, concept_id="k", statement=claim_id, **extra)


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _support(source: str, target: str, *, strength: str = "defeasible") -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"supports:{source}->{target}",
        conclusion_claim_id=target,
        premise_claim_ids=(source,),
        rule_kind="supports",
        rule_strength=strength,
    )


def _bundle() -> GroundedRulesBundle:
    return GroundedRulesBundle.empty()


# --- T1 claims_to_literals ---------------------------------------------------


def test_every_claim_has_a_literal_keyed_by_claim_key() -> None:
    literals = claims_to_literals([_claim("c1"), _claim("c2")])
    assert claim_key("c1") in literals
    assert claim_key("c2") in literals


def test_claim_literal_is_a_positive_ist_atom() -> None:
    literals = claims_to_literals([_claim("c1")])
    literal = literals[claim_key("c1")]
    assert literal.atom.predicate == "ist"
    assert literal.atom.arguments[-1] == "c1"
    assert literal.negated is False


def test_no_duplicate_atoms() -> None:
    literals = claims_to_literals([_claim("c1"), _claim("c2")])
    atoms = [literal.atom for literal in literals.values()]
    assert len(atoms) == len(set(atoms))


# --- T2 justifications_to_rules ----------------------------------------------


def test_reported_claims_produce_no_rules() -> None:
    literals = claims_to_literals([_claim("c1")])
    strict, defeasible = justifications_to_rules([_reported("c1")], literals)
    assert not strict
    assert not defeasible


def test_defeasible_rule_carries_justification_id_as_name() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b")])
    _strict, defeasible = justifications_to_rules([_support("a", "b")], literals)
    rule = next(iter(defeasible))
    assert rule.kind == "defeasible"
    assert rule.name == "supports:a->b"
    assert rule.consequent == literals[claim_key("b")]
    assert rule.antecedents == (literals[claim_key("a")],)


def test_strict_rule_has_no_name() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b")])
    strict, _defeasible = justifications_to_rules([_support("a", "b", strength="strict")], literals)
    rule = next(iter(strict))
    assert rule.kind == "strict"
    assert rule.name is None


def test_empty_premise_non_reported_justification_is_rejected() -> None:
    literals = claims_to_literals([_claim("b")])
    bad = CanonicalJustification(justification_id="supports:->b", conclusion_claim_id="b", rule_kind="supports")
    with pytest.raises(ValueError, match="empty-premise"):
        justifications_to_rules([bad], literals)


# --- T3 stances_to_contrariness ----------------------------------------------


def test_rebut_produces_symmetric_contradictories() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b")])
    cfn = stances_to_contrariness(
        [StanceInput(claim_id="a", target_claim_id="b", stance_type=StanceType.REBUTS)],
        literals,
        frozenset(),
    )
    a = literals[claim_key("a")]
    b = literals[claim_key("b")]
    assert cfn.is_contradictory(a, b)
    assert cfn.is_contradictory(b, a)


def test_supersedes_produces_asymmetric_contrary() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b")])
    cfn = stances_to_contrariness(
        [StanceInput(claim_id="a", target_claim_id="b", stance_type=StanceType.SUPERSEDES)],
        literals,
        frozenset(),
    )
    a = literals[claim_key("a")]
    b = literals[claim_key("b")]
    assert cfn.is_contrary(a, b)
    assert not cfn.is_contrary(b, a)


def test_undercut_targets_the_named_defeasible_rule() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b"), _claim("attacker")])
    _strict, defeasible = justifications_to_rules([_support("a", "b")], literals)
    cfn = stances_to_contrariness(
        [
            StanceInput(claim_id="attacker", target_claim_id="b", stance_type=StanceType.UNDERCUTS, target_justification_id="supports:a->b")
        ],
        literals,
        defeasible,
    )
    attacker = literals[claim_key("attacker")]
    rule_lit = Literal(atom=GroundAtom("supports:a->b"), negated=False)
    assert cfn.is_contrary(attacker, rule_lit)


def test_undercut_without_rule_id_is_ambiguous_with_multiple_rules() -> None:
    literals = claims_to_literals([_claim("a"), _claim("c"), _claim("b"), _claim("attacker")])
    _strict, defeasible = justifications_to_rules([_support("a", "b"), _support("c", "b")], literals)
    with pytest.raises(ValueError, match="target_justification_id"):
        stances_to_contrariness(
            [StanceInput(claim_id="attacker", target_claim_id="b", stance_type=StanceType.UNDERCUTS)],
            literals,
            defeasible,
        )


# --- T4 claims_to_kb ---------------------------------------------------------


def test_necessary_claims_are_axioms_ordinary_are_premises() -> None:
    literals = claims_to_literals([_claim("n", premise_kind="necessary"), _claim("o")])
    kb = claims_to_kb(
        [_claim("n", premise_kind="necessary"), _claim("o")],
        [_reported("n"), _reported("o")],
        literals,
    )
    assert literals[claim_key("n")] in kb.axioms
    assert literals[claim_key("o")] in kb.premises
    assert not (kb.axioms & kb.premises)


# --- T5 build_preference_config ----------------------------------------------


def test_rule_order_outside_defeasible_rules_is_rejected() -> None:
    literals = claims_to_literals([_claim("a"), _claim("b")])
    _strict, defeasible = justifications_to_rules([_support("a", "b")], literals)
    other = next(iter(defeasible))
    with pytest.raises(ValueError, match="rule_order contains rules outside"):
        build_preference_config(
            [_claim("a"), _claim("b")],
            literals,
            frozenset(),
            rule_order=frozenset({(other, other)}),
        )


def test_premise_order_is_irreflexive() -> None:
    claims = [_claim("a", sample_size=100, confidence=0.9), _claim("b", sample_size=5, confidence=0.4)]
    literals = claims_to_literals(claims)
    pref = build_preference_config(claims, literals, frozenset())
    assert all(weaker != stronger for weaker, stronger in pref.premise_order)


# --- CSAF assembly -----------------------------------------------------------


def test_no_stances_all_claims_survive() -> None:
    claims = [_claim("x"), _claim("y"), _claim("z")]
    csaf = build_bridge_csaf(claims, [_reported("x"), _reported("y"), _reported("z")], [], bundle=_bundle())
    assert len(csaf.defeats) == 0
    grounded = grounded_extension(csaf.framework)
    justified = {
        _conclusion_claim_id(conc(csaf.id_to_arg[arg_id])) for arg_id in grounded
    }
    assert {"x", "y", "z"} <= justified


def test_framework_is_a_valid_dung_af() -> None:
    claims = [_claim("a"), _claim("b")]
    csaf = build_bridge_csaf(
        claims,
        [_reported("a"), _reported("b")],
        [StanceInput(claim_id="a", target_claim_id="b", stance_type=StanceType.REBUTS)],
        bundle=_bundle(),
    )
    assert csaf.framework.attacks is not None
    assert csaf.framework.defeats <= csaf.framework.attacks
    for attacker, target in csaf.framework.defeats:
        assert attacker in csaf.framework.arguments
        assert target in csaf.framework.arguments


def test_rebut_stronger_claim_wins() -> None:
    claims = [
        _claim("a", sample_size=100, confidence=0.9),
        _claim("b", sample_size=5, confidence=0.4),
    ]
    csaf = build_bridge_csaf(
        claims,
        [_reported("a"), _reported("b")],
        [
            StanceInput(claim_id="a", target_claim_id="b", stance_type=StanceType.REBUTS),
            StanceInput(claim_id="b", target_claim_id="a", stance_type=StanceType.REBUTS),
        ],
        bundle=_bundle(),
    )
    grounded = grounded_extension(csaf.framework)
    justified = {_conclusion_claim_id(conc(csaf.id_to_arg[arg_id])) for arg_id in grounded}
    assert "a" in justified
    assert "b" not in justified


def test_query_claim_collects_arguments_for_and_against() -> None:
    claims = [_claim("goal"), _claim("anti")]
    result = query_claim(
        "goal",
        claims,
        [_reported("goal"), _reported("anti")],
        [StanceInput(claim_id="anti", target_claim_id="goal", stance_type=StanceType.REBUTS)],
        bundle=_bundle(),
    )
    assert any(conc(argument).atom.arguments[-1] == "goal" for argument in result.arguments_for)
    against_claims = {
        _conclusion_claim_id(conc(argument)) for argument in result.arguments_against
    }
    assert "anti" in against_claims


def test_query_unknown_claim_raises() -> None:
    with pytest.raises(KeyError):
        query_claim("missing", [_claim("x")], [_reported("x")], [], bundle=_bundle())


def _conclusion_claim_id(literal: Literal) -> str:
    atom = literal.atom
    if atom.predicate == "ist" and len(atom.arguments) == 2:
        return str(atom.arguments[1])
    return atom.predicate
