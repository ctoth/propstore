from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from argumentation.af_revision import ExtensionRevisionState
from argumentation.dung import ArgumentationFramework

from propstore.belief_set import (
    BOTTOM,
    TOP,
    Atom,
    BeliefSet,
    Formula,
    SpohnEpistemicState,
    conjunction,
    disjunction,
    expand,
    full_meet_contract,
    lexicographic_revise,
    negate,
    restrained_revise,
    revise,
    theory_subset,
)
from propstore.belief_set.af_revision_adapter import (
    NoStableExtensionRevisionTarget,
    revise_by_stable_framework,
)
from propstore.belief_set.core import align_belief_sets
from propstore.belief_set.entrenchment import EpistemicEntrenchment
from propstore.belief_set.ic_merge import ICMergeOperator, merge_belief_profile


pytestmark = pytest.mark.property

ALPHABET = frozenset({"p", "q", "r"})
P = Atom("p")
Q = Atom("q")
R = Atom("r")
FORMULAS: tuple[Formula, ...] = (
    P,
    Q,
    R,
    negate(P),
    conjunction(P, Q),
    disjunction(P, Q),
)


@dataclass(frozen=True)
class AuditCase:
    postulate_id: str
    assertion: Callable[[], None]


def _state() -> SpohnEpistemicState:
    worlds = BeliefSet.all_worlds(ALPHABET)
    return SpohnEpistemicState.from_ranks(
        ALPHABET,
        {world: len(world.symmetric_difference(frozenset({"p", "q"}))) for world in worlds},
    )


def _belief(formula: Formula) -> BeliefSet:
    return BeliefSet.from_formula(ALPHABET, formula)


def _entails(left: BeliefSet, right: BeliefSet) -> bool:
    aligned_left, aligned_right = align_belief_sets(left, right)
    return aligned_left.models <= aligned_right.models


def _equivalent(left: BeliefSet, right: BeliefSet) -> bool:
    return left.equivalent(right)


def _revision_case(postulate: str, formula: Formula, beta: Formula = Q) -> None:
    state = _state()
    result = revise(state, formula)
    expansion = expand(state.belief_set, formula)
    if postulate == "K*1":
        assert isinstance(result.belief_set, BeliefSet)
    elif postulate == "K*2":
        if _belief(formula).is_consistent:
            assert result.belief_set.entails(formula)
        else:
            assert not result.belief_set.is_consistent
    elif postulate == "K*3":
        assert theory_subset(result.belief_set, expansion)
    elif postulate == "K*4":
        if not state.belief_set.entails(negate(formula)):
            assert result.belief_set.equivalent(expansion)
    elif postulate == "K*5":
        assert result.belief_set.is_consistent is _belief(formula).is_consistent
    elif postulate == "K*6":
        equivalent_input = conjunction(formula, TOP)
        assert revise(state, formula).belief_set.equivalent(
            revise(state, equivalent_input).belief_set
        )
    elif postulate == "K*7":
        conjunction_result = revise(state, conjunction(formula, beta)).belief_set
        revise_then_expand = expand(revise(state, formula).belief_set, beta)
        assert theory_subset(conjunction_result, revise_then_expand)
    elif postulate == "K*8":
        if not revise(state, formula).belief_set.entails(negate(beta)):
            conjunction_result = revise(state, conjunction(formula, beta)).belief_set
            revise_then_expand = expand(revise(state, formula).belief_set, beta)
            assert theory_subset(revise_then_expand, conjunction_result)
    else:
        raise AssertionError(f"unknown revision postulate {postulate}")


def _contraction_case(postulate: str, formula: Formula, beta: Formula = Q) -> None:
    state = _state()
    contracted = full_meet_contract(state, formula)
    if postulate == "K-1":
        assert isinstance(contracted.belief_set, BeliefSet)
    elif postulate == "K-2":
        assert theory_subset(contracted.belief_set, state.belief_set)
    elif postulate == "K-3":
        if not state.belief_set.entails(formula):
            assert contracted.belief_set.equivalent(state.belief_set)
    elif postulate == "K-4":
        if not _belief(formula).models == BeliefSet.all_worlds(ALPHABET):
            assert not contracted.belief_set.entails(formula)
    elif postulate == "K-5":
        assert theory_subset(state.belief_set, expand(contracted.belief_set, formula))
    elif postulate == "K-6":
        assert full_meet_contract(state, conjunction(formula, TOP)).belief_set.equivalent(
            contracted.belief_set
        )
    elif postulate == "K-7":
        both = full_meet_contract(state, conjunction(formula, beta)).belief_set
        left = full_meet_contract(state, formula).belief_set
        right = full_meet_contract(state, beta).belief_set
        assert theory_subset(left.intersection_theory(right), both)
    elif postulate == "K-8":
        both = full_meet_contract(state, conjunction(formula, beta)).belief_set
        if not both.entails(formula):
            assert theory_subset(both, full_meet_contract(state, formula).belief_set)
    elif postulate == "Harper":
        harper = state.belief_set.intersection_theory(revise(state, negate(formula)).belief_set)
        assert contracted.belief_set.equivalent(harper)
    else:
        raise AssertionError(f"unknown contraction postulate {postulate}")


