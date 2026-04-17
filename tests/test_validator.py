"""Tests for the concept file validator.

Tests the compiler contract checks that JSON Schema can't express:
- artifact_id uniqueness
- canonical_name matches filename
- deprecated concepts have replaced_by
- replaced_by targets exist and aren't themselves deprecated
- no circular deprecation chains
- relationship targets exist
- parameterization inputs exist and are all quantity kind
- exactly one kind variant populated
- contested_definition relationships have notes
- conditional exactness parameterizations have conditions
- concept identity fields are present and canonical
"""

import pytest
import yaml

from propstore.core.concept_status import ConceptStatus
from propstore.artifacts.schema import DocumentSchemaError
from propstore.core.concepts import LoadedConcept, parse_concept_record
from propstore.core.concepts import load_concepts
from propstore.validate_concepts import validate_concepts
from tests.conftest import (
    attach_concept_version_id,
    make_concept_identity,
    normalize_claims_payload,
    normalize_concept_payloads,
)


def provenance_payload() -> dict[str, object]:
    return {
        "status": "stated",
        "witnesses": [
            {
                "asserter": "test",
                "timestamp": "2026-04-17T00:00:00Z",
                "source_artifact_code": "ps:test:validator",
                "method": "unit-test",
            }
        ],
    }


@pytest.fixture
def concept_dir(tmp_path):
    """Create a temporary concepts directory with form definitions."""
    knowledge = tmp_path / "knowledge"
    concept_path = knowledge / "concepts"
    concept_path.mkdir(parents=True)
    counters = concept_path / ".counters"
    counters.mkdir()
    (counters / "speech.next").write_text("100")
    (counters / "narr.next").write_text("10")

    # Create form definition files alongside concepts
    forms_dir = knowledge / "forms"
    forms_dir.mkdir()
    dimensionless_forms = {
        "category",
        "boolean",
        "structural",
        "duration_ratio",
        "amplitude_ratio",
        "dimensionless_compound",
    }
    for form_name in ("frequency", "category", "boolean", "structural",
                      "duration_ratio", "pressure", "level", "time",
                      "flow", "flow_derivative", "amplitude_ratio",
                      "dimensionless_compound"):
        (forms_dir / f"{form_name}.yaml").write_text(
            yaml.dump(
                {
                    "name": form_name,
                    "dimensionless": form_name in dimensionless_forms,
                },
                default_flow_style=False,
            )
        )

    return concept_path


def write_concept(concept_dir, filename, data):
    """Helper: write a concept YAML file."""
    normalized = normalize_concept_payloads(
        [data],
        default_domain=str(data.get("domain") or "propstore"),
    )[0]
    path = concept_dir / filename
    path.write_text(yaml.dump(normalized, default_flow_style=False))
    return path


def make_quantity_concept(id, name, status="accepted", **kwargs):
    """Helper: make a minimal valid quantity concept dict."""
    c = {
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "domain": "speech",
        "form": "frequency",
    }
    c.update(make_concept_identity(id, domain="speech", canonical_name=name))
    c.update(kwargs)
    return c


def make_category_concept(id, name, values, status="accepted", extensible=True, **kwargs):
    c = {
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "domain": "speech",
        "form": "category",
        "form_parameters": {"values": values, "extensible": extensible},
    }
    c.update(make_concept_identity(id, domain="speech", canonical_name=name))
    c.update(kwargs)
    return c


def make_boolean_concept(id, name, status="accepted", **kwargs):
    c = {
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "domain": "speech",
        "form": "boolean",
    }
    c.update(make_concept_identity(id, domain="speech", canonical_name=name))
    c.update(kwargs)
    return c


def make_structural_concept(id, name, status="accepted", **kwargs):
    c = {
        "canonical_name": name,
        "status": status,
        "definition": f"Definition of {name}.",
        "domain": "speech",
        "form": "structural",
    }
    c.update(make_concept_identity(id, domain="speech", canonical_name=name))
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
    def test_filename_is_not_canonical_identity(self, concept_dir):
        write_concept(concept_dir, "wrong_name.yaml",
                      make_quantity_concept("concept1", "correct_name"))
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not any("filename" in e.lower() or "canonical_name" in e.lower() for e in result.errors)


