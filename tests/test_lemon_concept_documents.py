from __future__ import annotations

import pytest

from propstore.artifacts import CONCEPT_FILE_FAMILY, ConceptFileRef
from propstore.artifacts.schema import DocumentSchemaError
from propstore.core.concepts import parse_concept_record_document
from propstore.repository import Repository


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


def test_concept_document_rejects_flat_pre_lemon_shape(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(DocumentSchemaError):
        repo.artifacts.coerce(
            CONCEPT_FILE_FAMILY,
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
    document = repo.artifacts.coerce(
        CONCEPT_FILE_FAMILY,
        _lemon_concept_payload(),
        source="concepts/temperature.yaml",
    )

    repo.artifacts.save(
        CONCEPT_FILE_FAMILY,
        ref,
        document,
        message="Write lemon concept",
    )
    loaded = repo.artifacts.require(CONCEPT_FILE_FAMILY, ref)

    assert loaded.lexical_entry.canonical_form.written_rep == "temperature"
    assert loaded.lexical_entry.physical_dimension_form == "temperature"
    assert loaded.ontology_reference.uri == "tag:prop.store,2026:concept/temperature"


def test_lemon_concept_document_projects_record_at_boundary(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    document = repo.artifacts.coerce(
        CONCEPT_FILE_FAMILY,
        _lemon_concept_payload(),
        source="concepts/temperature.yaml",
    )

    record = parse_concept_record_document(document)

    assert record.canonical_name == "temperature"
    assert record.definition == "A thermal state quantity."
    assert record.form == "temperature"
