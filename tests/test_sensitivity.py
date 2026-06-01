"""Tests for sensitivity analysis — Feature 6."""

import pytest
import yaml

from propstore.families.identity.concepts import derive_concept_artifact_id
from tests.family_helpers import materialized_world_store_path
from propstore.sensitivity import (
    analyze_sensitivity,
)
from propstore.world import WorldQuery
from tests.conftest import (
    normalize_claims_payload,
    normalize_concept_payloads,
    write_test_context,
)


# ── Fixtures ─────────────────────────────────────────────────────────


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


@pytest.fixture
def repo(concept_dir):
    from propstore.repository import Repository

    return Repository(concept_dir.parent)


@pytest.fixture
def world(concept_dir, repo, claim_files):
    """Build sidecar and return a WorldQuery."""
    materialized_world_store_path(repo)
    return WorldQuery(repo)


# ── Nonlinear fixture (separate, minimal) ────────────────────────────


# ── Tests ─────────────────────────────────────────────────────────────


class TestSensitivityLinear:
    """concept5 = concept6 * concept1 under speech, with overrides."""

    def test_sensitivity_linear(self, world):
        bound = world.bind(task="speech")
        result = analyze_sensitivity(
            world,
            "concept5",
            bound,
            override_values={"concept1": 200.0, "concept6": 0.001},
        )
        assert result is not None
        assert result.concept_id == _concept_artifact("concept5")
        assert len(result.entries) == 2

        # Both inputs should have partial derivatives
        ids = {e.input_concept_id for e in result.entries}
        assert ids == {
            _concept_artifact("concept1"),
            _concept_artifact("concept6"),
        }

        # Check partial derivative values:
        #   d(concept6 * concept1)/d(concept1) = concept6 = 0.001
        #   d(concept6 * concept1)/d(concept6) = concept1 = 200.0
        for entry in result.entries:
            assert entry.partial_derivative_value is not None
            if entry.input_concept_id == _concept_artifact("concept1"):
                assert entry.partial_derivative_value == pytest.approx(0.001)
            elif entry.input_concept_id == _concept_artifact("concept6"):
                assert entry.partial_derivative_value == pytest.approx(200.0)


class TestSensitivityRanking:
    """Entries sorted by |elasticity| descending."""

    def test_sensitivity_ranking(self, world):
        bound = world.bind(task="speech")
        result = analyze_sensitivity(
            world,
            "concept5",
            bound,
            override_values={"concept1": 200.0, "concept6": 0.001},
        )
        assert result is not None
        assert len(result.entries) >= 2

        # For f = a * b, all elasticities are 1.0, so order doesn't matter
        # but they should all be present and sorted (ties are fine)
        elasticities = [
            abs(e.elasticity) for e in result.entries if e.elasticity is not None
        ]
        assert elasticities == sorted(elasticities, reverse=True)


class TestSensitivityNoParameterization:
    """concept2 has no parameterization -> returns None."""

    def test_sensitivity_no_parameterization(self, world):
        bound = world.bind(task="speech")
        result = analyze_sensitivity(world, "concept2", bound)
        assert result is None


class TestSensitivityUnderspecifiedInputs:
    """Returns None when inputs can't be resolved and no overrides given."""

    def test_sensitivity_underspecified_inputs(self, world):
        # Under speech, concept1 is conflicted (claims 1,2,7 have different values)
        # and no override is given, so we can't resolve
        bound = world.bind(task="speech")
        result = analyze_sensitivity(world, "concept5", bound)
        # concept1 is conflicted -> value_of returns conflicted -> can't resolve -> None
        assert result is None


class TestSensitivityElasticityValues:
    """For f = a * b: elasticity of each input = 1.0."""

    def test_sensitivity_elasticity_values(self, world):
        bound = world.bind(task="speech")
        result = analyze_sensitivity(
            world,
            "concept5",
            bound,
            override_values={"concept1": 200.0, "concept6": 0.001},
        )
        assert result is not None

        for entry in result.entries:
            assert entry.elasticity is not None
            assert entry.elasticity == pytest.approx(1.0)


class TestSensitivityNonlinear:
    """For f = a^2 * b: elasticity of a = 2.0, elasticity of b = 1.0."""

    def test_sensitivity_nonlinear(self, nonlinear_world):
        bound = nonlinear_world.bind()
        input_a = nonlinear_world.get_concept("test:input_a")
        input_b = nonlinear_world.get_concept("test:input_b")
        output = nonlinear_world.get_concept("test:output_nl")
        assert input_a is not None
        assert input_b is not None
        assert output is not None
        input_a_id = str(input_a.id)
        input_b_id = str(input_b.id)
        output_id = str(output.id)
        result = analyze_sensitivity(
            nonlinear_world,
            output_id,
            bound,
            override_values={"test:input_a": 3.0, "test:input_b": 2.0},
        )
        assert result is not None
        assert result.output_value == pytest.approx(18.0)  # 3^2 * 2

        by_id = {str(e.input_concept_id): e for e in result.entries}
        assert by_id[str(input_a_id)].elasticity == pytest.approx(2.0)
        assert by_id[str(input_b_id)].elasticity == pytest.approx(1.0)

        # input_a should be first (higher elasticity)
        assert str(result.entries[0].input_concept_id) == str(input_a_id)


class TestSensitivityConditionsRespected:
    """Parameterization with conditions task=='speech', bind singing -> returns None."""

    def test_sensitivity_conditions_respected(self, world):
        bound = world.bind(task="singing")
        result = analyze_sensitivity(world, "concept5", bound)
        assert result is None
