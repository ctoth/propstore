from __future__ import annotations

from propstore.core.claim_concept_link_roles import ClaimConceptLinkRole
from propstore.families.claims.documents import (
    ClaimSemanticCheck,
    claim_type_contract_for,
    iter_claim_type_contracts,
)
from propstore.core.claim_types import ClaimType


def test_parameter_contract_declares_value_unit_and_concept_reference() -> None:
    contract = claim_type_contract_for(ClaimType.PARAMETER)

    assert contract is not None
    assert contract.required_fields == ("output_concept",)
    assert contract.value_group is not None
    assert contract.unit_policy is not None
    assert contract.unit_policy.required is True
    assert contract.unit_policy.dimensionless_default_unit == "1"
    assert contract.unit_policy.form_concept_field == "output_concept"
    assert all(
        issubclass(semantic_check, ClaimSemanticCheck)
        for semantic_check in contract.semantic_checks
    )
    assert [link.field for link in contract.concept_links] == ["output_concept"]
    assert [link.role for link in contract.concept_links] == [
        ClaimConceptLinkRole.OUTPUT
    ]


def test_observation_like_contracts_share_declared_shape() -> None:
    observation = claim_type_contract_for(ClaimType.OBSERVATION)

    assert observation is not None
    for claim_type in (
        ClaimType.MECHANISM,
        ClaimType.COMPARISON,
        ClaimType.LIMITATION,
    ):
        contract = claim_type_contract_for(claim_type)

        assert contract is not None
        assert contract.required_fields == observation.required_fields
        assert contract.nonempty_fields == observation.nonempty_fields
        assert contract.concept_links == observation.concept_links


def test_every_runtime_claim_type_has_a_contract() -> None:
    claim_types = {contract.claim_type for contract in iter_claim_type_contracts()}

    assert claim_types == {
        ClaimType.ALGORITHM,
        ClaimType.COMPARISON,
        ClaimType.EQUATION,
        ClaimType.LIMITATION,
        ClaimType.MECHANISM,
        ClaimType.MEASUREMENT,
        ClaimType.MODEL,
        ClaimType.OBSERVATION,
        ClaimType.PARAMETER,
    }
