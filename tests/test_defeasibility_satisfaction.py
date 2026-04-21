"""CKR-style contextual satisfaction tests for justifiable exceptions."""

from __future__ import annotations

from propstore.cel_checker import ConceptInfo, KindType
from propstore.defeasibility import (
    ClaimApplicability,
    ContextualClaimUse,
    CelBinding,
    DecidabilityStatus,
    JustifiableException,
    LiftingRuleSupport,
    evaluate_contextual_claim,
)
from propstore.provenance import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)
from propstore.z3_conditions import SolverUnknown, SolverUnknownReason, Z3ConditionSolver


def _support(*variables: SourceVariableId) -> SupportEvidence:
    polynomial = ProvenancePolynomial.one()
    for variable in variables:
        polynomial = polynomial * ProvenancePolynomial.variable(variable)
    return SupportEvidence(polynomial, SupportQuality.EXACT)


def _exception(
    *,
    pattern: str,
    context: str = "ctx:trial",
    target_claim: str = "claim:aspirin-primary-prevention",
    support: SupportEvidence | None = None,
    justification_claims: tuple[str, ...] = ("claim:bleeding-risk",),
) -> JustifiableException:
    return JustifiableException(
        target_claim=target_claim,
        exception_pattern=pattern,
        justification_claims=justification_claims,
        context=context,
        support=support or _support(SourceVariableId("ps:source:exception")),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def _age_solver() -> Z3ConditionSolver:
    return Z3ConditionSolver(
        {
            "age": ConceptInfo(
                id="concept:age",
                canonical_name="age",
                kind=KindType.QUANTITY,
            )
        }
    )


def test_justified_exception_applies_only_to_selected_instance() -> None:
    exception = _exception(pattern="age > 70")
    selected_use = ContextualClaimUse(
        context="ctx:trial",
        claim="claim:aspirin-primary-prevention",
        bindings=(CelBinding("age", 75),),
    )
    unselected_use = ContextualClaimUse(
        context="ctx:trial",
        claim="claim:aspirin-primary-prevention",
        bindings=(CelBinding("age", 60),),
    )

    selected = evaluate_contextual_claim(
        selected_use,
        (exception,),
        solver=_age_solver(),
    )
    unselected = evaluate_contextual_claim(
        unselected_use,
        (exception,),
        solver=_age_solver(),
    )

    assert selected.applicability is ClaimApplicability.EXCEPTED
    assert selected.applied_exceptions == (exception,)
    assert len(selected.defeats) == 1
    assert unselected.applicability is ClaimApplicability.HOLDS
    assert unselected.applied_exceptions == ()


def test_exception_lifts_iff_lifting_rule_licenses_target_context() -> None:
    exception_source = SourceVariableId("ps:source:exception")
    lifting_source = SourceVariableId("ps:source:lifting")
    exception = _exception(pattern="true", support=_support(exception_source))
    clinic_use = ContextualClaimUse(
        context="ctx:clinic",
        claim="claim:aspirin-primary-prevention",
    )
    lifting_rule = LiftingRuleSupport(
        source_context="ctx:trial",
        target_context="ctx:clinic",
        support=_support(lifting_source),
    )

    without_lift = evaluate_contextual_claim(clinic_use, (exception,))
    with_lift = evaluate_contextual_claim(
        clinic_use,
        (exception,),
        lifting_rules=(lifting_rule,),
    )

    assert without_lift.applicability is ClaimApplicability.HOLDS
    assert with_lift.applicability is ClaimApplicability.EXCEPTED
    assert with_lift.applied_exceptions[0].context == "ctx:clinic"
    assert with_lift.applied_exceptions[0].support.polynomial == (
        ProvenancePolynomial.variable(exception_source)
        * ProvenancePolynomial.variable(lifting_source)
    )


def test_solver_unknown_is_not_treated_as_an_exception() -> None:
    class UnknownSolver:
        def is_condition_satisfied_result(self, condition, bindings):
            return SolverUnknown(SolverUnknownReason.TIMEOUT, "test timeout")

    exception = _exception(pattern="age > 70")
    use = ContextualClaimUse(
        context="ctx:trial",
        claim="claim:aspirin-primary-prevention",
        bindings=(CelBinding("age", 75),),
    )

    result = evaluate_contextual_claim(use, (exception,), solver=UnknownSolver())

    assert result.applicability is ClaimApplicability.UNKNOWN
    assert result.decidability_status is DecidabilityStatus.INCOMPLETE_SOUND
    assert result.applied_exceptions == ()
    assert result.defeats == ()


def test_missing_binding_makes_pattern_authoring_unbound_not_applied() -> None:
    exception = _exception(pattern="age > 70")
    use = ContextualClaimUse(
        context="ctx:trial",
        claim="claim:aspirin-primary-prevention",
    )

    result = evaluate_contextual_claim(use, (exception,), solver=_age_solver())

    assert result.applicability is ClaimApplicability.UNKNOWN
    assert result.decidability_status is DecidabilityStatus.AUTHORING_UNBOUND
    assert result.applied_exceptions == ()


def test_multiple_applicable_exceptions_are_flagged_not_collapsed() -> None:
    first = _exception(
        pattern="true",
        support=_support(SourceVariableId("ps:source:exception:first")),
    )
    second = _exception(
        pattern="true",
        support=_support(SourceVariableId("ps:source:exception:second")),
        justification_claims=("claim:renal-risk",),
    )
    use = ContextualClaimUse(
        context="ctx:trial",
        claim="claim:aspirin-primary-prevention",
    )

    result = evaluate_contextual_claim(use, (first, second))

    assert result.applicability is ClaimApplicability.EXCEPTED
    assert result.applied_exceptions == (first, second)
    assert len(result.policy_issues) == 1
    assert result.policy_issues[0].exceptions == (first, second)
