"""Phase 4 CKR satisfaction: ``ist(c, p)`` applicability under exceptions.

propstore composes condition-ir (CEL gate) and provenance-semiring (support)
directly. These prove the satisfaction verdict — HOLDS / EXCEPTED / UNKNOWN —
and that solver ``UNKNOWN`` / unbound patterns stay honest (never a fabricated
positive exception). The CKR -> Dung defeat injection at the ASPIC+ boundary is
Phase 5 (CSAF) and is not exercised here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from condition_ir import (
    CheckedCondition,
    ConceptInfo,
    ConditionSolver,
    KindType,
    SolverResult,
    SolverUnknown,
    SolverUnknownReason,
)
from provenance_semiring import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)

import propstore.claim_conditions as cc
from propstore.defeasibility import (
    CelBinding,
    CelScalar,
    ClaimApplicability,
    ContextualClaimUse,
    DecidabilityStatus,
    ExceptionPolicyIssueKind,
    JustifiableException,
    LiftingRuleSupport,
    evaluate_contextual_claim,
)


def _age_solver() -> ConditionSolver:
    registry = cc.condition_registry(
        [ConceptInfo(id="age", canonical_name="age", kind=KindType.QUANTITY)]
    )
    return ConditionSolver(registry)


def _support(name: str) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId(name)), SupportQuality.EXACT
    )


@dataclass(frozen=True)
class _TimeoutSolver:
    """A solver whose registry type-checks but whose verdict is always UNKNOWN."""

    inner: ConditionSolver

    @property
    def registry(self) -> Mapping[str, ConceptInfo]:
        return self.inner.registry

    def is_condition_satisfied_result(
        self, condition: CheckedCondition, bindings: Mapping[str, CelScalar]
    ) -> SolverResult:
        return SolverUnknown(SolverUnknownReason.TIMEOUT, "timeout")


def _exception(pattern: str, *, context: str = "ctx:trial") -> JustifiableException:
    return JustifiableException(
        target_claim="claim:dosage",
        exception_pattern=pattern,
        justification_claims=("claim:override",),
        context=context,
        support=_support("ps:exception"),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def test_selected_use_is_excepted_and_unselected_holds() -> None:
    solver = _age_solver()
    exception = _exception("age > 70")
    excepted = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:dosage", (CelBinding("age", 75),)),
        (exception,),
        solver=solver,
    )
    assert excepted.applicability is ClaimApplicability.EXCEPTED
    assert excepted.applied_exceptions == (exception,)
    assert len(excepted.defeats) == 1

    holds = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:dosage", (CelBinding("age", 60),)),
        (exception,),
        solver=solver,
    )
    assert holds.applicability is ClaimApplicability.HOLDS
    assert holds.applied_exceptions == ()


def test_lifting_rule_carries_exception_across_contexts() -> None:
    exception = _exception("true", context="ctx:trial")
    use = ContextualClaimUse("ctx:clinic", "claim:dosage")

    without_rule = evaluate_contextual_claim(use, (exception,))
    assert without_rule.applicability is ClaimApplicability.HOLDS

    rule = LiftingRuleSupport("ctx:trial", "ctx:clinic", _support("ps:lift"))
    with_rule = evaluate_contextual_claim(use, (exception,), lifting_rules=(rule,))
    assert with_rule.applicability is ClaimApplicability.EXCEPTED
    lifted = with_rule.applied_exceptions[0]
    assert lifted.context == "ctx:clinic"
    expected = ProvenancePolynomial.variable(
        SourceVariableId("ps:exception")
    ) * ProvenancePolynomial.variable(SourceVariableId("ps:lift"))
    assert lifted.support.polynomial == expected


def test_solver_unknown_is_incomplete_sound_not_excepted() -> None:
    solver = _TimeoutSolver(_age_solver())
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:dosage", (CelBinding("age", 75),)),
        (_exception("age > 70"),),
        solver=solver,
    )
    assert result.applicability is ClaimApplicability.UNKNOWN
    assert result.decidability_status is DecidabilityStatus.INCOMPLETE_SOUND
    assert result.applied_exceptions == ()
    assert result.defeats == ()


def test_unbound_pattern_variable_is_authoring_unbound() -> None:
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:dosage"),
        (_exception("age > 70"),),
        solver=_age_solver(),
    )
    assert result.applicability is ClaimApplicability.UNKNOWN
    assert result.decidability_status is DecidabilityStatus.AUTHORING_UNBOUND
    assert result.applied_exceptions == ()


def test_two_applicable_exceptions_raise_a_policy_issue_not_collapsed() -> None:
    first = _exception("true")
    second = _exception("true")
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:dosage"),
        (first, second),
    )
    assert result.applicability is ClaimApplicability.EXCEPTED
    assert result.applied_exceptions == (first, second)
    assert len(result.policy_issues) == 1
    issue = result.policy_issues[0]
    assert issue.kind is ExceptionPolicyIssueKind.MULTIPLE_APPLICABLE_EXCEPTIONS
    assert issue.exceptions == (first, second)