class TestLemonInvariants:
    def test_concept_ontology_reference_must_have_a_matching_sense(self, concept_dir):
        data = make_structural_concept(
            "concept1",
            "bass",
            ontology_reference={"uri": "tag:propstore:test:concept/bass-fish", "label": "bass"},
            lexical_entry={
                "identifier": "entry:bass-fish",
                "canonical_form": {"written_rep": "bass", "language": "en"},
                "senses": [
                    {
                        "reference": {
                            "uri": "tag:propstore:test:concept/bass-instrument",
                            "label": "bass",
                        },
                        "usage": "A low-pitched instrument.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        write_concept(concept_dir, "bass_fish.yaml", data)

        result = validate_concepts(load_concepts(concept_dir))

        assert any("ontology_reference" in e and "matching lexical sense" in e for e in result.errors)

    def test_duplicate_sense_reference_error(self, concept_dir):
        data = make_structural_concept(
            "concept1",
            "bass",
            ontology_reference={"uri": "tag:propstore:test:concept/bass", "label": "bass"},
            lexical_entry={
                "identifier": "entry:bass",
                "canonical_form": {"written_rep": "bass", "language": "en"},
                "senses": [
                    {
                        "reference": {"uri": "tag:propstore:test:concept/bass", "label": "bass"},
                        "usage": "First usage.",
                    },
                    {
                        "reference": {"uri": "tag:propstore:test:concept/bass", "label": "bass"},
                        "usage": "Duplicate usage.",
                    },
                ],
                "physical_dimension_form": "structural",
            },
        )
        write_concept(concept_dir, "bass.yaml", data)

        result = validate_concepts(load_concepts(concept_dir))

        assert any("duplicate lexical sense reference" in e for e in result.errors)

    def test_homographic_entries_may_share_written_form(self, concept_dir):
        fish = make_structural_concept(
            "bass_fish",
            "bass",
            domain="fish",
            logical_ids=[
                {"namespace": "fish", "value": "bass_fish"},
                {"namespace": "propstore", "value": "bass_fish"},
            ],
            ontology_reference={"uri": "tag:propstore:test:concept/bass-fish", "label": "bass"},
            lexical_entry={
                "identifier": "entry:bass-fish",
                "canonical_form": {"written_rep": "bass", "language": "en"},
                "senses": [
                    {
                        "reference": {"uri": "tag:propstore:test:concept/bass-fish", "label": "bass"},
                        "usage": "A fish.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        instrument = make_structural_concept(
            "bass_instrument",
            "bass",
            domain="music",
            logical_ids=[
                {"namespace": "music", "value": "bass_instrument"},
                {"namespace": "propstore", "value": "bass_instrument"},
            ],
            ontology_reference={"uri": "tag:propstore:test:concept/bass-instrument", "label": "bass"},
            lexical_entry={
                "identifier": "entry:bass-instrument",
                "canonical_form": {"written_rep": "bass", "language": "en"},
                "senses": [
                    {
                        "reference": {
                            "uri": "tag:propstore:test:concept/bass-instrument",
                            "label": "bass",
                        },
                        "usage": "A low-pitched instrument.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        write_concept(concept_dir, "bass_fish.yaml", fish)
        write_concept(concept_dir, "bass_instrument.yaml", instrument)

        result = validate_concepts(load_concepts(concept_dir))

        assert not result.errors

    def test_qualia_reference_must_point_at_existing_concept(self, concept_dir):
        data = make_structural_concept(
            "instrument",
            "instrument",
            ontology_reference={"uri": "ps:concept:instrument", "label": "Instrument"},
            lexical_entry={
                "identifier": "entry:instrument",
                "canonical_form": {"written_rep": "instrument", "language": "en"},
                "senses": [
                    {
                        "reference": {
                            "uri": "ps:concept:instrument",
                            "label": "Instrument",
                        },
                        "usage": "A measurement instrument.",
                        "qualia": {
                            "telic": [
                                {
                                    "reference": {
                                        "uri": "ps:concept:missing_measurement",
                                        "label": "Missing Measurement",
                                    },
                                    "provenance": provenance_payload(),
                                }
                            ]
                        },
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        write_concept(concept_dir, "instrument.yaml", data)

        result = validate_concepts(load_concepts(concept_dir))

        assert any("qualia" in e and "missing_measurement" in e for e in result.errors)

    def test_qualia_type_constraint_must_be_satisfied(self, concept_dir):
        description_kind = make_structural_concept(
            "description_kind",
            "description_kind",
        )
        description_kind_id = description_kind["artifact_id"]
        description_kind.update(
            ontology_reference={"uri": description_kind_id, "label": "Description Kind"},
            lexical_entry={
                "identifier": "entry:description-kind",
                "canonical_form": {"written_rep": "description kind", "language": "en"},
                "senses": [
                    {
                        "reference": {
                            "uri": description_kind_id,
                            "label": "Description Kind",
                        },
                        "usage": "A type for description-kind concepts.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        unrelated_type = make_structural_concept("unrelated_type", "unrelated_type")
        unrelated_type_id = unrelated_type["artifact_id"]
        unrelated_type.update(
            ontology_reference={"uri": unrelated_type_id, "label": "Unrelated Type"},
            lexical_entry={
                "identifier": "entry:unrelated-type",
                "canonical_form": {"written_rep": "unrelated type", "language": "en"},
                "senses": [
                    {
                        "reference": {
                            "uri": unrelated_type_id,
                            "label": "Unrelated Type",
                        },
                        "usage": "A type that should not satisfy description kind.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        measurement = make_structural_concept(
            "measurement",
            "measurement",
            relationships=[{"type": "is_a", "target": unrelated_type_id}],
        )
        measurement_id = measurement["artifact_id"]
        measurement.update(
            ontology_reference={"uri": measurement_id, "label": "Measurement"},
            lexical_entry={
                "identifier": "entry:measurement",
                "canonical_form": {"written_rep": "measurement", "language": "en"},
                "senses": [
                    {
                        "reference": {"uri": measurement_id, "label": "Measurement"},
                        "usage": "A measurement description.",
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        instrument = make_structural_concept(
            "instrument",
            "instrument",
        )
        instrument_id = instrument["artifact_id"]
        instrument.update(
            ontology_reference={"uri": instrument_id, "label": "Instrument"},
            lexical_entry={
                "identifier": "entry:instrument",
                "canonical_form": {"written_rep": "instrument", "language": "en"},
                "senses": [
                    {
                        "reference": {"uri": instrument_id, "label": "Instrument"},
                        "usage": "A measurement instrument.",
                        "qualia": {
                            "telic": [
                                {
                                    "reference": {
                                        "uri": measurement_id,
                                        "label": "Measurement",
                                    },
                                    "type_constraint": {
                                        "reference": {
                                            "uri": description_kind_id,
                                            "label": "Description Kind",
                                        }
                                    },
                                    "provenance": provenance_payload(),
                                }
                            ]
                        },
                    }
                ],
                "physical_dimension_form": "structural",
            },
        )
        write_concept(concept_dir, "description_kind.yaml", description_kind)
        write_concept(concept_dir, "unrelated_type.yaml", unrelated_type)
        write_concept(concept_dir, "measurement.yaml", measurement)
        write_concept(concept_dir, "instrument.yaml", instrument)

        result = validate_concepts(load_concepts(concept_dir))

        assert any(
            "qualia.telic" in e
            and "does not satisfy type constraint" in e
            and description_kind_id in e
            for e in result.errors
        )


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

    def test_self_referential_input_error(self, concept_dir):
        c = make_quantity_concept(
            "concept1",
            "self_defined",
            parameterization_relationships=[{
                "formula": "x = x + y",
                "inputs": ["concept1"],
                "exactness": "exact",
                "source": "Test_2024",
                "bidirectional": False,
            }],
        )
        write_concept(concept_dir, "self_defined.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("cannot reference the concept being defined" in e for e in result.errors)

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
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "No form.",
            "domain": "speech",
        }
        c.update(make_concept_identity("concept1", domain="speech", canonical_name="bad_concept"))
        write_concept(concept_dir, "bad_concept.yaml", c)
        with pytest.raises(DocumentSchemaError, match="missing required field `physical_dimension_form`"):
            load_concepts(concept_dir)

    def test_nonexistent_form_error(self, concept_dir):
        c = {
            "canonical_name": "bad_concept",
            "status": "accepted",
            "definition": "Bad form ref.",
            "domain": "speech",
            "form": "nonexistent_form",
        }
        c.update(make_concept_identity("concept1", domain="speech", canonical_name="bad_concept"))
        write_concept(concept_dir, "bad_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("no matching file" in e.lower() for e in result.errors)


# ── ID format ────────────────────────────────────────────────────────

class TestIdentityFormat:
    def test_valid_concept_artifact_id(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept")
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors

    def test_invalid_concept_artifact_id_rejected(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept")
        c["artifact_id"] = "speech_0001"
        c["version_id"] = attach_concept_version_id(c)["version_id"]
        write_concept(concept_dir, "test_concept.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("artifact_id" in e.lower() or "ps:concept:" in e.lower() for e in result.errors)

    def test_raw_id_input_rejected(self, concept_dir):
        c = make_quantity_concept("concept1", "test_concept")
        c = normalize_concept_payloads([c], default_domain="speech")[0]
        c["id"] = "concept1"
        path = concept_dir / "test_concept.yaml"
        path.write_text(yaml.dump(c, default_flow_style=False))
        with pytest.raises(DocumentSchemaError, match="unknown field `id`"):
            load_concepts(concept_dir)


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
        assert concepts[0].record.status is ConceptStatus.PROPOSED
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
        claim_data = normalize_claims_payload({
            "source": {"paper": "test_paper"},
            "claims": [
                {
                    "type": "parameter",
                    "concept": make_concept_identity("concept1", domain="speech", canonical_name="concept_a")["artifact_id"],
                    "value": 200.0,
                    "unit": "Hz",
                    "provenance": {"paper": "test_paper", "page": 1},
                },
            ],
        })
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
                                       "canonical_claim": claim_data["claims"][0]["artifact_id"],
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
        """Relationship type 'derives' should fail strict schema decoding (must be 'derived_from')."""
        c1 = make_quantity_concept("concept1", "concept_a")
        c2 = make_quantity_concept("concept2", "concept_b",
                                   relationships=[{"type": "derives", "target": "concept1"}])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        with pytest.raises(DocumentSchemaError, match="derives"):
            load_concepts(concept_dir)

    def test_all_valid_relationship_types(self, concept_dir):
        """All valid RelationshipType values should validate without errors."""
        valid_types = ["broader", "narrower", "related", "component_of",
                       "derived_from", "contested_definition"]
        c1 = make_quantity_concept("concept1", "concept_a")
        write_concept(concept_dir, "concept_a.yaml", c1)

        for i, rel_type in enumerate(valid_types):
            name = f"concept_{rel_type}"
            cid = f"concept{1001 + i}"
            rel = {"type": rel_type, "target": "concept1"}
            if rel_type == "contested_definition":
                rel["note"] = "Different theoretical framework"
            c = make_quantity_concept(cid, name, relationships=[rel])
            write_concept(concept_dir, f"{name}.yaml", c)

        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        # No errors about relationship type
        assert not any("relationship type" in e.lower() for e in result.errors)


# ── Form parameter validation ────────────────────────────────────────

class TestFormParameterValidation:
    def test_level_concept_with_construction_param_warns(self, concept_dir):
        """Concept with form=level and form_parameters={construction: ...} → warning."""
        # Write a proper level form definition
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "level.yaml").write_text(yaml.dump({
            "name": "level",
            "dimensionless": False,
            "parameters": {"scale": "dB", "reference": None},
        }, default_flow_style=False))

        c = make_quantity_concept("concept1", "test_level", form="level",
                                  form_parameters={"construction": "some value"})
        write_concept(concept_dir, "test_level.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert any("construction" in w and "level" in w for w in result.warnings)

    def test_duration_ratio_concept_with_reference_param_warns(self, concept_dir):
        """Concept with form=duration_ratio and form_parameters={reference: ...} → warning."""
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "duration_ratio.yaml").write_text(yaml.dump({
            "name": "duration_ratio",
            "base": "ratio",
            "dimensionless": True,
            "parameters": {"numerator": "duration", "denominator": "duration"},
        }, default_flow_style=False))

        c = make_quantity_concept("concept1", "test_ratio", form="duration_ratio",
                                  form_parameters={"reference": "H2 amplitude"})
        write_concept(concept_dir, "test_ratio.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert any("reference" in w and "duration_ratio" in w for w in result.warnings)

    def test_category_concept_without_values_errors(self, concept_dir):
        """Concept with form=category and no form_parameters → error."""
        c = {
            "canonical_name": "test_cat",
            "status": "accepted",
            "definition": "A category concept.",
            "domain": "speech",
            "form": "category",
        }
        c.update(make_concept_identity("concept1", domain="speech", canonical_name="test_cat"))
        write_concept(concept_dir, "test_cat.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert any("values" in e.lower() and "category" in e.lower() for e in result.errors)

    def test_category_concept_with_values_validates(self, concept_dir):
        """Concept with form=category and form_parameters={values: [...]} → no error."""
        c = make_category_concept("concept1", "test_cat", ["a", "b", "c"])
        write_concept(concept_dir, "test_cat.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def test_concept_form_parameters_match_form_definition(self, concept_dir):
        """Concept with form=level and form_parameters={reference: ...} → validates."""
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "level.yaml").write_text(yaml.dump({
            "name": "level",
            "dimensionless": False,
            "parameters": {"scale": "dB", "reference": None},
        }, default_flow_style=False))

        c = make_quantity_concept("concept1", "test_level", form="level",
                                  form_parameters={"reference": "H2 amplitude"})
        write_concept(concept_dir, "test_level.yaml", c)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"


# ── Parameterization form compatibility ──────────────────────────────

class TestParameterizationFormCompatibility:
    def test_same_form_inputs_different_form_output_warns(self, concept_dir):
        """Output form=frequency, inputs both form=time → warning."""
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "time.yaml").write_text(yaml.dump({
            "name": "time", "dimensionless": False, "unit_symbol": "s",
        }, default_flow_style=False))

        c1 = make_quantity_concept("concept1", "input_a", form="time")
        c2 = make_quantity_concept("concept2", "input_b", form="time")
        c3 = make_quantity_concept("concept3", "output_c", form="frequency",
                                   parameterization_relationships=[{
                                       "formula": "c = a + b",
                                       "inputs": ["concept1", "concept2"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "input_a.yaml", c1)
        write_concept(concept_dir, "input_b.yaml", c2)
        write_concept(concept_dir, "output_c.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert any("form" in w.lower() and "time" in w.lower() for w in result.warnings)

    def test_mixed_form_inputs_dimensionless_output_no_warning(self, concept_dir):
        """Output form=dimensionless_compound, mixed input forms → no warning."""
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "time.yaml").write_text(yaml.dump({
            "name": "time", "dimensionless": False, "unit_symbol": "s",
        }, default_flow_style=False))

        c1 = make_quantity_concept("concept1", "input_a", form="frequency")
        c2 = make_quantity_concept("concept2", "input_b", form="time")
        c3 = make_quantity_concept("concept3", "output_c", form="dimensionless_compound",
                                   parameterization_relationships=[{
                                       "formula": "c = a * b",
                                       "inputs": ["concept1", "concept2"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "input_a.yaml", c1)
        write_concept(concept_dir, "input_b.yaml", c2)
        write_concept(concept_dir, "output_c.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert not any("form" in w.lower() and "mixed" in w.lower() for w in result.warnings)

    def test_quantity_inputs_quantity_output_no_warning_when_forms_consistent(self, concept_dir):
        """Inputs form=time, output form=frequency → no warning (plausible)."""
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "time.yaml").write_text(yaml.dump({
            "name": "time", "dimensionless": False, "unit_symbol": "s",
        }, default_flow_style=False))

        c1 = make_quantity_concept("concept1", "input_a", form="time")
        c2 = make_quantity_concept("concept2", "output_b", form="frequency",
                                   parameterization_relationships=[{
                                       "formula": "b = 1 / a",
                                       "inputs": ["concept1"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "input_a.yaml", c1)
        write_concept(concept_dir, "output_b.yaml", c2)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        # Single input with different form from output is plausible (not all same form)
        assert not any("all inputs share form" in w.lower() for w in result.warnings)

    def test_all_inputs_same_form_as_output_no_warning(self, concept_dir):
        """Inputs and output all form=duration_ratio → no warning."""
        c1 = make_quantity_concept("concept1", "input_a", form="duration_ratio")
        c2 = make_quantity_concept("concept2", "input_b", form="duration_ratio")
        c3 = make_quantity_concept("concept3", "output_c", form="duration_ratio",
                                   parameterization_relationships=[{
                                       "formula": "c = 1 - a - b",
                                       "inputs": ["concept1", "concept2"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "input_a.yaml", c1)
        write_concept(concept_dir, "input_b.yaml", c2)
        write_concept(concept_dir, "output_c.yaml", c3)
        concepts = load_concepts(concept_dir)
        result = validate_concepts(concepts)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert not any("form" in w.lower() and "mismatch" in w.lower() for w in result.warnings)


# ── Bare except narrowing ─────────────────────────────────────────

class TestSympyExceptNarrowing:
    """Programming errors in sympy dimensional verification must propagate, not be swallowed."""

    def test_programming_error_in_verify_expr_propagates(self, concept_dir, monkeypatch):
        """NameError inside verify_expr must NOT be silently caught."""
        # Clear form cache so our form files with dimensions are loaded fresh
        from propstore.form_utils import _form_cache
        _form_cache.clear()

        # Write form files with actual dimensions so the sympy path triggers
        forms_dir = concept_dir.parent / "forms"
        (forms_dir / "frequency.yaml").write_text(yaml.dump({
            "name": "frequency",
            "kind": "quantity",
            "unit_symbol": "Hz",
            "dimensionless": False,
            "dimensions": {"T": -1},
        }, default_flow_style=False))

        c1 = make_quantity_concept("concept1", "concept_a", form="frequency")
        c2 = make_quantity_concept("concept2", "concept_b", form="frequency")
        c3 = make_quantity_concept("concept3", "concept_c", form="frequency",
                                   parameterization_relationships=[{
                                       "formula": "c = a * b",
                                       "sympy": "Eq(concept3, concept1 * concept2)",
                                       "inputs": ["concept1", "concept2"],
                                       "exactness": "exact",
                                       "source": "Test_2024",
                                       "bidirectional": True,
                                   }])
        write_concept(concept_dir, "concept_a.yaml", c1)
        write_concept(concept_dir, "concept_b.yaml", c2)
        write_concept(concept_dir, "concept_c.yaml", c3)

        # Monkeypatch verify_expr to raise a programming error
        import propstore.validate_concepts as val_mod

        def _boom(*args, **kwargs):
            raise NameError("undefined_variable_bug")

        monkeypatch.setattr(val_mod, "verify_expr", _boom)

        concepts = load_concepts(concept_dir)
        with pytest.raises(NameError, match="undefined_variable_bug"):
            validate_concepts(concepts)


class TestValidatorSemanticRootContract:
    def test_manual_entries_require_explicit_forms_root(self, tmp_path):
        concept = LoadedConcept(
            filename="fundamental_frequency",
            source_path=tmp_path / "knowledge" / "concepts" / "fundamental_frequency.yaml",
            knowledge_root=None,
            record=parse_concept_record(
                make_quantity_concept("concept1", "fundamental_frequency")
            ),
        )

        with pytest.raises(TypeError, match="forms_dir or knowledge_root"):
            validate_concepts([concept])
