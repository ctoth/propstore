"""Finite grades survive the registered Concept family's storage boundaries."""

from __future__ import annotations

from pathlib import Path

import msgspec
import pytest
from quire.sqlalchemy_store import readonly_session
from sqlalchemy import select

from propstore.core.lemon import (
    DescriptionKind,
    GradedEntailment,
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    ParticipantSlot,
    ProtoAgentProperty,
    ProtoPatientProperty,
    ProtoRoleBundle,
)
from propstore.families.concepts import Concept
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.repository import Repository
from propstore.storage import ConceptRepository


NONFINITE = pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "-inf"]
)


def _entailment(
    value: float, property: str = ProtoAgentProperty.CAUSATION
) -> GradedEntailment:
    return GradedEntailment(
        property=property,
        value=value,
        provenance=Provenance(
            status=ProvenanceStatus.STATED,
            witnesses=(
                ProvenanceWitness(
                    asserter="tests",
                    timestamp="2026-10-20T00:00:00Z",
                    source_artifact_code="tests:proto-role-grades",
                    method="unit-test",
                ),
            ),
        ),
    )


def _concept(value: float) -> Concept:
    bundle = ProtoRoleBundle(
        proto_agent_entailments=(_entailment(value),),
        proto_patient_entailments=(
            _entailment(value, ProtoPatientProperty.CAUSALLY_AFFECTED),
        ),
    )
    return Concept(
        concept_id="concept:measurement",
        canonical_name="Measurement",
        lexical_entry=LexicalEntry(
            identifier="entry:measurement",
            canonical_form=LexicalForm(written_rep="measurement", language="en"),
            senses=(
                LexicalSense(
                    reference=OntologyReference(uri="ps:concept:measurement"),
                    description_kind=DescriptionKind(
                        name="Measurement",
                        reference=OntologyReference(uri="ps:concept:measurement"),
                        slots=(
                            ParticipantSlot(
                                name="instrument",
                                type_constraint=OntologyReference(
                                    uri="ps:concept:instrument"
                                ),
                                proto_role_bundle=bundle,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


@NONFINITE
def test_nonfinite_grade_rejected_at_construction(value: float) -> None:
    with pytest.raises(ValueError, match="scalar float must be finite"):
        _entailment(value)


@pytest.mark.parametrize("value", [False, True])
def test_boolean_grade_rejected_at_construction(value: bool) -> None:
    with pytest.raises(ValueError, match="graded entailment value must be numeric"):
        _entailment(value)


@NONFINITE
@pytest.mark.parametrize("decoder", ["convert", "msgpack"])
def test_nonfinite_grade_rejected_at_typed_decode(value: float, decoder: str) -> None:
    payload = msgspec.to_builtins(_entailment(0.5))
    payload["value"] = value
    with pytest.raises(msgspec.ValidationError, match="scalar float must be finite"):
        if decoder == "convert":
            msgspec.convert(payload, type=GradedEntailment)
        else:
            msgspec.msgpack.decode(
                msgspec.msgpack.encode(payload), type=GradedEntailment
            )


@NONFINITE
@pytest.mark.parametrize("decoder", ["charter", "yaml", "msgpack"])
@pytest.mark.parametrize(
    "entailments", ["proto_agent_entailments", "proto_patient_entailments"]
)
def test_nested_nonfinite_grade_rejected_at_typed_concept_decode(
    value: float, decoder: str, entailments: str
) -> None:
    payload = msgspec.to_builtins(_concept(0.5))
    bundle = payload["lexical_entry"]["senses"][0]["description_kind"]["slots"][0][
        "proto_role_bundle"
    ]
    bundle[entailments][0]["value"] = value
    # MessagePack retains IEEE non-finite floats; JSON encoding would turn them
    # into null and test the float annotation instead of the semantic invariant.
    with pytest.raises(msgspec.ValidationError, match="scalar float must be finite"):
        codec = Concept.__charter__.document_codec()
        if decoder == "charter":
            codec.convert(payload, Concept, source="concept/measurement.yaml")
        elif decoder == "yaml":
            codec.decode(
                msgspec.yaml.encode(payload), Concept, source="concept/measurement.yaml"
            )
        else:
            msgspec.msgpack.decode(msgspec.msgpack.encode(payload), type=Concept)


@NONFINITE
def test_nonfinite_concept_cannot_be_authored(value: float, tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    before = repo.require_git().head_sha()
    with pytest.raises(ValueError, match="scalar float must be finite"):
        repo.families.concept.save(
            "concept:measurement", _concept(value), message="author invalid grade"
        )
        repo.families.concept.load("concept:measurement")
    assert repo.require_git().head_sha() == before
    assert repo.families.concept.load("concept:measurement") is None
    assert list(repo.families.concept.iter_handles()) == []


@pytest.mark.parametrize("value", [False, True])
def test_boolean_concept_cannot_be_authored(value: bool, tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    before = repo.require_git().head_sha()
    with pytest.raises(ValueError, match="graded entailment value must be numeric"):
        repo.families.concept.save(
            "concept:measurement",
            _concept(value),
            message="author invalid boolean grade",
        )
        repo.families.concept.load("concept:measurement")
    assert repo.require_git().head_sha() == before
    assert repo.families.concept.load("concept:measurement") is None
    assert list(repo.families.concept.iter_handles()) == []


@pytest.mark.parametrize("value", [0, 0.0, 0.5, 1.0, 1])
def test_slot_grade_round_trips_through_registered_concept_family(
    value: float, tmp_path: Path
) -> None:
    repo = Repository.init(tmp_path / "source" / "knowledge")
    concept = _concept(value)
    family = repo.families.concept
    family.save(concept.concept_id, concept, message="author valid slot grades")

    assert family.load(concept.concept_id) == concept
    assert [handle.document for handle in family.iter_handles()] == [concept]
    codec = Concept.__charter__.document_codec()
    assert (
        codec.decode(
            family.render(concept).encode(), Concept, source="concept/measurement.yaml"
        )
        == concept
    )

    projection = ConceptRepository(backend=repo.require_git())
    assert projection.get(concept.concept_id) == concept
    assert list(projection.iter_concepts()) == [concept]
    sidecar = tmp_path / "concept.sqlite"
    schema = projection.build_sidecar(sidecar)
    with readonly_session(sidecar, schema) as session:
        row = session.scalars(select(schema.model("concept"))).one()
        assert row.lexical_entry == concept.lexical_entry
        sense = row.lexical_entry.senses[0]
        assert sense.role_bundles is None
        bundle = sense.description_kind.slots[0].proto_role_bundle
        assert bundle.proto_agent_entailments[0].value == value
        assert bundle.proto_patient_entailments[0].value == value

    destination = Repository.init(tmp_path / "destination" / "knowledge")
    result = commit_repository_import(
        destination, plan_repository_import(destination, repo.root.parent)
    )
    imported = list(destination.families.concept.iter_handles(commit=result.commit_sha))
    assert len(imported) == 1
    document = imported[0].document
    assert document == msgspec.structs.replace(concept, concept_id=document.concept_id)
