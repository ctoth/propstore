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
        "statement": claim_id,
        "premise_kind": "ordinary",
    }


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _csaf_with_ckr_exception():
    claims = [
        _claim("claim:target"),
        _claim("claim:exception-justification"),
    ]
    csaf = build_bridge_csaf(
        claims,
        [_reported("claim:target"), _reported("claim:exception-justification")],
        [],
        bundle=GroundedRulesBundle.empty(),
    )
    support = SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId("ps:source:exception")),
        SupportQuality.EXACT,
    )
    exception = JustifiableException(
        target_claim="claim:target",
        exception_pattern="true",
        justification_claims=("claim:exception-justification",),
        context="ctx:trial",
        support=support,
        decidability_status=DecidabilityStatus.DECIDABLE,
    )
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"),
        (exception,),
    )
    return csaf, result


def test_ckr_exception_defeats_in_defeats_only_not_attacks() -> None:
    csaf, result = _csaf_with_ckr_exception()

    enriched = apply_exception_defeats_to_csaf(csaf, (result,))

    attacker_ids = {
        enriched.arg_to_id[arg]
        for arg in enriched.arguments
        if conc(arg).atom.predicate == "claim:exception-justification"
    }
    target_ids = {
        enriched.arg_to_id[arg]
        for arg in enriched.arguments
        if conc(arg).atom.predicate == "claim:target"
    }
    ckr_edges = {
        (attacker_id, target_id)
        for attacker_id in attacker_ids
        for target_id in target_ids
    }
    exception_edges = ckr_edges & enriched.framework.defeats

    assert exception_edges
    assert enriched.framework.attacks is not None
    assert exception_edges.isdisjoint(enriched.framework.attacks)
