"""Unit tests for the Phase 7a-world-C0 spine (``propstore.world.types``).

Covers the types this slice lands: the canonical :class:`RenderPolicy`
(round-trip + lifecycle ``admits``), ``apply_decision_criterion`` (the
Jøsang/Denoeux/Smets criteria), the value-status / resolution-strategy
coercers, ``IntegrityConstraint`` (de)serialization, ``QueryableAssumption``
coercion, and the substrate-boundary invariants (one canonical
``RenderPolicy``; ``MergeOperator`` owned by ``assignment_selection``; no
mirror of the merge value types; ``ClaimView`` landed by the journal-step bridge).
"""

from __future__ import annotations

import pytest

from assignment_selection import MergeOperator as PackageMergeOperator
from propstore.families.concepts import ConceptStatus
from propstore.world.types import (
    DecisionValueSource,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeOperator,
    ReasoningBackend,
    QueryableAssumption,
    RenderPolicy,
    ResolutionStrategy,
    ResolvedResult,
    ValueResult,
    ValueStatus,
    apply_decision_criterion,
    coerce_queryable_assumptions,
    coerce_value_status,
    normalize_merge_operator,
    normalize_queryable_cel,
)


# --- substrate-boundary / zen invariants ------------------------------------


def test_render_policy_is_one_canonical_type() -> None:
    from propstore.render import RenderPolicy as RenderRenderPolicy

    assert RenderRenderPolicy is RenderPolicy


def test_merge_operator_is_the_assignment_selection_package_type() -> None:
    assert MergeOperator is PackageMergeOperator


def test_world_types_does_not_redefine_merge_value_types() -> None:
    import propstore.world.types as world_types

    for redefined in (
        "MergeAssignment",
        "MergeSource",
        "MergeAssignmentScore",
        "AssignmentSelectionProblem",
        "AssignmentSelectionResult",
        "Constraint",
        "Problem",
        "Result",
    ):
        assert not hasattr(world_types, redefined), redefined


def test_claim_view_is_landed_by_journal_step_bridge() -> None:
    # The journal-step bridge (slice W0) lands ``ClaimView`` on the spine as the
    # return type of ``at_journal_step``. It carries the canonical charter
    # ``Claim`` — no ``ClaimRow`` mirror — plus a snapshot scope and optional
    # heavy-path stances/conflicts.
    from propstore.support_revision.state import RevisionScope
    from propstore.world.types import ClaimView

    fields = ClaimView.__dataclass_fields__
    assert set(fields) == {"claims", "scope", "bound", "stances", "conflicts"}
    empty = ClaimView(claims={}, scope=RevisionScope(bindings={}, context_id=None))
    assert empty.claim_ids() == set()
    assert empty.stances == ()
    assert empty.conflicts == ()


# --- RenderPolicy: round-trip + lifecycle admits ----------------------------


def test_render_policy_round_trips_through_the_document_codec() -> None:
    # The policy is persisted as a typed charter field, so the round trip that
    # matters is Quire's — there is no hand-written to_dict/from_dict pair to be
    # a fixed point of.
    from quire.documents import convert_document_value, to_document_builtins

    policy = RenderPolicy(
        strategy=ResolutionStrategy.RECENCY,
        reasoning_backend=ReasoningBackend.ASPIC,
        merge_operator=MergeOperator.GMAX,
        comparison="democratic",
        link="first",
        decision_criterion="hurwicz",
        pessimism_index=0.25,
        branch_filter=("main", "exp"),
        branch_weights={"main": 2.0},
        future_queryables=("x == 1",),
        future_limit=4,
        overrides={"c1": "claim:7"},
        concept_strategies={"c2": ResolutionStrategy.SAMPLE_SIZE},
        include_drafts=True,
        include_blocked=True,
        show_quarantined=True,
        integrity_constraints=(
            IntegrityConstraint(
                kind=IntegrityConstraintKind.RANGE,
                concept_ids=("c1",),
                metadata={"min": 0.0, "max": 1.0},
            ),
        ),
    )

    restored = convert_document_value(
        to_document_builtins(policy), RenderPolicy, source="render policy"
    )

    assert restored == policy
    assert restored.strategy is ResolutionStrategy.RECENCY
    assert restored.merge_operator is MergeOperator.GMAX
    assert restored.concept_strategies["c2"] is ResolutionStrategy.SAMPLE_SIZE
    assert restored.integrity_constraints[0].kind is IntegrityConstraintKind.RANGE


def test_render_policy_normalizes_merge_operator_and_freezes_collections() -> None:
    policy = RenderPolicy(merge_operator="max", branch_filter=["a"], overrides={"c": "x"})
    assert policy.merge_operator is MergeOperator.MAX
    assert policy.branch_filter == ("a",)
    assert isinstance(policy.integrity_constraints, tuple)


