from __future__ import annotations

import pytest

from quire.documents import DocumentSchemaError, convert_document

from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.models import FORM_CHARTER
from propstore.families.registry import ConceptFileRef, FormRef

from propstore.families.concepts.stages import parse_concept_record_document
from propstore.repository import Repository

FormDocument = FORM_CHARTER.generated_document()


def test_phase3_qualia_reference_requires_provenance(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    payload = _lemon_concept_payload()
    payload["lexical_entry"]["senses"][0]["qualia"] = {
        "telic": [
            {
                "reference": {"uri": "ps:concept:measurement", "label": "Measurement"},
                "type_constraint": {
                    "reference": {"uri": "ps:concept:description_kind"}
                },
            }
        ]
    }

    with pytest.raises(DocumentSchemaError, match="provenance"):
        convert_document(
            payload,
            ConceptDocument,
            source="concepts/instrument.yaml",
        )


def test_phase3_proto_role_entailment_rejects_out_of_range_grade(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    payload = _lemon_concept_payload()
    payload["lexical_entry"]["senses"][0]["role_bundles"] = {
        "agent": {
            "proto_agent_entailments": [
                {
                    "property": "volition",
                    "value": 1.5,
                    "provenance": _provenance_payload(),
                }
            ]
        }
    }

    with pytest.raises(DocumentSchemaError, match=r"\[0, 1\]"):
        convert_document(
            payload,
            ConceptDocument,
            source="concepts/bad-role.yaml",
        )


def test_concept_document_rejects_flat_pre_lemon_shape(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(DocumentSchemaError):
        convert_document(
            {
                "canonical_name": "temperature",
                "status": "accepted",
                "definition": "A thermal state quantity.",
                "form": "temperature",
            },
            ConceptDocument,
            source="concepts/temperature.yaml",
        )


def test_concept_document_round_trips_lemon_entry_and_reference(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.forms.save(
        FormRef("temperature"),
        FormDocument(name="temperature", dimensionless=False),
        message="Write temperature form",
    )
    ref = ConceptFileRef("temperature")
    document = convert_document(
        _lemon_concept_payload(),
        ConceptDocument,
        source="concepts/temperature.yaml",
    )

    repo.families.concepts.save(
        ref,
        document,
        message="Write lemon concept",
    )
    loaded = repo.families.concepts.require(ref)

    assert loaded.lexical_entry.canonical_form.written_rep == "temperature"
    assert loaded.lexical_entry.physical_dimension_form == "temperature"
    assert loaded.ontology_reference.uri == "tag:prop.store,2026:concept/temperature"


def test_lemon_concept_document_projects_record_at_boundary(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    document = convert_document(
        _lemon_concept_payload(),
        ConceptDocument,
        source="concepts/temperature.yaml",
    )

    record = parse_concept_record_document(document)

    assert record.canonical_name == "temperature"
    assert record.definition == "A thermal state quantity."
    assert record.form == "temperature"
