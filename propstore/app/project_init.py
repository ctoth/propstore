"""Owner-layer project initialization (the ``pks init`` owner core).

``initialize_project`` is idempotent: on a fresh directory it runs
:meth:`Repository.init` and then seeds the packaged default *forms* and *base
concepts* (shipped under ``propstore/_resources``) into the store in a single
commit; on an already-initialized directory it is a no-op. The seed gives a new
knowledge base the dimensional forms claims reference and the OntoLex-Lemon base
concepts (the description-kind vocabulary: observation, measurement, assertion,
decision, reaction, …) other authoring builds on.

The packaged seed files are authored in the historical resource shape
(``dimensionless`` / ``common_alternatives``); this module maps them onto the
current charter types (:class:`FormDefinition`, :class:`Concept` with a lemon
:class:`LexicalEntry`). The seed's ``is_a`` links have no charter field in this
slice and are not stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import msgspec

from propstore.core.lemon import (
    DescriptionKind,
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
    ParticipantSlot,
    ProtoRoleBundle,
    QualiaReference,
    QualiaStructure,
    TypeConstraint,
)
from propstore.core.lemon.proto_roles import GradedEntailment
from propstore.dimensions import UnitConversion
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition, KindType
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.repository import Repository
from propstore.resources import iter_resource_files, load_resource_text

_FORMS_DIR = "forms"
_CONCEPTS_SEED = "concepts/phase3_seed.yaml"


class ProjectInitError(Exception):
    """An expected failure while initializing a project."""


@dataclass(frozen=True)
class ProjectInitReport:
    """The outcome of :func:`initialize_project`."""

    root: Path
    initialized: bool


# ── seed payload structs (the historical resource shape) ─────────────────────


class _SeedAlternative(msgspec.Struct):
    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class _SeedForm(msgspec.Struct):
    name: str
    kind: str
    dimensionless: bool = False
    unit_symbol: str | None = None
    dimensions: dict[str, int] | None = None
    common_alternatives: tuple[_SeedAlternative, ...] = ()
    delta_alternatives: tuple[_SeedAlternative, ...] = ()
    min_value: float | None = None
    max_value: float | None = None


class _SeedQualiaReference(msgspec.Struct):
    reference: str
    label: str | None = None
    type_constraint: str | None = None


class _SeedQualia(msgspec.Struct):
    formal: tuple[_SeedQualiaReference, ...] = ()
    constitutive: tuple[_SeedQualiaReference, ...] = ()
    telic: tuple[_SeedQualiaReference, ...] = ()
    agentive: tuple[_SeedQualiaReference, ...] = ()


class _SeedSlot(msgspec.Struct):
    name: str
    type: str
    proto_agent: dict[str, float] | None = None
    proto_patient: dict[str, float] | None = None


class _SeedDescriptionKind(msgspec.Struct):
    slots: tuple[_SeedSlot, ...] = ()


class _SeedConcept(msgspec.Struct):
    ref: str
    name: str
    artifact_id: str
    definition: str | None = None
    form: str = "structural"
    qualia: _SeedQualia | None = None
    description_kind: _SeedDescriptionKind | None = None


class _SeedConceptFile(msgspec.Struct):
    concepts: tuple[_SeedConcept, ...] = ()


def _seed_provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="propstore",
                timestamp="2026-04-17T00:00:00Z",
                source_artifact_code="ps:resource:phase3-seed",
                method="packaged-resource",
            ),
        ),
    )


# ── form mapping ─────────────────────────────────────────────────────────────


def _unit_conversion(alternative: _SeedAlternative) -> UnitConversion:
    return UnitConversion(
        unit=alternative.unit,
        type=alternative.type,
        multiplier=alternative.multiplier,
        offset=alternative.offset,
        base=alternative.base,
        divisor=alternative.divisor,
        reference=alternative.reference,
    )


def _form_from_seed(seed: _SeedForm) -> FormDefinition:
    return FormDefinition(
        name=seed.name,
        kind=KindType(seed.kind),
        unit_symbol=seed.unit_symbol,
        is_dimensionless=seed.dimensionless,
        dimensions=seed.dimensions,
        conversions={alt.unit: _unit_conversion(alt) for alt in seed.common_alternatives},
        delta_conversions={
            alt.unit: _unit_conversion(alt) for alt in seed.delta_alternatives
        },
        min_value=seed.min_value,
        max_value=seed.max_value,
    )


def _seed_forms() -> list[FormDefinition]:
    forms: list[FormDefinition] = []
    for file_name in iter_resource_files(_FORMS_DIR):
        if not file_name.endswith(".yaml"):
            continue
        seed = msgspec.yaml.decode(
            load_resource_text(f"{_FORMS_DIR}/{file_name}"), type=_SeedForm
        )
        forms.append(_form_from_seed(seed))
    return forms


# ── concept mapping ──────────────────────────────────────────────────────────


def _proto_role_bundle(slot: _SeedSlot, provenance: Provenance) -> ProtoRoleBundle | None:
    if slot.proto_agent is None and slot.proto_patient is None:
        return None
    return ProtoRoleBundle(
        proto_agent_entailments=tuple(
            GradedEntailment(property=name, value=value, provenance=provenance)
            for name, value in (slot.proto_agent or {}).items()
        ),
        proto_patient_entailments=tuple(
            GradedEntailment(property=name, value=value, provenance=provenance)
            for name, value in (slot.proto_patient or {}).items()
        ),
    )


def _description_kind(
    seed: _SeedConcept,
    description: _SeedDescriptionKind,
    provenance: Provenance,
) -> DescriptionKind:
    return DescriptionKind(
        name=seed.name,
        reference=OntologyReference(uri=seed.artifact_id, label=seed.name),
        slots=tuple(
            ParticipantSlot(
                name=slot.name,
                type_constraint=OntologyReference(uri=slot.type),
                proto_role_bundle=_proto_role_bundle(slot, provenance),
            )
            for slot in description.slots
        ),
    )


def _qualia_references(
    references: tuple[_SeedQualiaReference, ...],
    provenance: Provenance,
) -> tuple[QualiaReference, ...]:
    return tuple(
        QualiaReference(
            reference=OntologyReference(uri=reference.reference, label=reference.label),
            provenance=provenance,
            type_constraint=(
                None
                if reference.type_constraint is None
                else TypeConstraint(reference=OntologyReference(uri=reference.type_constraint))
            ),
        )
        for reference in references
    )


def _qualia_structure(seed: _SeedQualia, provenance: Provenance) -> QualiaStructure:
    return QualiaStructure(
        formal=_qualia_references(seed.formal, provenance),
        constitutive=_qualia_references(seed.constitutive, provenance),
        telic=_qualia_references(seed.telic, provenance),
        agentive=_qualia_references(seed.agentive, provenance),
    )


def _concept_from_seed(seed: _SeedConcept, provenance: Provenance) -> Concept:
    sense = LexicalSense(
        reference=OntologyReference(uri=seed.artifact_id, label=seed.name),
        usage=seed.definition,
        provenance=provenance,
        qualia=None if seed.qualia is None else _qualia_structure(seed.qualia, provenance),
        description_kind=(
            None
            if seed.description_kind is None
            else _description_kind(seed, seed.description_kind, provenance)
        ),
    )
    entry = LexicalEntry(
        identifier=f"entry:{seed.ref}",
        canonical_form=LexicalForm(written_rep=seed.name, language="en"),
        senses=(sense,),
        physical_dimension_form=seed.form,
    )
    return Concept(
        concept_id=seed.artifact_id,
        canonical_name=seed.name,
        definition=seed.definition,
        lexical_entry=entry,
    )


def _seed_concepts() -> list[Concept]:
    provenance = _seed_provenance()
    seed_file = msgspec.yaml.decode(
        load_resource_text(_CONCEPTS_SEED), type=_SeedConceptFile
    )
    return [_concept_from_seed(concept, provenance) for concept in seed_file.concepts]


# ── entry point ──────────────────────────────────────────────────────────────


def initialize_project(root: Path) -> ProjectInitReport:
    """Initialize a propstore repository at ``root`` and seed the defaults.

    Idempotent: returns ``initialized=False`` without touching an existing
    propstore repository, and seeds forms + base concepts in a single commit on a
    fresh one.
    """

    if Repository.is_propstore_repo(root):
        return ProjectInitReport(root=root, initialized=False)

    repo = Repository.init(root)
    forms = _seed_forms()
    concepts = _seed_concepts()
    transaction = repo.families.transact(message="Seed default forms and concepts")
    with transaction as bound:
        for form in forms:
            bound.form.save(form.name, form)
        for concept in concepts:
            bound.concept.save(concept.concept_id, concept)
    repo.write_bootstrap_manifest(seed_commit=transaction.commit_sha)
    return ProjectInitReport(root=root, initialized=True)
