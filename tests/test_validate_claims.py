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

from propstore.identity import derive_concept_artifact_id
from propstore.artifacts.schema import DocumentSchemaError
from propstore.claims import loaded_claim_file_from_payload, load_claim_files
from propstore.identity import parse_claim_id
from propstore.compiler.passes import (
    validate_claims,
    validate_single_claim_file,
)


def _concept_artifact(local_id: str) -> str:
    return derive_concept_artifact_id("propstore", local_id)


def _rewrite_claim_concept_refs(claim: dict) -> dict:
    rewritten = dict(claim)
    concept = rewritten.get("concept")
    if isinstance(concept, str) and concept.startswith("concept"):
        rewritten["concept"] = _concept_artifact(concept)

    target_concept = rewritten.get("target_concept")
    if isinstance(target_concept, str) and target_concept.startswith("concept"):
        rewritten["target_concept"] = _concept_artifact(target_concept)

    concepts = rewritten.get("concepts")
    if isinstance(concepts, list):
        rewritten["concepts"] = [
            _concept_artifact(value) if isinstance(value, str) and value.startswith("concept") else value
            for value in concepts
        ]

    variables = rewritten.get("variables")
    if isinstance(variables, list):
        rewritten["variables"] = []
        for variable in variables:
            if not isinstance(variable, dict):
                rewritten["variables"].append(variable)
                continue
            variable_copy = dict(variable)
            value = variable_copy.get("concept")
            if isinstance(value, str) and value.startswith("concept"):
                variable_copy["concept"] = _concept_artifact(value)
            rewritten["variables"].append(variable_copy)

    parameters = rewritten.get("parameters")
    if isinstance(parameters, list):
        rewritten["parameters"] = []
        for parameter in parameters:
            if not isinstance(parameter, dict):
                rewritten["parameters"].append(parameter)
                continue
            parameter_copy = dict(parameter)
            value = parameter_copy.get("concept")
            if isinstance(value, str) and value.startswith("concept"):
                parameter_copy["concept"] = _concept_artifact(value)
            rewritten["parameters"].append(parameter_copy)

    return rewritten
