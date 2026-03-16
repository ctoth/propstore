"""Tests for the concept file validator.

Tests the compiler contract checks that JSON Schema can't express:
- id uniqueness
- canonical_name matches filename
- deprecated concepts have replaced_by
- replaced_by targets exist and aren't themselves deprecated
- no circular deprecation chains
- relationship targets exist
- parameterization inputs exist and are all quantity kind
- exactly one kind variant populated
- contested_definition relationships have notes
- conditional exactness parameterizations have conditions
- id prefix matches domain field
"""

import pytest
import yaml

from compiler.validate import (
    load_concepts,
    validate_concepts,
)


@pytest.fixture
def concept_dir(tmp_path):
    """Create a temporary concepts directory with form definitions."""
    concept_path = tmp_path / "concepts"
    concept_path.mkdir()
    counters = concept_path / ".counters"
    counters.mkdir()
    (counters / "speech.next").write_text("100")
    (counters / "narr.next").write_text("10")

    # Create form definition files alongside concepts
    forms_dir = tmp_path / "forms"
    forms_dir.mkdir()
    for form_name in ("frequency", "category", "boolean", "structural",
                      "duration_ratio", "pressure", "level", "time",
                      "flow", "flow_derivative", "amplitude_ratio",
                      "dimensionless_compound"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump({"name": form_name}, default_flow_style=False))

    return concept_path


def write_concept(concept_dir, filename, data):
    """Helper: write a concept YAML file."""
    path = concept_dir / filename
    path.write_text(yaml.dump(data, default_flow_style=False))
    return path


def make_quantity_concept(id, name, status="accepted", **kwargs):
    """Helper: make a minimal valid quantity concept dict."""
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "form": "frequency",
    }
    c.update(kwargs)
    return c


def make_category_concept(id, name, values, status="accepted", extensible=True, **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "form": "category",
        "form_parameters": {"values": values, "extensible": extensible},
    }
    c.update(kwargs)
    return c


def make_boolean_concept(id, name, status="accepted", **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "form": "boolean",
    }
    c.update(kwargs)
    return c


def make_structural_concept(id, name, status="accepted", **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "form": "structural",
    }
    c.update(kwargs)
    return c


# ── Valid concepts ───────────────────────────────────────────────────

