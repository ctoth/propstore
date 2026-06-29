"""Phase 3 claim-type contracts + the claim-validate workflow.

Ports the reference claim-type-contract spec (PARAMETER specifics, the shared
narrative-type shape, full runtime coverage) and proves the validate workflow
delegates sympy generation to human-to-sympy while never aborting.
"""

from __future__ import annotations

from propstore.claim_contracts import (
    ClaimConceptLinkRole,
    ClaimSemanticCheck,
    SympyGenerationCheck,
    claim_type_contract_for,
    iter_claim_type_contracts,
    validate_claim,
)
from propstore.families.claims import Claim, ClaimType


def test_parameter_contract_shape() -> None:
    contract = claim_type_contract_for(ClaimType.PARAMETER)
    assert contract is not None
    assert contract.required_fields == ("output_concept",)
    assert contract.value_group is not None
    assert contract.unit_policy is not None
    assert contract.unit_policy.required is True
    assert contract.unit_policy.dimensionless_default_unit == "1"
    assert contract.unit_policy.form_concept_field == "output_concept"
    assert all(isinstance(check, ClaimSemanticCheck) for check in contract.semantic_checks)
    output_links = [
        link for link in contract.concept_links if link.role is ClaimConceptLinkRole.OUTPUT
    ]
    assert len(output_links) == 1


def test_narrative_types_share_one_contract_shape() -> None:
    types = [
        ClaimType.OBSERVATION,
        ClaimType.MECHANISM,
        ClaimType.COMPARISON,
        ClaimType.LIMITATION,
    ]
    contracts = [claim_type_contract_for(t) for t in types]
    assert all(c is not None for c in contracts)
    shapes = {
        (c.required_fields, c.nonempty_fields, c.concept_links)
        for c in contracts
        if c is not None
    }
    assert len(shapes) == 1


def test_contracts_cover_exactly_the_runtime_claim_types() -> None:
    covered = {c.claim_type for c in iter_claim_type_contracts()}
    runtime = {t for t in ClaimType if t is not ClaimType.UNKNOWN}
    assert covered == runtime
    assert ClaimType.UNKNOWN not in covered


def test_unknown_type_has_no_contract() -> None:
    assert claim_type_contract_for(ClaimType.UNKNOWN) is None
    assert claim_type_contract_for(None) is None


def test_validate_parameter_reports_missing_required_field() -> None:
    report = validate_claim(Claim(claim_id="c1", claim_type=ClaimType.PARAMETER))
    fields = {d.field for d in report.diagnostics}
    assert "output_concept" in fields


def test_validate_equation_generates_sympy_via_human_to_sympy() -> None:
    claim = Claim(claim_id="c1", claim_type=ClaimType.EQUATION, expression="x + z")
    report = validate_claim(claim)
    assert report.sympy_generated is not None
    assert report.sympy_error is None
    # The dimensional check is declared but deferred to a later phase, explicitly.
    assert "DimensionalConsistencyCheck" in report.deferred_checks


def test_validate_is_non_committal_on_bad_expression() -> None:
    claim = Claim(claim_id="c1", claim_type=ClaimType.EQUATION, expression="x +")
    report = validate_claim(claim)
    # A bad expression is diagnosed, never raised.
    assert report.sympy_error is not None
    assert any(d.field == "expression" for d in report.diagnostics)


def test_sympy_check_is_a_semantic_check() -> None:
    assert issubclass(SympyGenerationCheck, ClaimSemanticCheck)
