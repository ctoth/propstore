"""Worldline compute forms: query inputs, revision query, and result.

These are the world-shaped compute types a worldline runner consumes and
produces. They live *above* the storage-pure charter
(:mod:`propstore.worldline.definition`) because they reference the canonical
``propstore.world`` / result / revision types directly. The charter persists
their dict serialization; the runner compiles these forms one-way from those
mappings at use time (``Environment.from_dict``, ``RenderPolicy.from_dict``,
``WorldlineRevisionQuery.from_dict``) — a boundary crossing that is a call, not a
conversion (CLAUDE.md substrate discipline point 3).

The pure helpers (``_optional_mapping``, ``_is_mapping``, ``_is_sequence``) and
the single canonical revision-target validator
(:func:`~propstore.worldline.definition._validated_revision_target`) live on the
charter module and are imported here so there is exactly one spelling of each.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from propstore.world.types import Environment
from propstore.worldline.definition import validated_revision_target
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
    coerce_worldline_step,
    coerce_worldline_target_value,
)
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    RevisionConflictSelection,
    WorldlineRevisionState,
)


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _is_sequence(value: object) -> TypeGuard[Sequence[Any]]:
    return isinstance(value, (tuple, list))


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not _is_mapping(value):
        raise ValueError(f"worldline field '{field_name}' must be a mapping")
    return value


@dataclass
class WorldlineInputs:
    """The input specification for a worldline query."""

    environment: Environment = field(default_factory=Environment)
    overrides: dict[str, float | str] = field(default_factory=dict[str, float | str])

    @classmethod
    def from_dict(cls, data: object) -> WorldlineInputs:
        if data is None:
            return cls()
        payload = _optional_mapping(data, "inputs")
        if not payload:
            return cls()
        return cls(
            environment=Environment.from_dict(payload),
            overrides=dict(_optional_mapping(payload.get("overrides"), "overrides")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = self.environment.to_dict()
        if self.overrides:
            data["overrides"] = dict(self.overrides)
        return data


@dataclass
class WorldlineRevisionQuery:
    operation: str = ""
    atom: RevisionAtomRef | None = None
    target: str | None = None
    conflicts: RevisionConflictSelection = field(default_factory=RevisionConflictSelection)
    operator: str | None = None
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: dict[str, Any] | None = None
    merge_parent_commits: tuple[str, ...] = ()
    max_alphabet_size: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> WorldlineRevisionQuery | None:
        if not data:
            return None
        max_alphabet_size = data.get("max_alphabet_size")
        return cls(
            operation=str(data.get("operation", "")),
            atom=RevisionAtomRef.from_mapping(data.get("atom")),
            target=validated_revision_target(str(data.get("operation", "")), data.get("target")),
            conflicts=RevisionConflictSelection.from_mapping(data.get("conflicts")),
            operator=data.get("merge_operator") or data.get("operator"),
            profile_atom_ids=_revision_profile_atom_ids(data.get("profile_atom_ids") or ()),
            integrity_constraint=(
                None
                if data.get("integrity_constraint") is None
                else dict(_optional_mapping(data.get("integrity_constraint"), "integrity_constraint"))
            ),
            merge_parent_commits=tuple(str(commit) for commit in (data.get("merge_parent_commits") or ())),
            max_alphabet_size=(
                None
                if max_alphabet_size is None
                else int(max_alphabet_size)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"operation": self.operation}
        if self.atom is not None:
            data["atom"] = self.atom.to_dict()
        if self.target is not None:
            data["target"] = self.target
        if self.conflicts.targets_by_atom_id:
            data["conflicts"] = self.conflicts.to_dict()
        if self.operator is not None:
            data["operator"] = self.operator
        if self.profile_atom_ids:
            data["profile_atom_ids"] = [list(profile) for profile in self.profile_atom_ids]
        if self.integrity_constraint is not None:
            data["integrity_constraint"] = dict(self.integrity_constraint)
        if self.merge_parent_commits:
            data["merge_parent_commits"] = list(self.merge_parent_commits)
        if self.max_alphabet_size is not None:
            data["max_alphabet_size"] = self.max_alphabet_size
        return data


def _revision_profile_atom_ids(value: object) -> tuple[tuple[str, ...], ...]:
    if not _is_sequence(value):
        raise ValueError("worldline revision profile_atom_ids must be a sequence")
    profiles: list[tuple[str, ...]] = []
    for profile in value:
        if not _is_sequence(profile):
            raise ValueError("worldline revision profile_atom_ids entries must be sequences")
        profiles.append(tuple(str(atom_id) for atom_id in profile))
    return tuple(profiles)


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
        self.values = {
            str(target_name): coerce_worldline_target_value(value)
            for target_name, value in self.values.items()
        }
        self.steps = tuple(coerce_worldline_step(step) for step in self.steps)

    @classmethod
    def from_dict(cls, data: object) -> WorldlineResult | None:
        if data is None:
            return None
        payload = _optional_mapping(data, "results")
        if not payload:
            return None
        raw_values = _optional_mapping(payload.get("values"), "values")
        values: dict[str, WorldlineTargetValue] = {}
        for target_name, value in raw_values.items():
            if not _is_mapping(value):
                raise ValueError(f"worldline field 'values.{target_name}' must be a mapping")
            values[str(target_name)] = WorldlineTargetValue.from_mapping(value)
        return cls(
            computed=payload.get("computed", ""),
            content_hash=payload.get("content_hash", ""),
            values=values,
            steps=tuple(
                WorldlineStep.from_mapping(step)
                for step in (payload.get("steps") or ())
                if _is_mapping(step)
            ),
            dependencies=WorldlineDependencies.from_mapping(payload.get("dependencies")),
            sensitivity=WorldlineSensitivityReport.from_mapping(payload.get("sensitivity")),
            argumentation=WorldlineArgumentationState.from_mapping(payload.get("argumentation")),
            revision=WorldlineRevisionState.from_mapping(payload.get("revision")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "computed": self.computed,
            "content_hash": self.content_hash,
            "values": {
                target_name: target_value.to_dict()
                for target_name, target_value in self.values.items()
            },
            "steps": [step.to_dict() for step in self.steps],
            "dependencies": self.dependencies.to_dict(),
        }
        if self.sensitivity is not None:
            data["sensitivity"] = self.sensitivity.to_dict()
        if self.argumentation is not None:
            data["argumentation"] = self.argumentation.to_dict()
        if self.revision is not None:
            data["revision"] = self.revision.to_dict()
        return data
