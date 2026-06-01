"""Phase 1 SPIKE — prove the relations-as-concepts spine on ``published_in``.

This is an ADDITIVE spike. It changes NO existing production type. It proves,
end-to-end, that a relation authored as an ordinary concept carrying a lemon
``DescriptionKind`` can be:

1. authored + stored through the real concept storage path,
2. resolved by concept FK (``FamilyReferenceIndex.resolve_id``) exactly like any
   other concept reference,
3. used to validate a situated assertion's role bindings against the relation's
   description-kind via ``validate_slot_bindings`` (valid passes; unknown /
   ill-typed fails),
4. round-tripped through the situated-assertion codec with stable identity.

Design: ``proposals/relations-as-concepts-2026-05-31.md``.
Findings report: ``reports/relations-phase1-spike.md``.

The spine deliberately does NOT touch ``RelationConceptRef`` / ``RoleBinding`` /
``RoleBindingSet`` — the bare role types stay. The test instead exercises the
lemon ``DescriptionKind`` / ``SlotBinding`` layer that Phase 2 migrates onto, and
documents the impedance between the two (see ``_role_binding_to_slot_binding``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quire.references import FamilyReferenceIndex

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import ConceptId, ContextId, ProvenanceGraphId
from propstore.core.lemon.description_kinds import (
    DescriptionKind,
    ParticipantSlot,
    SlotBinding,
    validate_slot_bindings,
)
from propstore.core.lemon.references import OntologyReference
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
)
from propstore.families.concepts.declaration import (
    ConceptDocument,
    LexicalEntryDocument,
    LexicalFormDocument,
    LexicalSenseDocument,
    OntologyReferenceDocument,
)
from propstore.families.concepts.types import ConceptStatus
from propstore.families.forms.models import FORM_CHARTER
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.families.registry import ConceptFileRef, FormRef
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.repository import Repository

FormDocument = FORM_CHARTER.generated_document()


# --- fixed identities for the spike -----------------------------------------

PUBLISHED_IN_ID = derive_concept_artifact_id("propstore", "published_in")
PAPER_TYPE_ID = derive_concept_artifact_id("propstore", "paper")
VENUE_TYPE_ID = derive_concept_artifact_id("propstore", "venue")

# concrete instances bound at assertion time
PAPER_INSTANCE = "ps:concept:paper:clark-2014"
VENUE_INSTANCE = "ps:concept:venue:j-biomed-semantics"


def _spike_provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="spike",
                timestamp="2026-05-31T00:00:00Z",
                source_artifact_code="relations-phase1-spike",
                method="authored",
            ),
        ),
    )


def _published_in_description_kind() -> DescriptionKind:
    """The role signature for ``published_in`` expressed as a lemon kind.

    Slots are the role names; ``type_constraint`` is the role range; the kind's
    ``reference`` is the relation identity (= role domain).
    """

    return DescriptionKind(
        name="published_in",
        reference=OntologyReference(uri=PUBLISHED_IN_ID, label="published_in"),
        slots=(
            ParticipantSlot(
                name="paper",
                type_constraint=OntologyReference(uri=PAPER_TYPE_ID, label="paper"),
            ),
            ParticipantSlot(
                name="venue",
                type_constraint=OntologyReference(uri=VENUE_TYPE_ID, label="venue"),
            ),
        ),
    )


def _relation_concept_document() -> ConceptDocument:
    """Author ``published_in`` as an ordinary concept whose sense carries the kind."""

    return ConceptDocument(
        status=ConceptStatus.ACCEPTED,
        ontology_reference=OntologyReferenceDocument(
            uri=PUBLISHED_IN_ID, label="published_in"
        ),
        lexical_entry=LexicalEntryDocument(
            identifier="published_in",
            canonical_form=LexicalFormDocument(
                written_rep="published in", language="en"
            ),
            physical_dimension_form="structural",
            senses=(
                LexicalSenseDocument(
                    reference=OntologyReferenceDocument(
                        uri=PUBLISHED_IN_ID, label="published_in"
                    ),
                    description_kind=_published_in_description_kind(),
                ),
            ),
        ),
        artifact_id=PUBLISHED_IN_ID,
        logical_ids=(),
    )


def _author_published_in(repo: Repository) -> str:
    """Step 1: store the relation concept through the real concept family path.

    Seeds the ``structural`` form first: the concept charter declares a real FK
    (``concept_form``) from ``lexical_entry.physical_dimension_form`` into the
    ``forms`` family, validated at the write boundary. A relation concept is an
    ordinary structural concept, so it needs the structural form to exist — this
    is legitimate repo setup, not a shim around a type mismatch.

    Note the slot ``type_constraint`` references (paper / venue ontology refs)
    live inside the embedded ``DescriptionKind`` and are NOT FK-validated by the
    concept charter, so no paper/venue concepts need to be authored.
    """

    repo.families.forms.save(
        FormRef("structural"),
        FormDocument(name="structural", dimensionless=True),
        message="Spike: seed structural form",
    )
    document = _relation_concept_document()
    repo.families.concepts.save(
        ConceptFileRef("published_in"),
        document,
        message="Spike: author published_in relation concept",
    )
    return PUBLISHED_IN_ID


def _loaded_description_kind(repo: Repository, concept_id: str) -> DescriptionKind:
    """Reload the relation concept and recover the embedded description-kind."""

    document = repo.families.concepts.reference_index().records_by_id[concept_id]
    sense = document.lexical_entry.senses[0]
    kind = sense.description_kind
    assert kind is not None, "relation concept sense must carry a description_kind"
    return kind


def _role_binding_to_slot_binding(
    binding: RoleBinding,
    *,
    kind: DescriptionKind,
    provenance: Provenance,
) -> SlotBinding:
    """Lower a bare ``RoleBinding`` into a lemon ``SlotBinding``.

    THE IMPEDANCE, made concrete. ``RoleBinding`` carries only ``role`` + ``value``.
    ``SlotBinding`` additionally requires ``value_type`` (an ``OntologyReference``)
    and ``provenance``. Neither is present on the ``RoleBinding`` — they must be
    supplied from outside:

    * ``value`` (a bare id string on ``RoleBinding``) must be wrapped as an
      ``OntologyReference``.
    * ``value_type`` is NOT carried by the binding. Here it is *borrowed from the
      slot's own ``type_constraint``*, which makes validation tautological — the
      real Phase-2 path must instead resolve the value's actual concept kind.
    * ``provenance`` must be threaded from the situated assertion's provenance ref
      (which today is an audit ref that does not participate in identity).
    """

    slot = {s.name: s for s in kind.slots}[binding.role]
    return SlotBinding(
        slot=binding.role,
        value=OntologyReference(uri=str(binding.value)),
        value_type=slot.type_constraint,
        provenance=provenance,
    )


def _published_in_assertion(relation_id: str) -> SituatedAssertion:
    """Build the situated assertion referencing the relation BY its FK id."""

    return SituatedAssertion(
        relation=RelationConceptRef(ConceptId(relation_id)),
        role_bindings=RoleBindingSet(
            (
                RoleBinding("paper", PAPER_INSTANCE),
                RoleBinding("venue", VENUE_INSTANCE),
            )
        ),
        context=ContextReference(ContextId("ctx_literature")),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef(
            ProvenanceGraphId("urn:propstore:provenance:source")
        ),
    )


# === STEP 1: author + store ================================================


def test_step1_published_in_authored_as_concept_with_description_kind(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)

    index = repo.families.concepts.reference_index()
    assert relation_id in index.records_by_id
    kind = _loaded_description_kind(repo, relation_id)
    assert kind.name == "published_in"
    assert {slot.name for slot in kind.slots} == {"paper", "venue"}
    assert kind.reference.uri == relation_id


# === STEP 2: resolve relation concept by FK =================================


def test_step2_relation_concept_resolvable_by_fk(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)

    index: FamilyReferenceIndex[ConceptDocument] = (
        repo.families.concepts.reference_index()
    )

    # A relation concept is reachable as an ordinary concept FK — by artifact id
    # and by the canonical reference key the charter exposes.
    assert index.resolve_id(relation_id) == relation_id
    assert index.require_id(relation_id) == relation_id
    assert index.exists(relation_id)

    # An unknown reference does not resolve (honest ignorance, not a minted id).
    assert index.resolve_id("ps:concept:relation:does-not-exist") is None


# === STEP 3: validate role bindings against the description-kind ============


def test_step3_valid_bindings_pass_validation(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)
    kind = _loaded_description_kind(repo, relation_id)
    provenance = _spike_provenance()

    bindings = (
        SlotBinding(
            slot="paper",
            value=OntologyReference(uri=PAPER_INSTANCE),
            value_type=OntologyReference(uri=PAPER_TYPE_ID),
            provenance=provenance,
        ),
        SlotBinding(
            slot="venue",
            value=OntologyReference(uri=VENUE_INSTANCE),
            value_type=OntologyReference(uri=VENUE_TYPE_ID),
            provenance=provenance,
        ),
    )

    validation = validate_slot_bindings(kind, bindings)
    assert validation.ok
    assert validation.errors == ()


def test_step3_unknown_slot_fails_validation(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)
    kind = _loaded_description_kind(repo, relation_id)

    bad = (
        SlotBinding(
            slot="publisher",  # not a slot on published_in
            value=OntologyReference(uri="ps:concept:publisher:acme"),
            value_type=OntologyReference(uri="ps:concept:publisher"),
            provenance=_spike_provenance(),
        ),
    )

    validation = validate_slot_bindings(kind, bad)
    assert not validation.ok
    assert any("unknown slot 'publisher'" in error for error in validation.errors)


def test_step3_ill_typed_binding_fails_validation(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)
    kind = _loaded_description_kind(repo, relation_id)

    ill_typed = (
        SlotBinding(
            slot="paper",
            value=OntologyReference(uri=PAPER_INSTANCE),
            # wrong type: venue's type given for the paper slot
            value_type=OntologyReference(uri=VENUE_TYPE_ID),
            provenance=_spike_provenance(),
        ),
    )

    validation = validate_slot_bindings(kind, ill_typed)
    assert not validation.ok
    assert any("requires type" in error for error in validation.errors)


def test_step3_role_bindings_lowered_to_slot_bindings_validate(
    tmp_path: Path,
) -> None:
    """The situated-assertion ``RoleBindingSet`` lowered into lemon SlotBindings.

    This is the concrete Phase-2 lowering, and it shows the impedance: the
    ``value_type`` and ``provenance`` for each ``SlotBinding`` are NOT available on
    the ``RoleBinding`` — they are supplied here from the slot's type constraint
    and the spike provenance respectively.
    """

    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)
    kind = _loaded_description_kind(repo, relation_id)
    assertion = _published_in_assertion(relation_id)
    provenance = _spike_provenance()

    slot_bindings = tuple(
        _role_binding_to_slot_binding(binding, kind=kind, provenance=provenance)
        for binding in assertion.role_bindings.bindings
    )

    validation = validate_slot_bindings(kind, slot_bindings)
    assert validation.ok


# === STEP 4: codec round-trip ==============================================


# === property-style: FK round-trips for any of the spike's reference keys ===


@pytest.mark.property
@pytest.mark.parametrize("reference", [PUBLISHED_IN_ID])
def test_property_relation_fk_resolves_to_itself(
    tmp_path: Path, reference: str
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    relation_id = _author_published_in(repo)
    index = repo.families.concepts.reference_index()
    assert index.resolve_id(reference) == relation_id
