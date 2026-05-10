from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.core.id_types import AssumptionId, to_assumption_ids


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"support revision explanation field '{field_name}' must be a mapping")
    return value


@dataclass(frozen=True)
class RevisionAtomDetail:
    reason: str | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()
    selection_rule: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "support_sets",
            tuple(to_assumption_ids(support_set) for support_set in self.support_sets),
        )

    @classmethod
    def from_mapping(cls, data: object) -> RevisionAtomDetail:
        if data is None:
            return cls()
        payload = _optional_mapping(data, "atom_detail")
        if not payload:
            return cls()
        return cls(
            reason=None if payload.get("reason") is None else str(payload.get("reason")),
            incision_set=tuple(str(atom_id) for atom_id in (payload.get("incision_set") or ())),
            support_sets=tuple(
                to_assumption_ids(support_set)
                for support_set in (payload.get("support_sets") or ())
            ),
            selection_rule=None if payload.get("selection_rule") is None else str(payload.get("selection_rule")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.reason is not None:
            data["reason"] = self.reason
        if self.incision_set:
            data["incision_set"] = list(self.incision_set)
        if self.support_sets:
            data["support_sets"] = [list(support_set) for support_set in self.support_sets]
        if self.selection_rule is not None:
            data["selection_rule"] = self.selection_rule
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
    def from_mapping(cls, data: object) -> EntrenchmentReason:
        if data is None:
            return cls()
        payload = _optional_mapping(data, "entrenchment_reason")
        if not payload:
            return cls()
        raw_override_priority = payload.get("override_priority", payload.get("override"))
        raw_support_count = payload.get("support_count")
        return cls(
            override_priority=_coerce_override_priority(raw_override_priority),
            override_key=None if payload.get("override_key") is None else str(payload.get("override_key")),
            support_count=(
                None if raw_support_count is None else int(raw_support_count)
            ),
            essential_support=to_assumption_ids(payload.get("essential_support") or ()),
            iterated_operator=(
                None
                if payload.get("iterated_operator") is None
                else str(payload.get("iterated_operator"))
            ),
            revised_in=(
                None if payload.get("revised_in") is None else bool(payload.get("revised_in"))
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
        if ranking_data is not None and not isinstance(ranking_data, Mapping):
            raise ValueError("support revision explanation field 'ranking' must be a mapping")
        return cls(
            status=str(data.get("status") or "accepted"),
            reason=str(data.get("reason") or "unchanged"),
            ranking=(
                None
                if ranking_data is None
                else EntrenchmentReason.from_mapping(ranking_data)
            ),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            support_sets=tuple(
                to_assumption_ids(support_set)
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
        atoms_payload = _optional_mapping(data.get("atoms"), "atoms")
        atoms: dict[str, RevisionAtomExplanation] = {}
        for atom_id, atom_data in atoms_payload.items():
            if not isinstance(atom_data, Mapping):
                raise ValueError(f"support revision explanation field 'atoms.{atom_id}' must be a mapping")
            atoms[str(atom_id)] = RevisionAtomExplanation.from_mapping(atom_data)
        return cls(
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (data.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (data.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            atoms=atoms,
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
