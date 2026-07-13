"""Typed worldline revision-query and revision-result shapes (data only).

A captured :class:`WorldlineRevisionState` carries the ``support_revision``
``RevisionEvent`` materialized by ``worldline/revision_capture.py``, the
``EpistemicSnapshot`` the revision landed on, and the ``RevisionExplanation``
that justifies it — all as their own canonical package types. They were
previously typed ``Any`` and lowered through hand-written ``to_dict`` hops; the
charter now stores them typed and Quire's codec owns the encoding.

This module is **storage-pure**: it imports only ``propstore.core`` and
``propstore.support_revision`` (both of which are themselves world-free), so the
worldline charter can reach it without breaking the layering contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from condition_ir import to_cel_expr

from propstore.core.environment import AssumptionRef
from propstore.core.id_types import to_assumption_id
from propstore.support_revision.explanation_types import RevisionExplanation
from propstore.support_revision.history import EpistemicSnapshot
from propstore.support_revision.state import AssumptionAtom, RevisionEvent
from propstore.worldline.result_types import WorldlineCaptureError


@dataclass(frozen=True)
class RevisionAtomRef:
    kind: str = "assertion"
    assertion_id: str | None = None
    assumption_id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None

    def to_belief_atom_input(self) -> str | AssumptionAtom:
        """Resolve this ref to a typed revision input — no dict hop.

        Assertion refs resolve to the atom id string (the atom must already
        exist in the belief base); assumption refs construct the typed
        :class:`AssumptionAtom` directly.
        """
        if self.kind == "assertion":
            atom_id = self.atom_id or self.assertion_id
            if atom_id is None:
                raise ValueError("Assertion revision atom requires an assertion_id")
            return str(atom_id)
        if self.kind == "assumption":
            if self.assumption_id is None:
                raise ValueError("Assumption revision atom requires an assumption_id")
            return AssumptionAtom(
                atom_id=str(self.atom_id or f"assumption:{self.assumption_id}"),
                assumption=AssumptionRef(
                    assumption_id=to_assumption_id(self.assumption_id),
                    cel=to_cel_expr(""),
                    kind="",
                    source="",
                ),
            )
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
    targets_by_atom_id: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict[str, tuple[str, ...]]
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "targets_by_atom_id",
            {
                str(atom_id): tuple(str(target_id) for target_id in target_ids)
                for atom_id, target_ids in self.targets_by_atom_id.items()
            },
        )

    def targets_for(self, atom_id: str) -> tuple[str, ...]:
        return self.targets_by_atom_id.get(atom_id, ())


@dataclass(frozen=True)
class WorldlineRevisionResult:
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: RevisionExplanation | None = None

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
            self,
            "incision_set",
            tuple(str(atom_id) for atom_id in self.incision_set),
        )


@dataclass(frozen=True)
class WorldlineRevisionState:
    operation: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    result: WorldlineRevisionResult | None = None
    state: EpistemicSnapshot | None = None
    status: str | None = None
    error: WorldlineCaptureError | None = None
    event: RevisionEvent | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "target_atom_ids",
            tuple(str(atom_id) for atom_id in self.target_atom_ids),
        )


__all__ = [
    "RevisionAtomRef",
    "RevisionConflictSelection",
    "WorldlineRevisionResult",
    "WorldlineRevisionState",
]
