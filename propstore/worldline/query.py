"""Worldline compute forms: the revision query and the materialized result.

These are the two typed documents the ``worldlines`` charter persists directly
(``WorldlineDefinition.revision`` and ``.results``). Quire's charter codec owns
their encoding and decoding, so there is no ``from_dict``/``to_dict`` pair here:
crossing the storage boundary is a call, not a conversion (CLAUDE.md substrate
discipline point 3).

The module is **storage-pure** — it reaches only ``propstore.core`` and the
sibling worldline payload modules — which is what lets the charter, read by the
storage layer, declare these as typed fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from propstore.support_revision.integrity_constraints import IntegrityConstraintSpec
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
    validated_revision_target,
)
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    RevisionConflictSelection,
    WorldlineRevisionState,
)


@dataclass
class WorldlineRevisionQuery:
    """The revision a worldline asks for, if any."""

    operation: str = ""
    atom: RevisionAtomRef | None = None
    target: str | None = None
    conflicts: RevisionConflictSelection = field(
        default_factory=RevisionConflictSelection
    )
    operator: str | None = None
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: IntegrityConstraintSpec | None = None
    merge_parent_commits: tuple[str, ...] = ()
    max_alphabet_size: int | None = None

    def __post_init__(self) -> None:
        self.target = validated_revision_target(self.operation, self.target)
        self.profile_atom_ids = tuple(
            tuple(str(atom_id) for atom_id in profile)
            for profile in self.profile_atom_ids
        )
        self.merge_parent_commits = tuple(
            str(commit) for commit in self.merge_parent_commits
        )


@dataclass
class WorldlineResult:
    """The materialized results of a worldline query."""

    computed: str = ""
    content_hash: str = ""
    values: dict[str, WorldlineTargetValue] = field(
        default_factory=dict[str, WorldlineTargetValue]
    )
    steps: tuple[WorldlineStep, ...] = ()
    dependencies: WorldlineDependencies = field(default_factory=WorldlineDependencies)
    sensitivity: WorldlineSensitivityReport | None = None
    argumentation: WorldlineArgumentationState | None = None
    revision: WorldlineRevisionState | None = None

    def __post_init__(self) -> None:
        self.steps = tuple(self.steps)


__all__ = ["WorldlineResult", "WorldlineRevisionQuery"]
