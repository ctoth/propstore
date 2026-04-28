from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.belief_set import (
    BOTTOM,
    TOP,
    Atom,
    BeliefSet,
    Formula,
    SpohnEpistemicState,
    conjunction,
    disjunction,
    equivalent,
    expand,
    full_meet_contract,
    negate,
    revise,
    theory_subset,
)
from propstore.belief_set.entrenchment import EpistemicEntrenchment
from propstore.belief_set.ic_merge import ICMergeOperator, merge_belief_profile


pytestmark = pytest.mark.property

ALPHABET = frozenset({"p", "q", "r"})
P = Atom("p")
Q = Atom("q")
R = Atom("r")

FORMULAS: tuple[Formula, ...] = (
    TOP,
    BOTTOM,
    P,
    Q,
    R,
    negate(P),
    negate(Q),
    negate(R),
    conjunction(P, Q),
    conjunction(P, negate(Q)),
    conjunction(Q, R),
    disjunction(P, Q),
    disjunction(negate(P), R),
    disjunction(conjunction(P, Q), R),
)

st_formula = st.sampled_from(FORMULAS)
st_nontrivial_formula = st.sampled_from(tuple(f for f in FORMULAS if f not in {TOP, BOTTOM}))
st_operator = st.sampled_from((ICMergeOperator.SIGMA, ICMergeOperator.GMAX))


@st.composite
def st_state(draw) -> SpohnEpistemicState:
    ranks = {
        world: draw(st.integers(min_value=0, max_value=4))
        for world in BeliefSet.all_worlds(ALPHABET)
    }
    return SpohnEpistemicState.from_ranks(ALPHABET, ranks)


@st.composite
def st_consistent_state(draw) -> SpohnEpistemicState:
    state = draw(st_state())
    assume(state.belief_set.is_consistent)
    return state


@st.composite
def st_profile(draw) -> tuple[Formula, ...]:
    formulas = draw(st.lists(st_formula, min_size=1, max_size=4))
    return tuple(formulas)


def _belief(formula: Formula) -> BeliefSet:
    return BeliefSet.from_formula(ALPHABET, formula)


def _is_tautology(formula: Formula) -> bool:
    return _belief(formula).models == BeliefSet.all_worlds(ALPHABET)


@pytest.mark.property
@given(st_formula, st_formula)
@settings(deadline=None)
def test_agm_1985_cn_is_inclusive_monotonic_and_idempotent(a: Formula, b: Formula) -> None:
    base = _belief(a)
    stronger = BeliefSet.from_formula(ALPHABET, conjunction(a, b))

    assert base.entails(a)
    assert base.cn().equivalent(base.cn().cn())
    assert theory_subset(base, stronger) or theory_subset(stronger, base)
    if theory_subset(base, stronger):
        assert stronger.models.issubset(base.models)


@pytest.mark.property
@given(st_consistent_state(), st_formula, st_formula)
@settings(deadline=None)
def test_alchourron_gardenfors_makinson_1985_revision_k_star_postulates(
    state: SpohnEpistemicState,
    a: Formula,
    b: Formula,
) -> None:
    assume(_belief(a).is_consistent)
    result = revise(state, a)
    expansion = expand(state.belief_set, a)

    assert result.belief_set.entails(a)
    assert theory_subset(result.belief_set, expansion)
    if not state.belief_set.entails(negate(a)):
        assert result.belief_set.equivalent(expansion)
    assert result.belief_set.is_consistent
    assert result.trace.provenance is not None
    assert result.trace.pre_image_fingerprint == state.belief_set.fingerprint()

    equivalent_input = conjunction(a, TOP)
    assert equivalent(a, equivalent_input, alphabet=ALPHABET)
    assert revise(state, a).belief_set.equivalent(revise(state, equivalent_input).belief_set)

    conjunction_result = revise(state, conjunction(a, b)).belief_set
    revise_then_expand = expand(revise(state, a).belief_set, b)
    assert theory_subset(conjunction_result, revise_then_expand)
    if not revise(state, a).belief_set.entails(negate(b)):
        assert theory_subset(revise_then_expand, conjunction_result)


@pytest.mark.property
@given(st_consistent_state(), st_nontrivial_formula)
@settings(deadline=None)
def test_alchourron_gardenfors_makinson_1985_contraction_and_harper_identity(
    state: SpohnEpistemicState,
    a: Formula,
) -> None:
    contracted = full_meet_contract(state, a)

    assert theory_subset(contracted.belief_set, state.belief_set)
    if not state.belief_set.entails(a):
        assert contracted.belief_set.equivalent(state.belief_set)
    if not _is_tautology(a):
        assert not contracted.belief_set.entails(a)

    recovered = expand(contracted.belief_set, a)
    assert theory_subset(state.belief_set, recovered)

    harper = state.belief_set.intersection_theory(revise(state, negate(a)).belief_set)
    assert contracted.belief_set.equivalent(harper)


