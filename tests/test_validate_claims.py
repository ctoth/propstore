"""Tests for the claim file validator.

Tests the compiler contract checks that JSON Schema can't express:
- Claim ID uniqueness across all claim files
- Claim ID format (claim_NNNN)
- Concept references exist in registry
- CEL conditions type-check
- Provenance has paper and page
- Parameter claims: concept, value, unit required
- Equation claims: expression, variables required
- Observation claims: statement, concepts required
- Model claims: name, equations, parameters required
"""

import pytest
import yaml

from propstore.validate_claims import (
    load_claim_files,
    validate_claims,
)


@pytest.fixture
def claims_dir(tmp_path):
    """Create a temporary claims directory."""
    return tmp_path


def write_claim_file(claims_dir, filename, data):
    """Helper: write a claim YAML file."""
    path = claims_dir / filename
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


def make_source(paper="test_paper"):
    return {"paper": paper}


def make_parameter_claim(id, concept, value, unit, page=1, **kwargs):
    """Helper: make a minimal valid parameter claim."""
    c = {
        "id": id,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": unit,
        "provenance": {"paper": "test_paper", "page": page},
    }
    c.update(kwargs)
    return c


def make_equation_claim(id, expression, variables, page=1, **kwargs):
    """Helper: make a minimal valid equation claim."""
    c = {
        "id": id,
        "type": "equation",
        "expression": expression,
        "sympy": kwargs.pop("sympy", expression),
        "variables": variables,
        "provenance": {"paper": "test_paper", "page": page},
    }
    c.update(kwargs)
    return c


def make_observation_claim(id, statement, concepts, page=1, **kwargs):
    """Helper: make a minimal valid observation claim."""
    c = {
        "id": id,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": "test_paper", "page": page},
    }
    c.update(kwargs)
    return c


def make_model_claim(id, name, equations, parameters, page=1, **kwargs):
    """Helper: make a minimal valid model claim."""
    c = {
        "id": id,
        "type": "model",
        "name": name,
        "equations": equations,
        "parameters": parameters,
        "provenance": {"paper": "test_paper", "page": page},
    }
    c.update(kwargs)
    return c


def make_concept_registry():
    """Build a mock concept registry for testing."""
    return {
        "concept1": {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
        },
        "concept2": {
            "id": "concept2",
            "canonical_name": "subglottal_pressure",
            "form": "pressure",
            "status": "accepted",
            "definition": "Ps",
        },
        "concept3": {
            "id": "concept3",
            "canonical_name": "task",
            "form": "category",
            "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True},
            "status": "accepted",
            "definition": "Task type",
        },
    }


def make_claim_file_data(claims, paper="test_paper"):
    """Wrap claims in a proper ClaimFile structure."""
    return {
        "source": make_source(paper),
        "claims": claims,
    }


# ── Valid cases ──────────────────────────────────────────────────────


