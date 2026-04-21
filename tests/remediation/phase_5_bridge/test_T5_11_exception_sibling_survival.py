import pytest
from argumentation.aspic import conc

from propstore.aspic_bridge import build_bridge_csaf
from propstore.core.justifications import CanonicalJustification
from propstore.defeasibility import (
    ContextualClaimUse,
    DecidabilityStatus,
    JustifiableException,
    apply_exception_defeats_to_csaf,
    evaluate_contextual_claim,
)
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.provenance import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)


def _claim(claim_id: str) -> dict[str, str]:
    return {
        "id": claim_id,
        "concept_id": f"concept:{claim_id}",
        "premise_kind": "ordinary",
    }


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _support(variable: str) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId(variable)),
        SupportQuality.EXACT,
    )


def _exception(justification_claim: str, variable: str) -> JustifiableException:
    return JustifiableException(
        target_claim="claim:target",
        exception_pattern="true",
        justification_claims=(justification_claim,),
        context="ctx:trial",
        support=_support(variable),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def test_zero_attacker_exception_does_not_suppress_sibling_exception_defeats() -> None:
    csaf = build_bridge_csaf(
        [_claim("claim:target"), _claim("claim:exception-justification")],
        [_reported("claim:target"), _reported("claim:exception-justification")],
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    missing_attacker = _exception("claim:missing-justification", "ps:source:missing")
    live_sibling = _exception("claim:exception-justification", "ps:source:sibling")
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"),
        (missing_attacker, live_sibling),
    )

    with pytest.warns(UserWarning, match="no ASPIC argument"):
        integrated = apply_exception_defeats_to_csaf(csaf, (result,))

    attacker_ids = {
        integrated.arg_to_id[argument]
        for argument in integrated.arguments
        if conc(argument).atom.predicate == "claim:exception-justification"
    }
    target_ids = {
        integrated.arg_to_id[argument]
        for argument in integrated.arguments
        if conc(argument).atom.predicate == "claim:target"
    }

    assert attacker_ids
    assert target_ids
    assert any(
        (attacker_id, target_id) in integrated.framework.defeats
        for attacker_id in attacker_ids
        for target_id in target_ids
    )
