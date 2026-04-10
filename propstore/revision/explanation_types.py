from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import AssumptionId, to_assumption_ids


@dataclass(frozen=True)
class RevisionAtomDetail:
    reason: str | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "support_sets",
            tuple(to_assumption_ids(support_set) for support_set in self.support_sets),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> RevisionAtomDetail:
        if not data:
            return cls()
        return cls(
            reason=None if data.get("reason") is None else str(data.get("reason")),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            support_sets=tuple(
                tuple(str(assumption_id) for assumption_id in support_set)
                for support_set in (data.get("support_sets") or ())
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.reason is not None:
            data["reason"] = self.reason
        if self.incision_set:
            data["incision_set"] = list(self.incision_set)
        if self.support_sets:
            data["support_sets"] = [list(support_set) for support_set in self.support_sets]
        return data


RevisionAtomDetailInput = RevisionAtomDetail | Mapping[str, Any]


def coerce_revision_atom_detail(detail: RevisionAtomDetailInput) -> RevisionAtomDetail:
    if isinstance(detail, RevisionAtomDetail):
        return detail
    return RevisionAtomDetail.from_mapping(detail)


@dataclass(frozen=True)
class EntrenchmentReason:
    override_priority: int | str | None = None
    override_key: str | None = None
    support_count: int | None = None
    essential_support: tuple[AssumptionId, ...] = ()
    iterated_operator: str | None = None
    revised_in: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "essential_support", to_assumption_ids(self.essential_support))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> EntrenchmentReason:
        if not data:
            return cls()
        raw_override_priority = data.get("override_priority", data.get("override"))
        return cls(
            override_priority=_coerce_override_priority(raw_override_priority),
            override_key=None if data.get("override_key") is None else str(data.get("override_key")),
            support_count=(
                None if data.get("support_count") is None else int(data.get("support_count"))
            ),
            essential_support=tuple(
                str(assumption_id)
                for assumption_id in (data.get("essential_support") or ())
            ),
            iterated_operator=(
                None
                if data.get("iterated_operator") is None
                else str(data.get("iterated_operator"))
            ),
            revised_in=(
                None if data.get("revised_in") is None else bool(data.get("revised_in"))
            ),
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
    return EntrenchmentReason.from_mapping(reason)


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
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "support_sets",
            tuple(to_assumption_ids(support_set) for support_set in self.support_sets),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> RevisionAtomExplanation:
        ranking_data = data.get("ranking")
        return cls(
            status=str(data.get("status") or "accepted"),
            reason=str(data.get("reason") or "unchanged"),
            ranking=(
                None
                if not isinstance(ranking_data, Mapping)
                else EntrenchmentReason.from_mapping(ranking_data)
            ),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            support_sets=tuple(
                tuple(str(assumption_id) for assumption_id in support_set)
                for support_set in (data.get("support_sets") or ())
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
            data["support_sets"] = [list(support_set) for support_set in self.support_sets]
        return data


@dataclass(frozen=True)
class RevisionExplanation:
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = ()
    atoms: Mapping[str, RevisionAtomExplanation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(self, "atoms", dict(self.atoms))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> RevisionExplanation:
        return cls(
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (data.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (data.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            atoms={
                str(atom_id): RevisionAtomExplanation.from_mapping(atom_data)
                for atom_id, atom_data in (data.get("atoms") or {}).items()
                if isinstance(atom_data, Mapping)
            },
        )

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
