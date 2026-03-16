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

from compiler.validate_claims import (
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
        "value": value if isinstance(value, list) else [value],
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
        "speech_0001": {
            "id": "speech_0001",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
        },
        "speech_0002": {
            "id": "speech_0002",
            "canonical_name": "subglottal_pressure",
            "form": "pressure",
            "status": "accepted",
            "definition": "Ps",
        },
        "speech_0003": {
            "id": "speech_0003",
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
        claim = make_parameter_claim("claim_0001", "speech_0001", [440.0], "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_equation_claim(self, claims_dir):
        claim = make_equation_claim(
            "claim_0001",
            "F0 = Ps * k",
            [
                {"symbol": "F0", "concept": "speech_0001"},
                {"symbol": "Ps", "concept": "speech_0002"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_observation_claim(self, claims_dir):
        claim = make_observation_claim(
            "claim_0001",
            "Higher subglottal pressure increases F0",
            ["speech_0001", "speech_0002"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_valid_model_claim(self, claims_dir):
        claim = make_model_claim(
            "claim_0001",
            "Linear F0 model",
            ["F0 = Ps * k + b"],
            [
                {"name": "k", "concept": "speech_0001"},
                {"name": "b", "concept": "speech_0002"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_multiple_valid_claims(self, claims_dir):
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", [440.0], "Hz"),
            make_observation_claim(
                "claim_0002",
                "F0 varies with pressure",
                ["speech_0001", "speech_0002"],
            ),
            make_equation_claim(
                "claim_0003",
                "F0 = Ps * k",
                [
                    {"symbol": "F0", "concept": "speech_0001"},
                    {"symbol": "Ps", "concept": "speech_0002"},
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
            make_parameter_claim("claim_0001", "speech_0001", [440.0], "Hz"),
        ], paper="paper_a")
        data2 = make_claim_file_data([
            make_parameter_claim("claim_0001", "speech_0002", [100.0], "Pa"),
        ], paper="paper_b")
        write_claim_file(claims_dir, "paper_a.yaml", data1)
        write_claim_file(claims_dir, "paper_b.yaml", data2)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("duplicate" in e.lower() for e in result.errors)

    def test_invalid_claim_id_format(self, claims_dir):
        claim = make_parameter_claim("bad_id", "speech_0001", [440.0], "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("format" in e.lower() or "claim_" in e.lower() for e in result.errors)


# ── Concept reference errors ─────────────────────────────────────────


class TestConceptReferenceErrors:
    def test_nonexistent_concept_parameter_error(self, claims_dir):
        claim = make_parameter_claim("claim_0001", "speech_9999", [440.0], "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("speech_9999" in e for e in result.errors)

    def test_nonexistent_concept_equation_error(self, claims_dir):
        claim = make_equation_claim(
            "claim_0001",
            "F0 = X * k",
            [
                {"symbol": "F0", "concept": "speech_0001"},
                {"symbol": "X", "concept": "speech_9999"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("speech_9999" in e for e in result.errors)

    def test_nonexistent_concept_observation_error(self, claims_dir):
        claim = make_observation_claim(
            "claim_0001",
            "Some statement",
            ["speech_0001", "speech_9999"],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("speech_9999" in e for e in result.errors)

    def test_nonexistent_concept_model_error(self, claims_dir):
        claim = make_model_claim(
            "claim_0001",
            "Bad model",
            ["F0 = k * Ps"],
            [
                {"name": "k", "concept": "speech_9999"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("speech_9999" in e for e in result.errors)


# ── Provenance errors ────────────────────────────────────────────────


class TestProvenanceErrors:
    def test_missing_provenance_error(self, claims_dir):
        claim = {
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
            "value": [440.0],
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
            "value": [440.0],
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
    def test_parameter_missing_value_error(self, claims_dir):
        claim = {
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
            "value": [440.0],
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
            "id": "claim_0001",
            "type": "parameter",
            "value": [440.0],
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
            "id": "claim_0001",
            "type": "equation",
            "variables": [{"symbol": "F0", "concept": "speech_0001"}],
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
            "id": "claim_0001",
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
            "id": "claim_0001",
            "type": "observation",
            "concepts": ["speech_0001"],
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
            "id": "claim_0001",
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
            "id": "claim_0001",
            "type": "model",
            "equations": ["F0 = k * Ps"],
            "parameters": [{"name": "k", "concept": "speech_0001"}],
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
            "id": "claim_0001",
            "type": "model",
            "name": "Test model",
            "parameters": [{"name": "k", "concept": "speech_0001"}],
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
            "id": "claim_0001",
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
        registry["narr_0001"] = {
            "id": "narr_0001",
            "canonical_name": "focalization",
            "form": "structural",
            "status": "accepted",
            "definition": "Narrative focalization",
        }

        claim = make_parameter_claim(
            "claim_0001", "speech_0001", [440.0], "Hz",
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
            "claim_0001", "speech_0001", [440.0], "Hz",
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
        claim_id = f"claim_{claim_id_num:04d}"
        claim = make_parameter_claim(claim_id, "speech_0001", [value], "Hz", page=page)
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
            "id": "claim_0001",
            "type": "parameter",
            "concept": "speech_0001",
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
