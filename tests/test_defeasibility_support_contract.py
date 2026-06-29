"""Phase 4 CKR support contract: provenance-semiring liveness of exceptions.

These prove the non-commitment support algebra: an exception with no
justification has zero support; a nogood kills support WITHOUT deleting the
exception object; lifting multiplies support; defeat liveness is the why-provenance
of the live support. provenance-semiring owns every polynomial type — propstore
calls it directly.
"""

from __future__ import annotations

from provenance_semiring import (
    NogoodWitness,
    ProvenanceNogood,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    boolean_presence,
    live,
    why_provenance,
)

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


def _support(name: str, quality: SupportQuality = SupportQuality.EXACT) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId(name)), quality
    )


def _nogood(name: str) -> ProvenanceNogood:
    return ProvenanceNogood(
        frozenset({SourceVariableId(name)}), NogoodWitness("test", name)
    )


def _exception(
    *,
    justification_claims: tuple[str, ...],
    support: SupportEvidence,
    context: str = "ctx:trial",
) -> JustifiableException:
    return JustifiableException(
        target_claim="claim:dosage",
        exception_pattern="true",
        justification_claims=justification_claims,
        context=context,
        support=support,
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def test_exception_without_justification_has_zero_support() -> None:
    exception = _exception(justification_claims=(), support=_support("ps:exception"))
    assert exception_live_support(exception).polynomial == ProvenancePolynomial.zero()
    assert not exception_is_applied(exception)


def test_lift_exception_multiplies_support() -> None:
    exception = _exception(
        justification_claims=("claim:override",), support=_support("ps:exception")
    )
    rule = LiftingRuleSupport("ctx:trial", "ctx:clinic", _support("ps:lift"))
    lifted = lift_exception(exception, rule)
    assert lifted.context == "ctx:clinic"
    expected = ProvenancePolynomial.variable(
        SourceVariableId("ps:exception")
    ) * ProvenancePolynomial.variable(SourceVariableId("ps:lift"))
    assert lifted.support.polynomial == expected
    assert lifted.support.quality is SupportQuality.EXACT


def test_nogood_kills_support_but_keeps_the_exception() -> None:
    exception = _exception(
        justification_claims=("claim:override",), support=_support("ps:exception")
    )
    defeat = build_exception_defeat(
        "ist(ctx:trial, claim:dosage)",
        exception,
        nogoods=(_nogood("ps:exception"),),
    )
    assert defeat.exception is exception
    assert defeat.support.polynomial == ProvenancePolynomial.zero()
    assert not exception_defeat_is_live(defeat)


def test_live_defeat_reports_boolean_presence_and_why_provenance() -> None:
    exception = _exception(
        justification_claims=("claim:override",), support=_support("ps:exception")
    )
    defeat = build_exception_defeat("ist(ctx:trial, claim:dosage)", exception)
    live_support = live(defeat.support.polynomial, ())
    assert boolean_presence(live_support, {SourceVariableId("ps:exception")}) is True
    assert exception_defeat_is_live(defeat) == bool(why_provenance(live_support))


def test_build_exception_defeat_preserves_support_quality() -> None:
    exception = _exception(
        justification_claims=("claim:override",),
        support=_support("ps:exception", SupportQuality.SEMANTIC_COMPATIBLE),
    )
    defeat = build_exception_defeat("ist(ctx:trial, claim:dosage)", exception)
    assert defeat.support.quality is SupportQuality.SEMANTIC_COMPATIBLE
