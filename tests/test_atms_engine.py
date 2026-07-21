"""Charter-native tests for the ATMS engine and the BoundWorld pass-through.

These exercise ``propstore.world.atms.ATMSEngine`` over the in-memory charter
feed (``tests.atms_feed``): exact-support propagation, nogood pruning from
conflicts and from derived-value contradictions, bounded future replay,
stability/relevance/intervention analysis, and the explanation surface. The
reference suite's CLI / worldline / app-layer / sidecar paths are deferred to
their owning phases (see docs/rewrite/deferred-tests.md).
"""

from __future__ import annotations

import pytest

from propstore.core.labels import EnvironmentKey, make_environment_key
from propstore.world.atms import ATMSEngine, BudgetExhausted
from propstore.world.types import (
    ATMSNodeStatus,
    ATMSOutKind,
    QueryableAssumption,
    SupportQuality,
    ValueStatus,
)
from tests.atms_feed import (
    ClaimSpec,
    ConflictSpec,
    MicropubSpec,
    ParamSpec,
    assumption_id_for,
    build_bound,
)


def test_unconditional_claim_is_true_and_supported() -> None:
    bound = build_bound(claims=[ClaimSpec("c_a", "concept1", value=1.0)])
    status = bound.claim_status("c_a")
    assert status.status is ATMSNodeStatus.TRUE
    assert status.support_quality is SupportQuality.EXACT
    assert bound.atms_engine().supported_claim_ids("concept1") == {"c_a"}
    assert bound.atms_engine().supported_claim_ids("other") == set()


def test_conditional_claim_under_matching_binding_is_in_with_exact_label() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_b", "concept1", value=2.0, conditions=("x == 1",))],
        bindings={"x": 1},
    )
    status = bound.claim_status("c_b")
    assert status.status is ATMSNodeStatus.IN
    assert status.label is not None
    assert len(status.label.environments) == 1
    assert status.support_quality is SupportQuality.EXACT


def test_conditional_claim_without_binding_is_out_semantic_only() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_c", "concept1", value=2.0, conditions=("x == 1",))],
    )
    status = bound.claim_status("c_c")
    assert status.status is ATMSNodeStatus.OUT
    assert status.out_kind is ATMSOutKind.MISSING_SUPPORT
    assert status.support_quality is SupportQuality.SEMANTIC_COMPATIBLE


def test_value_of_attaches_merged_atms_label() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_b", "concept1", value=2.0, conditions=("x == 1",))],
        bindings={"x": 1},
    )
    result = bound.value_of("concept1")
    assert result.status is ValueStatus.DETERMINED
    assert result.label is not None
    assert result.label.environments


def test_conflict_between_joint_conditions_prunes_via_nogood() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("c1", "concept1", value=1.0, conditions=("a == 1",)),
            ClaimSpec("c2", "concept2", value=2.0, conditions=("b == 1",)),
            ClaimSpec("c3", "concept3", value=3.0, conditions=("a == 1", "b == 1")),
        ],
        conflicts=[ConflictSpec("concept1", "c1", "c2")],
        bindings={"a": 1, "b": 1},
    )
    engine = bound.atms_engine()
    nogood = make_environment_key(
        assumption_ids=(
            assumption_id_for(bound, "a == 1"),
            assumption_id_for(bound, "b == 1"),
        )
    )
    assert nogood in engine.nogoods.environments

    # c1 and c2 keep their singleton environments; only the joint c3 is pruned.
    assert bound.claim_status("c1").status is ATMSNodeStatus.IN
    assert bound.claim_status("c2").status is ATMSNodeStatus.IN
    c3 = bound.claim_status("c3")
    assert c3.status is ATMSNodeStatus.OUT
    assert c3.out_kind is ATMSOutKind.NOGOOD_PRUNED


def test_parameterization_materializes_derived_support() -> None:
    bound = build_bound(
        claims=[ClaimSpec("claim_a", "concept1", value=4.0, conditions=("a == 1",))],
        parameterizations=[
            ParamSpec("concept3", ("concept1",), "Eq(concept3, concept1)", "z=a")
        ],
        bindings={"a": 1},
    )
    derived = bound.derived_value("concept3")
    assert derived.status is ValueStatus.DERIVED
    assert derived.value == 4.0
    label = bound.atms_engine().derived_label("concept3", 4.0)
    assert label is not None
    assert label.environments


def test_derived_value_contradiction_is_conflicted_and_seeds_nogood() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("claim_a", "concept1", value=1.0, conditions=("a == 1",)),
            ClaimSpec("claim_b", "concept2", value=2.0, conditions=("b == 2",)),
        ],
        parameterizations=[
            ParamSpec("concept3", ("concept1",), "Eq(concept3, concept1)", "z=a"),
            ParamSpec("concept3", ("concept2",), "Eq(concept3, concept2)", "z=b"),
        ],
        bindings={"a": 1, "b": 2},
    )
    result = bound.derived_value("concept3")
    assert result.status is ValueStatus.CONFLICTED
    assert result.value is None
    nogood = make_environment_key(
        assumption_ids=(
            assumption_id_for(bound, "a == 1"),
            assumption_id_for(bound, "b == 2"),
        )
    )
    assert nogood in bound.atms_engine().nogoods.environments


def test_future_replay_shows_out_claim_could_become_in() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_c", "concept1", value=2.0, conditions=("x == 1",))],
    )
    report = bound.claim_future_statuses(
        "c_c",
        [QueryableAssumption.from_cel("x == 1")],
        limit=8,
    )
    assert report.current.status is ATMSNodeStatus.OUT
    assert report.could_become_in is True
    assert any(entry.status is ATMSNodeStatus.IN for entry in report.futures)