@pytest.mark.parametrize(
    ("status", "include_drafts", "include_blocked", "expected"),
    [
        (ConceptStatus.AUTHORED, False, False, True),
        (ConceptStatus.DRAFT, False, False, False),
        (ConceptStatus.DRAFT, True, False, True),
        (ConceptStatus.BLOCKED, False, False, False),
        (ConceptStatus.BLOCKED, False, True, True),
    ],
)
def test_render_policy_admits_lifecycle_visibility(
    status: ConceptStatus,
    include_drafts: bool,
    include_blocked: bool,
    expected: bool,
) -> None:
    policy = RenderPolicy(include_drafts=include_drafts, include_blocked=include_blocked)
    assert policy.admits(status) is expected


# --- decision criteria ------------------------------------------------------


def test_apply_decision_criterion_pignistic() -> None:
    # Smets & Kennes 1994 (p.202): BetP(x) = b + u/2.
    result = apply_decision_criterion(0.6, 0.1, 0.3, 0.5, None, "pignistic")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(0.75)


def test_apply_decision_criterion_projected_probability() -> None:
    # Jøsang 2001 Def.6 (p.5): E(ω) = b + a·u.
    result = apply_decision_criterion(0.6, 0.1, 0.3, 0.5, None, "projected_probability")
    assert result.value == pytest.approx(0.75)


def test_apply_decision_criterion_bounds_and_hurwicz() -> None:
    assert apply_decision_criterion(0.6, 0.1, 0.3, 0.5, None, "lower_bound").value == pytest.approx(0.6)
    assert apply_decision_criterion(0.6, 0.1, 0.3, 0.5, None, "upper_bound").value == pytest.approx(0.9)
    # Denoeux 2019 (p.17): α·Bel + (1-α)·Pl, with Bel=0.6, Pl=0.9, α=0.5.
    assert apply_decision_criterion(
        0.6, 0.1, 0.3, 0.5, None, "hurwicz", pessimism_index=0.5
    ).value == pytest.approx(0.75)


def test_apply_decision_criterion_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown decision criterion"):
        apply_decision_criterion(0.6, 0.1, 0.3, 0.5, None, "bogus")


def test_apply_decision_criterion_no_data_is_honest() -> None:
    result = apply_decision_criterion(None, None, None, None, None)
    assert result.source is DecisionValueSource.NO_DATA
    assert result.value is None


# --- coercers ---------------------------------------------------------------


def test_coerce_value_status() -> None:
    assert coerce_value_status("conflicted") is ValueStatus.CONFLICTED
    assert coerce_value_status(ValueStatus.DETERMINED) is ValueStatus.DETERMINED
    with pytest.raises(ValueError):
        coerce_value_status("not_a_status")


def test_resolution_strategy_string_membership() -> None:
    assert ResolutionStrategy("assignment_selection_merge") is ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE


def test_normalize_merge_operator() -> None:
    assert normalize_merge_operator("sigma") is MergeOperator.SIGMA
    assert normalize_merge_operator(MergeOperator.GMAX) is MergeOperator.GMAX
    with pytest.raises(ValueError, match="Unknown merge_operator"):
        normalize_merge_operator("nonsense")


def test_value_result_coerces_claims_to_tuple() -> None:
    result = ValueResult(concept_id="c1", status="determined", claims=[])
    assert isinstance(result.claims, tuple)
    assert result.status is ValueStatus.DETERMINED


def test_resolved_result_coerces_claims_to_tuple() -> None:
    result = ResolvedResult(concept_id="c1", status=ValueStatus.RESOLVED)
    assert isinstance(result.claims, tuple)


# --- IntegrityConstraint ----------------------------------------------------


def test_integrity_constraint_requires_concept_ids() -> None:
    with pytest.raises(ValueError, match="at least one concept id"):
        IntegrityConstraint(kind=IntegrityConstraintKind.RANGE, concept_ids=())


def test_integrity_constraint_rejects_duplicate_concept_ids() -> None:
    with pytest.raises(ValueError, match="duplicate concept ids"):
        IntegrityConstraint(kind=IntegrityConstraintKind.RANGE, concept_ids=("c1", "c1"))


def test_custom_integrity_constraint_requires_a_callable_predicate() -> None:
    with pytest.raises(TypeError, match="requires callable"):
        IntegrityConstraint(
            kind=IntegrityConstraintKind.CUSTOM,
            concept_ids=("c1",),
            metadata={},
        )


# --- QueryableAssumption ----------------------------------------------------


def test_normalize_queryable_cel_equality_and_assignment_forms() -> None:
    assert "==" in str(normalize_queryable_cel("color=red"))
    assert str(normalize_queryable_cel("x == 1")) == "x == 1"


def test_queryable_assumption_from_cel_is_deterministic() -> None:
    first = QueryableAssumption.from_cel("x == 1")
    second = QueryableAssumption.from_cel("x == 1")
    assert first == second


def test_coerce_queryable_assumptions_dedups_and_sorts() -> None:
    coerced = coerce_queryable_assumptions(["x == 1", "x == 1", QueryableAssumption.from_cel("y == 2")])
    assert len(coerced) == 2
    assert all(isinstance(item, QueryableAssumption) for item in coerced)
    # coerce_queryable_assumptions returns the deduped set ordered by (cel, id).
    cels = [str(item.cel) for item in coerced]
    assert cels == sorted(cels)
