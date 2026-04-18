from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from quire.documents import DocumentStruct
from propstore.core.lemon.proto_roles import ProtoRoleBundle
from propstore.core.lemon.references import OntologyReference
from argumentation.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.provenance import Provenance


class ParticipantSlot(DocumentStruct):
    name: str
    type_constraint: OntologyReference
    proto_role_bundle: ProtoRoleBundle | None = None


class DescriptionKind(DocumentStruct):
    name: str
    reference: OntologyReference
    slots: tuple[ParticipantSlot, ...]

    def __post_init__(self) -> None:
        names = [slot.name for slot in self.slots]
        if len(names) != len(set(names)):
            raise ValueError("description kind slots must have unique names")


class SlotBinding(DocumentStruct):
    slot: str
    value: OntologyReference
    value_type: OntologyReference
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class BindingValidation:
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_slot_bindings(
    kind: DescriptionKind,
    bindings: tuple[SlotBinding, ...],
) -> BindingValidation:
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


class DescriptionClaim(DocumentStruct):
    claim_id: str
    kind: DescriptionKind
    bindings: tuple[SlotBinding, ...]
    provenance: Provenance

    def __post_init__(self) -> None:
        validation = validate_slot_bindings(self.kind, self.bindings)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors))


class MergeArgument(DocumentStruct):
    argument_id: str
    description_claim_ids: tuple[str, ...]
    supports: tuple[str, ...]
    provenance: Provenance
    attacks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CoreferenceQuery:
    merge_arguments: tuple[MergeArgument, ...]
    framework: ArgumentationFramework

    def clusters(self, *, semantics: str = "grounded") -> tuple[frozenset[str], ...]:
        if semantics == "grounded":
            extensions = (grounded_extension(self.framework),)
        elif semantics == "preferred":
            extensions = tuple(preferred_extensions(self.framework))
        elif semantics == "stable":
            extensions = tuple(stable_extensions(self.framework))
        else:
            raise ValueError(f"unknown coreference semantics: {semantics}")

        by_id = {argument.argument_id: argument for argument in self.merge_arguments}
        clusters = {
            frozenset(by_id[argument_id].description_claim_ids)
            for extension in extensions
            for argument_id in extension
            if argument_id in by_id
        }
        return tuple(sorted(clusters, key=lambda cluster: tuple(sorted(cluster))))


def coreference_argument(
    first: DescriptionClaim,
    second: DescriptionClaim,
    *,
    argument_id: str,
    provenance: Provenance,
) -> MergeArgument:
    return MergeArgument(
        argument_id=argument_id,
        description_claim_ids=(first.claim_id, second.claim_id),
        supports=(first.claim_id, second.claim_id),
        provenance=provenance,
    )


def coreference_query(
    merge_arguments: tuple[MergeArgument, ...],
    *,
    attacks: tuple[tuple[str, str], ...] = (),
) -> CoreferenceQuery:
    argument_ids = frozenset(argument.argument_id for argument in merge_arguments)
    unknown = {
        argument_id
        for attack in attacks
        for argument_id in attack
        if argument_id not in argument_ids
    }
    if unknown:
        raise ValueError(f"coreference attacks reference unknown arguments: {sorted(unknown)!r}")
    return CoreferenceQuery(
        merge_arguments=merge_arguments,
        framework=ArgumentationFramework(
            arguments=argument_ids,
            defeats=frozenset(attacks),
        ),
    )


class CausalAccount(StrEnum):
    STATED = "stated"
    COUNTERFACTUAL = "counterfactual"
    STATISTICAL = "statistical"
    MECHANISTIC = "mechanistic"


class CausalConnectionAssertion(DocumentStruct):
    cause_description_id: str
    effect_description_id: str
    account: CausalAccount
    provenance: Provenance


def causal_transitivity_allowed(
    first: CausalConnectionAssertion,
    second: CausalConnectionAssertion,
) -> bool:
    """Causal closure is account-sensitive, never a unified primitive."""

    if first.effect_description_id != second.cause_description_id:
        return False
    if first.account != second.account:
        return False
    return first.account in {
        CausalAccount.COUNTERFACTUAL,
        CausalAccount.MECHANISTIC,
    }