from tests.conftest import (
    TEST_CONTEXT_ID,
    attach_claim_version_id,
    make_claim_identity,
    make_parameter_claim,
    make_concept_registry,
    normalize_concept_payloads,
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


def make_equation_claim(id, expression, variables, page=1, **kwargs):
    """Helper: make a minimal valid equation claim."""
    c = {
        **make_claim_identity(id),
        "type": "equation",
        "expression": expression,
        "sympy": kwargs.pop("sympy", expression),
        "variables": variables,
        "provenance": {"paper": "test_paper", "page": page},
        "context": {"id": TEST_CONTEXT_ID},
    }
    c.update(kwargs)
    return attach_claim_version_id(c)


def make_observation_claim(id, statement, concepts, page=1, **kwargs):
    """Helper: make a minimal valid observation claim."""
    c = {
        **make_claim_identity(id),
        "type": "observation",
        "statement": statement,
        "concepts": [
            _concept_artifact(value) if isinstance(value, str) and value.startswith("concept") else value
            for value in concepts
        ],
        "provenance": {"paper": "test_paper", "page": page},
        "context": {"id": TEST_CONTEXT_ID},
    }
    c.update(kwargs)
    return attach_claim_version_id(c)


def make_model_claim(id, name, equations, parameters, page=1, **kwargs):
    """Helper: make a minimal valid model claim."""
    c = {
        **make_claim_identity(id),
        "type": "model",
        "name": name,
        "equations": equations,
        "parameters": [
            {
                **parameter,
                "concept": _concept_artifact(parameter["concept"])
                if isinstance(parameter, dict) and isinstance(parameter.get("concept"), str)
                and parameter["concept"].startswith("concept")
                else parameter.get("concept") if isinstance(parameter, dict) else parameter,
            }
            if isinstance(parameter, dict) else parameter
            for parameter in parameters
        ],
        "provenance": {"paper": "test_paper", "page": page},
        "context": {"id": TEST_CONTEXT_ID},
    }
    c.update(kwargs)
    return attach_claim_version_id(c)


def make_claim_file_data(claims, paper="test_paper"):
    """Wrap claims in a proper ClaimFile structure."""
    normalized_claims = []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue
        normalized = dict(claim)
        normalized = _rewrite_claim_concept_refs(normalized)
        if "artifact_id" not in normalized:
            raw_id = normalized.pop("id", f"claim{index}")
            normalized.update(make_claim_identity(str(raw_id), namespace=paper))
        normalized.setdefault("context", {"id": TEST_CONTEXT_ID})
        normalized["version_id"] = attach_claim_version_id(normalized)["version_id"]
        normalized_claims.append(normalized)
    return {
        "source": make_source(paper),
        "claims": normalized_claims,
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
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Hz")
        claim["artifact_id"] = "bad-artifact-id"
        claim["version_id"] = attach_claim_version_id(claim)["version_id"]
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("format" in e.lower() for e in result.errors)


# ── Concept reference errors ─────────────────────────────────────────


class TestConceptReferenceErrors:
    def test_nonexistent_concept_parameter_error(self, claims_dir):
        claim = make_parameter_claim("claim1", "concept9999", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any(_concept_artifact("concept9999") in e for e in result.errors)

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
        assert any(_concept_artifact("concept9999") in e for e in result.errors)

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
        assert any(_concept_artifact("concept9999") in e for e in result.errors)

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
        assert any(_concept_artifact("concept9999") in e for e in result.errors)


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

        with pytest.raises(DocumentSchemaError, match="page"):
            load_claim_files(claims_dir)


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
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
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

    def test_parameter_missing_unit_dimensionless_autofill(self, claims_dir):
        """Dimensionless forms auto-fill unit='1' when unit is missing."""
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "hazard_ratio",
            "value": 0.94,
            "provenance": {"paper": "test_paper", "page": 1},
            # No unit field — should auto-fill '1' for dimensionless ratio form
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"

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


# ── Stance graph integrity ───────────────────────────────────────────


class TestStanceGraphIntegrity:
    def test_inline_stance_target_must_exist(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{"type": "rebuts", "target": "missing_claim"}],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any("missing_claim" in e and "stance" in e.lower() for e in result.errors)

    def test_inline_stance_type_must_be_recognized(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{"type": "contradicts", "target": "claim1"}],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="contradicts"):
            load_claim_files(claims_dir)

    def test_inline_target_justification_id_must_be_string(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{
                    "type": "undercuts",
                    "target": "claim1",
                    "target_justification_id": 123,
                }],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="target_justification_id"):
            load_claim_files(claims_dir)

    def test_inline_conditions_differ_must_be_string(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{
                    "type": "supports",
                    "target": "claim1",
                    "conditions_differ": ["vowel = /a/"],
                }],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="conditions_differ"):
            load_claim_files(claims_dir)

    def test_inline_resolution_must_be_mapping(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{
                    "type": "supports",
                    "target": "claim1",
                    "resolution": ["nli_first_pass"],
                }],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="resolution"):
            load_claim_files(claims_dir)

    def test_inline_resolution_method_required(self, claims_dir):
        data = make_claim_file_data([
            make_parameter_claim("claim1", "concept1", 440.0, "Hz"),
            make_parameter_claim(
                "claim2",
                "concept1",
                450.0,
                "Hz",
                stances=[{
                    "type": "supports",
                    "target": "claim1",
                    "resolution": {
                        "model": "test-model",
                        "confidence": 0.9,
                    },
                }],
            ),
        ])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="method"):
            load_claim_files(claims_dir)


