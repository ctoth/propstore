from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"worldline revision field '{field_name}' must be a mapping")
    return value


@dataclass(frozen=True)
class RevisionAtomRef:
    kind: str = "assertion"
    assertion_id: str | None = None
    assumption_id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None

    @classmethod
    def from_mapping(cls, data: object) -> RevisionAtomRef | None:
        if data is None:
            return None
        payload = _optional_mapping(data, "atom")
        if not payload:
            return None
        kind = str(payload.get("kind") or "assertion")
        assertion_id = payload.get("assertion_id")
        assumption_id = payload.get("assumption_id")
        if assertion_id is None and kind == "assertion":
            assertion_id = payload.get("id")
        if assumption_id is None and kind == "assumption":
            assumption_id = payload.get("id")
        return cls(
            kind=kind,
            assertion_id=None if assertion_id is None else str(assertion_id),
            assumption_id=None if assumption_id is None else str(assumption_id),
            atom_id=None if payload.get("atom_id") is None else str(payload.get("atom_id")),
            value=payload.get("value"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind}
        if self.kind == "assertion" and self.assertion_id is not None:
            data["id"] = self.assertion_id
        if self.kind == "assumption" and self.assumption_id is not None:
            data["id"] = self.assumption_id
        if self.atom_id is not None:
            data["atom_id"] = self.atom_id
        if self.value is not None:
            data["value"] = self.value
        return data

    def to_revision_input(self) -> dict[str, Any]:
        data = self.to_dict()
        if self.kind == "assertion":
            if self.assertion_id is None:
                raise ValueError("Assertion revision atom requires an assertion_id")
            data["assertion_id"] = self.assertion_id
            if self.atom_id is not None:
                data["atom_id"] = self.atom_id
            return data
        if self.kind == "assumption":
            if self.assumption_id is None:
                raise ValueError("Assumption revision atom requires an assumption_id")
            data["assumption_id"] = self.assumption_id
            if self.atom_id is not None:
                data["atom_id"] = self.atom_id
            return data
        raise ValueError(f"Unsupported revision atom kind: {self.kind}")

    def resolved_atom_id(self) -> str | None:
        if self.atom_id:
            return self.atom_id
        if self.kind == "assertion" and self.assertion_id:
            return self.assertion_id
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
    def from_mapping(cls, data: object) -> RevisionConflictSelection:
        if data is None:
            return cls()
        payload = _optional_mapping(data, "conflicts")
        if not payload:
            return cls()
        return cls(
            targets_by_atom_id={
                str(atom_id): tuple(str(target_id) for target_id in target_ids)
                for atom_id, target_ids in payload.items()
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
    explanation: Any | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))

    @classmethod
    def from_mapping(cls, data: object) -> WorldlineRevisionResult | None:
        if data is None:
            return None
        payload = _optional_mapping(data, "result")
        if not payload:
            return None
        explanation_data = payload.get("explanation")
        if explanation_data is not None and not isinstance(explanation_data, Mapping):
            raise ValueError("worldline revision field 'explanation' must be a mapping")
        return cls(
            accepted_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("accepted_atom_ids") or ())),
            rejected_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("rejected_atom_ids") or ())),
            incision_set=tuple(str(atom_id) for atom_id in (payload.get("incision_set") or ())),
            explanation=None if explanation_data is None else dict(explanation_data),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "accepted_atom_ids": list(self.accepted_atom_ids),
            "rejected_atom_ids": list(self.rejected_atom_ids),
            "incision_set": list(self.incision_set),
        }
        if self.explanation is not None:
            data["explanation"] = _to_plain_data(self.explanation)
        return data


@dataclass(frozen=True)
class WorldlineRevisionState:
    operation: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    result: WorldlineRevisionResult | None = None
    state: Any | None = None
    status: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_atom_ids", tuple(str(atom_id) for atom_id in self.target_atom_ids))

    @classmethod
    def from_mapping(cls, data: object) -> WorldlineRevisionState | None:
        if data is None:
            return None
        payload = _optional_mapping(data, "revision")
        if not payload:
            return None
        state_data = payload.get("state")
        result_data = payload.get("result")
        if result_data is not None and not isinstance(result_data, Mapping):
            raise ValueError("worldline revision field 'result' must be a mapping")
        if state_data is not None and not isinstance(state_data, Mapping):
            raise ValueError("worldline revision field 'state' must be a mapping")
        return cls(
            operation=str(payload.get("operation") or ""),
            input_atom_id=None if payload.get("input_atom_id") is None else str(payload.get("input_atom_id")),
            target_atom_ids=tuple(str(atom_id) for atom_id in (payload.get("target_atom_ids") or ())),
            result=WorldlineRevisionResult.from_mapping(result_data),
            state=None if state_data is None else dict(state_data),
            status=None if payload.get("status") is None else str(payload.get("status")),
            error=None if payload.get("error") is None else str(payload.get("error")),
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
            data["state"] = _to_plain_data(self.state)
        if self.status is not None:
            data["status"] = self.status
        if self.error is not None:
            data["error"] = self.error
        return data


def _to_plain_data(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, Mapping):
        return {
            str(key): _to_plain_data(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_to_plain_data(item) for item in value]
    if isinstance(value, list):
        return [_to_plain_data(item) for item in value]
    return value
