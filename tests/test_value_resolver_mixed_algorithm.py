"""Mixed direct + multi-statement algorithm resolution via ast equivalence.

A single direct-value claim plus a multi-statement algorithm claim that
evaluates (via ``collect_known_values``) to the same value is a clean
consensus: ``DETERMINED``. Ported from ``test_semantic_repairs`` as a direct
``ActiveClaimResolver`` test — the rest of that module exercises ``WorldQuery``
and lands with the bound world / concrete store slices.
"""

from __future__ import annotations

from propstore.core.active_claims import ActiveClaim
from propstore.families.claims import ClaimType
from propstore.world.types import ValueStatus
from propstore.world.value_resolver import ActiveClaimResolver


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
