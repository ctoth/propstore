"""ASPIC+ boundary tests for CKR-derived exception defeats."""

from __future__ import annotations

from argumentation.aspic import conc
from propstore.aspic_bridge import build_bridge_csaf
from propstore.core.justifications import CanonicalJustification
from propstore.defeasibility import (
    ClaimApplicability,
    ContextualClaimUse,
    DecidabilityStatus,
    JustifiableException,
    apply_exception_defeats_to_csaf,
    evaluate_contextual_claim,
)
from argumentation.dung import complete_extensions, conflict_free, grounded_extension
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


def _support(variable: str) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId(variable)),
        SupportQuality.EXACT,
    )


def _exception() -> JustifiableException:
    return JustifiableException(
        target_claim="claim:target",
        exception_pattern="true",
        justification_claims=("claim:exception-justification",),
        context="ctx:trial",
        support=_support("ps:source:exception"),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def _csaf():
    claims = [
        _claim("claim:target"),
        _claim("claim:exception-justification"),
    ]
    return build_bridge_csaf(
        claims,
        [_reported("claim:target"), _reported("claim:exception-justification")],
        [],
        bundle=GroundedRulesBundle.empty(),
    )


def _concludes_claim(arg, claim_id: str) -> bool:
    atom = conc(arg).atom
    return atom.predicate == "ist" and atom.arguments[-1:] == (claim_id,)


def test_exception_defeat_adds_justification_argument_defeat_to_csaf() -> None:
    csaf = _csaf()
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"),
        (_exception(),),
    )

    integrated = apply_exception_defeats_to_csaf(csaf, (result,))

    assert result.applicability is ClaimApplicability.EXCEPTED
    attacker_ids = {
        integrated.arg_to_id[arg]
        for arg in integrated.arguments
        if _concludes_claim(arg, "claim:exception-justification")
    }
    target_ids = {
        integrated.arg_to_id[arg]
        for arg in integrated.arguments
        if _concludes_claim(arg, "claim:target")
    }
    assert attacker_ids
    assert target_ids
    assert any(
        (attacker_id, target_id) in integrated.framework.defeats
        for attacker_id in attacker_ids
        for target_id in target_ids
    )


def test_exception_defeat_participates_in_dung_extension_computation() -> None:
    csaf = _csaf()
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"),
        (_exception(),),
    )

    integrated = apply_exception_defeats_to_csaf(csaf, (result,))
    grounded = grounded_extension(integrated.framework)

    target_ids = {
        integrated.arg_to_id[arg]
        for arg in integrated.arguments
        if _concludes_claim(arg, "claim:target")
    }
    attacker_ids = {
        integrated.arg_to_id[arg]
        for arg in integrated.arguments
        if _concludes_claim(arg, "claim:exception-justification")
    }
    assert attacker_ids <= grounded
    assert target_ids.isdisjoint(grounded)


def test_exception_augmented_framework_remains_attack_conflict_free() -> None:
    csaf = _csaf()
    result = evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"),
        (_exception(),),
    )

    integrated = apply_exception_defeats_to_csaf(csaf, (result,))

    assert integrated.framework.attacks is not None
    for extension in complete_extensions(integrated.framework):
        assert conflict_free(extension, integrated.framework.attacks)
