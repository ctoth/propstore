"""Semiring support contract tests for CKR justifiable exceptions."""

from __future__ import annotations

from propstore.defeasibility import (
    DecidabilityStatus,
    JustifiableException,
    LiftingRuleSupport,
    build_exception_defeat,
    exception_defeat_is_live,
    exception_is_applied,
    exception_live_support,
    lift_exception,
)
from propstore.provenance import (
    NogoodWitness,
    Provenance,
    ProvenanceNogood,
    ProvenancePolynomial,
    ProvenanceStatus,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    boolean_presence,
    live,
    why_provenance,
)


def _support(*variables: SourceVariableId, quality: SupportQuality = SupportQuality.EXACT) -> SupportEvidence:
    polynomial = ProvenancePolynomial.one()
    for variable in variables:
        polynomial = polynomial * ProvenancePolynomial.variable(variable)
    return SupportEvidence(polynomial, quality)


def _exception(
    *,
    support: SupportEvidence,
    justification_claims: tuple[str, ...] = ("claim:justification",),
) -> JustifiableException:
    return JustifiableException(
        target_claim="claim:generalization",
        exception_pattern="age > 70",
        justification_claims=justification_claims,
        context="ctx:trial",
        support=support,
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def _nogood(*variables: SourceVariableId) -> ProvenanceNogood:
    return ProvenanceNogood(
        frozenset(variables),
        NogoodWitness("z3", "solver conflict"),
        Provenance(status=ProvenanceStatus.MEASURED, witnesses=()),
    )


def test_unsupported_exception_has_zero_live_support_and_is_not_applied() -> None:
    source = SourceVariableId("ps:source:claim:exception")
    exception = _exception(
        support=_support(source),
        justification_claims=(),
    )

    assert exception_live_support(exception).polynomial == ProvenancePolynomial.zero()
    assert not exception_is_applied(exception)


def test_lifted_exception_support_multiplies_by_lifting_rule_support() -> None:
    exception_source = SourceVariableId("ps:source:claim:exception")
    lifting_source = SourceVariableId("ps:source:lifting_rule:trial-to-clinic")
    exception = _exception(support=_support(exception_source))
    lifting_rule = LiftingRuleSupport(
        source_context="ctx:trial",
        target_context="ctx:clinic",
        support=_support(lifting_source),
    )

    lifted = lift_exception(exception, lifting_rule)

    assert lifted.context == "ctx:clinic"
    assert lifted.support.polynomial == (
        ProvenancePolynomial.variable(exception_source)
        * ProvenancePolynomial.variable(lifting_source)
    )
    assert lifted.support.quality is SupportQuality.EXACT


def test_solver_nogood_kills_exception_support_without_deleting_exception() -> None:
    source = SourceVariableId("ps:source:claim:exception")
    exception = _exception(support=_support(source))
    defeat = build_exception_defeat(
        "use:generalization",
        exception,
        solver_witness=NogoodWitness("z3", "conflicting instance"),
        nogoods=(_nogood(source),),
    )

    assert defeat.exception is exception
    assert defeat.support.polynomial == ProvenancePolynomial.zero()
    assert not exception_defeat_is_live(defeat)


def test_boolean_projection_matches_live_why_provenance_nonempty() -> None:
    source = SourceVariableId("ps:source:claim:exception")
    exception = _exception(support=_support(source))
    defeat = build_exception_defeat("use:generalization", exception)
    live_support = live(defeat.support.polynomial, ())

    assert boolean_presence(live_support, {source}) is True
    assert exception_defeat_is_live(defeat) == bool(why_provenance(live_support))


def test_support_quality_is_preserved_across_exception_defeat() -> None:
    source = SourceVariableId("ps:source:claim:exception")
    exception = _exception(
        support=_support(source, quality=SupportQuality.SEMANTIC_COMPATIBLE),
    )

    defeat = build_exception_defeat("use:generalization", exception)

    assert defeat.support.quality is SupportQuality.SEMANTIC_COMPATIBLE
