"""Phase-2 SPIKE — does the claim projector decompose HONESTLY?

ADDITIVE prototype only. Touches NO production type. It imports the *real*
``AtomicPropositionDocument`` / ``ClaimType`` / ``CelExpr`` so the claim documents
under test carry the ACTUAL authored field shapes, then projects them through a
*prototype* value union + signature + projector defined entirely in this file.

Purpose (per ``prompts/relations-phase2-projector-spike.md``): prove or disprove
that a real heterogeneous claim decomposes into TYPED relation fillers per its
relation's description-kind signature, WITHOUT fabricating a type or resurrecting
a blob. Two claims stress opposite ends:

1. a structured ``measurement`` claim, and
2. a free-text ``observation`` claim.

Findings are written up in ``reports/relations-phase2-projector-spike.md``. The
load-bearing result of this file: ``measurement`` decomposes cleanly into typed
fillers (every field finds an honest typed home); ``observation`` does NOT have a
multi-role relation signature — its proposition IS the prose ``statement`` — so the
projector returns a non-relation ``TextAtom`` rather than forcing a fake one-role
relation whose sole filler is a ``TextValue`` blob wearing a type.

Design reference: ``proposals/relations-unified-substrate-2026-05-31.md`` §1 (the
value union incl. ``TextValue``), §4 (the projector), §5 (honesty checkpoints);
``reports/relations-unified-substrate-adversary.md`` risk #1 (the deleted blob has
no typed home for prose) and risk #3 (the non-relation atom must be a stored,
queryable artifact, never a dropped row).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Union

import pytest

# Real production types — READ ONLY. We build claims from the genuine field shapes,
# we do not modify these. This is the "use the ACTUAL field shapes" requirement.
from propstore.cel_types import to_cel_exprs
from propstore.families.claims.declaration import AtomicPropositionDocument
from propstore.families.claims.types import ClaimType


# ──────────────────────────────────────────────────────────────────────────────
# 1. Prototype RelationValue union (a CLOSED tagged union — no untyped map variant,
#    so it cannot decay into a new blob). Mirrors proposal §1.
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ConceptValue:
    """Filler IS a formal ontology/concept entity. Identity = the URI/id."""

    reference: str


@dataclass(frozen=True)
class FamilyRefValue:
    """Filler POINTS AT another first-class storage artifact (claim/context/...).

    Distinct from a scalar string so a claim-id and a free-text token that happen
    to spell the same never collide. (Proposal §1; Decision 9.1.)
    """

    family: str  # {"claim","context","condition","assumption","justification"}
    id: str


@dataclass(frozen=True)
class ScalarValue:
    """Exactly the ASPIC ``Scalar`` vocabulary: str|int|float|bool.

    A scalar *string* is an enum/operator/token (e.g. ``"jnd_absolute"``,
    ``"ratio"``, ``"sd"``). It is NOT a home for prose. (Proposal §1, §5.)
    """

    value: Union[str, int, float, bool]


@dataclass(frozen=True)
class TextValue:
    """Irreducible free-text propositional content (statement/body/notes/...).

    DISTINCT from ``ScalarValue(str)``: a scalar string is a token; a ``TextValue``
    is honest prose. Prose is NEVER absorbed into ``ScalarValue`` — that would
    fabricate "this prose is a scalar". (Adversary fix; honest-ignorance.)
    """

    text: str


@dataclass(frozen=True)
class CelValue:
    """Wraps the existing branded CEL source (a condition expression)."""

    expression: str


@dataclass(frozen=True)
class TimepointValue:
    """Separate from ``ScalarValue(float)``; KindType.TIMEPOINT != QUANTITY."""

    lexical: str


@dataclass(frozen=True)
class ListValue:
    """Repeated fillers without duplicate roles. Preserves multiplicity by default."""

    items: tuple["RelationValue", ...]
    ordered: bool = True


RelationValue = Union[
    ConceptValue,
    FamilyRefValue,
    ScalarValue,
    TextValue,
    CelValue,
    TimepointValue,
    ListValue,
]


# ──────────────────────────────────────────────────────────────────────────────
# 2. A DescriptionKind-style signature: named slots, each with a value-kind
#    constraint. (Generalizes lemon ParticipantSlot.type_constraint to a tagged
#    value-kind constraint — proposal §2.)
# ──────────────────────────────────────────────────────────────────────────────


# Value-kind tags used by the signature constraint and the identity canonicalizer.
KIND_CONCEPT = "concept"
KIND_SCALAR = "scalar"
KIND_TEXT = "text"
KIND_CEL = "cel"
KIND_FAMILYREF = "familyref"
KIND_TIMEPOINT = "timepoint"
KIND_LIST = "list"


def value_kind(value: RelationValue) -> str:
    if isinstance(value, ConceptValue):
        return KIND_CONCEPT
    if isinstance(value, ScalarValue):
        return KIND_SCALAR
    if isinstance(value, TextValue):
        return KIND_TEXT
    if isinstance(value, CelValue):
        return KIND_CEL
    if isinstance(value, FamilyRefValue):
        return KIND_FAMILYREF
    if isinstance(value, TimepointValue):
        return KIND_TIMEPOINT
    if isinstance(value, ListValue):
        return KIND_LIST
    raise TypeError(f"unknown RelationValue: {value!r}")


@dataclass(frozen=True)
class ParticipantSlot:
    role: str
    value_kind: str  # one of the KIND_* tags
    required: bool = False


@dataclass(frozen=True)
class DescriptionKind:
    relation: str  # the relation-concept ref this signature types
    slots: tuple[ParticipantSlot, ...]

    def slot(self, role: str) -> ParticipantSlot | None:
        for s in self.slots:
            if s.role == role:
                return s
        return None


# Signature for the ``measurement`` relation. Derived from the authored contract
# (CLAIM_TYPE_CONTRACTS[MEASUREMENT]: required target_concept+measure, value_group,
# unit_policy) — every authored field maps to exactly one typed slot.
MEASUREMENT_SIGNATURE = DescriptionKind(
    relation="ps:relation:measurement",
    slots=(
        ParticipantSlot("target", KIND_CONCEPT, required=True),
        ParticipantSlot("measure", KIND_SCALAR, required=True),
        ParticipantSlot("value", KIND_SCALAR),
        ParticipantSlot("lower_bound", KIND_SCALAR),
        ParticipantSlot("upper_bound", KIND_SCALAR),
        ParticipantSlot("uncertainty", KIND_SCALAR),
        ParticipantSlot("uncertainty_type", KIND_SCALAR),
        ParticipantSlot("sample_size", KIND_SCALAR),
        ParticipantSlot("confidence", KIND_SCALAR),
        ParticipantSlot("unit", KIND_SCALAR),
        ParticipantSlot("condition", KIND_CEL),
    ),
)


# ──────────────────────────────────────────────────────────────────────────────
# 3. The projector output types: RelationInstance (relation-shaped) and the
#    NonRelationAtom (a text assertion that is NOT a relation instance). Both are
#    first-class STORED artifacts; the NonRelationAtom is the substrate's honest
#    answer to "this claim is not relation-shaped" — it is NOT a dropped row.
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RelationBinding:
    role: str
    value: RelationValue


@dataclass(frozen=True)
class RelationInstance:
    relation: str
    bindings: tuple[RelationBinding, ...]

    def binding(self, role: str) -> RelationBinding | None:
        for b in self.bindings:
            if b.role == role:
                return b
        return None


@dataclass(frozen=True)
class NonRelationAtom:
    """A claim whose proposition is irreducible prose, ABOUT zero or more concepts.

    This is the explicit "not a relation instance" branch. The proposition is the
    ``content`` TextValue; ``about`` carries the concept the prose is about (the
    only structured role observation has). Storing it as a distinct atom kind is
    HONEST: we do not invent a multi-role relation signature the data does not have.
    """

    kind: str  # the claim type, e.g. "observation"
    content: TextValue
    about: tuple[ConceptValue, ...] = ()
    aux: tuple[RelationBinding, ...] = ()  # notes/methodology, also TextValue


ProjectionResult = Union[RelationInstance, NonRelationAtom]


# ──────────────────────────────────────────────────────────────────────────────
# 4. The projector. Per-claim-family. Decomposes each field into a typed filler
#    per the signature, OR returns a NonRelationAtom when the claim has no relation
#    signature. Honesty rules are enforced — see the asserts in the tests.
# ──────────────────────────────────────────────────────────────────────────────


def _scalar_num(v: float | int) -> ScalarValue:
    # bool-before-int already handled by msgspec field types (no bools here).
    return ScalarValue(v)


def project_measurement(doc: AtomicPropositionDocument) -> RelationInstance:
    """Project a MEASUREMENT claim into typed relation fillers.

    Every authored measurement field maps to exactly one typed slot. No field is
    cast to the wrong kind, no field is dropped, no JSON blob is produced.
    """
    bindings: list[RelationBinding] = []

    # target_concept -> ConceptValue (the TARGET concept link; a real FK).
    if doc.target_concept is not None:
        bindings.append(RelationBinding("target", ConceptValue(doc.target_concept)))

    # measure="jnd_absolute" -> ScalarValue(str) TOKEN. It is NOT a concept link
    # (the authored contract links only target_concept), and it is NOT prose — it
    # is an enum-like measurement-kind token. Honest ScalarValue(str).
    if doc.measure is not None:
        bindings.append(RelationBinding("measure", ScalarValue(doc.measure)))

    # numeric quantities -> ScalarValue(num) (QUANTITY).
    for role, raw in (
        ("value", doc.value),
        ("lower_bound", doc.lower_bound),
        ("upper_bound", doc.upper_bound),
        ("uncertainty", doc.uncertainty),
        ("sample_size", doc.sample_size),
        ("confidence", doc.confidence),
    ):
        if raw is not None:
            bindings.append(RelationBinding(role, _scalar_num(raw)))

    # uncertainty_type="sd" -> ScalarValue(str) token (enum-like label).
    if doc.uncertainty_type is not None:
        bindings.append(
            RelationBinding("uncertainty_type", ScalarValue(doc.uncertainty_type))
        )

    # unit="ratio" -> ScalarValue(str) token. (dimensions subsystem owns unit
    # algebra; the filler here is the unit string token, no KindType.UNIT exists.)
    if doc.unit is not None:
        bindings.append(RelationBinding("unit", ScalarValue(doc.unit)))

    # conditions -> CelValue (one binding per condition; ListValue if repeated).
    if doc.conditions:
        cel_items = tuple(CelValue(str(c)) for c in doc.conditions)
        if len(cel_items) == 1:
            bindings.append(RelationBinding("condition", cel_items[0]))
        else:
            bindings.append(RelationBinding("condition", ListValue(cel_items)))

    return RelationInstance(MEASUREMENT_SIGNATURE.relation, tuple(bindings))


def project_observation(doc: AtomicPropositionDocument) -> NonRelationAtom:
    """Project an OBSERVATION claim.

    An observation's authored contract is: required ``statement`` (prose) +
    nonempty ``concepts`` (an ABOUT concept list). There is NO multi-role relation
    signature — the proposition IS the prose statement. So we return a
    NonRelationAtom (a text assertion ABOUT some concepts), NOT a fake one-role
    relation whose only filler is a TextValue. (This is the fourth-wall finding.)
    """
    assert doc.statement is not None, "observation requires a statement"
    about = tuple(ConceptValue(c) for c in doc.concepts)
    aux: list[RelationBinding] = []
    if doc.notes is not None:
        aux.append(RelationBinding("notes", TextValue(doc.notes)))
    if doc.methodology is not None:
        aux.append(RelationBinding("methodology", TextValue(doc.methodology)))
    return NonRelationAtom(
        kind="observation",
        content=TextValue(doc.statement),
        about=about,
        aux=tuple(aux),
    )


def project_claim_to_fillers(doc: AtomicPropositionDocument) -> ProjectionResult:
    """Per-claim-family dispatch (the two families this spike covers)."""
    if doc.type is ClaimType.MEASUREMENT:
        return project_measurement(doc)
    if doc.type is ClaimType.OBSERVATION:
        return project_observation(doc)
    raise NotImplementedError(f"spike covers measurement/observation only: {doc.type}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Tagged identity canonicalization. ``ScalarValue(1)`` != ``ScalarValue("1")``;
#    ``TextValue("x")`` != ``ScalarValue("x")``. Fixes the present-day str(value)
#    collapse. (Proposal §3.)
# ──────────────────────────────────────────────────────────────────────────────


def canonical_value(value: RelationValue) -> tuple:
    if isinstance(value, ScalarValue):
        v = value.value
        if isinstance(v, bool):  # bool before int
            return (KIND_SCALAR, "bool", "true" if v else "false")
        if isinstance(v, int):
            return (KIND_SCALAR, "int", str(v))
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                raise ValueError("non-finite scalar rejected")
            return (KIND_SCALAR, "float", repr(v))
        return (KIND_SCALAR, "str", v)
    if isinstance(value, TextValue):
        return (KIND_TEXT, value.text)
    if isinstance(value, ConceptValue):
        return (KIND_CONCEPT, value.reference)
    if isinstance(value, FamilyRefValue):
        return (KIND_FAMILYREF, value.family, value.id)
    if isinstance(value, CelValue):
        return (KIND_CEL, value.expression)
    if isinstance(value, TimepointValue):
        return (KIND_TIMEPOINT, value.lexical)
    if isinstance(value, ListValue):
        items = tuple(canonical_value(i) for i in value.items)
        if not value.ordered:
            items = tuple(sorted(items, key=repr))
        return (KIND_LIST, value.ordered, items)
    raise TypeError(f"unknown RelationValue: {value!r}")


def validate_against_signature(
    instance: RelationInstance, signature: DescriptionKind
) -> list[str]:
    errors: list[str] = []
    for b in instance.bindings:
        slot = signature.slot(b.role)
        if slot is None:
            errors.append(f"no slot for role '{b.role}'")
            continue
        got = value_kind(b.value)
        if got != slot.value_kind:
            errors.append(f"role '{b.role}' wants {slot.value_kind!r} got {got!r}")
    for slot in signature.slots:
        if slot.required and instance.binding(slot.role) is None:
            errors.append(f"required role '{slot.role}' missing")
    return errors


# ──────────────────────────────────────────────────────────────────────────────
# Representative real claim documents (ACTUAL field shapes — see
# tests/test_description_generator.py:153 for the genuine measurement shape, and
# tests/test_concept_views.py:281 for the genuine observation shape).
# ──────────────────────────────────────────────────────────────────────────────


def _measurement_claim() -> AtomicPropositionDocument:
    return AtomicPropositionDocument(
        type=ClaimType.MEASUREMENT,
        target_concept="ps:concept:open_quotient",
        measure="jnd_absolute",
        value=0.05,
        lower_bound=0.04,
        upper_bound=0.06,
        uncertainty=0.01,
        uncertainty_type="sd",
        sample_size=42,
        confidence=0.9,
        unit="ratio",
        conditions=to_cel_exprs(["voice_quality == 'modal'"]),
    )


def _observation_claim() -> AtomicPropositionDocument:
    return AtomicPropositionDocument(
        type=ClaimType.OBSERVATION,
        statement=(
            "Listeners reliably perceived breathiness increasing with open "
            "quotient in synthesized modal-to-breathy continua."
        ),
        concepts=("ps:concept:open_quotient", "ps:concept:breathiness"),
        notes="Effect attenuated at the breathy extreme.",
        methodology="Two-alternative forced choice, 24 listeners.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# FINDING 1 — measurement decomposes field-by-field into honest typed fillers.
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_measurement_decomposes_to_typed_fillers() -> None:
    doc = _measurement_claim()
    result = project_claim_to_fillers(doc)

    assert isinstance(result, RelationInstance)
    assert result.relation == "ps:relation:measurement"

    by_role = {b.role: b.value for b in result.bindings}

    # concept FK -> ConceptValue (honest).
    assert by_role["target"] == ConceptValue("ps:concept:open_quotient")
    # measure token -> ScalarValue(str) (honest token, NOT prose, NOT a concept).
    assert by_role["measure"] == ScalarValue("jnd_absolute")
    # numerics -> ScalarValue(num) QUANTITY (honest).
    assert by_role["value"] == ScalarValue(0.05)
    assert by_role["lower_bound"] == ScalarValue(0.04)
    assert by_role["upper_bound"] == ScalarValue(0.06)
    assert by_role["uncertainty"] == ScalarValue(0.01)
    assert by_role["sample_size"] == ScalarValue(42)
    assert by_role["confidence"] == ScalarValue(0.9)
    # unit + uncertainty_type tokens -> ScalarValue(str) (honest tokens).
    assert by_role["unit"] == ScalarValue("ratio")
    assert by_role["uncertainty_type"] == ScalarValue("sd")
    # CEL condition -> CelValue (honest; its own type, no scalar cast).
    assert by_role["condition"] == CelValue("voice_quality == 'modal'")

    # NO field forced into the wrong kind, NO TextValue, NO blob.
    assert not any(isinstance(v, TextValue) for v in by_role.values()), (
        "measurement should have NO prose filler — all fields are typed tokens/"
        "numerics/concepts/CEL"
    )

    # Every binding is honest against the signature.
    assert validate_against_signature(result, MEASUREMENT_SIGNATURE) == []


# ──────────────────────────────────────────────────────────────────────────────
# FINDING 2 / 3 — observation is NOT relation-shaped. Its proposition IS the prose
# statement; the only structured role is ABOUT. The projector returns a
# NonRelationAtom rather than a fake one-role relation. This is the fourth wall:
# the design needs a non-relation atom branch.
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_observation_is_not_relation_shaped_returns_text_atom() -> None:
    doc = _observation_claim()
    result = project_claim_to_fillers(doc)

    # THE WALL, asserted explicitly: observation does NOT project to a
    # RelationInstance. It is a text assertion, not a relation over typed args.
    assert isinstance(result, NonRelationAtom), (
        "observation has no multi-role relation signature; forcing one would be a "
        "blob wearing a type"
    )
    assert isinstance(result, RelationInstance) is False

    # The proposition is honest prose -> TextValue (NOT ScalarValue(str)).
    assert isinstance(result.content, TextValue)
    assert result.content.text.startswith("Listeners reliably perceived")
    assert not isinstance(result.content, ScalarValue)  # prose is never a scalar

    # The only structured role observation has is ABOUT (the concept list).
    assert result.about == (
        ConceptValue("ps:concept:open_quotient"),
        ConceptValue("ps:concept:breathiness"),
    )

    # notes / methodology are ALSO prose -> TextValue, never ScalarValue(str).
    aux = {b.role: b.value for b in result.aux}
    assert isinstance(aux["notes"], TextValue)
    assert isinstance(aux["methodology"], TextValue)

    # The atom is a STORED, queryable artifact carrying the content verbatim — it
    # is not a dropped row. (Adversary risk #3.)
    assert result.content.text == doc.statement


@pytest.mark.unit
def test_observation_text_is_not_castable_to_a_one_role_relation() -> None:
    """Demonstrate the wall: if we *tried* to force observation into the
    measurement-style relation shape, the prose has NO honest typed home — the
    only place to put it would be a ScalarValue(str) cast (forbidden) or a TextValue
    in a fabricated single 'statement' role with no signature backing it. We assert
    that the honest projector refuses to do this."""
    doc = _observation_claim()
    result = project_claim_to_fillers(doc)
    # The projector did NOT manufacture a RelationInstance with a 'statement' role.
    assert not isinstance(result, RelationInstance)


# ──────────────────────────────────────────────────────────────────────────────
# FINDING 4 — tagged identity distinguishes what the old str(value) blob collapsed.
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_tagged_identity_distinguishes_prose_from_concept_and_token() -> None:
    # "open_quotient" as a concept ref, as a free-text token, and as prose all
    # collapse under str(); tagged canonicalization keeps all three distinct.
    s = "open_quotient"
    assert (
        canonical_value(ConceptValue(s))
        != canonical_value(ScalarValue(s))
        != canonical_value(TextValue(s))
    )
    assert canonical_value(ConceptValue(s)) != canonical_value(TextValue(s))


@pytest.mark.unit
def test_two_measurements_differing_only_in_value_get_distinct_identity() -> None:
    a = project_claim_to_fillers(_measurement_claim())
    b_doc = _measurement_claim()
    b_doc = AtomicPropositionDocument(
        type=ClaimType.MEASUREMENT,
        target_concept=b_doc.target_concept,
        measure=b_doc.measure,
        value=0.06,  # the ONLY difference
        lower_bound=b_doc.lower_bound,
        upper_bound=b_doc.upper_bound,
        uncertainty=b_doc.uncertainty,
        uncertainty_type=b_doc.uncertainty_type,
        sample_size=b_doc.sample_size,
        confidence=b_doc.confidence,
        unit=b_doc.unit,
        conditions=b_doc.conditions,
    )
    b = project_claim_to_fillers(b_doc)
    assert isinstance(a, RelationInstance) and isinstance(b, RelationInstance)
    assert instance_identity(a) != instance_identity(b)