def _iterated_case(operator_name: str, postulate: str) -> None:
    operator = {
        "bullet": revise,
        "lexicographic": lexicographic_revise,
        "restrained": restrained_revise,
    }[operator_name]
    state = _state()
    if postulate in {"C1", "CR1"}:
        mu = P
        alpha = conjunction(P, Q)
    elif postulate in {"C2", "CR2"}:
        mu = P
        alpha = negate(P)
    elif postulate in {"C3", "CR3"}:
        mu = P
        alpha = conjunction(P, Q)
    else:
        mu = P
        alpha = Q

    after_mu_then_alpha = operator(operator(state, mu).state, alpha).belief_set
    after_alpha = operator(state, alpha).belief_set
    if postulate in {"C1", "CR1"}:
        assert after_mu_then_alpha.equivalent(after_alpha)
    elif postulate in {"C2", "CR2"}:
        assert after_mu_then_alpha.equivalent(after_alpha)
    elif postulate in {"C3", "CR3"}:
        if after_alpha.entails(mu):
            assert after_mu_then_alpha.entails(mu)
    elif postulate in {"C4", "CR4"}:
        if not after_alpha.entails(negate(mu)):
            assert not after_mu_then_alpha.entails(negate(mu))
    else:
        raise AssertionError(f"unknown iterated postulate {postulate}")


def _ic_case(postulate: str) -> None:
    if postulate == "IC4":
        result = merge_belief_profile(
            ALPHABET,
            (conjunction(P, Q), conjunction(negate(P), Q)),
            Q,
            operator=ICMergeOperator.SIGMA,
        ).belief_set
        assert not result.entails(negate(conjunction(P, Q)))
    elif postulate == "Maj":
        dominant = merge_belief_profile(ALPHABET, (P,), TOP, operator=ICMergeOperator.SIGMA).belief_set
        combined = merge_belief_profile(
            ALPHABET,
            (negate(P), P, P),
            TOP,
            operator=ICMergeOperator.SIGMA,
        ).belief_set
        assert _entails(combined, dominant)
    elif postulate == "Arb":
        result = merge_belief_profile(
            frozenset({"S", "T", "P", "I"}),
            (
                conjunction(Atom("S"), Atom("T"), Atom("P")),
                conjunction(Atom("S"), Atom("T"), Atom("P")),
                conjunction(negate(Atom("S")), negate(Atom("T")), negate(Atom("P")), negate(Atom("I"))),
                conjunction(Atom("T"), Atom("P"), negate(Atom("I"))),
            ),
            disjunction(
                negate(disjunction(
                    conjunction(Atom("S"), Atom("T")),
                    conjunction(Atom("S"), Atom("P")),
                    conjunction(Atom("T"), Atom("P")),
                )),
                Atom("I"),
            ),
            operator=ICMergeOperator.GMAX,
        ).belief_set
        assert result.models == frozenset({frozenset({"P"}), frozenset({"T"})})
    else:
        raise AssertionError(f"unknown IC postulate {postulate}")


def _entrenchment_case(postulate: str, formula: Formula = P, beta: Formula = Q) -> None:
    state = _state()
    entrenchment = EpistemicEntrenchment.from_state(state)
    if postulate == "EE1":
        if entrenchment.leq(formula, beta) and entrenchment.leq(beta, R):
            assert entrenchment.leq(formula, R)
    elif postulate == "EE2":
        if _belief(formula).entails(beta):
            assert entrenchment.leq(formula, beta)
    elif postulate == "EE3":
        assert entrenchment.leq(formula, conjunction(formula, beta)) or entrenchment.leq(
            beta, conjunction(formula, beta)
        )
    elif postulate == "EE4":
        if state.belief_set.is_consistent and not state.belief_set.entails(formula):
            assert all(entrenchment.leq(formula, candidate) for candidate in FORMULAS)
    elif postulate == "EE5":
        if all(entrenchment.leq(candidate, formula) for candidate in FORMULAS):
            assert _belief(formula).models == BeliefSet.all_worlds(ALPHABET)
    else:
        raise AssertionError(f"unknown entrenchment postulate {postulate}")


def _af_no_stable_case() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c"), ("c", "a")}),
    )
    state = ExtensionRevisionState.from_extensions(frozenset(), (frozenset(),))
    with pytest.raises(NoStableExtensionRevisionTarget):
        revise_by_stable_framework(state, framework)


def _cases() -> list[AuditCase]:
    cases: list[AuditCase] = []
    for postulate in ("K*1", "K*2", "K*3", "K*4", "K*5", "K*6", "K*7", "K*8"):
        for formula in (*FORMULAS[:4], BOTTOM):
            cases.append(AuditCase(f"{postulate}[{formula!r}]", lambda p=postulate, f=formula: _revision_case(p, f)))
    for postulate in ("K-1", "K-2", "K-3", "K-4", "K-5", "K-6", "K-7", "K-8", "Harper"):
        for formula in FORMULAS[:3]:
            cases.append(AuditCase(f"{postulate}[{formula!r}]", lambda p=postulate, f=formula: _contraction_case(p, f)))
    for operator_name in ("bullet", "lexicographic", "restrained"):
        for postulate in ("C1", "C2", "C3", "C4", "CR1", "CR2", "CR3", "CR4"):
            cases.append(AuditCase(f"{operator_name}:{postulate}", lambda o=operator_name, p=postulate: _iterated_case(o, p)))
    for postulate in ("IC4", "Maj", "Arb"):
        cases.append(AuditCase(postulate, lambda p=postulate: _ic_case(p)))
    for postulate in ("EE1", "EE2", "EE3", "EE4", "EE5"):
        cases.append(AuditCase(postulate, lambda p=postulate: _entrenchment_case(p)))
    cases.append(AuditCase("agm_af_no_stable_distinct_from_empty_stable", _af_no_stable_case))
    return cases


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.postulate_id)
def test_ws_g_postulate_audit(case: AuditCase) -> None:
    case.assertion()
