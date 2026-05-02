from propstore.defeasibility import (
    CelBinding,
    ClaimApplicability,
    ContextualClaimUse,
    DecidabilityStatus,
    JustifiableException,
    evaluate_contextual_claim,
)
from propstore.provenance import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions.solver import SolverUnknown, SolverUnknownReason


def _support() -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId("ps:source:exception")),
        SupportQuality.EXACT,
    )


def _exception(pattern: str) -> JustifiableException:
    return JustifiableException(
        target_claim="claim:target",
        exception_pattern=pattern,
        justification_claims=("claim:exception",),
        context="ctx:trial",
        support=_support(),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def test_unbound_exception_pattern_is_distinct_from_solver_unknown() -> None:
    class UnknownSolver:
        @property
        def registry(self):
            return {
                "age": ConceptInfo(
                    id="age",
                    canonical_name="age",
                    kind=KindType.QUANTITY,
                )
            }

        def is_condition_satisfied_result(self, condition, bindings):
            return SolverUnknown(SolverUnknownReason.TIMEOUT, "test timeout")

    exception = _exception("age > 70")
    unbound_use = ContextualClaimUse("ctx:trial", "claim:target")
    solver_unknown_use = ContextualClaimUse(
        "ctx:trial",
        "claim:target",
        bindings=(CelBinding("age", 75),),
    )

    unbound = evaluate_contextual_claim(
        unbound_use,
        (exception,),
        solver=UnknownSolver(),
    )
    solver_unknown = evaluate_contextual_claim(
        solver_unknown_use,
        (exception,),
        solver=UnknownSolver(),
    )

    assert unbound.applicability is ClaimApplicability.UNKNOWN
    assert unbound.applied_exceptions == ()
    assert unbound.defeats == ()
    assert unbound.decidability_status.value == "authoring_unbound"
    assert solver_unknown.decidability_status is DecidabilityStatus.INCOMPLETE_SOUND
    assert unbound.decidability_status != solver_unknown.decidability_status
