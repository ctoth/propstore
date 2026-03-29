"""Tests for branch-aware reasoning over the formal merge object."""
from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from propstore.core.labels import AssumptionRef, EnvironmentKey, NogoodSet
from propstore.repo.branch_reasoning import (
    branch_nogoods_from_merge,
    inject_branch_stances,
    make_branch_assumption,
)
from propstore.repo.merge_classifier import MergeArgument, RepoMergeFramework
from propstore.repo.merge_framework import PartialArgumentationFramework


st_assumption_kind = st.sampled_from(["binding", "context", "branch"])
st_assumption_id = st.from_regex(r"[a-z][a-z0-9_]{2,15}", fullmatch=True)
st_assumption_ref = st.builds(
    AssumptionRef,
    assumption_id=st_assumption_id,
    kind=st_assumption_kind,
    source=st_assumption_id,
    cel=st.just("true"),
)
st_env_key = st.lists(st_assumption_id, min_size=1, max_size=5).map(
    lambda ids: EnvironmentKey(tuple(sorted(set(ids))))
)
st_nogood_set = st.lists(st_env_key, min_size=0, max_size=3).map(
    lambda keys: NogoodSet(tuple(keys))
)


def _argument(claim_id: str, branch: str) -> MergeArgument:
    return MergeArgument(
        claim_id=claim_id,
        canonical_claim_id="claim_shared",
        concept_id="concept_x",
        claim={
            "id": claim_id,
            "type": "observation",
            "statement": claim_id,
            "concepts": ["concept_x"],
            "provenance": {"paper": "test"},
        },
        branch_origins=(branch,),
    )


def _merge_with_relations(
    *,
    attacks: set[tuple[str, str]],
    ignorance: set[tuple[str, str]],
) -> RepoMergeFramework:
    left = _argument("claim_shared__master", "master")
    right = _argument("claim_shared__paper_test", "paper/test")
    arguments = (left, right)
    framework = PartialArgumentationFramework(
        arguments={argument.claim_id for argument in arguments},
        attacks=attacks,
        ignorance=ignorance,
        non_attacks={
            (a.claim_id, b.claim_id)
            for a in arguments
            for b in arguments
        }
        - attacks
        - ignorance,
    )
    return RepoMergeFramework(
        branch_a="master",
        branch_b="paper/test",
        arguments=arguments,
        framework=framework,
    )


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(ref=st_assumption_ref)
def test_branch_assumption_ref_valid(ref: AssumptionRef) -> None:
    if ref.kind != "branch":
        return
    cache = {ref: True}
    assert cache[ref] is True
    other = AssumptionRef(
        assumption_id="zzz_other",
        kind="binding",
        source="other",
        cel="true",
    )
    assert len(sorted([ref, other])) == 2


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(a=st_env_key, b=st_env_key)
def test_environment_key_union_commutative(a: EnvironmentKey, b: EnvironmentKey) -> None:
    assert a.union(b) == b.union(a)


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(a=st_env_key, b=st_env_key, c=st_env_key)
def test_environment_key_union_associative(
    a: EnvironmentKey,
    b: EnvironmentKey,
    c: EnvironmentKey,
) -> None:
    assert a.union(b).union(c) == a.union(b.union(c))


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(nogood_env=st_env_key, extra_ids=st.lists(st_assumption_id, min_size=0, max_size=3))
def test_nogood_monotonicity(
    nogood_env: EnvironmentKey,
    extra_ids: list[str],
) -> None:
    nogoods = NogoodSet((nogood_env,))
    assert nogoods.excludes(nogood_env)
    superset_ids = tuple(sorted(set(nogood_env.assumption_ids + tuple(extra_ids))))
    assert nogoods.excludes(EnvironmentKey(superset_ids))


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(nogoods=st_nogood_set, new_env=st_env_key)
def test_adding_nogood_reduces_consistent_envs(
    nogoods: NogoodSet,
    new_env: EnvironmentKey,
) -> None:
    new_nogoods = NogoodSet(nogoods.environments + (new_env,))
    test_envs = [
        EnvironmentKey(("a",)),
        EnvironmentKey(("b",)),
        EnvironmentKey(("a", "b")),
        EnvironmentKey(("a", "b", "c")),
        new_env,
    ]
    for environment in test_envs:
        if nogoods.excludes(environment):
            assert new_nogoods.excludes(environment)


def test_make_branch_assumption() -> None:
    ref = make_branch_assumption("paper/test")
    assert ref.kind == "branch"
    assert ref.source == "paper/test"
    assert "branch" in ref.cel


def test_branch_nogoods_from_mutual_attack() -> None:
    merge = _merge_with_relations(
        attacks={
            ("claim_shared__master", "claim_shared__paper_test"),
            ("claim_shared__paper_test", "claim_shared__master"),
        },
        ignorance=set(),
    )

    nogoods = branch_nogoods_from_merge(merge)
    left_ref = make_branch_assumption("master")
    right_ref = make_branch_assumption("paper/test")
    assert nogoods.excludes(
        EnvironmentKey(tuple(sorted([left_ref.assumption_id, right_ref.assumption_id])))
    )


def test_branch_nogoods_skip_ignorance_and_one_way_attack() -> None:
    ignorant = _merge_with_relations(attacks=set(), ignorance={
        ("claim_shared__master", "claim_shared__paper_test"),
        ("claim_shared__paper_test", "claim_shared__master"),
    })
    one_way = _merge_with_relations(
        attacks={("claim_shared__master", "claim_shared__paper_test")},
        ignorance=set(),
    )

    assert branch_nogoods_from_merge(ignorant) == NogoodSet(())
    assert branch_nogoods_from_merge(one_way) == NogoodSet(())


def test_inject_branch_stances_from_attacks() -> None:
    merge = _merge_with_relations(
        attacks={
            ("claim_shared__master", "claim_shared__paper_test"),
            ("claim_shared__paper_test", "claim_shared__master"),
        },
        ignorance=set(),
    )

    stances = inject_branch_stances(merge)
    assert len(stances) == 2
    assert {stance["stance_type"] for stance in stances} == {"contradicts"}


def test_inject_branch_stances_skips_ignorance() -> None:
    merge = _merge_with_relations(attacks=set(), ignorance={
        ("claim_shared__master", "claim_shared__paper_test"),
        ("claim_shared__paper_test", "claim_shared__master"),
    })
    assert inject_branch_stances(merge) == []


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(include_reverse=st.booleans())
def test_inject_branch_stances_count_matches_attack_count(include_reverse: bool) -> None:
    attacks = {("claim_shared__master", "claim_shared__paper_test")}
    if include_reverse:
        attacks.add(("claim_shared__paper_test", "claim_shared__master"))
    merge = _merge_with_relations(attacks=attacks, ignorance=set())
    assert len(inject_branch_stances(merge)) == len(attacks)
