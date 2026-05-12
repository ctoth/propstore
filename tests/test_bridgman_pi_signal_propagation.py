from __future__ import annotations

import bridgman

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.dimensional_invariants import (
    check_dimensionless_product,
    count_dimensionless_groups,
)
from propstore.equation_comparison import (
    EquationComparisonStatus,
    compare_equation_claims,
)


PROPSTORE_REYNOLDS_QUANTITIES = {
    "ps:concept:density": {"M": 1, "L": -3},
    "ps:concept:velocity": {"L": 1, "T": -1},
    "ps:concept:length": {"L": 1},
    "ps:concept:dynamic-viscosity": {"M": 1, "L": -1, "T": -1},
}

PROPSTORE_REYNOLDS_PRODUCT = {
    "ps:concept:density": 1,
    "ps:concept:velocity": 1,
    "ps:concept:length": 1,
    "ps:concept:dynamic-viscosity": -1,
}


def test_propstore_consumes_bridgman_pi_public_api() -> None:
    assert hasattr(bridgman, "count_pi_groups")
    assert hasattr(bridgman, "is_dimensionless_product")
    assert hasattr(bridgman, "pi_groups")


def test_propstore_counts_reynolds_pi_group_with_opaque_concept_labels() -> None:
    diagnostic = count_dimensionless_groups(PROPSTORE_REYNOLDS_QUANTITIES)

    assert diagnostic.ok
    assert diagnostic.value == 1
    assert diagnostic.error is None


def test_propstore_checks_authored_reynolds_product() -> None:
    diagnostic = check_dimensionless_product(
        PROPSTORE_REYNOLDS_QUANTITIES,
        PROPSTORE_REYNOLDS_PRODUCT,
    )

    assert diagnostic.ok
    assert diagnostic.value is True
    assert diagnostic.error is None


def test_propstore_reports_pi_adapter_errors_without_silent_acceptance() -> None:
    unknown = check_dimensionless_product(
        {"ps:concept:velocity": {"L": 1, "T": -1}},
        {"ps:concept:density": 1},
    )
    bad_exponent = check_dimensionless_product(
        {"ps:concept:velocity": {"L": 1, "T": -1}},
        {"ps:concept:velocity": 1.5},
    )
    bad_dimensions = count_dimensionless_groups(
        {"ps:concept:velocity": {"L": 1, "T": -1.5}},
    )

    assert not unknown.ok
    assert unknown.value is None
    assert "unknown quantity" in (unknown.error or "")
    assert not bad_exponent.ok
    assert bad_exponent.value is None
    assert "exponent" in (bad_exponent.error or "")
    assert not bad_dimensions.ok
    assert bad_dimensions.value is None
    assert "exponent" in (bad_dimensions.error or "")


def test_pi_diagnostics_do_not_make_equations_equivalent() -> None:
    left = _equation_claim("Re = rho*v*L/mu")
    right = _equation_claim("Re = rho*v + L/mu")

    comparison = compare_equation_claims(left, right)

    assert comparison.status is not EquationComparisonStatus.EQUIVALENT


def _equation_claim(expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=expression,
        claim_type="equation",
        expression=expression,
        sympy=None,
        variables=(
            ConflictClaimVariable("reynolds-number", "Re", "dependent"),
            ConflictClaimVariable("density", "rho", "independent"),
            ConflictClaimVariable("velocity", "v", "independent"),
            ConflictClaimVariable("length", "L", "independent"),
            ConflictClaimVariable("dynamic-viscosity", "mu", "independent"),
        ),
    )
