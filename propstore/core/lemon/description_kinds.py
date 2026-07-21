"""Description kinds, slots, and merge-argument DATA for description claims.

A :class:`DescriptionKind` is a typed frame (Pustejovsky/FrameNet flavoured) with
named :class:`ParticipantSlot` participants, each carrying a type constraint and
an optional Dowty proto-role bundle. A :class:`DescriptionClaim` instantiates a
kind by binding its slots; bindings are type-checked against the slot constraints.

Coreference between description claims is NOT a stored fact. It is a defeasible
*merge argument* (:class:`CoreferenceMergeArgument`) that says "these claims may denote the
same thing". Whether two claims actually corefer is decided at RENDER time by
running Dung argumentation over the merge arguments — see
:mod:`propstore.core.lemon.coreference`. This module holds only the argument DATA
and the merge *protocol* (arguments + their attacks); it deliberately imports NO
argumentation engine (architecture boundary — enforced by
``tests/test_lemon_boundaries.py``). The render-time consumer crosses that
boundary by calling the ``argumentation`` package directly.
"""

from __future__ import annotations

from enum import StrEnum

import msgspec

from propstore.core.lemon.proto_roles import ProtoRoleBundle
from propstore.core.lemon.references import OntologyReference
from propstore.provenance import Provenance


class ParticipantSlot(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A named participant of a description kind, with a type constraint."""

    name: str
    type_constraint: OntologyReference
    proto_role_bundle: ProtoRoleBundle | None = None


class DescriptionKind(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A typed description frame with uniquely-named participant slots."""

    name: str
    reference: OntologyReference
    slots: tuple[ParticipantSlot, ...]

    def __post_init__(self) -> None:
        names = [slot.name for slot in self.slots]
        if len(names) != len(set(names)):
            raise ValueError("description kind slots must have unique names")


class SlotBinding(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A provenance-bearing binding of one slot to a typed value."""

    slot: str
    value: OntologyReference
    value_type: OntologyReference
    provenance: Provenance


class BindingValidation(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The outcome of checking slot bindings against a description kind."""

    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_slot_bindings(
    kind: DescriptionKind,
    bindings: tuple[SlotBinding, ...],
) -> BindingValidation:
    """Check that each binding targets a known slot with the right value type."""

    slots = {slot.name: slot for slot in kind.slots}
    errors: list[str] = []
    for binding in bindings:
        slot = slots.get(binding.slot)
        if slot is None:
            errors.append(f"unknown slot '{binding.slot}'")
            continue
        if binding.value_type.uri != slot.type_constraint.uri:
            errors.append(
                f"slot '{binding.slot}' requires type '{slot.type_constraint.uri}' "
                f"but got '{binding.value_type.uri}'"
            )
    return BindingValidation(errors=tuple(errors))


class DescriptionClaim(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A description kind instantiated by type-checked slot bindings."""

    claim_id: str
    kind: DescriptionKind
    bindings: tuple[SlotBinding, ...]
    provenance: Provenance

    def __post_init__(self) -> None:
        validation = validate_slot_bindings(self.kind, self.bindings)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors))


class CoreferenceMergeArgument(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A defeasible argument that some description claims corefer.

    ``supports`` are the claim ids this argument would merge if accepted. This is
    plain argument DATA; acceptance is decided by the render-time Dung query.
    """

    argument_id: str
    description_claim_ids: tuple[str, ...]
    supports: tuple[str, ...]
    provenance: Provenance
    attacks: tuple[str, ...] = ()


class DescriptionKindMergeProtocol(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True
):
    """A set of coreference merge arguments and the attacks among them."""

    merge_arguments: tuple[CoreferenceMergeArgument, ...]
    attacks: tuple[tuple[str, str], ...] = ()

    @property
    def argument_ids(self) -> frozenset[str]:
        return frozenset(argument.argument_id for argument in self.merge_arguments)

    def __post_init__(self) -> None:
        unknown = {
            argument_id
            for attack in self.attacks
            for argument_id in attack
            if argument_id not in self.argument_ids
        }
        if unknown:
            raise ValueError(
                f"coreference attacks reference unknown arguments: {sorted(unknown)!r}"
            )


def coreference_argument(
    first: DescriptionClaim,
    second: DescriptionClaim,
    *,
    argument_id: str,
    provenance: Provenance,
) -> CoreferenceMergeArgument:
    """Build a merge argument asserting that ``first`` and ``second`` corefer."""

    return CoreferenceMergeArgument(
        argument_id=argument_id,
        description_claim_ids=(first.claim_id, second.claim_id),
        supports=(first.claim_id, second.claim_id),
        provenance=provenance,
    )


class CausalAccount(StrEnum):
    """The kind of causal account asserted for a connection."""

    STATED = "stated"
    COUNTERFACTUAL = "counterfactual"
    STATISTICAL = "statistical"
    MECHANISTIC = "mechanistic"


class CausalConnectionAssertion(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True
):
    """A provenance-bearing causal connection between two description claims."""

    cause_description_id: str
    effect_description_id: str
    account: CausalAccount
    provenance: Provenance


def causal_transitivity_allowed(
    first: CausalConnectionAssertion,
    second: CausalConnectionAssertion,
) -> bool:
    """Causal closure is account-sensitive, never a unified primitive.

    Transitivity holds only when ``first`` chains into ``second`` under the SAME
    account, and only for accounts that license composition (counterfactual or
    mechanistic) — not for merely stated or statistical connections.
    """

    if first.effect_description_id != second.cause_description_id:
        return False
    if first.account != second.account:
        return False
    return first.account in {
        CausalAccount.COUNTERFACTUAL,
        CausalAccount.MECHANISTIC,
    }