class TestDraftArtifactBoundary:
    def test_draft_claim_file_traverses_binding_with_info_diagnostic(self, tmp_path):
        """Drafts populate through the compile path; diagnostic downgrades to info.

        Per ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
        axis-1 finding 3.2: the former build-time drop of draft files —
        which replaced their claims with an empty tuple — becomes a
        render-time policy filter. Draft claims traverse the same binding
        path as final claims; the SemanticDiagnostic survives as
        ``level='info'``, not ``level='error'``. ``validate_claims``
        returns ``ok=True`` because an info diagnostic is not an error.

        Inversion of the prior
        ``test_draft_claim_file_rejected_from_final_validation`` assertion.
        """

        draft_file = loaded_claim_file_from_payload(
            filename="draft_claims",
            source_path=tmp_path / "draft_claims.yaml",
            data={
                "stage": "draft",
                "source": make_source(),
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "Unlinked draft observation",
                        "concepts": [],
                        "context": {"id": TEST_CONTEXT_ID},
                        "provenance": {"paper": "test_paper", "page": 0},
                    }
                ],
            },
        )

        result = validate_claims([draft_file], make_concept_registry())
        # A draft stage alone must not produce a validation error. Any
        # residual error must not be the "draft artifacts are not accepted"
        # message from the old build-time gate.
        draft_gate_errors = [
            error
            for error in result.errors
            if "draft artifacts are not accepted" in error.lower()
        ]
        assert not draft_gate_errors, (
            "draft-stage files must no longer produce the "
            "'draft artifacts are not accepted' error; got: "
            f"{draft_gate_errors!r}"
        )

    def test_draft_claim_file_surfaces_in_compilation_bundle(self, tmp_path):
        """Draft claim files emit their claims into the semantic bundle.

        Property: with the gate removed, ``compile_claim_files`` binds
        draft claims like any other file. The returned
        ``SemanticClaimFile`` for a draft has non-empty ``claims`` (the
        prior behavior replaced ``claims`` with ``tuple()``).
        """

        from propstore.compiler.passes import compile_claim_files
        from propstore.compiler.context import compilation_context_from_concept_registry

        draft_file = loaded_claim_file_from_payload(
            filename="draft_claims",
            source_path=tmp_path / "draft_claims.yaml",
            data={
                "stage": "draft",
                "source": make_source(),
                "claims": [
                    make_observation_claim(
                        "draft_claim_1",
                        "A draft observation",
                        [],
                        page=0,
                    )
                ],
            },
        )
        context = compilation_context_from_concept_registry(
            make_concept_registry(),
            claim_files=[draft_file],
        )
        bundle = compile_claim_files([draft_file], context)

        assert len(bundle.semantic_files) == 1
        draft_semantic_file = bundle.semantic_files[0]
        assert len(draft_semantic_file.claims) == 1, (
            "draft file must surface its claims into the semantic bundle "
            "(was previously replaced with an empty tuple)"
        )

        # Any diagnostic emitted for draft stage must be at info level.
        draft_stage_diagnostics = [
            diagnostic
            for diagnostic in bundle.diagnostics
            if diagnostic.filename == "draft_claims"
            and "draft" in diagnostic.message.lower()
        ]
        for diagnostic in draft_stage_diagnostics:
            assert not diagnostic.is_error, (
                f"draft-stage diagnostic must not be level='error'; got "
                f"{diagnostic.level!r}: {diagnostic.message!r}"
            )

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
        registry[_concept_artifact("concept101")] = {
            "artifact_id": _concept_artifact("concept101"),
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
@settings()
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
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
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
        from propstore.repository import Repository
        from propstore.compiler.context import build_concept_registry

        knowledge = tmp_path / "knowledge"
        repo = Repository.init(knowledge)
        # Create forms directory with real form definitions
        forms_dir = knowledge / "forms"

        import yaml as _yaml
        _yaml.dump({"name": "frequency", "dimensionless": False, "unit_symbol": "Hz",
                     "dimensions": {"T": -1}},
                    (forms_dir / "frequency.yaml").open("w"))
        _yaml.dump({"name": "pressure", "dimensionless": False, "unit_symbol": "Pa",
                     "dimensions": {"M": 1, "L": -1, "T": -2},
                     "common_alternatives": [{"unit": "cmH2O", "type": "multiplicative", "multiplier": 98.0665}]},
                    (forms_dir / "pressure.yaml").open("w"))
        _yaml.dump({"name": "duration_ratio", "dimensionless": True, "base": "ratio",
                     "dimensions": {},
                     "parameters": {"numerator": "duration", "denominator": "duration"}},
                    (forms_dir / "duration_ratio.yaml").open("w"))
        _yaml.dump({"name": "level", "dimensionless": True, "unit_symbol": "dB",
                     "dimensions": {},
                     "parameters": {"scale": "dB", "reference": None}},
                    (forms_dir / "level.yaml").open("w"))
        _yaml.dump({"name": "category", "dimensionless": True, "parameters": {"values": [], "extensible": False}},
                    (forms_dir / "category.yaml").open("w"))

        # Create concepts directory
        concepts_dir = knowledge / "concepts"

        # Write concept files
        concept_payloads = normalize_concept_payloads(
            [
                {"id": "concept1", "canonical_name": "fundamental_frequency",
                 "form": "frequency", "status": "accepted", "definition": "F0", "domain": "speech"},
                {"id": "concept2", "canonical_name": "subglottal_pressure",
                 "form": "pressure", "status": "accepted", "definition": "Ps", "domain": "speech"},
                {"id": "concept3", "canonical_name": "task",
                 "form": "category", "status": "accepted", "definition": "Task type", "domain": "speech",
                 "form_parameters": {"values": ["speech", "singing", "whisper"], "extensible": True}},
                {"id": "concept4", "canonical_name": "open_quotient",
                 "form": "duration_ratio", "status": "accepted", "definition": "OQ", "domain": "speech"},
                {"id": "concept5", "canonical_name": "h1_h2_difference",
                 "form": "level", "status": "accepted", "definition": "H1-H2", "domain": "speech"},
            ],
            default_domain="speech",
        )
        for cdata in concept_payloads:
            canonical_form = cdata["lexical_entry"]["canonical_form"]
            concept_slug = canonical_form["written_rep"]
            (concepts_dir / f"{concept_slug}.yaml").write_text(
                _yaml.dump(cdata, default_flow_style=False))

        adds = {
            relpath.relative_to(knowledge).as_posix(): relpath.read_bytes()
            for relpath in sorted(forms_dir.glob("*.yaml"))
        }
        adds.update(
            {
                relpath.relative_to(knowledge).as_posix(): relpath.read_bytes()
                for relpath in sorted(concepts_dir.glob("*.yaml"))
            }
        )
        repo.git.commit_files(adds, "Seed form-aware validation fixture")
        repo.git.sync_worktree()
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

    def test_parameter_claim_on_concept_without_form_definition_errors(self, claims_dir):
        """Missing form metadata is a hard validation error."""
        registry = make_concept_registry()
        registry[_concept_artifact("concept1")].pop("_form_definition", None)
        claim = make_parameter_claim("claim1", "concept1", 440.0, "anything")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)
        files = load_claim_files(claims_dir)
        result = validate_claims(files, registry)
        assert not result.ok
        assert any("missing a loaded form definition" in e for e in result.errors)


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
        """claims: null now fails at the document boundary."""
        data = {"source": make_source(), "claims": None}
        write_claim_file(claims_dir, "null_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="claims"):
            load_claim_files(claims_dir)

    def test_missing_claims_key_errors(self, claims_dir):
        """File with no 'claims' key now fails at the document boundary."""
        data = {"source": make_source()}
        write_claim_file(claims_dir, "no_claims.yaml", data)

        with pytest.raises(DocumentSchemaError, match="claims"):
            load_claim_files(claims_dir)

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

    def test_algorithm_mapping_variables_rejected_at_document_boundary(self, claims_dir):
        claim = make_algorithm_claim(
            "claim1",
            VALID_ALGORITHM_BODY,
            {"x": "concept1", "ps": "concept2"},
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="variables"):
            load_claim_files(claims_dir)

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


# ── Step 1: Source-prefixed claim IDs ────────────────────────────────


class TestClaimIdFormat:
    def test_source_prefixed_claim_id_valid(self, claims_dir):
        """Dung_1995_AcceptabilityArguments:claim1 is a valid claim ID."""
        claim = make_parameter_claim(
            "Dung_1995_AcceptabilityArguments:claim1", "concept1", 440.0, "Hz"
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        id_errors = [e for e in result.errors if "format" in e.lower() or "claimN" in e.lower()]
        assert not id_errors, f"Prefixed ID rejected: {id_errors}"

    def test_bare_claim_id_still_valid(self, claims_dir):
        """claim1 remains valid for paper-local files."""
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Hz")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        id_errors = [e for e in result.errors if "format" in e.lower() or "claimN" in e.lower()]
        assert not id_errors, f"Bare ID rejected: {id_errors}"

    def test_invalid_claim_id_rejected(self, claims_dir):
        """Empty string, spaces, bare numbers rejected."""
        for bad_id in ["", " ", "123", "claim-1", "claim 1"]:
            claim = make_parameter_claim(bad_id or "x", "concept1", 440.0, "Hz")
            if bad_id == "":
                claim["id"] = ""
            else:
                claim["id"] = bad_id
            data = make_claim_file_data([claim])
            write_claim_file(claims_dir, "test_paper.yaml", data)

            files = load_claim_files(claims_dir)
            result = validate_claims(files, make_concept_registry())
            assert not result.ok, f"Bad ID '{bad_id}' was accepted"

    def test_source_with_hyphens_valid(self, claims_dir):
        """Source names can contain hyphens and underscores."""
        claim = make_parameter_claim(
            "de-Kleer_1986:claim1", "concept1", 440.0, "Hz"
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        id_errors = [e for e in result.errors if "format" in e.lower()]
        assert not id_errors, f"Hyphenated source rejected: {id_errors}"


class TestParseClaimId:
    def test_parse_with_source(self):
        source, local = parse_claim_id("Dung_1995:claim1")
        assert source == "Dung_1995"
        assert local == "claim1"

    def test_parse_bare(self):
        source, local = parse_claim_id("claim1")
        assert source is None
        assert local == "claim1"

    def test_parse_complex_source(self):
        source, local = parse_claim_id("deKleer_1986_AssumptionBasedTMS:claim42")
        assert source == "deKleer_1986_AssumptionBasedTMS"
        assert local == "claim42"


# ── Step 2: Single-file validation ──────────────────────────────────


class TestValidateSingleFile:
    def test_catches_missing_provenance_page(self, claims_dir, tmp_path):
        claim = {
            "id": "claim1",
            "type": "parameter",
            "concept": "concept1",
            "value": 440.0,
            "unit": "Hz",
            "provenance": {"paper": "test_paper"},  # missing page
        }
        data = make_claim_file_data([claim])
        filepath = write_claim_file(tmp_path, "test.yaml", data)

        with pytest.raises(DocumentSchemaError, match="page"):
            validate_single_claim_file(filepath, make_concept_registry())

    def test_catches_missing_variables_on_equation(self, claims_dir, tmp_path):
        claim = {
            "id": "claim1",
            "type": "equation",
            "expression": "F0 = X * k",
            "provenance": {"paper": "test_paper", "page": 1},
            # missing variables
        }
        data = make_claim_file_data([claim])
        filepath = write_claim_file(tmp_path, "test.yaml", data)

        result = validate_single_claim_file(filepath, make_concept_registry())
        assert not result.ok
        assert any("variables" in e.lower() for e in result.errors)

    def test_valid_file_passes(self, claims_dir, tmp_path):
        claim = make_parameter_claim("claim1", "concept1", 440.0, "Hz")
        data = make_claim_file_data([claim])
        filepath = write_claim_file(tmp_path, "test.yaml", data)

        result = validate_single_claim_file(filepath, make_concept_registry())
        assert result.ok, f"Unexpected errors: {result.errors}"


# ── New claim types: mechanism, comparison, limitation ───────────────


class TestNewClaimTypes:
    def test_mechanism_claim_valid(self, claims_dir):
        """A mechanism claim with statement and concepts validates."""
        claim = make_observation_claim("claim1", "X works by Y", ["concept1"])
        claim["type"] = "mechanism"
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        type_errors = [e for e in result.errors if "unrecognized type" in e]
        assert not type_errors, f"Mechanism type rejected: {type_errors}"

    def test_comparison_claim_valid(self, claims_dir):
        """A comparison claim with statement and concepts validates."""
        claim = make_observation_claim("claim1", "X outperforms Y because Z", ["concept1"])
        claim["type"] = "comparison"
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        type_errors = [e for e in result.errors if "unrecognized type" in e]
        assert not type_errors, f"Comparison type rejected: {type_errors}"

    def test_limitation_claim_valid(self, claims_dir):
        """A limitation claim with statement and concepts validates."""
        claim = make_observation_claim("claim1", "X cannot handle Y", ["concept1"])
        claim["type"] = "limitation"
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        type_errors = [e for e in result.errors if "unrecognized type" in e]
        assert not type_errors, f"Limitation type rejected: {type_errors}"


# ── Bare except narrowing ─────────────────────────────────────────


class TestSympyExceptNarrowing:
    """Programming errors in equation dimensional verification must propagate."""

    def test_programming_error_in_verify_expr_propagates(self, claims_dir, monkeypatch):
        """NameError inside verify_expr must NOT be silently caught."""
        from propstore.form_utils import FormDefinition
        from propstore.cel_checker import KindType

        # Build registry with form definitions that have dimensions
        registry = {
            _concept_artifact("concept1"): {
                "artifact_id": _concept_artifact("concept1"),
                "canonical_name": "frequency",
                "form": "frequency",
                "status": "accepted",
                "definition": "F0",
                "_form_definition": FormDefinition(
                    name="frequency", kind=KindType.QUANTITY,
                    dimensions={"T": -1},
                ),
            },
            _concept_artifact("concept2"): {
                "artifact_id": _concept_artifact("concept2"),
                "canonical_name": "pressure",
                "form": "pressure",
                "status": "accepted",
                "definition": "Ps",
                "_form_definition": FormDefinition(
                    name="pressure", kind=KindType.QUANTITY,
                    dimensions={"M": 1, "L": -1, "T": -2},
                ),
            },
        }

        # Equation claim with sympy that will trigger dimensional check
        claim = make_equation_claim(
            "claim1", "F0 = Ps", sympy="Eq(F0, Ps)",
            variables=[
                {"symbol": "F0", "concept": "concept1"},
                {"symbol": "Ps", "concept": "concept2"},
            ],
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        # Monkeypatch bridgman.verify_expr (imported locally inside the try block)
        import bridgman

        def _boom(*args, **kwargs):
            raise NameError("undefined_variable_bug")

        monkeypatch.setattr(bridgman, "verify_expr", _boom)

        files = load_claim_files(claims_dir)
        with pytest.raises(NameError, match="undefined_variable_bug"):
            validate_claims(files, registry)

    def test_programming_error_in_unit_compatibility_check_propagates(
        self,
        claims_dir,
        monkeypatch,
    ):
        """NameError inside pint unit translation must NOT be silently caught."""
        claim = make_parameter_claim("claim1", "concept1", 440.0, "custom_unit")
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_units.yaml", data)

        import propstore.dimensions as dimensions

        def _boom(*_args, **_kwargs):
            raise NameError("unit_translation_bug")

        monkeypatch.setattr(dimensions, "_pint_unit", _boom)

        files = load_claim_files(claims_dir)
        with pytest.raises(NameError, match="unit_translation_bug"):
            validate_claims(files, make_concept_registry())


# ── Wrong error label bug (7C) ──────────────────────────────────────


class TestClaimTypeErrorLabels:
    """Error messages must use the actual claim type, not hardcoded 'observation'."""

    @pytest.mark.parametrize("ctype", ["mechanism", "comparison", "limitation"])
    def test_missing_statement_error_uses_correct_type(self, claims_dir, ctype):
        claim = {
            "id": "claim1",
            "type": ctype,
            "concepts": ["concept1"],
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        # Must say the actual type, not "observation"
        assert any(f"{ctype} claim" in e for e in result.errors), (
            f"Expected '{ctype} claim' in errors, got: {result.errors}"
        )
        assert not any("observation claim" in e for e in result.errors), (
            f"Error should not say 'observation' for {ctype} claims: {result.errors}"
        )

    @pytest.mark.parametrize("ctype", ["mechanism", "comparison", "limitation"])
    def test_missing_concepts_error_uses_correct_type(self, claims_dir, ctype):
        claim = {
            "id": "claim1",
            "type": ctype,
            "statement": "Some statement",
            "provenance": {"paper": "test_paper", "page": 1},
        }
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        files = load_claim_files(claims_dir)
        result = validate_claims(files, make_concept_registry())
        assert not result.ok
        assert any(f"{ctype} claim" in e for e in result.errors), (
            f"Expected '{ctype} claim' in errors, got: {result.errors}"
        )
        assert not any("observation claim" in e for e in result.errors), (
            f"Error should not say 'observation' for {ctype} claims: {result.errors}"
        )


# ── Non-numeric bounds / uncertainty ────────────────────────────────


class TestNonNumericBounds:
    """Validation must reject non-numeric lower_bound, upper_bound, and uncertainty."""

    def test_non_numeric_lower_bound(self, claims_dir):
        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            lower_bound="abc", upper_bound=450.0,
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="lower_bound"):
            load_claim_files(claims_dir)

    def test_non_numeric_upper_bound(self, claims_dir):
        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            lower_bound=430.0, upper_bound="not_a_number",
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="upper_bound"):
            load_claim_files(claims_dir)

    def test_non_numeric_uncertainty(self, claims_dir):
        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            uncertainty="high", uncertainty_type="std",
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="uncertainty"):
            load_claim_files(claims_dir)

    def test_numeric_string_bounds_fail_at_document_boundary(self, claims_dir):
        claim = make_parameter_claim(
            "claim1", "concept1", 440.0, "Hz",
            lower_bound="430.5", upper_bound="450.5",
        )
        data = make_claim_file_data([claim])
        write_claim_file(claims_dir, "test_paper.yaml", data)

        with pytest.raises(DocumentSchemaError, match="lower_bound"):
            load_claim_files(claims_dir)