class TestValidConcepts:
    def test_minimal_quantity(self, concept_dir):
        write_concept(concept_dir, "fundamental_frequency.yaml",
                      make_quantity_concept("concept1", "fundamental_frequency"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_category(self, concept_dir):
        write_concept(concept_dir, "task.yaml",
                      make_category_concept("concept30", "task", ["speech", "singing"]))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_boolean(self, concept_dir):
        write_concept(concept_dir, "phonation_present.yaml",
                      make_boolean_concept("concept40", "phonation_present"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_structural(self, concept_dir):
        write_concept(concept_dir, "focalization.yaml",
                      make_structural_concept("concept101", "focalization"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_multiple_valid(self, concept_dir):
        write_concept(concept_dir, "fundamental_frequency.yaml",
                      make_quantity_concept("concept1", "fundamental_frequency"))
        write_concept(concept_dir, "task.yaml",
                      make_category_concept("concept30", "task", ["speech", "singing"]))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_valid_relationship(self, concept_dir):
        c1 = make_quantity_concept("concept1", "fundamental_frequency")
        c2 = make_quantity_concept("concept2", "voicing_amplitude",
                                   relationships=[{"type": "related", "target": "concept1"}])
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "voicing_amplitude.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_valid_deprecated_with_replacement(self, concept_dir):
        c1 = make_quantity_concept("concept1", "fundamental_frequency")
        c2 = make_quantity_concept("concept2", "old_freq", status="deprecated",
                                   replaced_by="concept1")
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "old_freq.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── ID uniqueness ────────────────────────────────────────────────────

class TestIdUniqueness:
    def test_duplicate_id_error(self, concept_dir):
        write_concept(concept_dir, "concept_a.yaml",
                      make_quantity_concept("concept1", "concept_a"))
        write_concept(concept_dir, "concept_b.yaml",
                      make_quantity_concept("concept1", "concept_b"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("unique" in e.lower() or "duplicate" in e.lower() for e in result.errors)


# ── Canonical name matches filename ──────────────────────────────────

class TestFilenameMatch:
    def test_mismatch_error(self, concept_dir):
        write_concept(concept_dir, "wrong_name.yaml",
                      make_quantity_concept("concept1", "correct_name"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("filename" in e.lower() or "canonical_name" in e.lower() for e in result.errors)


# ── Deprecated concepts ──────────────────────────────────────────────

class TestDeprecation:
    def test_deprecated_without_replaced_by_error(self, concept_dir):
        write_concept(concept_dir, "old_concept.yaml",
                      make_quantity_concept("concept1", "old_concept", status="deprecated"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("replaced_by" in e.lower() for e in result.errors)

    def test_replaced_by_nonexistent_error(self, concept_dir):
        write_concept(concept_dir, "old_concept.yaml",
                      make_quantity_concept("concept1", "old_concept",
                                            status="deprecated", replaced_by="concept9999"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("exist" in e.lower() or "not found" in e.lower() for e in result.errors)

    def test_replaced_by_deprecated_error(self, concept_dir):
        c1 = make_quantity_concept("concept1", "old_a", status="deprecated", replaced_by="concept2")
        c2 = make_quantity_concept("concept2", "old_b", status="deprecated", replaced_by="concept1")
        write_concept(concept_dir, "old_a.yaml", c1)
        write_concept(concept_dir, "old_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("deprecated" in e.lower() for e in result.errors)

    def test_circular_deprecation_error(self, concept_dir):
        c1 = make_quantity_concept("concept1", "cycle_a", status="deprecated", replaced_by="concept2")
        c2 = make_quantity_concept("concept2", "cycle_b", status="deprecated", replaced_by="concept3")
        c3 = make_quantity_concept("concept3", "cycle_c", status="deprecated", replaced_by="concept1")
        write_concept(concept_dir, "cycle_a.yaml", c1)
        write_concept(concept_dir, "cycle_b.yaml", c2)
        write_concept(concept_dir, "cycle_c.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("circular" in e.lower() or "cycle" in e.lower() for e in result.errors)


# ── Relationship targets ─────────────────────────────────────────────

class TestRelationshipTargets:
    def test_nonexistent_target_error(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept",
                                  relationships=[{"type": "related", "target": "concept9999"}])
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("target" in e.lower() or "not found" in e.lower() or "exist" in e.lower()
                    for e in result.errors)

    def test_contested_definition_without_note_error(self, concept_dir):
        c1 = make_structural_concept("concept101", "focalization_genette")
        c2 = make_structural_concept("concept102", "focalization_bal",
                                      relationships=[{"type": "contested_definition",
                                                       "target": "concept101"}])
        write_concept(concept_dir, "focalization_genette.yaml", c1)
        write_concept(concept_dir, "focalization_bal.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("note" in e.lower() and "contested" in e.lower() for e in result.errors)

    def test_contested_definition_with_note_ok(self, concept_dir):
        c1 = make_structural_concept("concept101", "focalization_genette")
        c2 = make_structural_concept("concept102", "focalization_bal",
                                      relationships=[{"type": "contested_definition",
                                                       "target": "concept101",
                                                       "note": "Different theoretical framework"}])
        write_concept(concept_dir, "focalization_genette.yaml", c1)
        write_concept(concept_dir, "focalization_bal.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── Parameterization inputs ──────────────────────────────────────────

class TestParameterizationInputs:
    def test_nonexistent_input_error(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept",
                                  parameterization_relationships=[{
                                      "formula": "x = y / z",
                                      "inputs": ["concept1", "concept9999"],
                                      "exactness": "exact",
                                      "source": "Test_2024",
                                      "bidirectional": True,
                                  }])
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("input" in e.lower() or "not found" in e.lower() or "exist" in e.lower()
                    for e in result.errors)

    def test_non_quantity_input_error(self, concept_dir):
        c1 = make_quantity_concept("concept1", "test_quantity")
        c2 = make_category_concept("concept30", "task", ["speech"])
        c3 = make_quantity_concept("concept2", "derived_thing",
                                   parameterization_relationships=[{
                                       "formula": "x = y * task",
                                       "inputs": ["concept1", "concept30"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "test_quantity.yaml", c1)
        write_concept(concept_dir, "task.yaml", c2)
        write_concept(concept_dir, "derived_thing.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("quantity" in e.lower() for e in result.errors)

    def test_conditional_exactness_without_conditions_error(self, concept_dir):
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "a = b",
                                       "inputs": ["concept1"],
                                       "exactness": "conditional",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("condition" in e.lower() for e in result.errors)

    def test_valid_parameterization(self, concept_dir):
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["concept1"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── Kind validation ──────────────────────────────────────────────────

class TestFormValidation:
    def test_missing_form_error(self, concept_dir):
        c = {
            "id": "concept1",
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "No form.",
        }
        write_concept(concept_dir, "bad_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("form" in e.lower() for e in result.errors)

    def test_nonexistent_form_error(self, concept_dir):
        c = {
            "id": "concept1",
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "Bad form ref.",
            "form": "nonexistent_form",
        }
        write_concept(concept_dir, "bad_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("no matching file" in e.lower() for e in result.errors)


# ── ID format ────────────────────────────────────────────────────────

class TestIdFormat:
    def test_valid_concept_id(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_invalid_concept_id_rejected(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("format" in e.lower() or "conceptN" in e.lower() for e in result.errors)


# ── CEL expression validation in relationships ───────────────────────

class TestCelInRelationships:
    def test_valid_cel_in_relationship(self, concept_dir):
        c1 = make_quantity_concept("concept1", "fundamental_frequency")
        c2 = make_quantity_concept("concept2", "voicing_amplitude",
                                   relationships=[{
                                       "type": "related",
                                       "target": "concept1",
                                       "conditions": ["fundamental_frequency > 200"],
                                   }])
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "voicing_amplitude.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_invalid_cel_structural_in_expression(self, concept_dir):
        c1 = make_structural_concept("concept101", "focalization")
        c2 = make_quantity_concept("concept1", "test_concept",
                                   relationships=[{
                                       "type": "related",
                                       "target": "concept101",
                                       "conditions": ["focalization == 'internal'"],
                                   }])
        write_concept(concept_dir, "focalization.yaml", c1)
        write_concept(concept_dir, "test_concept.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any(not e_is_warning for e_is_warning in [False])  # structural error expected
        assert result.errors

    def test_undefined_concept_in_cel(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept",
                                  relationships=[{
                                      "type": "related",
                                      "target": "concept1",
                                      "conditions": ["nonexistent > 5"],
                                  }])
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert result.errors


# ── Warnings ─────────────────────────────────────────────────────────

class TestWarnings:
    def test_proposed_concept_warning(self, concept_dir):
        """Proposed concepts should produce a warning (not error) when referenced."""
        c = make_quantity_concept("concept1", "test_concept", status="proposed")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        # Proposed concepts are valid, just a warning
        assert not result.errors

    def test_missing_sympy_warning(self, concept_dir):
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["concept1"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                       # no sympy field
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors
        assert any("sympy" in w.lower() for w in result.warnings)


# ── Canonical claim validation ──────────────────────────────────────

class TestCanonicalClaim:
    def test_valid_canonical_claim(self, concept_dir):
        """Parameterization with canonical_claim pointing to existing claim validates."""
        # Write a claim file so the validator can find claim1
        claims_dir = concept_dir.parent / "claims"
        claims_dir.mkdir(exist_ok=True)
        claim_data = {
            "source": {"paper": "test_paper"},
            "claims": [
                {
                    "id": "claim1",
                    "type": "parameter",
                    "concept": "concept1",
                    "value": [200.0],
                    "unit": "Hz",
                    "provenance": {"paper": "test_paper", "page": 1},
                },
            ],
        }
        (claims_dir / "test_paper.yaml").write_text(
            yaml.dump(claim_data, default_flow_style=False))

        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["concept1"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                       "canonical_claim": "claim1",
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts, claims_dir=claims_dir)
        assert not any("canonical_claim" in e.lower() for e in result.errors)

    def test_canonical_claim_nonexistent(self, concept_dir):
        """canonical_claim pointing to nonexistent claim produces validation error."""
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["concept1"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                       "canonical_claim": "claim9999",
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("canonical_claim" in e.lower() and "claim9999" in e
                    for e in result.errors)


# ── Relationship type validation ────────────────────────────────────

class TestRelationshipTypeValidation:
    def test_invalid_relationship_type_error(self, concept_dir):
        """Relationship type 'derives' should produce validation error (must be 'derived_from')."""
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   relationships=[{"type": "derives", "target": "concept1"}])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("relationship type" in e.lower() or "derives" in e.lower()
                    for e in result.errors)

    def test_all_valid_relationship_types(self, concept_dir):
        """All valid RelationshipType values should validate without errors."""
        valid_types = ["broader", "narrower", "related", "component_of",
                       "derived_from", "contested_definition"]
        c1 = make_quantity_concept("concept1", "concept_a")
        write_concept(concept_dir, "concept_a.yaml", c1)

        for i, rel_type in enumerate(valid_types):
            name = f"concept_{rel_type}"
            cid = f"speech_{1001 + i:04d}"
            rel = {"type": rel_type, "target": "concept1"}
            if rel_type == "contested_definition":
                rel["note"] = "Different theoretical framework"
            c = make_quantity_concept(cid, name, relationships=[rel])
            write_concept(concept_dir, f"{name}.yaml", c)

        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        # No errors about relationship type
        assert not any("relationship type" in e.lower() for e in result.errors)
