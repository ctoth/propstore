"""Mixed direct + multi-statement algorithm resolution via ast equivalence.

A single direct-value claim plus a multi-statement algorithm claim that
evaluates (via ``collect_known_values``) to the same value is a clean
consensus: ``DETERMINED``. Ported from ``test_semantic_repairs`` as a direct
``ActiveClaimResolver`` test — the rest of that module exercises ``WorldQuery``
and lands with the bound world / concrete store slices.
"""

from __future__ import annotations

import pytest

from propstore.core.active_claims import ActiveClaim
from propstore.core.id_types import to_concept_id
from propstore.core.scalars import ScalarValue
from propstore.families.claims import ClaimType
from propstore.world.types import ValueResult, ValueStatus
from propstore.world.value_resolver import ActiveClaimResolver, collect_known_values


def test_mixed_direct_and_multistatement_algorithm_uses_ast_equivalence():
    resolver = ActiveClaimResolver(
        parameterizations_for=lambda cid: [],
        is_param_compatible=lambda conds: True,
        value_of=lambda cid: None,
        extract_variable_concepts=lambda claim: (
            ["input"] if claim.claim_type is ClaimType.ALGORITHM else []
        ),
        collect_known_values=lambda ids: {"input": 5.0},
        extract_bindings=lambda claim: {"x": "input"},
    )

    active = [
        ActiveClaim(claim_id="direct", claim_type=ClaimType.PARAMETER, value=10.0),
        ActiveClaim(
            claim_id="algo",
            claim_type=ClaimType.ALGORITHM,
            body="def compute(x):\n    y = x * 2\n    return y\n",
        ),
    ]

    result = resolver.value_of_from_active(active, "target")

    assert result.status is ValueStatus.DETERMINED


@pytest.mark.parametrize("value", ["red", True, 1, 1.0])
def test_direct_consensus_accepts_exact_typed_scalar(value: ScalarValue) -> None:
    resolver = ActiveClaimResolver(
        parameterizations_for=lambda cid: [],
        is_param_compatible=lambda conds: True,
        value_of=lambda cid: None,
        extract_variable_concepts=lambda claim: [],
        collect_known_values=lambda ids: {},
        extract_bindings=lambda claim: {},
    )
    result = resolver.value_of_from_active(
        [
            ActiveClaim(claim_id="a", value=value),
            ActiveClaim(claim_id="b", value=value),
        ],
        "target",
    )
    assert result.status is ValueStatus.DETERMINED


@pytest.mark.parametrize("left,right", [(True, 1), (1, 1.0)])
def test_direct_consensus_distinguishes_scalar_runtime_types(
    left: ScalarValue,
    right: ScalarValue,
) -> None:
    resolver = ActiveClaimResolver(
        parameterizations_for=lambda cid: [],
        is_param_compatible=lambda conds: True,
        value_of=lambda cid: None,
        extract_variable_concepts=lambda claim: [],
        collect_known_values=lambda ids: {},
        extract_bindings=lambda claim: {},
    )
    result = resolver.value_of_from_active(
        [
            ActiveClaim(claim_id="left", value=left),
            ActiveClaim(claim_id="right", value=right),
        ],
        "target",
    )
    assert result.status is ValueStatus.CONFLICTED


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, {}), ("5", {}), (5, {to_concept_id("input"): 5.0})],
)
def test_known_value_collection_accepts_only_numeric_claims(
    value: ScalarValue,
    expected: dict[object, float],
) -> None:
    claim = ActiveClaim(claim_id="input-claim", value=value)

    def value_of(concept_id: object) -> ValueResult:
        return ValueResult(
            concept_id=to_concept_id(str(concept_id)),
            status=ValueStatus.DETERMINED,
            claims=(claim,),
        )

    assert collect_known_values(("input",), value_of) == expected


@pytest.mark.parametrize("value", [True, "5"])
def test_parameterization_override_rejects_nonnumeric_scalar(
    value: ScalarValue,
) -> None:
    with pytest.raises(ValueError, match="Invalid override value"):
        ActiveClaimResolver._coerce_override_value(
            {"input": value},
            to_concept_id("input"),
        )