@pytest.mark.property
@given(st_consistent_state(), st_formula, st_formula)
@settings(deadline=None)
def test_darwiche_pearl_1997_c1_c4_for_spohn_bullet_revision(
    state: SpohnEpistemicState,
    mu: Formula,
    alpha: Formula,
) -> None:
    assume(_belief(mu).is_consistent)
    assume(_belief(alpha).is_consistent)

    after_mu_then_alpha = revise(revise(state, mu).state, alpha).belief_set
    after_alpha = revise(state, alpha).belief_set

    if _belief(alpha).entails(mu):
        assert after_mu_then_alpha.equivalent(after_alpha)
    if _belief(alpha).entails(negate(mu)):
        assert after_mu_then_alpha.equivalent(after_alpha)
    if after_alpha.entails(mu):
        assert after_mu_then_alpha.entails(mu)
    if not after_alpha.entails(negate(mu)):
        assert not after_mu_then_alpha.entails(negate(mu))


@pytest.mark.property
@given(st_consistent_state(), st_formula, st_formula, st_formula)
@settings(deadline=None)
def test_gardenfors_makinson_1988_epistemic_entrenchment_ee1_ee5(
    state: SpohnEpistemicState,
    a: Formula,
    b: Formula,
    c: Formula,
) -> None:
    entrenchment = EpistemicEntrenchment.from_state(state)

    if entrenchment.leq(a, b) and entrenchment.leq(b, c):
        assert entrenchment.leq(a, c)
    if _belief(a).entails(b):
        assert entrenchment.leq(a, b)
    assert entrenchment.leq(a, conjunction(a, b)) or entrenchment.leq(b, conjunction(a, b))

    if state.belief_set.is_consistent and not state.belief_set.entails(a):
        assert all(entrenchment.leq(a, candidate) for candidate in FORMULAS)

    if all(entrenchment.leq(candidate, a) for candidate in FORMULAS):
        assert _is_tautology(a)


@pytest.mark.property
@given(st_profile(), st_formula, st_operator)
@settings(deadline=None)
def test_konieczny_pino_perez_2002_ic0_ic3_and_ic7_ic8(
    profile: tuple[Formula, ...],
    mu: Formula,
    operator: ICMergeOperator,
) -> None:
    assume(_belief(mu).is_consistent)

    result = merge_belief_profile(ALPHABET, profile, mu, operator=operator)
    assert result.belief_set.entails(mu)
    assert result.belief_set.is_consistent

    profile_conjunction = conjunction(*profile)
    if _belief(conjunction(profile_conjunction, mu)).is_consistent:
        assert result.belief_set.equivalent(_belief(conjunction(profile_conjunction, mu)))

    syntactic_variant = tuple(conjunction(item, TOP) for item in profile)
    assert result.belief_set.equivalent(
        merge_belief_profile(ALPHABET, syntactic_variant, mu, operator=operator).belief_set
    )

    tighter_mu = conjunction(mu, P)
    assume(_belief(tighter_mu).is_consistent)
    loose = result.belief_set
    tight = merge_belief_profile(ALPHABET, profile, tighter_mu, operator=operator).belief_set
    assert theory_subset(tight, expand(loose, P))
    if expand(loose, P).is_consistent:
        assert theory_subset(loose, tight)


@pytest.mark.property
@given(st_profile(), st_profile(), st_formula, st_operator)
@settings(deadline=None)
def test_konieczny_pino_perez_2002_ic5_ic6_profile_decomposition(
    left: tuple[Formula, ...],
    right: tuple[Formula, ...],
    mu: Formula,
    operator: ICMergeOperator,
) -> None:
    assume(_belief(mu).is_consistent)

    left_result = merge_belief_profile(ALPHABET, left, mu, operator=operator).belief_set
    right_result = merge_belief_profile(ALPHABET, right, mu, operator=operator).belief_set
    combined = merge_belief_profile(ALPHABET, left + right, mu, operator=operator).belief_set
    left_aligned = left_result.with_alphabet(left_result.alphabet | right_result.alphabet)
    right_aligned = right_result.with_alphabet(left_result.alphabet | right_result.alphabet)
    intersection = BeliefSet(
        left_aligned.alphabet,
        left_aligned.models & right_aligned.models,
    )

    assert theory_subset(combined, intersection)
    if intersection.is_consistent:
        assert theory_subset(intersection, combined)
