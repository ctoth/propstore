"""Phase 3 claim-type contracts + the claim-validate workflow.

Ports the reference claim-type-contract spec (PARAMETER specifics, the shared
narrative-type shape, full runtime coverage) and proves the validate workflow
delegates sympy generation to human-to-sympy while never aborting.
"""

from __future__ import annotations

from condition_ir import ConceptInfo, KindType

from propstore.claim_contracts import (
    ClaimConceptLinkRole,
    ClaimSemanticCheck,
    SympyGenerationCheck,
    claim_type_contract_for,
    iter_claim_type_contracts,
    validate_claim,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.forms import FormDefinition


def test_parameter_contract_shape() -> None:
    contract = claim_type_contract_for(ClaimType.PARAMETER)
    assert contract is not None
    assert contract.required_fields == ("output_concept",)
    assert contract.value_group is not None
    assert contract.unit_policy is not None
    assert contract.unit_policy.required is True
    assert contract.unit_policy.dimensionless_default_unit == "1"
    assert contract.unit_policy.form_concept_field == "output_concept"
    assert all(
        isinstance(check, ClaimSemanticCheck) for check in contract.semantic_checks
    )
    output_links = [
        link
        for link in contract.concept_links
        if link.role is ClaimConceptLinkRole.OUTPUT
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


def test_validate_quantity_value_checks_type_and_bounds() -> None:
    form = FormDefinition(
        name="temperature",
        kind=KindType.QUANTITY,
        min_value=0.0,
        max_value=100.0,
    )
    report = validate_claim(
        Claim(
            claim_id="hot",
            claim_type=ClaimType.PARAMETER,
            output_concept="temperature",
            value=200.0,
        ),
        form=form,
    )
    assert any(d.field == "value" and "above" in d.message for d in report.diagnostics)

    wrong_type = validate_claim(
        Claim(
            claim_id="not-temperature",
            claim_type=ClaimType.PARAMETER,
            output_concept="temperature",
            value="hot",
        ),
        form=form,
    )
    assert any(
        d.field == "value" and "must be numeric" in d.message
        for d in wrong_type.diagnostics
    )


def test_validate_category_uses_closed_vocabulary_without_numeric_checks() -> None:
    form = FormDefinition(
        name="severity",
        kind=KindType.CATEGORY,
        min_value=0.0,
        max_value=1.0,
    )
    info = ConceptInfo(
        id="severity",
        canonical_name="severity",
        kind=KindType.CATEGORY,
        category_values=["low", "high"],
        category_extensible=False,
    )
    accepted = validate_claim(
        Claim(
            claim_id="known",
            claim_type=ClaimType.PARAMETER,
            output_concept="severity",
            value="low",
        ),
        form=form,
        concept_info=info,
    )
    assert not accepted.diagnostics

    rejected = validate_claim(
        Claim(
            claim_id="unknown",
            claim_type=ClaimType.PARAMETER,
            output_concept="severity",
            value="critical",
        ),
        form=form,
        concept_info=info,
    )
    assert any("closed category vocabulary" in d.message for d in rejected.diagnostics)


def test_validate_extensible_category_accepts_new_text() -> None:
    report = validate_claim(
        Claim(
            claim_id="new-category",
            claim_type=ClaimType.PARAMETER,
            output_concept="severity",
            value="critical",
        ),
        form=FormDefinition(name="severity", kind=KindType.CATEGORY),
        concept_info=ConceptInfo(
            id="severity",
            canonical_name="severity",
            kind=KindType.CATEGORY,
            category_values=["low", "high"],
            category_extensible=True,
        ),
    )
    assert not report.diagnostics


def test_validate_boolean_requires_bool_and_rejects_bounds() -> None:
    report = validate_claim(
        Claim(
            claim_id="text-bool",
            claim_type=ClaimType.PARAMETER,
            output_concept="enabled",
            value="true",
            lower_bound=0.0,
        ),
        form=FormDefinition(name="enabled", kind=KindType.BOOLEAN),
    )
    assert {d.field for d in report.diagnostics} == {"value", "lower_bound"}


def test_validate_structural_adds_no_scalar_policy() -> None:
    report = validate_claim(
        Claim(
            claim_id="structural",
            claim_type=ClaimType.PARAMETER,
            output_concept="structure",
            value="opaque",
            lower_bound=0.0,
        ),
        form=FormDefinition(name="structure", kind=KindType.STRUCTURAL),
    )
    assert not report.diagnostics
