from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from propstore.canonical_json import canonical_dumps
from propstore.support_revision.explanation_types import (
    RevisionAtomDetail,
    coerce_revision_atom_detail,
)
from propstore.support_revision.snapshot_types import EpistemicStateSnapshot
from propstore.support_revision.state import EpistemicState


EPistemicSnapshotVersion = "propstore.epistemic_snapshot.v1"
TransitionJournalVersion = "propstore.transition_journal.v1"


def _required_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"epistemic history requires mapping '{field_name}'")
    return value


def _to_plain_data(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, Mapping):
        return {str(key): _to_plain_data(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain_data(item) for item in value]
    if isinstance(value, list):
        return [_to_plain_data(item) for item in value]
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return canonical_dumps(_to_plain_data(payload))


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EpistemicSnapshot:
    state: EpistemicStateSnapshot
    schema_version: str = EPistemicSnapshotVersion

    def __post_init__(self) -> None:
        if not isinstance(self.state, EpistemicStateSnapshot):
            raise TypeError("EpistemicSnapshot requires an EpistemicStateSnapshot")
        if self.schema_version != EPistemicSnapshotVersion:
            raise ValueError(f"unsupported epistemic snapshot version: {self.schema_version}")

    @classmethod
    def from_state(cls, state: EpistemicState) -> EpistemicSnapshot:
        return cls(state=EpistemicStateSnapshot.from_state(state))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EpistemicSnapshot:
        payload = _required_mapping(data, "snapshot")
        schema_version = str(payload.get("schema_version") or "")
        if schema_version != EPistemicSnapshotVersion:
            raise ValueError(f"unsupported epistemic snapshot version: {schema_version}")
        state_payload = _required_mapping(payload.get("state"), "state")
        snapshot = cls(
            state=EpistemicStateSnapshot.from_mapping(state_payload),
            schema_version=schema_version,
        )
        recorded_hash = payload.get("content_hash")
        if recorded_hash is not None and str(recorded_hash) != snapshot.content_hash:
            raise ValueError("epistemic snapshot content_hash does not match payload")
        return snapshot

    @property
    def content_hash(self) -> str:
        return _stable_hash(self._hash_payload())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EpistemicSnapshot):
            return NotImplemented
        return self.content_hash == other.content_hash

    def __hash__(self) -> int:
        return hash(self.content_hash)

    def to_dict(self) -> dict[str, Any]:
        data = self._hash_payload()
        data["content_hash"] = self.content_hash
        return data

    def to_canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state": self.state.to_dict(),
        }


