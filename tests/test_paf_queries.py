"""Tests for completion-based query semantics over partial frameworks."""
from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from propstore.repo.merge_framework import PartialArgumentationFramework
from propstore.repo.paf_queries import (
    credulously_accepted_arguments,
    skeptically_accepted_arguments,
)


PAIR_ORDER = [("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")]
st_states = st.lists(
    st.sampled_from(["attack", "ignorance", "non_attack"]),
    min_size=len(PAIR_ORDER),
    max_size=len(PAIR_ORDER),
)


def _example_paf() -> PartialArgumentationFramework:
    return PartialArgumentationFramework(
        arguments={"A", "B"},
        attacks={("A", "B")},
        ignorance={("B", "A")},
        non_attacks={("A", "A"), ("B", "B")},
    )


def test_grounded_skeptical_and_credulous_acceptance_follow_completions():
    paf = _example_paf()

    skeptical = skeptically_accepted_arguments(paf, semantics="grounded")
    credulous = credulously_accepted_arguments(paf, semantics="grounded")

    assert skeptical == frozenset()
    assert credulous == frozenset({"A"})


def test_single_completion_matches_ordinary_dung_query():
    paf = PartialArgumentationFramework(
        arguments={"A", "B"},
        attacks={("A", "B")},
        ignorance=set(),
        non_attacks={("A", "A"), ("B", "A"), ("B", "B")},
    )

    assert skeptically_accepted_arguments(paf, semantics="grounded") == frozenset({"A"})
    assert credulously_accepted_arguments(paf, semantics="grounded") == frozenset({"A"})


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(states=st_states)
def test_fixing_ignorance_grows_skeptical_and_shrinks_credulous(states: list[str]):
    attacks = set()
    ignorance = set()
    non_attacks = set()
    for pair, state in zip(PAIR_ORDER, states, strict=True):
        if state == "attack":
            attacks.add(pair)
        elif state == "ignorance":
            ignorance.add(pair)
        else:
            non_attacks.add(pair)

    paf = PartialArgumentationFramework(
        arguments={"A", "B"},
        attacks=attacks,
        ignorance=ignorance,
        non_attacks=non_attacks,
    )
    if not paf.ignorance:
        return

    fixed_pair = next(iter(sorted(paf.ignorance)))
    fixed_attack = PartialArgumentationFramework(
        arguments=paf.arguments,
        attacks=paf.attacks | {fixed_pair},
        ignorance=paf.ignorance - {fixed_pair},
        non_attacks=paf.non_attacks,
    )

    original_skeptical = skeptically_accepted_arguments(paf, semantics="grounded")
    fixed_skeptical = skeptically_accepted_arguments(fixed_attack, semantics="grounded")
    original_credulous = credulously_accepted_arguments(paf, semantics="grounded")
    fixed_credulous = credulously_accepted_arguments(fixed_attack, semantics="grounded")

    assert original_skeptical <= fixed_skeptical
    assert fixed_credulous <= original_credulous
