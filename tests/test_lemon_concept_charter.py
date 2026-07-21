"""The Concept charter carries the lemon model as nested document fields, and the
sidecar projection falls out of that one charter — no hand-authored lemon DTO.

This is the Phase-2a "DTO vanishes" proof for the lemon layer: a concept authored
with a full :class:`LexicalEntry` (forms, senses, qualia, description kind, Dowty
role bundles) round-trips through git AND projects into the sidecar with the lemon
content intact, while a flat pre-lemon shape is rejected at the document boundary.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from quire.documents import DocumentSchemaError
from quire.sqlalchemy_store import readonly_session

from propstore.core.lemon import (
    DescriptionKind,
    GradedEntailment,
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    ParticipantSlot,
    ProtoAgentProperty,
    ProtoRoleBundle,
    QualiaReference,
    QualiaStructure,
    TypeConstraint,
)
from propstore.families.concepts import Concept
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.storage import ConceptRepository


def _provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="tests",
                timestamp="2026-04-17T00:00:00Z",
                source_artifact_code="tests:charter",
                method="unit-test",
            ),
        ),
    )


def _lemon_concept() -> Concept:
    bundle = ProtoRoleBundle(
        proto_agent_entailments=(
            GradedEntailment(
                property=ProtoAgentProperty.CAUSATION,
                value=0.75,
                provenance=_provenance(),
            ),
        )
    )
    sense = LexicalSense(
        reference=OntologyReference(
            uri="tag:prop.store,2026:concept/temperature", label="Temperature"
        ),
        usage="A thermal state quantity.",
        provenance=_provenance(),
        qualia=QualiaStructure(
            telic=(
                QualiaReference(
                    reference=OntologyReference(uri="ps:concept:measurement"),
                    type_constraint=TypeConstraint(
                        reference=OntologyReference(uri="ps:concept:description_kind")
                    ),
                    provenance=_provenance(),
                ),
            )
        ),
        description_kind=DescriptionKind(
            name="Measurement",
            reference=OntologyReference(uri="ps:concept:measurement"),
            slots=(
                ParticipantSlot(
                    name="instrument",
                    type_constraint=OntologyReference(
                        uri="ps:concept:measurement_instrument"
                    ),
                    proto_role_bundle=bundle,
                ),
            ),
        ),
        role_bundles={"instrument": bundle},
    )
    return Concept(
        concept_id="concept:temperature",
        canonical_name="temperature",
        definition="A thermal state quantity.",
        ontology_reference=OntologyReference(
            uri="tag:prop.store,2026:concept/temperature", label="Temperature"
        ),
        lexical_entry=LexicalEntry(
            identifier="entry:temperature",
            canonical_form=LexicalForm(written_rep="temperature", language="en"),
            senses=(sense,),
            physical_dimension_form="temperature",
        ),
    )


def test_concept_with_lemon_entry_round_trips_through_git() -> None:
    repo = ConceptRepository()
    concept = _lemon_concept()
    repo.author(concept, message="author lemon concept")

    loaded = repo.get("concept:temperature")
    assert loaded == concept
    assert loaded is not None
    assert loaded.lexical_entry is not None
    assert loaded.lexical_entry.canonical_form.written_rep == "temperature"
    # Dimensions live on the entry, not the form.
    assert loaded.lexical_entry.physical_dimension_form == "temperature"
    loaded_sense = loaded.lexical_entry.senses[0]
    assert loaded_sense.qualia is not None
    assert loaded_sense.qualia.telic[0].reference.uri == "ps:concept:measurement"
    assert loaded_sense.description_kind is not None
    assert loaded_sense.description_kind.slots[0].name == "instrument"
    assert loaded_sense.role_bundles is not None
    assert (
        loaded_sense.role_bundles["instrument"].proto_agent_entailments[0].value == 0.75
    )


def test_lemon_concept_projects_into_sidecar(tmp_path) -> None:
    repo = ConceptRepository()
    repo.author(_lemon_concept(), message="author lemon concept")

    sidecar = tmp_path / "concept.sqlite"
    schema = repo.build_sidecar(sidecar)
    model = schema.model("concept")
    with readonly_session(sidecar, schema) as session:
        rows = list(session.scalars(select(model)))

    assert len(rows) == 1
    row = rows[0]
    # The lemon entry is a charter-derived sidecar column — reconstructed, not a DTO.
    assert isinstance(row.lexical_entry, LexicalEntry)
    assert row.lexical_entry.senses[0].description_kind.name == "Measurement"
    assert isinstance(row.ontology_reference, OntologyReference)
    assert row.ontology_reference.label == "Temperature"


def test_concept_document_rejects_flat_pre_lemon_shape() -> None:
    """An unknown flat ``form`` key fails to decode (forbid_unknown_fields)."""

    codec = Concept.__charter__.document_codec()
    flat = (
        b'{"concept_id": "concept:t", "canonical_name": "temperature", '
        b'"status": "authored", "definition": "d", "form": "temperature"}'
    )
    with pytest.raises(DocumentSchemaError, match="form"):
        codec.decode(flat, Concept, source="concepts/temperature.yaml")
