from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeGuard

import msgspec

from quire.canonical import canonical_json_bytes
from quire.documents import convert_document_value, to_document_builtins
from msgspec.structs import replace as replace_struct

from propstore.support_revision.explanation_types import RevisionAtomDetail
from propstore.support_revision.state import EpistemicState

EPistemicSnapshotVersion = "propstore.epistemic_snapshot.v2"
TransitionJournalVersion = "propstore.transition_journal.v3"


class JournalOperator(Enum):
    EXPAND = "expand"
    REVISE = "revise"
    CONTRACT = "contract"
    ITERATED_REVISE = "iterated_revise"
    IC_MERGE = "ic_merge"


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _is_sequence(value: object) -> TypeGuard[Sequence[Any]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if _is_mapping(value) else {}


def _required_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not _is_mapping(value):
        raise ValueError(f"epistemic history requires mapping '{field_name}'")
    return value


def _to_plain_data(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if _is_mapping(value):
        return {str(key): _to_plain_data(item) for key, item in value.items()}
    if _is_sequence(value):
        return [_to_plain_data(item) for item in value]
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(_to_plain_data(payload))).hexdigest()


def _canonical_text(payload: Mapping[str, Any]) -> str:
    return canonical_json_bytes(_to_plain_data(payload)).decode("ascii")


def _journal_operator(value: JournalOperator | str) -> JournalOperator:
    if isinstance(value, JournalOperator):
        return value
    return JournalOperator(str(value))


def _version_policy_snapshot(
    value: Mapping[str, str],
) -> dict[str, str]:
    required = {
        "revision_policy_version",
        "ranking_policy_version",
        "entrenchment_policy_version",
    }
    snapshot = {str(key): str(item) for key, item in value.items()}
    missing = sorted(required - set(snapshot))
    if missing:
        raise ValueError(f"transition journal missing policy versions: {', '.join(missing)}")
    return snapshot


class EpistemicSnapshot(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
):
    state: EpistemicState
    schema_version: str = EPistemicSnapshotVersion
    content_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != EPistemicSnapshotVersion:
            raise ValueError(f"unsupported epistemic snapshot version: {self.schema_version}")
        computed = _stable_hash(self._hash_payload())
        if not self.content_hash:
            object.__setattr__(self, "content_hash", computed)
        elif str(self.content_hash) != computed:
            raise ValueError("epistemic snapshot content_hash does not match payload")

    @classmethod
    def from_state(cls, state: EpistemicState) -> EpistemicSnapshot:
        # Deep-copy through the document codec so the stored snapshot detaches
        # from the live state's mutable dict fields (WS-J Step 8). Same type on
        # both ends — this is copy semantics, not a type conversion.
        return cls(
            state=convert_document_value(
                to_document_builtins(state),
                EpistemicState,
                source="epistemic snapshot state",
            )
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EpistemicSnapshot:
        """Structural decode of a persisted snapshot; ``__post_init__`` verifies the hash."""
        return convert_document_value(
            dict(_required_mapping(data, "snapshot")),
            cls,
            source="epistemic snapshot",
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EpistemicSnapshot):
            return NotImplemented
        return self.content_hash == other.content_hash

    def __hash__(self) -> int:
        return hash(self.content_hash)

    def to_dict(self) -> dict[str, Any]:
        return dict(_required_mapping(to_document_builtins(self), "epistemic snapshot"))

    def to_canonical_json(self) -> str:
        return _canonical_text(self.to_dict())

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state": dict(
                _required_mapping(
                    to_document_builtins(self.state),
                    "epistemic snapshot state",
                )
            ),
        }


class TransitionOperation(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
):
    name: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    parameters: dict[str, Any] = msgspec.field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(
            self,
            "input_atom_id",
            None if self.input_atom_id is None else str(self.input_atom_id),
        )
        object.__setattr__(self, "target_atom_ids", tuple(str(item) for item in self.target_atom_ids))
        object.__setattr__(self, "parameters", _to_plain_data(dict(self.parameters)))

    def to_dict(self) -> dict[str, Any]:
        return dict(_required_mapping(to_document_builtins(self), "operation"))