@dataclass(frozen=True)
class TransitionOperation:
    name: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(
            self,
            "input_atom_id",
            None if self.input_atom_id is None else str(self.input_atom_id),
        )
        object.__setattr__(self, "target_atom_ids", tuple(str(item) for item in self.target_atom_ids))
        object.__setattr__(self, "parameters", _to_plain_data(dict(self.parameters)))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> TransitionOperation:
        payload = _required_mapping(data, "operation")
        return cls(
            name=str(payload.get("name") or ""),
            input_atom_id=None if payload.get("input_atom_id") is None else str(payload.get("input_atom_id")),
            target_atom_ids=tuple(str(item) for item in (payload.get("target_atom_ids") or ())),
            parameters=dict(_required_mapping(payload.get("parameters") or {}, "parameters")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "target_atom_ids": list(self.target_atom_ids),
            "parameters": _to_plain_data(self.parameters),
        }
        if self.input_atom_id is not None:
            data["input_atom_id"] = self.input_atom_id
        return data


@dataclass(frozen=True)
class TransitionJournalEntry:
    state_in: EpistemicSnapshot
    operation: TransitionOperation
    policy_id: str
    operator: str
    state_out: EpistemicSnapshot
    explanation: Mapping[str, RevisionAtomDetail] = field(default_factory=dict)
    policy_payload: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = TransitionJournalVersion

    def __post_init__(self) -> None:
        if self.schema_version != TransitionJournalVersion:
            raise ValueError(f"unsupported transition journal version: {self.schema_version}")
        object.__setattr__(self, "policy_id", str(self.policy_id))
        object.__setattr__(self, "operator", str(self.operator))
        object.__setattr__(self, "policy_payload", _to_plain_data(dict(self.policy_payload)))
        object.__setattr__(
            self,
            "explanation",
            {
                str(atom_id): coerce_revision_atom_detail(detail)
                for atom_id, detail in self.explanation.items()
            },
        )

    @classmethod
    def from_states(
        cls,
        *,
        state_in: EpistemicState,
        operation: TransitionOperation,
        policy_id: str,
        policy_payload: Mapping[str, Any] | None = None,
        operator: str,
        state_out: EpistemicState,
        explanation: Mapping[str, RevisionAtomDetail],
    ) -> TransitionJournalEntry:
        return cls(
            state_in=EpistemicSnapshot.from_state(state_in),
            operation=operation,
            policy_id=policy_id,
            policy_payload={} if policy_payload is None else policy_payload,
            operator=operator,
            state_out=EpistemicSnapshot.from_state(state_out),
            explanation=explanation,
        )

    @property
    def content_hash(self) -> str:
        return _stable_hash(self._hash_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._hash_payload()
        data["content_hash"] = self.content_hash
        return data

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state_in_hash": self.state_in.content_hash,
            "state_in": self.state_in.to_dict(),
            "operation": self.operation.to_dict(),
            "policy_id": self.policy_id,
            "policy": _to_plain_data(self.policy_payload),
            "operator": self.operator,
            "state_out_hash": self.state_out.content_hash,
            "state_out": self.state_out.to_dict(),
            "explanation": {
                atom_id: detail.to_dict()
                for atom_id, detail in self.explanation.items()
            },
        }


@dataclass(frozen=True)
class ReplayDeterminismReport:
    ok: bool
    checked_entry_hashes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransitionJournal:
    entries: tuple[TransitionJournalEntry, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    def check_replay_determinism(self) -> ReplayDeterminismReport:
        errors: list[str] = []
        checked: list[str] = []
        previous_out: str | None = None
        for index, entry in enumerate(self.entries):
            checked.append(entry.content_hash)
            if entry.to_dict()["state_in_hash"] != entry.state_in.content_hash:
                errors.append(f"entry {index} state_in hash mismatch")
            if entry.to_dict()["state_out_hash"] != entry.state_out.content_hash:
                errors.append(f"entry {index} state_out hash mismatch")
            if previous_out is not None and previous_out != entry.state_in.content_hash:
                errors.append(f"entry {index} state_in does not match previous state_out")
            previous_out = entry.state_out.content_hash
        return ReplayDeterminismReport(
            ok=not errors,
            checked_entry_hashes=tuple(checked),
            errors=tuple(errors),
        )


@dataclass(frozen=True)
class SemanticFieldDelta:
    surface: str
    key: str
    old_value: Any
    new_value: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "surface", str(self.surface))
        object.__setattr__(self, "key", str(self.key))
        object.__setattr__(self, "old_value", _to_plain_data(self.old_value))
        object.__setattr__(self, "new_value", _to_plain_data(self.new_value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass(frozen=True)
class EpistemicSemanticDiff:
    source_hash: str
    target_hash: str
    deltas: tuple[SemanticFieldDelta, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_hash", str(self.source_hash))
        object.__setattr__(self, "target_hash", str(self.target_hash))
        object.__setattr__(self, "deltas", tuple(self.deltas))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_hash": self.source_hash,
            "target_hash": self.target_hash,
            "deltas": [delta.to_dict() for delta in self.deltas],
        }


def diff_epistemic_snapshots(
    source: EpistemicSnapshot,
    target: EpistemicSnapshot,
) -> EpistemicSemanticDiff:
    source_state = source.state.to_dict()
    target_state = target.state.to_dict()
    deltas: list[SemanticFieldDelta] = []
    deltas.extend(_mapping_deltas("assertion_acceptance", _accepted_assertions(source_state), _accepted_assertions(target_state)))
    deltas.extend(_mapping_deltas("warrant", source_state.get("entrenchment_reasons") or {}, target_state.get("entrenchment_reasons") or {}))
    deltas.extend(_mapping_deltas("ranking", source_state.get("ranking") or {}, target_state.get("ranking") or {}))
    deltas.extend(_mapping_deltas("provenance", _assertion_provenance(source_state), _assertion_provenance(target_state)))
    deltas.extend(_mapping_deltas("dependency", _dependencies(source_state), _dependencies(target_state)))
    return EpistemicSemanticDiff(
        source_hash=source.content_hash,
        target_hash=target.content_hash,
        deltas=tuple(deltas),
    )


def apply_epistemic_diff(
    source: EpistemicSnapshot,
    diff: EpistemicSemanticDiff,
) -> EpistemicSnapshot:
    if diff.source_hash != source.content_hash:
        raise ValueError("semantic diff source_hash does not match source snapshot")
    state_payload = source.state.to_dict()
    for delta in diff.deltas:
        _assert_current_value(state_payload, delta)
        if delta.surface == "assertion_acceptance":
            _apply_acceptance_delta(state_payload, delta)
        elif delta.surface == "warrant":
            _set_mapping_value(state_payload, "entrenchment_reasons", delta.key, delta.new_value)
        elif delta.surface == "ranking":
            _set_mapping_value(state_payload, "ranking", delta.key, delta.new_value)
            _refresh_ranked_atom_ids(state_payload)
        elif delta.surface == "provenance":
            _set_atom_provenance(state_payload, delta.key, delta.new_value)
        elif delta.surface == "dependency":
            _apply_dependency_delta(state_payload, delta)
        else:
            raise ValueError(f"unsupported semantic diff surface: {delta.surface}")
    snapshot = EpistemicSnapshot.from_mapping({
        "schema_version": EPistemicSnapshotVersion,
        "state": state_payload,
    })
    if snapshot.content_hash != diff.target_hash:
        raise ValueError("semantic diff did not reproduce target snapshot")
    return snapshot


def _mapping_deltas(
    surface: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> tuple[SemanticFieldDelta, ...]:
    deltas: list[SemanticFieldDelta] = []
    for key in sorted(set(source) | set(target)):
        old_value = _to_plain_data(source.get(key))
        new_value = _to_plain_data(target.get(key))
        if old_value != new_value:
            deltas.append(SemanticFieldDelta(surface, key, old_value, new_value))
    return tuple(deltas)


def _accepted_assertions(state_payload: Mapping[str, Any]) -> dict[str, bool]:
    return {
        str(atom_id): True
        for atom_id in (state_payload.get("accepted_atom_ids") or ())
        if str(atom_id).startswith("ps:assertion:")
    }


def _assertion_provenance(state_payload: Mapping[str, Any]) -> dict[str, Any]:
    provenance: dict[str, Any] = {}
    for atom in ((state_payload.get("base") or {}).get("atoms") or ()):
        if not isinstance(atom, Mapping):
            continue
        if atom.get("kind") != "assertion":
            continue
        payload = atom.get("payload")
        if not isinstance(payload, Mapping):
            continue
        provenance[str(atom.get("atom_id"))] = _to_plain_data(payload.get("source_claims") or ())
    return provenance


def _dependencies(state_payload: Mapping[str, Any]) -> dict[str, Any]:
    base = state_payload.get("base") or {}
    if not isinstance(base, Mapping):
        return {}
    dependencies: dict[str, Any] = {}
    for field_name in ("support_sets", "essential_support"):
        field = base.get(field_name) or {}
        if not isinstance(field, Mapping):
            continue
        for atom_id, value in field.items():
            dependencies[f"{atom_id}.{field_name}"] = _to_plain_data(value)
    return dependencies


def _assert_current_value(state_payload: Mapping[str, Any], delta: SemanticFieldDelta) -> None:
    current = None
    if delta.surface == "assertion_acceptance":
        current = _accepted_assertions(state_payload).get(delta.key)
    elif delta.surface == "warrant":
        current = (state_payload.get("entrenchment_reasons") or {}).get(delta.key)
    elif delta.surface == "ranking":
        current = (state_payload.get("ranking") or {}).get(delta.key)
    elif delta.surface == "provenance":
        current = _assertion_provenance(state_payload).get(delta.key)
    elif delta.surface == "dependency":
        current = _dependencies(state_payload).get(delta.key)
    if _to_plain_data(current) != delta.old_value:
        raise ValueError(f"semantic diff old value mismatch for {delta.surface}.{delta.key}")


def _apply_acceptance_delta(state_payload: dict[str, Any], delta: SemanticFieldDelta) -> None:
    accepted = [str(atom_id) for atom_id in (state_payload.get("accepted_atom_ids") or ())]
    if delta.new_value is True and delta.key not in accepted:
        accepted.append(delta.key)
    if delta.new_value is not True:
        accepted = [atom_id for atom_id in accepted if atom_id != delta.key]
    state_payload["accepted_atom_ids"] = accepted


def _set_mapping_value(
    state_payload: dict[str, Any],
    field_name: str,
    key: str,
    value: Any,
) -> None:
    field = dict(state_payload.get(field_name) or {})
    if value is None:
        field.pop(key, None)
    else:
        field[key] = value
    state_payload[field_name] = field


def _refresh_ranked_atom_ids(state_payload: dict[str, Any]) -> None:
    ranking = state_payload.get("ranking") or {}
    if not isinstance(ranking, Mapping):
        return
    state_payload["ranked_atom_ids"] = [
        atom_id
        for atom_id, _ in sorted(ranking.items(), key=lambda item: (int(item[1]), str(item[0])))
    ]


def _set_atom_provenance(state_payload: dict[str, Any], atom_id: str, value: Any) -> None:
    base = dict(state_payload.get("base") or {})
    atoms: list[Any] = []
    for atom in base.get("atoms") or ():
        if not isinstance(atom, Mapping) or str(atom.get("atom_id")) != atom_id:
            atoms.append(atom)
            continue
        updated_atom = dict(atom)
        payload = dict(updated_atom.get("payload") or {})
        payload["source_claims"] = [] if value is None else value
        updated_atom["payload"] = payload
        atoms.append(updated_atom)
    base["atoms"] = atoms
    state_payload["base"] = base


def _apply_dependency_delta(state_payload: dict[str, Any], delta: SemanticFieldDelta) -> None:
    if "." not in delta.key:
        raise ValueError(f"dependency delta key must identify atom field: {delta.key}")
    atom_id, field_name = delta.key.rsplit(".", 1)
    if field_name not in {"support_sets", "essential_support"}:
        raise ValueError(f"unsupported dependency field: {field_name}")
    base = dict(state_payload.get("base") or {})
    field = dict(base.get(field_name) or {})
    if delta.new_value is None:
        field.pop(atom_id, None)
    else:
        field[atom_id] = delta.new_value
    base[field_name] = field
    state_payload["base"] = base
