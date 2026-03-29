"""Tests for exact merge operators over tiny argumentation frameworks."""
from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from propstore.dung import ArgumentationFramework
from propstore.repo.paf_merge import (
    consensual_expand,
    leximax_merge_frameworks,
    max_merge_frameworks,
    sum_merge_frameworks,
)


PAIR_SPACE = [("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")]
st_attack_pairs = st.sets(st.sampled_from(PAIR_SPACE), max_size=len(PAIR_SPACE))


def _af(arguments: set[str], attacks: set[tuple[str, str]]) -> ArgumentationFramework:
    return ArgumentationFramework(
        arguments=frozenset(arguments),
        defeats=frozenset(attacks),
        attacks=frozenset(attacks),
    )


def test_consensual_expand_preserves_in_scope_pairs_and_marks_out_of_scope_as_ignorance():
    af = _af({"A"}, {("A", "A")})

    expanded = consensual_expand(af, frozenset({"A", "B"}))

    assert ("A", "A") in expanded.attacks
    assert ("A", "B") in expanded.ignorance
    assert ("B", "A") in expanded.ignorance
    assert ("B", "B") in expanded.ignorance


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(attacks=st_attack_pairs)
def test_sum_merge_unanimity(attacks: set[tuple[str, str]]):
    framework = _af({"A", "B"}, attacks)

    result = sum_merge_frameworks({"left": framework, "right": framework})

    assert result == [framework]


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(left_attacks=st_attack_pairs, right_attacks=st_attack_pairs)
def test_sum_merge_profile_order_invariant(
    left_attacks: set[tuple[str, str]],
    right_attacks: set[tuple[str, str]],
):
    left = _af({"A", "B"}, left_attacks)
    right = _af({"A", "B"}, right_attacks)

    forward = sum_merge_frameworks({"left": left, "right": right})
    reverse = sum_merge_frameworks({"right": right, "left": left})

    assert forward == reverse


def test_sum_merge_matches_majority_profile_on_shared_universe():
    left = _af({"A", "B"}, {("A", "B")})
    middle = _af({"A", "B"}, {("A", "B")})
    right = _af({"A", "B"}, set())

    result = sum_merge_frameworks({"left": left, "middle": middle, "right": right})

    assert result == [_af({"A", "B"}, {("A", "B")})]


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(left_attacks=st_attack_pairs, right_attacks=st_attack_pairs)
def test_max_merge_profile_order_invariant(
    left_attacks: set[tuple[str, str]],
    right_attacks: set[tuple[str, str]],
):
    left = _af({"A", "B"}, left_attacks)
    right = _af({"A", "B"}, right_attacks)

    forward = max_merge_frameworks({"left": left, "right": right})
    reverse = max_merge_frameworks({"right": right, "left": left})

    assert forward == reverse


def test_leximax_refines_max_results():
    left = _af({"A", "B"}, {("A", "B")})
    middle = _af({"A", "B"}, {("B", "A")})
    right = _af({"A", "B"}, set())

    max_results = max_merge_frameworks({"left": left, "middle": middle, "right": right})
    leximax_results = leximax_merge_frameworks(
        {"left": left, "middle": middle, "right": right}
    )

    assert leximax_results
    assert set(leximax_results).issubset(set(max_results))