class TransitionJournalEntry(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
):
    state_in: EpistemicSnapshot
    operation: TransitionOperation
    policy_id: str
    operator: JournalOperator
    operator_input: dict[str, Any]
    version_policy_snapshot: dict[str, str]
    state_out: EpistemicSnapshot
    explanation: dict[str, RevisionAtomDetail] = msgspec.field(
        default_factory=dict[str, RevisionAtomDetail]
    )
    policy: dict[str, Any] = msgspec.field(default_factory=dict[str, Any])
    schema_version: str = TransitionJournalVersion
    content_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != TransitionJournalVersion:
            raise ValueError(f"unsupported transition journal version: {self.schema_version}")
        object.__setattr__(self, "policy_id", str(self.policy_id))
        object.__setattr__(self, "operator", _journal_operator(self.operator))
        object.__setattr__(self, "operator_input", _to_plain_data(dict(self.operator_input)))
        object.__setattr__(
            self,
            "version_policy_snapshot",
            _version_policy_snapshot(self.version_policy_snapshot),
        )
        canonical_json_bytes(_to_plain_data(self.operator_input))
        canonical_json_bytes(_to_plain_data(self.version_policy_snapshot))
        object.__setattr__(self, "policy", _to_plain_data(dict(self.policy)))
        object.__setattr__(
            self,
            "explanation",
            {str(atom_id): detail for atom_id, detail in self.explanation.items()},
        )
        computed = _stable_hash(self._hash_payload())
        if not self.content_hash:
            object.__setattr__(self, "content_hash", computed)
        elif str(self.content_hash) != computed:
            raise ValueError("transition journal entry content_hash does not match payload")

    @property
    def normalized_state_in(self) -> dict[str, Any]:
        """Canonical dict encoding of ``state_in`` — derived, never stored twice."""
        return self.state_in.state.to_canonical_dict()

    @property
    def normalized_state_out(self) -> dict[str, Any]:
        """Canonical dict encoding of ``state_out`` — derived, never stored twice."""
        return self.state_out.state.to_canonical_dict()

    @classmethod
    def from_states(
        cls,
        *,
        state_in: EpistemicState,
        operation: TransitionOperation,
        policy_id: str,
        operator: JournalOperator,
        operator_input: Mapping[str, Any],
        version_policy_snapshot: Mapping[str, str],
        state_out: EpistemicState,
        explanation: Mapping[str, RevisionAtomDetail],
        policy_payload: Mapping[str, Any] | None = None,
    ) -> TransitionJournalEntry:
        journal_state_out = _state_with_journal_event_policy(
            state_out,
            version_policy_snapshot=version_policy_snapshot,
        )
        return cls(
            state_in=EpistemicSnapshot.from_state(state_in),
            operation=operation,
            policy_id=policy_id,
            operator=operator,
            operator_input=dict(operator_input),
            version_policy_snapshot=dict(version_policy_snapshot),
            state_out=EpistemicSnapshot.from_state(journal_state_out),
            explanation=dict(explanation),
            policy={} if policy_payload is None else dict(policy_payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(_required_mapping(to_document_builtins(self), "journal entry"))

    def _hash_payload(self) -> dict[str, Any]:
        payload = dict(_required_mapping(to_document_builtins(self), "journal entry"))
        payload.pop("content_hash", None)
        return payload


def _state_with_journal_event_policy(
    state: EpistemicState,
    *,
    version_policy_snapshot: Mapping[str, str],
) -> EpistemicState:
    if not state.history:
        return state
    latest = state.history[-1]
    if latest.event is None:
        return state
    event = latest.event
    if event.policy_snapshot == dict(version_policy_snapshot) and event.replay_status == "replayed":
        return state
    updated_event = replace_struct(
        event,
        policy_snapshot=version_policy_snapshot,
        replay_status="replayed",
    )
    updated_latest = replace_struct(latest, event=updated_event)
    return replace_struct(state, history=state.history[:-1] + (updated_latest,))


@dataclass(frozen=True)
class ChainIntegrityReport:
    ok: bool
    checked_entry_hashes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReplayDivergence:
    entry_index: int
    operator: JournalOperator
    operator_input: Mapping[str, Any]
    expected_state_hash: str
    actual_state_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_index", int(self.entry_index))
        object.__setattr__(self, "operator", _journal_operator(self.operator))
        object.__setattr__(self, "operator_input", _to_plain_data(dict(self.operator_input)))
        object.__setattr__(self, "expected_state_hash", str(self.expected_state_hash))
        object.__setattr__(self, "actual_state_hash", str(self.actual_state_hash))


@dataclass(frozen=True)
class ReplayReport:
    ok: bool
    checked_entry_hashes: tuple[str, ...] = ()
    divergences: tuple[ReplayDivergence, ...] = ()
    errors: tuple[str, ...] = ()


class TransitionJournal(
    msgspec.Struct,
    frozen=True,
    kw_only=True,
    forbid_unknown_fields=True,
):
    entries: tuple[TransitionJournalEntry, ...] = ()
    schema_version: str = TransitionJournalVersion

    def __post_init__(self) -> None:
        if self.schema_version != TransitionJournalVersion:
            raise ValueError(f"unsupported transition journal version: {self.schema_version}")
        object.__setattr__(self, "entries", tuple(self.entries))

    def check_chain_integrity(self) -> ChainIntegrityReport:
        errors: list[str] = []
        checked: list[str] = []
        previous_out: str | None = None
        for index, entry in enumerate(self.entries):
            checked.append(entry.content_hash)
            if previous_out is not None and previous_out != entry.state_in.content_hash:
                errors.append(f"entry {index} state_in does not match previous state_out")
            previous_out = entry.state_out.content_hash
        return ChainIntegrityReport(
            ok=not errors,
            checked_entry_hashes=tuple(checked),
            errors=tuple(errors),
        )

    def replay(self) -> ReplayReport:
        from propstore.support_revision.dispatch import dispatch

        checked: list[str] = []
        divergences: list[ReplayDivergence] = []
        errors: list[str] = []
        for index, entry in enumerate(self.entries):
            checked.append(entry.content_hash)
            policy_error = _entry_event_policy_error(entry)
            if policy_error is not None:
                errors.append(f"entry {index} {policy_error}")
                continue
            try:
                replayed_state = dispatch(
                    entry.operator,
                    state_in=entry.normalized_state_in,
                    operator_input=entry.operator_input,
                    policy=entry.version_policy_snapshot,
                )
            except Exception as exc:
                errors.append(f"entry {index} replay failed for {entry.operator.value}: {exc}")
                continue
            replayed_snapshot = EpistemicSnapshot.from_state(replayed_state)
            if replayed_state.to_canonical_dict() != entry.normalized_state_out:
                divergences.append(
                    ReplayDivergence(
                        entry_index=index,
                        operator=entry.operator,
                        operator_input=entry.operator_input,
                        expected_state_hash=entry.state_out.content_hash,
                        actual_state_hash=replayed_snapshot.content_hash,
                    )
                )
        return ReplayReport(
            ok=not errors and not divergences,
            checked_entry_hashes=tuple(checked),
            divergences=tuple(divergences),
            errors=tuple(errors),
        )


def _entry_event_policy_error(entry: TransitionJournalEntry) -> str | None:
    history = entry.state_out.state.history
    if not history:
        return None
    event = history[-1].event
    if event is None:
        return None
    expected = {str(key): str(value) for key, value in entry.version_policy_snapshot.items()}
    if dict(event.policy_snapshot) != expected:
        return "policy snapshot mismatch between revision event and journal entry"
    return None


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
    source_state = _required_mapping(
        to_document_builtins(source.state),
        "source epistemic state",
    )
    target_state = _required_mapping(
        to_document_builtins(target.state),
        "target epistemic state",
    )
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
    state_payload = dict(
        _required_mapping(
            to_document_builtins(source.state),
            "source epistemic state",
        )
    )
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
    for atom in (_as_mapping(state_payload.get("base")).get("atoms") or ()):
        if not _is_mapping(atom):
            continue
        if atom.get("type") != "assertion":
            continue
        provenance[str(atom.get("atom_id"))] = _to_plain_data(
            atom.get("source_claims") or ()
        )
    return provenance


def _dependencies(state_payload: Mapping[str, Any]) -> dict[str, Any]:
    base = _as_mapping(state_payload.get("base"))
    dependencies: dict[str, Any] = {}
    for field_name in ("support_sets", "essential_support"):
        field_data = _as_mapping(base.get(field_name))
        for atom_id, value in field_data.items():
            dependencies[f"{atom_id}.{field_name}"] = _to_plain_data(value)
    return dependencies


def _assert_current_value(state_payload: Mapping[str, Any], delta: SemanticFieldDelta) -> None:
    current = None
    if delta.surface == "assertion_acceptance":
        current = _accepted_assertions(state_payload).get(delta.key)
    elif delta.surface == "warrant":
        current = _as_mapping(state_payload.get("entrenchment_reasons")).get(delta.key)
    elif delta.surface == "ranking":
        current = _as_mapping(state_payload.get("ranking")).get(delta.key)
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
    field_data = dict(_as_mapping(state_payload.get(field_name)))
    if value is None:
        field_data.pop(key, None)
    else:
        field_data[key] = value
    state_payload[field_name] = field_data


def _refresh_ranked_atom_ids(state_payload: dict[str, Any]) -> None:
    ranking = _as_mapping(state_payload.get("ranking"))
    state_payload["ranked_atom_ids"] = [
        atom_id
        for atom_id, _ in sorted(ranking.items(), key=lambda item: (int(item[1]), str(item[0])))
    ]


def _set_atom_provenance(state_payload: dict[str, Any], atom_id: str, value: Any) -> None:
    base = dict(_as_mapping(state_payload.get("base")))
    atoms: list[Any] = []
    for atom in base.get("atoms") or ():
        if not _is_mapping(atom) or str(atom.get("atom_id")) != atom_id:
            atoms.append(atom)
            continue
        updated_atom = dict(atom)
        updated_atom["source_claims"] = [] if value is None else value
        atoms.append(updated_atom)
    base["atoms"] = atoms
    state_payload["base"] = base


def _apply_dependency_delta(state_payload: dict[str, Any], delta: SemanticFieldDelta) -> None:
    if "." not in delta.key:
        raise ValueError(f"dependency delta key must identify atom field: {delta.key}")
    atom_id, field_name = delta.key.rsplit(".", 1)
    if field_name not in {"support_sets", "essential_support"}:
        raise ValueError(f"unsupported dependency field: {field_name}")
    base = dict(_as_mapping(state_payload.get("base")))
    field_data = dict(_as_mapping(base.get(field_name)))
    if delta.new_value is None:
        field_data.pop(atom_id, None)
    else:
        field_data[atom_id] = delta.new_value
    base[field_name] = field_data
    state_payload["base"] = base
