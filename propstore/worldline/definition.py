"""Worldline definitions and materialized results.

The document-codec (``from_document``/``to_document``) and ``journal`` paths
live with the concrete repository/document surfaces (Phase 8/9); this module
carries the mapping-based (``from_dict``/``to_dict``) shapes the in-memory
materialization runner uses. The revision *capture* (``WorldlineRevisionState``
population, transition journal) lands in Phase 7b.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeGuard

from propstore.world.types import Environment, RenderPolicy
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


class WorldlineRevisionTargetValidationError(ValueError):
    """Raised when a revision target cannot be resolved as an atom id."""


def _validated_revision_target(operation: str, target: object) -> str | None:
    if target is None:
        return None
    target_id = str(target)
    if operation == "contract" and not (
        target_id.startswith("ps:assertion:")
        or target_id.startswith("assumption:")
    ):
        raise WorldlineRevisionTargetValidationError(
            "Worldline revision target must be an assertion or assumption atom id: "
            f"{target_id}"
        )
    return target_id


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
    integrity_constraint: Mapping[str, Any] | None = None
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
            target=_validated_revision_target(str(data.get("operation", "")), data.get("target")),
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


@dataclass
class WorldlineDefinition:
    """A worldline: question + optional answer."""

    id: str
    name: str = ""
    created: str = ""
    inputs: WorldlineInputs = field(default_factory=WorldlineInputs)
    policy: RenderPolicy = field(default_factory=RenderPolicy)
    targets: list[str] = field(default_factory=list[str])
    revision: WorldlineRevisionQuery | None = None
    results: WorldlineResult | None = None
    # 7b seam: the transition ``journal`` field (support_revision.history) attaches
    # with revision capture in Phase 7b.

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorldlineDefinition:
        if "id" not in data:
            raise ValueError("Worldline definition requires 'id'")
        targets = data.get("targets")
        if not targets:
            raise ValueError("Worldline definition requires 'targets'")

        return cls(
            id=data["id"],
            name=data.get("name", ""),
            created=data.get("created", ""),
            inputs=WorldlineInputs.from_dict(data.get("inputs")),
            policy=RenderPolicy.from_dict(data.get("policy")),
            targets=list(targets),
            revision=WorldlineRevisionQuery.from_dict(data.get("revision")),
            results=WorldlineResult.from_dict(data.get("results")),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id}
        if self.name:
            data["name"] = self.name
        if self.created:
            data["created"] = self.created

        inputs = self.inputs.to_dict()
        if inputs:
            data["inputs"] = inputs

        policy = self.policy.to_dict()
        if policy:
            data["policy"] = policy

        data["targets"] = list(self.targets)

        if self.revision is not None:
            data["revision"] = self.revision.to_dict()
        if self.results is not None:
            data["results"] = self.results.to_dict()
        return data

    def is_stale(self, world: Any) -> bool:
        if self.results is None:
            return False

        stored_hash = self.results.content_hash
        if not stored_hash:
            return True

        from propstore.worldline.runner import run_worldline

        current_results = run_worldline(self, world)
        return current_results.content_hash != stored_hash
