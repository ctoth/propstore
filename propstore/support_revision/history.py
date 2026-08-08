from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeGuard, cast

import msgspec

from quire.canonical import canonical_json_bytes
from quire.documents import convert_document_value, to_document_builtins
from msgspec.structs import replace as replace_struct

from propstore.policies import PolicyProfile
from propstore.reporting import json_ready
from propstore.support_revision.explanation_types import RevisionAtomDetail
from propstore.support_revision.operator_inputs import OperatorInput
from propstore.support_revision.state import EpistemicState

EPistemicSnapshotVersion = "propstore.epistemic_snapshot.v2"
TransitionJournalVersion = "propstore.transition_journal.v5"


class JournalOperator(Enum):
    EXPAND = "expand"
    REVISE = "revise"
    CONTRACT = "contract"
    ITERATED_REVISE = "iterated_revise"
    IC_MERGE = "ic_merge"


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _required_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not _is_mapping(value):
        raise ValueError(f"epistemic history requires mapping '{field_name}'")
    return value


def _without_nulls(value: object) -> object:
    """Drop unset optional fields so they cannot reach the fingerprint.

    An absent field and a field explicitly set to ``null`` are the same fact,
    and encoders are free to elide one and emit the other: the charter's JSON
    drops an optional field left at ``None`` that the in-memory lowering keeps.
    A fingerprint that changes depending on which encoder produced the payload
    is not fingerprinting the content — it is fingerprinting the serializer.

    Inside a journal entry a ``null`` is never data: every mapping the entry
    reaches (``trace``, ``journal_metadata``) carries ids, hashes, and lists,
    so eliding nulls loses nothing. A payload whose ``null`` is meaningful must
    not be fingerprinted through this function.
    """

    if _is_mapping(value):
        return {
            str(key): _without_nulls(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_without_nulls(item) for item in cast("list[Any]", value)]
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    """Fingerprint a journal payload through the one canonical lowering.

    This used to prefer a value's own ``to_dict()`` when it had one, so a type
    carrying a hand-written encoder was hashed through *that* rather than
    through its fields — and a ``to_dict`` that emitted derived extras (a
    content hash, a derived id) made the fingerprint disagree with the document
    the codec actually stores. ``json_ready`` lowers every value the same way,
    and :func:`_without_nulls` removes the unset optionals, so what is hashed is
    what is written — by whichever encoder writes it.
    """

    return hashlib.sha256(
        canonical_json_bytes(_without_nulls(json_ready(payload)))
    ).hexdigest()


def _canonical_text(payload: Mapping[str, Any]) -> str:
    return canonical_json_bytes(json_ready(payload)).decode("ascii")


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
        raise ValueError(
            f"transition journal missing policy versions: {', '.join(missing)}"
        )
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
            raise ValueError(
                f"unsupported epistemic snapshot version: {self.schema_version}"
            )
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(
            self,
            "input_atom_id",
            None if self.input_atom_id is None else str(self.input_atom_id),
        )
        object.__setattr__(
            self, "target_atom_ids", tuple(str(item) for item in self.target_atom_ids)
        )

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
    operator_input: OperatorInput
    version_policy_snapshot: dict[str, str]
    state_out: EpistemicSnapshot
    explanation: dict[str, RevisionAtomDetail] = msgspec.field(
        default_factory=dict[str, RevisionAtomDetail]
    )
    policy: PolicyProfile | None = None
    schema_version: str = TransitionJournalVersion
    content_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != TransitionJournalVersion:
            raise ValueError(
                f"unsupported transition journal version: {self.schema_version}"
            )
        object.__setattr__(self, "policy_id", str(self.policy_id))
        object.__setattr__(self, "operator", _journal_operator(self.operator))
        object.__setattr__(
            self,
            "version_policy_snapshot",
            _version_policy_snapshot(self.version_policy_snapshot),
        )
        canonical_json_bytes(json_ready(self.operator_input))
        canonical_json_bytes(json_ready(self.version_policy_snapshot))
        object.__setattr__(
            self,
            "explanation",
            {str(atom_id): detail for atom_id, detail in self.explanation.items()},
        )
        computed = _stable_hash(self._hash_payload())
        if not self.content_hash:
            object.__setattr__(self, "content_hash", computed)
        elif str(self.content_hash) != computed:
            raise ValueError(
                "transition journal entry content_hash does not match payload"
            )

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
        operator_input: OperatorInput,
        version_policy_snapshot: Mapping[str, str],
        state_out: EpistemicState,
        explanation: Mapping[str, RevisionAtomDetail],
        policy_payload: PolicyProfile | None = None,
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
            operator_input=operator_input,
            version_policy_snapshot=dict(version_policy_snapshot),
            state_out=EpistemicSnapshot.from_state(journal_state_out),
            explanation=dict(explanation),
            policy=policy_payload,
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
    if (
        event.policy_snapshot == dict(version_policy_snapshot)
        and event.replay_status == "replayed"
    ):
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
    operator_input: OperatorInput
    expected_state_hash: str
    actual_state_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_index", int(self.entry_index))
        object.__setattr__(self, "operator", _journal_operator(self.operator))
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
            raise ValueError(
                f"unsupported transition journal version: {self.schema_version}"
            )
        object.__setattr__(self, "entries", tuple(self.entries))

    def check_chain_integrity(self) -> ChainIntegrityReport:
        errors: list[str] = []
        checked: list[str] = []
        previous_out: str | None = None
        for index, entry in enumerate(self.entries):
            checked.append(entry.content_hash)
            if previous_out is not None and previous_out != entry.state_in.content_hash:
                errors.append(
                    f"entry {index} state_in does not match previous state_out"
                )
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
                errors.append(
                    f"entry {index} replay failed for {entry.operator.value}: {exc}"
                )
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
    expected = {
        str(key): str(value) for key, value in entry.version_policy_snapshot.items()
    }
    if dict(event.policy_snapshot) != expected:
        return "policy snapshot mismatch between revision event and journal entry"
    return None