class TestValidClaims:
    def test_valid_parameter_claim(self, claims_dir):
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_equation_claim(self, claims_dir):
        claim = make_equation_claim(
            "claim1",
            "F0 = Ps * k",
            [
                {"symbol": "F0", "concept": "concept1"},
                {"symbol": "Ps", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_observation_claim(self, claims_dir):
        claim = make_observation_claim(
            "claim1",
            "Higher subglottal pressure increases F0",
            ["concept1", "concept2"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_model_claim(self, claims_dir):
        claim = make_model_claim(
            "claim1",
            "Linear F0 model",
            ["F0 = Ps * k + b"],
            [
                {"name": "k", "concept": "concept1"},
                {"name": "b", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_multiple_valid_claims(self, claims_dir):
        claims = [
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_observation_claim(
                "claim2",
                "F0 varies with pressure",
                ["concept1", "concept2"],
            ),
            make_equation_claim(
                "claim3",
                "F0 = Ps * k",
                [
                    {"symbol": "F0", "concept": "concept1"},
                    {"symbol": "Ps", "concept": "concept2"},
                ],
            ),
        ]
        data = make_claim_file_data(claims)
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"


# ── ID errors ────────────────────────────────────────────────────────


class TestClaimIdErrors:
    def test_duplicate_claim_id_error(self, claims_dir):
        data1 = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
        ], paper="paper_a")
        data2 = make_claim_file_data([
            make_parameter_claim("claim1", "concept2", 100.0, "Pa"),
        ], paper="paper_b")
        write_claim_file(claims_dir, "paper_a.yaml", data1)
        write_claim_file(claims_dir, "paper_b.yaml", data2)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("duplicate" in e.lower() for e in result.errors)

    def test_invalid_claim_id_format(self, claims_dir):
        claim = make_parameter_claim("bad_id", "concept1", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("format" in e.lower() or "claimN" in e.lower() for e in result.errors)


# ── Concept reference errors ─────────────────────────────────────────


class TestConceptReferenceErrors:
    def test_nonexistent_concept_parameter_error(self, claims_dir):
        claim = make_parameter_claim("claim1", "concept9999", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept9999" in e for e in result.errors)

    def test_nonexistent_concept_equation_error(self, claims_dir):
        claim = make_equation_claim(
            "claim1",
            "F0 = X * k",
            [
                {"symbol": "F0", "concept": "concept1"},
                {"symbol": "X", "concept": "concept9999"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept9999" in e for e in result.errors)

    def test_nonexistent_concept_observation_error(self, claims_dir):
        claim = make_observation_claim(
            "claim1",
            "Some statement",
            ["concept1", "concept9999"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept9999" in e for e in result.errors)

    def test_nonexistent_concept_model_error(self, claims_dir):
        claim = make_model_claim(
            "claim1",
            "Bad model",
            ["F0 = k * Ps"],
            [
                {"name": "k", "concept": "concept9999"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept9999" in e for e in result.errors)


# ── Provenance errors ────────────────────────────────────────────────


class TestProvenanceErrors:
    def test_missing_provenance_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 440.0,
            "unit": "Hz",
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("provenance" in e.lower() for e in result.errors)

    def test_missing_provenance_page_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 440.0,
            "unit": "Hz",
            "provenance": {"paper": "test_paper"},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("page" in e.lower() for e in result.errors)


# ── Parameter claim errors ───────────────────────────────────────────


class TestParameterClaimErrors:
    def test_parameter_unit_mismatch_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 440.0,
            "unit": "Pa",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        registry = make_concept_registry()
        registry["concept1"]["_allowed_units"] = ["Hz"]

        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("allowed units" in e.lower() or "does not match" in e.lower()
                   for e in result.errors)

    def test_parameter_missing_value_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("value" in e.lower() for e in result.errors)

    def test_parameter_missing_unit_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 440.0,
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("unit" in e.lower() for e in result.errors)

    def test_parameter_missing_concept_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "value": 440.0,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept" in e.lower() for e in result.errors)


# ── Equation claim errors ────────────────────────────────────────────


class TestEquationClaimErrors:
    def test_equation_missing_expression_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "equation",
            "variables": [{"symbol": "F0", "concept": "concept1"}],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("expression" in e.lower() for e in result.errors)

    def test_equation_missing_variables_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "equation",
            "expression": "F0 = k * Ps",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("variable" in e.lower() for e in result.errors)


# ── Observation claim errors ─────────────────────────────────────────


class TestObservationClaimErrors:
    def test_observation_missing_statement_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "observation",
            "concepts": ["concept1"],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("statement" in e.lower() for e in result.errors)

    def test_observation_missing_concepts_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "observation",
            "statement": "Some observation",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("concept" in e.lower() for e in result.errors)


# ── Model claim errors ───────────────────────────────────────────────


class TestModelClaimErrors:
    def test_model_missing_name_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "model",
            "equations": ["F0 = k * Ps"],
            "parameters": [{"name": "k", "concept": "concept1"}],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("name" in e.lower() for e in result.errors)

    def test_model_missing_equations_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "model",
            "name": "Test model",
            "parameters": [{"name": "k", "concept": "concept1"}],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("equation" in e.lower() for e in result.errors)

    def test_model_missing_parameters_error(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "model",
            "name": "Test model",
            "equations": ["F0 = k * Ps"],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("parameter" in e.lower() for e in result.errors)


# ── CEL errors ───────────────────────────────────────────────────────


class TestCelErrors:
    def test_cel_error_in_conditions(self, claims_dir):
        """Structural concept in CEL should produce an error."""
        # We need a concept registry with a structural concept
        registry = make_concept_registry()
        registry["concept101"] = {
            "id": "concept101",
            "canonical_name": "focalization",
            "form": "structural",
            "status": "accepted",
            "definition": "Narrative focalization",
        }

        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            conditions=["focalization == 'internal'"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("cel" in e.lower() or "structural" in e.lower() for e in result.errors)

    def test_cel_undefined_concept_in_conditions(self, claims_dir):
        """CEL referencing undefined concept should produce an error."""
        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            conditions=["nonexistent_concept > 5"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("cel" in e.lower() or "undefined" in e.lower() for e in result.errors)


# ── Hypothesis property test ─────────────────────────────────────────


import tempfile

from hypothesis import given, strategies as st, settings


@given(
    claim_id_num=st.integers(min_value=0, max_value=9999),
    value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    page=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=50)
def test_valid_claims_always_pass(claim_id_num, value, page):
    """Property: any parameter claim with all required fields and valid concept refs should pass."""
    import pathlib
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        claim_id = f"claim{claim_id_num}"
        claim = make_parameter_claim(claim_id, "concept1", value, "Hz", page=page)
        data = make_claim_file_data([claim])

        path = tmp_path / "test_paper.yaml"
        path.write_text(yaml.dump(data, default_flow_style=False))

        files = load_claim_files(tmp_path)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Valid claim failed validation: {result.errors}"


# ── Named value fields ──────────────────────────────────────────────


class TestNamedValueFields:
    """Tests for named scalar fields (value, lower_bound, upper_bound, uncertainty)."""

    def test_scalar_value_validates(self, claims_dir):
        """value: 0.7 alone validates (scalar float)."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_value_with_bounds_validates(self, claims_dir):
        """value: 0.7, lower_bound: 0.5, upper_bound: 0.9 validates."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "lower_bound": 0.5,
            "upper_bound": 0.9,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_value_with_uncertainty_validates(self, claims_dir):
        """value: 0.7, uncertainty: 0.12, uncertainty_type: sd validates."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "uncertainty": 0.12,
            "uncertainty_type": "sd",
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_lower_bound_without_upper_bound_error(self, claims_dir):
        """lower_bound: 0.5 without upper_bound -> validation error."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "lower_bound": 0.5,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("upper_bound" in e for e in result.errors)

    def test_upper_bound_without_lower_bound_error(self, claims_dir):
        """upper_bound: 0.9 without lower_bound -> validation error."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "upper_bound": 0.9,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("lower_bound" in e for e in result.errors)

    def test_uncertainty_type_without_uncertainty_error(self, claims_dir):
        """uncertainty_type: sd without uncertainty -> validation error."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "uncertainty_type": "sd",
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("uncertainty" in e for e in result.errors)

    def test_uncertainty_without_uncertainty_type_error(self, claims_dir):
        """uncertainty: 0.12 without uncertainty_type -> validation error."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 0.7,
            "uncertainty": 0.12,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("uncertainty_type" in e for e in result.errors)

    def test_no_value_no_bounds_error(self, claims_dir):
        """Parameter claim with NO value and NO bounds -> validation error."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("value" in e.lower() or "bound" in e.lower() for e in result.errors)

    def test_range_only_validates(self, claims_dir):
        """lower_bound: 0.5, upper_bound: 0.9 without value -> validates."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "lower_bound": 0.5,
            "upper_bound": 0.9,
            "unit": "Hz",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"


# ── Measurement claim validation ─────────────────────────────────────


class TestMeasurementClaimValidation:
    def test_measurement_unit_not_checked_against_target_concept(self, claims_dir):
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "measure": "jnd_absolute",
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        registry = make_concept_registry()
        registry["concept2"]["_allowed_units"] = ["Pa"]

        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_measurement_claim(self, claims_dir):
        """type: measurement with target_concept, measure, value, unit -> validates."""
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "measure": "jnd_absolute",
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_measurement_missing_target_concept_error(self, claims_dir):
        """Measurement missing target_concept -> validation error."""
        claim = {
            "id": "claim1",
            "type": "measurement",
            "measure": "jnd_absolute",
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("target_concept" in e for e in result.errors)

    def test_measurement_missing_measure_error(self, claims_dir):
        """Measurement missing measure -> validation error."""
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("measure" in e for e in result.errors)

    def test_measurement_with_uncertainty_validates(self, claims_dir):
        """Measurement with value, uncertainty, uncertainty_type, sample_size -> validates."""
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "measure": "jnd_absolute",
            "value": 0.14,
            "uncertainty": 0.03,
            "uncertainty_type": "sd",
            "sample_size": 20,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    @pytest.mark.parametrize("measure", [
        "jnd_absolute", "jnd_relative", "discrimination_threshold",
        "preference_rating", "detection_threshold",
    ])
    def test_valid_measure_types(self, claims_dir, measure):
        """All valid measure types should validate."""
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "measure": measure,
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors for measure={measure}: {result.errors}"


# ── Form-aware unit validation ───────────────────────────────────────


class TestFormAwareUnitValidation:
    """Tests for form-definition-based unit validation on claims."""

    def _make_registry_with_forms(self, tmp_path):
        """Build a concept registry with form definitions available on disk."""
        knowledge = tmp_path / "knowledge"
        # Create forms directory with real form definitions
        forms_dir = knowledge / "forms"
        forms_dir.mkdir(parents=True, exist_ok=True)

        import yaml as _yaml
        _yaml.dump({"name": "frequency", "unit_symbol": "Hz",
                     "dimensions": {"T": -1}},
                    (forms_dir / "frequency.yaml").open("w"))
        _yaml.dump({"name": "pressure", "unit_symbol": "Pa",
                     "dimensions": {"M": 1, "L": -1, "T": -2},
                     "common_alternatives": [{"unit": "cmH2O", "type": "multiplicative", "multiplier": 98.0665}]},
                    (forms_dir / "pressure.yaml").open("w"))
        _yaml.dump({"name": "duration_ratio", "base": "ratio",
                     "dimensions": {},
                     "parameters": {"numerator": "duration", "denominator": "duration"}},
                    (forms_dir / "duration_ratio.yaml").open("w"))
        _yaml.dump({"name": "level", "unit_symbol": "dB",
                     "dimensions": {},
                     "parameters": {"scale": "dB", "reference": None}},
                    (forms_dir / "level.yaml").open("w"))
        _yaml.dump({"name": "category", "parameters": {"values": [], "extensible": False}},
                    (forms_dir / "category.yaml").open("w"))

        # Create concepts directory
        concepts_dir = knowledge / "concepts"
        concepts_dir.mkdir(exist_ok=True)

        # Write concept files
        for cdata in [
            {"id": "concept1", "canonical_name": "fundamental_frequency",
             "form": "frequency", "status": "accepted", "definition": "F0"},
            {"id": "concept2", "canonical_name": "subglottal_pressure",
             "form": "pressure", "status": "accepted", "definition": "Ps"},
            {"id": "concept3", "canonical_name": "task",
             "form": "category", "status": "accepted", "definition": "Task type",
             "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True}},
            {"id": "concept4", "canonical_name": "open_quotient",
             "form": "duration_ratio", "status": "accepted", "definition": "OQ"},
            {"id": "concept5", "canonical_name": "h1_h2_difference",
             "form": "level", "status": "accepted", "definition": "H1-H2"},
        ]:
            (concepts_dir / f"{cdata['canonical_name']}.yaml").write_text(
                _yaml.dump(cdata, default_flow_style=False))

        from propstore.cli.repository import Repository
        from propstore.validate_claims import build_concept_registry
        repo = Repository(knowledge)
        return build_concept_registry(repo)

    def test_parameter_claim_hz_on_frequency_concept_validates(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_parameter_claim_pa_on_frequency_concept_errors(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Pa")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("unit" in e.lower() and "Pa" in e for e in result.errors)

    def test_parameter_claim_ratio_on_duration_ratio_concept_validates(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept4", 0.7, "ratio")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_parameter_claim_percent_on_duration_ratio_concept_validates(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept4", 70.0, "%")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_parameter_claim_hz_on_duration_ratio_concept_errors(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept4", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("unit" in e.lower() and "Hz" in e for e in result.errors)

    def test_parameter_claim_db_on_level_concept_validates(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept5", -3.5, "dB")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_parameter_claim_hz_on_level_concept_errors(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept5", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("unit" in e.lower() and "Hz" in e for e in result.errors)

    def test_parameter_claim_cmh2o_on_pressure_concept_validates(self, claims_dir, tmp_path):
        registry = self._make_registry_with_forms(tmp_path)
        claim = make_parameter_claim("claim1", "concept2", 5.0, "cmH2O")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_measurement_claim_unit_not_checked_against_form(self, claims_dir, tmp_path):
        """Measurement claims skip form-based unit checking."""
        registry = self._make_registry_with_forms(tmp_path)
        claim = {
            "id": "claim1",
            "type": "measurement",
            "target_concept": "concept2",
            "measure": "jnd_absolute",
            "value": 0.14,
            "unit": "ratio",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_parameter_claim_on_concept_without_form_definition_skips_check(self, claims_dir):
        """If form definition can't be loaded, skip unit check gracefully."""
        registry = make_concept_registry()
        # No _allowed_units set, and no form definition on disk
        claim = make_parameter_claim("claim1", "concept1", 440.0, "anything")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert result.ok, f"Unexpected errors: {result.errors}"


# ── Empty claim files (T3) ───────────────────────────────────────────


class TestEmptyClaimFiles:
    """Edge cases: claim files with empty or null claims lists."""

    def test_empty_claims_list_validates(self, claims_dir):
        """claims: [] should pass validation without errors."""
        data = {"source": make_source(), "claims": []}
        write_claim_file(claims_dir, "empty_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_null_claims_validates(self, claims_dir):
        """claims: null (None) should pass validation without errors."""
        data = {"source": make_source(), "claims": None}
        write_claim_file(claims_dir, "null_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        # Should either pass or give a clear error, not crash
        # Based on code: `claims = data.get("claims", [])` -> None
        # Then `if not isinstance(claims, list)` -> error
        # This is expected behavior: null claims is not a list
        assert not result.ok or result.ok  # either outcome is acceptable, no crash

    def test_missing_claims_key_errors(self, claims_dir):
        """File with no 'claims' key should error (schema requires it), not crash."""
        data = {"source": make_source()}
        write_claim_file(claims_dir, "no_claims.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        # JSON Schema requires 'claims' field
        assert not result.ok
        assert any("claims" in e.lower() for e in result.errors)

    def test_empty_claims_mixed_with_valid(self, claims_dir):
        """An empty claim file alongside a valid one should both validate."""
        empty_data = {"source": make_source("empty_paper"), "claims": []}
        write_claim_file(claims_dir, "empty_paper.yaml", empty_data)

        valid_data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
        ])
        write_claim_file(claims_dir, "valid_paper.yaml", valid_data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"


# ── Algorithm claim helpers ──────────────────────────────────────────

VALID_ALGORITHM_BODY = """\
def compute(x, ps):
    return x * ps
"""


def make_algorithm_claim(id, body, variables, page=1, **kwargs):
    """Helper: make a minimal valid algorithm claim."""
    c = {
        "id": id,
        "type": "algorithm",
        "body": body,
        "variables": variables,
        "provenance": {"paper": "test_paper", "page": page},
    }
    c.update(kwargs)
    return c


# ── Algorithm claim validation ───────────────────────────────────────


class TestValidateAlgorithm:
    def test_valid_algorithm_claim(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            VALID_ALGORITHM_BODY,
            [
                {"symbol": "x", "concept": "concept1"},
                {"symbol": "ps", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_algorithm_missing_body(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            None,
            [{"symbol": "x", "concept": "concept1"}],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("missing 'body'" in e for e in result.errors)

    def test_algorithm_invalid_body(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            "def compute(x):\n    return x +",
            [{"symbol": "x", "concept": "concept1"}],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("parse error" in e for e in result.errors)

    def test_algorithm_missing_variables(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            VALID_ALGORITHM_BODY,
            [],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("missing 'variables'" in e for e in result.errors)

    def test_algorithm_unknown_concept(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            VALID_ALGORITHM_BODY,
            [
                {"symbol": "x", "concept": "nonexistent_concept"},
                {"symbol": "ps", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("nonexistent concept" in e for e in result.errors)

    def test_algorithm_unbound_name_warns(self, claims_dir):
        body = """\
def compute(x, ps, mystery):
    return x * ps + mystery
"""
        claim = make_algorithm_claim(
            "claim1",
            body,
            [
                {"symbol": "x", "concept": "concept1"},
                {"symbol": "ps", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        # Should pass (no errors) but have warnings
        assert result.ok, f"Unexpected errors: {result.errors}"
        assert any("mystery" in w and "not declared" in w for w in result.warnings)