def test_stability_distinguishes_stable_and_unstable_claims() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("c_true", "concept0", value=1.0),
            ClaimSpec("c_cond", "concept1", value=2.0, conditions=("x == 1",)),
        ],
    )
    queryables = [QueryableAssumption.from_cel("x == 1")]
    assert bound.claim_is_stable("c_true", queryables, limit=8) is True
    assert bound.claim_is_stable("c_cond", queryables, limit=8) is False


def test_relevance_marks_the_flipping_queryable() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_cond", "concept1", value=2.0, conditions=("x == 1",))],
    )
    relevant = bound.claim_relevant_queryables(
        "c_cond",
        [
            QueryableAssumption.from_cel("x == 1"),
            QueryableAssumption.from_cel("y == 9"),
        ],
        limit=16,
    )
    assert "x == 1" in relevant
    assert "y == 9" not in relevant


def test_interventions_and_next_queryables_target_in() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_cond", "concept1", value=2.0, conditions=("x == 1",))],
    )
    queryables = [QueryableAssumption.from_cel("x == 1")]
    plans = bound.claim_interventions("c_cond", queryables, ATMSNodeStatus.IN, limit=8)
    assert plans
    assert all(plan.target_status is ATMSNodeStatus.IN for plan in plans)
    assert any("x == 1" in plan.queryable_cels for plan in plans)

    suggestions = bound.claim_next_queryables(
        "c_cond", queryables, ATMSNodeStatus.IN, limit=8
    )
    assert any(suggestion.queryable_cel == "x == 1" for suggestion in suggestions)


def test_explain_node_and_verify_labels() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_b", "concept1", value=2.0, conditions=("x == 1",))],
        bindings={"x": 1},
    )
    explanation = bound.explain_claim_support("c_b")
    assert explanation.status is ATMSNodeStatus.IN
    assert explanation.traces
    report = bound.verify_atms_labels()
    assert report.ok is True


def test_explain_nogood_returns_provenance() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("c1", "concept1", value=1.0, conditions=("a == 1",)),
            ClaimSpec("c2", "concept2", value=2.0, conditions=("b == 1",)),
        ],
        conflicts=[ConflictSpec("concept1", "c1", "c2")],
        bindings={"a": 1, "b": 1},
    )
    nogood = make_environment_key(
        assumption_ids=(
            assumption_id_for(bound, "a == 1"),
            assumption_id_for(bound, "b == 1"),
        )
    )
    detail = bound.explain_nogood(nogood)
    assert detail is not None
    assert detail.provenance
    assert detail.provenance[0].claim_a_id in {"c1", "c2"}


def test_claims_in_environment_lists_supported_assertions() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_b", "concept1", value=2.0, conditions=("x == 1",))],
        bindings={"x": 1},
    )
    node_id = bound.claim_status("c_b").node_id
    assert node_id.startswith("ps:assertion:")
    visible = bound.claims_in_environment(
        make_environment_key(assumption_ids=(assumption_id_for(bound, "x == 1"),))
    )
    assert node_id in visible


def test_micropublication_node_supported_when_claims_and_context_supported() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_ctx", "concept1", value=1.0, context_id="ctx1")],
        micropublications=[MicropubSpec("mp1", "ctx1", ("c_ctx",))],
    )
    engine = bound.atms_engine()
    assert "mp1" in engine.supported_micropub_ids()
    assert engine.micropub_label("mp1") is not None


def test_environment_context_serialisation_splits_assumption_and_context_ids() -> None:
    bound = build_bound(
        claims=[ClaimSpec("c_ctx", "concept1", value=1.0, context_id="ctx1")],
    )
    engine = bound.atms_engine()
    label = engine.claim_label("c_ctx")
    assert label is not None
    serialized = engine._serialize_label(label)
    assert serialized is not None
    assert serialized == [{"assumption_ids": [], "context_ids": ["ctx1"]}]


def test_future_budget_exhaustion_raises() -> None:
    # The claim depends on ``w == 5``, which none of the offered queryables can
    # supply, so its status never flips and the stability stream keeps drawing
    # future subsets until the budget is exhausted.
    bound = build_bound(
        claims=[ClaimSpec("c_cond", "concept1", value=2.0, conditions=("w == 5",))],
    )
    queryables = [
        QueryableAssumption.from_cel("x == 1"),
        QueryableAssumption.from_cel("y == 2"),
        QueryableAssumption.from_cel("z == 3"),
    ]
    with pytest.raises(BudgetExhausted):
        bound.claim_stability("c_cond", queryables, limit=1)


def test_argumentation_state_reports_supported_and_defeated() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("c_true", "concept0", value=1.0),
            ClaimSpec("c_out", "concept1", value=2.0, conditions=("x == 1",)),
        ],
    )
    state = bound.atms_engine().argumentation_state()
    assert state.backend == "atms"
    assert "c_true" in state.supported
    assert "c_out" in state.defeated


def test_engine_constructed_directly_from_bound_matches_pass_through() -> None:
    bound = build_bound(claims=[ClaimSpec("c_a", "concept1", value=1.0)])
    engine = ATMSEngine(bound)
    assert engine.supported_claim_ids() == bound.atms_engine().supported_claim_ids()


def test_coerce_environment_key_round_trips_assumption_ids() -> None:
    key = make_environment_key(assumption_ids=("asm-1", "asm-2"))
    assert isinstance(key, EnvironmentKey)
    assert ATMSEngine._coerce_environment_key(key) == key
