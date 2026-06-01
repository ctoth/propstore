from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import AssumptionId


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(
            f"support revision explanation field '{field_name}' must be a mapping"
        )
    return value


@dataclass(frozen=True)
class RevisionAtomDetail:
    reason: str | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()
    selection_rule: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(
            self,
            "support_sets",
            tuple(
                tuple(AssumptionId(value) for value in support_set)
                for support_set in self.support_sets
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.reason is not None:
            data["reason"] = self.reason
        if self.incision_set:
            data["incision_set"] = list(self.incision_set)
        if self.support_sets:
            data["support_sets"] = [
                list(support_set) for support_set in self.support_sets
            ]
        if self.selection_rule is not None:
            data["selection_rule"] = self.selection_rule
        return data


RevisionAtomDetailInput = RevisionAtomDetail | Mapping[str, Any]


def coerce_revision_atom_detail(detail: RevisionAtomDetailInput) -> RevisionAtomDetail:
    if isinstance(detail, RevisionAtomDetail):
        return detail
    return RevisionAtomDetail.from_json_payload(detail)


@dataclass(frozen=True)
class EntrenchmentReason:
    override_priority: int | str | None = None
    override_key: str | None = None
    support_count: int | None = None
    essential_support: tuple[AssumptionId, ...] = ()
    iterated_operator: str | None = None
    revised_in: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "essential_support",
            tuple(AssumptionId(value) for value in self.essential_support),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.override_priority is not None:
            data["override_priority"] = self.override_priority
        if self.override_key is not None:
            data["override_key"] = self.override_key
        if self.support_count is not None:
            data["support_count"] = self.support_count
        if self.essential_support:
            data["essential_support"] = list(self.essential_support)
        if self.iterated_operator is not None:
            data["iterated_operator"] = self.iterated_operator
        if self.revised_in is not None:
            data["revised_in"] = self.revised_in
        return data


EntrenchmentReasonInput = EntrenchmentReason | Mapping[str, Any]


def coerce_entrenchment_reason(reason: EntrenchmentReasonInput) -> EntrenchmentReason:
    if isinstance(reason, EntrenchmentReason):
        return reason
    return EntrenchmentReason.from_json_payload(reason)


def _coerce_override_priority(value: Any) -> int | str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return str(value)


@dataclass(frozen=True)
class RevisionAtomExplanation:
    status: str
    reason: str
    ranking: EntrenchmentReason | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(
            self,
            "support_sets",
            tuple(
                tuple(AssumptionId(value) for value in support_set)
                for support_set in self.support_sets
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "status": self.status,
            "reason": self.reason,
        }
        if self.ranking is not None:
            data["ranking"] = self.ranking.to_dict()
        if self.incision_set:
            data["incision_set"] = list(self.incision_set)
        if self.support_sets:
            data["support_sets"] = [
                list(support_set) for support_set in self.support_sets
            ]
        return data


@dataclass(frozen=True)
class RevisionExplanation:
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = ()
    atoms: Mapping[str, RevisionAtomExplanation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_atom_ids",
            tuple(str(atom_id) for atom_id in self.accepted_atom_ids),
        )
        object.__setattr__(
            self,
            "rejected_atom_ids",
            tuple(str(atom_id) for atom_id in self.rejected_atom_ids),
        )
        object.__setattr__(
            self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set)
        )
        object.__setattr__(self, "atoms", dict(self.atoms))

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "rejected_atom_ids": list(self.rejected_atom_ids),
            "incision_set": list(self.incision_set),
            "atoms": {
                atom_id: explanation.to_dict()
                for atom_id, explanation in self.atoms.items()
            },
        }
