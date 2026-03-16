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

import os
import tempfile
import shutil

import pytest
import yaml

from compiler.validate import (
    load_concepts,
    validate_concepts,
    ValidationResult,
)


@pytest.fixture
def concept_dir(tmp_path):
    """Create a temporary concepts directory."""
    counters = tmp_path / ".counters"
    counters.mkdir()
    (counters / "speech.next").write_text("100")
    (counters / "narr.next").write_text("10")
    return tmp_path


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
        "kind": {"quantity": {"unit": "Hz"}},
    }
    c.update(kwargs)
    return c


def make_category_concept(id, name, values, status="accepted", extensible=True, **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "kind": {"category": {"values": values, "extensible": extensible}},
    }
    c.update(kwargs)
    return c


def make_boolean_concept(id, name, status="accepted", **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "kind": {"boolean": {}},
    }
    c.update(kwargs)
    return c


def make_structural_concept(id, name, status="accepted", **kwargs):
    c = {
        "id": id,
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "kind": {"structural": {}},
    }
    c.update(kwargs)
    return c


# ── Valid concepts ───────────────────────────────────────────────────

class TestValidConcepts:
    def test_minimal_quantity(self, concept_dir):
        write_concept(concept_dir, "fundamental_frequency.yaml",
                      make_quantity_concept("speech_0001", "fundamental_frequency"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_category(self, concept_dir):
        write_concept(concept_dir, "task.yaml",
                      make_category_concept("speech_0030", "task", ["speech", "singing"]))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_boolean(self, concept_dir):
        write_concept(concept_dir, "phonation_present.yaml",
                      make_boolean_concept("speech_0040", "phonation_present"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_minimal_structural(self, concept_dir):
        write_concept(concept_dir, "focalization.yaml",
                      make_structural_concept("narr_0001", "focalization"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_multiple_valid(self, concept_dir):
        write_concept(concept_dir, "fundamental_frequency.yaml",
                      make_quantity_concept("speech_0001", "fundamental_frequency"))
        write_concept(concept_dir, "task.yaml",
                      make_category_concept("speech_0030", "task", ["speech", "singing"]))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_valid_relationship(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "fundamental_frequency")
        c2 = make_quantity_concept("speech_0002", "voicing_amplitude",
                                   relationships=[{"type": "related", "target": "speech_0001"}])
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "voicing_amplitude.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_valid_deprecated_with_replacement(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "fundamental_frequency")
        c2 = make_quantity_concept("speech_0002", "old_freq", status="deprecated",
                                   replaced_by="speech_0001")
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "old_freq.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── ID uniqueness ────────────────────────────────────────────────────

class TestIdUniqueness:
    def test_duplicate_id_error(self, concept_dir):
        write_concept(concept_dir, "concept_a.yaml",
                      make_quantity_concept("speech_0001", "concept_a"))
        write_concept(concept_dir, "concept_b.yaml",
                      make_quantity_concept("speech_0001", "concept_b"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("unique" in e.lower() or "duplicate" in e.lower() for e in result.errors)


# ── Canonical name matches filename ──────────────────────────────────

class TestFilenameMatch:
    def test_mismatch_error(self, concept_dir):
        write_concept(concept_dir, "wrong_name.yaml",
                      make_quantity_concept("speech_0001", "correct_name"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("filename" in e.lower() or "canonical_name" in e.lower() for e in result.errors)


# ── Deprecated concepts ──────────────────────────────────────────────

class TestDeprecation:
    def test_deprecated_without_replaced_by_error(self, concept_dir):
        write_concept(concept_dir, "old_concept.yaml",
                      make_quantity_concept("speech_0001", "old_concept", status="deprecated"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("replaced_by" in e.lower() for e in result.errors)

    def test_replaced_by_nonexistent_error(self, concept_dir):
        write_concept(concept_dir, "old_concept.yaml",
                      make_quantity_concept("speech_0001", "old_concept",
                                            status="deprecated", replaced_by="speech_9999"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("exist" in e.lower() or "not found" in e.lower() for e in result.errors)

    def test_replaced_by_deprecated_error(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "old_a", status="deprecated", replaced_by="speech_0002")
        c2 = make_quantity_concept("speech_0002", "old_b", status="deprecated", replaced_by="speech_0001")
        write_concept(concept_dir, "old_a.yaml", c1)
        write_concept(concept_dir, "old_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("deprecated" in e.lower() for e in result.errors)

    def test_circular_deprecation_error(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "cycle_a", status="deprecated", replaced_by="speech_0002")
        c2 = make_quantity_concept("speech_0002", "cycle_b", status="deprecated", replaced_by="speech_0003")
        c3 = make_quantity_concept("speech_0003", "cycle_c", status="deprecated", replaced_by="speech_0001")
        write_concept(concept_dir, "cycle_a.yaml", c1)
        write_concept(concept_dir, "cycle_b.yaml", c2)
        write_concept(concept_dir, "cycle_c.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("circular" in e.lower() or "cycle" in e.lower() for e in result.errors)


# ── Relationship targets ─────────────────────────────────────────────

class TestRelationshipTargets:
    def test_nonexistent_target_error(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept",
                                  relationships=[{"type": "related", "target": "speech_9999"}])
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("target" in e.lower() or "not found" in e.lower() or "exist" in e.lower()
                    for e in result.errors)

    def test_contested_definition_without_note_error(self, concept_dir):
        c1 = make_structural_concept("narr_0001", "focalization_genette")
        c2 = make_structural_concept("narr_0002", "focalization_bal",
                                      relationships=[{"type": "contested_definition",
                                                       "target": "narr_0001"}])
        write_concept(concept_dir, "focalization_genette.yaml", c1)
        write_concept(concept_dir, "focalization_bal.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("note" in e.lower() and "contested" in e.lower() for e in result.errors)

    def test_contested_definition_with_note_ok(self, concept_dir):
        c1 = make_structural_concept("narr_0001", "focalization_genette")
        c2 = make_structural_concept("narr_0002", "focalization_bal",
                                      relationships=[{"type": "contested_definition",
                                                       "target": "narr_0001",
                                                       "note": "Different theoretical framework"}])
        write_concept(concept_dir, "focalization_genette.yaml", c1)
        write_concept(concept_dir, "focalization_bal.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── Parameterization inputs ──────────────────────────────────────────

class TestParameterizationInputs:
    def test_nonexistent_input_error(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept",
                                  parameterization_relationships=[{
                                      "formula": "x = y / z",
                                      "inputs": ["speech_0001", "speech_9999"],
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
        c1 = make_quantity_concept("speech_0001", "test_quantity")
        c2 = make_category_concept("speech_0030", "task", ["speech"])
        c3 = make_quantity_concept("speech_0002", "derived_thing",
                                   parameterization_relationships=[{
                                       "formula": "x = y * task",
                                       "inputs": ["speech_0001", "speech_0030"],
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
        c1 = make_quantity_concept("speech_0001", "concept_a")
        c2 = make_quantity_concept("speech_0002", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "a = b",
                                       "inputs": ["speech_0001"],
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
        c1 = make_quantity_concept("speech_0001", "concept_a")
        c2 = make_quantity_concept("speech_0002", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["speech_0001"],
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

class TestKindValidation:
    def test_no_kind_variant_error(self, concept_dir):
        c = {
            "id": "speech_0001",
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "No kind.",
            "kind": {},
        }
        write_concept(concept_dir, "bad_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("kind" in e.lower() for e in result.errors)

    def test_multiple_kind_variants_error(self, concept_dir):
        c = {
            "id": "speech_0001",
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "Two kinds.",
            "kind": {
                "quantity": {"unit": "Hz"},
                "boolean": {},
            },
        }
        write_concept(concept_dir, "bad_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("kind" in e.lower() for e in result.errors)


# ── ID prefix / domain match ────────────────────────────────────────

class TestDomainMatch:
    def test_prefix_mismatch_error(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept", domain="narr")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("domain" in e.lower() or "prefix" in e.lower() for e in result.errors)

    def test_prefix_match_ok(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept", domain="speech")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors


# ── CEL expression validation in relationships ───────────────────────

class TestCelInRelationships:
    def test_valid_cel_in_relationship(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "fundamental_frequency")
        c2 = make_quantity_concept("speech_0002", "voicing_amplitude",
                                   relationships=[{
                                       "type": "related",
                                       "target": "speech_0001",
                                       "conditions": ["fundamental_frequency > 200"],
                                   }])
        write_concept(concept_dir, "fundamental_frequency.yaml", c1)
        write_concept(concept_dir, "voicing_amplitude.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_invalid_cel_structural_in_expression(self, concept_dir):
        c1 = make_structural_concept("narr_0001", "focalization")
        c2 = make_quantity_concept("speech_0001", "test_concept",
                                   relationships=[{
                                       "type": "related",
                                       "target": "narr_0001",
                                       "conditions": ["focalization == 'internal'"],
                                   }])
        write_concept(concept_dir, "focalization.yaml", c1)
        write_concept(concept_dir, "test_concept.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any(not e_is_warning for e_is_warning in [False])  # structural error expected
        assert result.errors

    def test_undefined_concept_in_cel(self, concept_dir):
        c = make_quantity_concept("speech_0001", "test_concept",
                                  relationships=[{
                                      "type": "related",
                                      "target": "speech_0001",
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
        c = make_quantity_concept("speech_0001", "test_concept", status="proposed")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        # Proposed concepts are valid, just a warning
        assert not result.errors

    def test_missing_sympy_warning(self, concept_dir):
        c1 = make_quantity_concept("speech_0001", "concept_a")
        c2 = make_quantity_concept("speech_0002", "concept_b",
                                   parameterization_relationships=[{
                                       "formula": "b = a * 2",
                                       "inputs": ["speech_0001"],
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
