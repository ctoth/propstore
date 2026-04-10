from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.revision.explanation_types import RevisionExplanation
from propstore.revision.snapshot_types import EpistemicStateSnapshot


@dataclass(frozen=True)
class RevisionAtomRef:
    kind: str = "claim"
    claim_id: str | None = None
    assumption_id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> RevisionAtomRef | None:
        if not data:
            return None
        kind = str(data.get("kind") or "claim")
        claim_id = data.get("claim_id")
        assumption_id = data.get("assumption_id")
        if claim_id is None and kind == "claim":
            claim_id = data.get("id")
        if assumption_id is None and kind == "assumption":
            assumption_id = data.get("id")
        return cls(
            kind=kind,
            claim_id=None if claim_id is None else str(claim_id),
            assumption_id=None if assumption_id is None else str(assumption_id),
            atom_id=None if data.get("atom_id") is None else str(data.get("atom_id")),
            value=data.get("value"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind}
        if self.kind == "claim" and self.claim_id is not None:
            data["id"] = self.claim_id
        if self.kind == "assumption" and self.assumption_id is not None:
            data["id"] = self.assumption_id
        if self.atom_id is not None:
            data["atom_id"] = self.atom_id
        if self.value is not None:
            data["value"] = self.value
        return data

    def to_revision_input(self) -> dict[str, Any]:
        return self.to_dict()

    def resolved_atom_id(self) -> str | None:
        if self.atom_id:
            return self.atom_id
        if self.kind == "claim" and self.claim_id:
            return f"claim:{self.claim_id}"
        if self.kind == "assumption" and self.assumption_id:
            return f"assumption:{self.assumption_id}"
        return None


@dataclass(frozen=True)
class RevisionConflictSelection:
    targets_by_atom_id: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "targets_by_atom_id",
            {
                str(atom_id): tuple(str(target_id) for target_id in target_ids)
                for atom_id, target_ids in self.targets_by_atom_id.items()
            },
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> RevisionConflictSelection:
        if not data:
            return cls()
        return cls(
            targets_by_atom_id={
                str(atom_id): tuple(str(target_id) for target_id in target_ids)
                for atom_id, target_ids in data.items()
            }
        )

    def to_dict(self) -> dict[str, list[str]]:
        return {
            atom_id: list(target_ids)
            for atom_id, target_ids in self.targets_by_atom_id.items()
        }

    def targets_for(self, atom_id: str) -> tuple[str, ...]:
        return self.targets_by_atom_id.get(atom_id, ())

    def to_revision_input(self) -> dict[str, tuple[str, ...]]:
        return {
            atom_id: tuple(target_ids)
            for atom_id, target_ids in self.targets_by_atom_id.items()
        }


@dataclass(frozen=True)
class WorldlineRevisionResult:
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: RevisionExplanation | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WorldlineRevisionResult | None:
        if not data:
            return None
        explanation_data = data.get("explanation")
        return cls(
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (data.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (data.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (data.get("incision_set") or ())),
            explanation=(
                None
                if not isinstance(explanation_data, Mapping)
                else RevisionExplanation.from_mapping(explanation_data)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "rejected_atom_ids": list(self.rejected_atom_ids),
            "incision_set": list(self.incision_set),
        }
        if self.explanation is not None:
            data["explanation"] = self.explanation.to_dict()
        return data


@dataclass(frozen=True)
class WorldlineRevisionState:
    operation: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    result: WorldlineRevisionResult | None = None
    state: EpistemicStateSnapshot | None = None
    status: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_atom_ids", tuple(str(atom_id) for atom_id in self.target_atom_ids))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WorldlineRevisionState | None:
        if not data:
            return None
        state_data = data.get("state")
        return cls(
            operation=str(data.get("operation") or ""),
            input_atom_id=None if data.get("input_atom_id") is None else str(data.get("input_atom_id")),
            target_atom_ids=tuple(str(atom_id) for atom_id in (data.get("target_atom_ids") or ())),
            result=WorldlineRevisionResult.from_mapping(
                data.get("result") if isinstance(data.get("result"), Mapping) else None
            ),
            state=(
                None
                if not isinstance(state_data, Mapping)
                else EpistemicStateSnapshot.from_mapping(state_data)
            ),
            status=None if data.get("status") is None else str(data.get("status")),
            error=None if data.get("error") is None else str(data.get("error")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "operation": self.operation,
            "target_atom_ids": list(self.target_atom_ids),
        }
        if self.input_atom_id is not None:
            data["input_atom_id"] = self.input_atom_id
        if self.result is not None:
            data["result"] = self.result.to_dict()
        if self.state is not None:
            data["state"] = self.state.to_dict()
        if self.status is not None:
            data["status"] = self.status
        if self.error is not None:
            data["error"] = self.error
        return data
