"""generate_description over the charter Claim (Phase 10-0)."""

from __future__ import annotations

from propstore.description_generator import generate_description
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept

_REGISTRY = {
    "speed": Concept(concept_id="speed", canonical_name="Speed"),
    "distance": Concept(concept_id="distance", canonical_name="Distance"),
}


def test_explicit_statement_is_preserved() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.PARAMETER,
        statement="A pre-written statement.",
        output_concept="speed",
        value=3.0,
    )
    assert generate_description(claim, _REGISTRY) == "A pre-written statement."


def test_parameter_with_value_and_unit() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.PARAMETER,
        output_concept="speed",
        value=3.0,
        unit="m/s",
    )
    assert generate_description(claim, _REGISTRY) == "Speed = 3 m/s"


def test_parameter_with_uncertainty() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.PARAMETER,
        output_concept="speed",
        value=3.0,
        uncertainty=0.5,
        uncertainty_type="std",
        unit="m/s",
    )
    assert generate_description(claim, _REGISTRY) == "Speed = 3 ± 0.5 (std) m/s"


def test_parameter_with_interval_and_condition() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.PARAMETER,
        output_concept="speed",
        lower_bound=1.0,
        upper_bound=2.0,
        conditions=("medium == 'air'",),
    )
    assert generate_description(claim, _REGISTRY) == "Speed ∈ [1, 2] (air medium)"


def test_unknown_concept_falls_back_to_id() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.PARAMETER,
        output_concept="mystery",
        value=7.0,
    )
    assert generate_description(claim, _REGISTRY) == "mystery = 7"


def test_equation_uses_expression() -> None:
    claim = Claim(
        claim_id="c", claim_type=ClaimType.EQUATION, expression="v = d / t"
    )
    assert generate_description(claim, _REGISTRY) == "v = d / t"


def test_measurement_description() -> None:
    claim = Claim(
        claim_id="c",
        claim_type=ClaimType.MEASUREMENT,
        target_concept="distance",
        measure="length",
        value=10.0,
        unit="m",
    )
    assert generate_description(claim, _REGISTRY) == "length of Distance = 10 m"


def test_model_and_algorithm() -> None:
    model = Claim(claim_id="m", claim_type=ClaimType.MODEL, name="Newtonian")
    assert generate_description(model, _REGISTRY) == "Model: Newtonian"
    algo = Claim(
        claim_id="a",
        claim_type=ClaimType.ALGORITHM,
        name="bfs",
        output_concept="distance",
    )
    assert generate_description(algo, _REGISTRY) == "Algorithm: bfs -> distance"


def test_unrecognized_type_returns_none() -> None:
    claim = Claim(claim_id="c", claim_type=ClaimType.COMPARISON)
    assert generate_description(claim, _REGISTRY) is None
