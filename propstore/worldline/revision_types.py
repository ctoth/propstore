from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


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
