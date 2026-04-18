from __future__ import annotations

import pytest

from propstore.artifacts.refs import ConceptFileRef
from quire.documents import DocumentSchemaError
from propstore.core.concepts import concept_document_to_payload, parse_concept_record_document
from propstore.repository import Repository


def _provenance_payload() -> dict[str, object]:
    return {
        "status": "stated",
        "witnesses": [
            {
                "asserter": "test",
                "timestamp": "2026-04-17T00:00:00Z",
                "source_artifact_code": "ps:test:phase3",
                "method": "unit-test",
            }
        ],
    }


def _lemon_concept_payload() -> dict[str, object]:
    return {
        "status": "accepted",
        "ontology_reference": {
            "uri": "tag:prop.store,2026:concept/temperature",
            "label": "Temperature",
        },
        "lexical_entry": {
            "identifier": "entry:temperature",
            "canonical_form": {
                "written_rep": "temperature",
                "language": "en",
            },
            "senses": [
                {
                    "reference": {
                        "uri": "tag:prop.store,2026:concept/temperature",
                        "label": "Temperature",
                    },
                    "usage": "A thermal state quantity.",
                }
            ],
            "physical_dimension_form": "temperature",
        },
    }


def test_concept_document_round_trips_phase3_sense_semantics(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    payload = _lemon_concept_payload()
    sense = payload["lexical_entry"]["senses"][0]
    sense["provenance"] = _provenance_payload()
    sense["qualia"] = {
        "telic": [
            {
                "reference": {"uri": "ps:concept:measurement", "label": "Measurement"},
                "type_constraint": {
                    "reference": {
                        "uri": "ps:concept:description_kind",
                        "label": "Description Kind",
                    }
                },
                "provenance": _provenance_payload(),
            }
        ]
    }
    sense["description_kind"] = {
        "name": "Measurement",
        "reference": {"uri": "ps:concept:measurement", "label": "Measurement"},
        "slots": [
            {
                "name": "instrument",
                "type_constraint": {
                    "uri": "ps:concept:measurement_instrument",
                    "label": "Measurement Instrument",
                },
                "proto_role_bundle": {
                    "proto_agent_entailments": [
                        {
                            "property": "causation",
                            "value": 0.75,
                            "provenance": _provenance_payload(),
                        }
                    ]
                },
            }
        ],
    }
    sense["role_bundles"] = {
        "instrument": {
            "proto_agent_entailments": [
                {
                    "property": "causation",
                    "value": 0.75,
                    "provenance": _provenance_payload(),
                }
            ],
            "proto_patient_entailments": [],
        }
    }

    document = repo.families.concepts.coerce(
        payload,
        source="concepts/measurement.yaml",
    )

    loaded_sense = document.lexical_entry.senses[0]
    assert loaded_sense.provenance is not None
    assert loaded_sense.qualia is not None
    assert loaded_sense.qualia.telic[0].reference.uri == "ps:concept:measurement"
    assert loaded_sense.description_kind is not None
    assert loaded_sense.description_kind.slots[0].name == "instrument"
    assert loaded_sense.role_bundles is not None
    assert loaded_sense.role_bundles["instrument"].proto_agent_entailments[0].value == 0.75

    rendered = concept_document_to_payload(document)
    rendered_sense = rendered["lexical_entry"]["senses"][0]
    assert rendered_sense["qualia"]["telic"][0]["provenance"]["status"] == "stated"
    assert rendered_sense["description_kind"]["slots"][0]["proto_role_bundle"][
        "proto_agent_entailments"
    ][0]["property"] == "causation"


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
        repo.families.concepts.coerce(
            payload,
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
        repo.families.concepts.coerce(
            payload,
            source="concepts/bad-role.yaml",
        )


def test_concept_document_rejects_flat_pre_lemon_shape(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(DocumentSchemaError):
        repo.families.concepts.coerce(
            {
                "canonical_name": "temperature",
                "status": "accepted",
                "definition": "A thermal state quantity.",
                "form": "temperature",
            },
            source="concepts/temperature.yaml",
        )


def test_concept_document_round_trips_lemon_entry_and_reference(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    ref = ConceptFileRef("temperature")
    document = repo.families.concepts.coerce(
        _lemon_concept_payload(),
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
    document = repo.families.concepts.coerce(
        _lemon_concept_payload(),
        source="concepts/temperature.yaml",
    )

    record = parse_concept_record_document(document)

    assert record.canonical_name == "temperature"
    assert record.definition == "A thermal state quantity."
    assert record.form == "temperature"
