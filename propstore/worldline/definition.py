"""Worldline definitions and materialized results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from propstore.families.worldlines.declaration import (
    WorldlineDefinitionDocument,
    WorldlineInputsDocument,
    WorldlineRevisionQueryDocument,
    WorldlineResultDocument,
)
from quire.documents import convert_document_value
from propstore.support_revision.history import TransitionJournal
from propstore.world.types import Environment, RenderPolicy
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
)
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    RevisionConflictSelection,
    WorldlineRevisionState,
)

if TYPE_CHECKING:
    from propstore.worldline.interfaces import WorldlineStore


def _required_document_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"worldline field '{field_name}' must be a mapping")
    return value


class WorldlineRevisionTargetValidationError(ValueError):
    """Raised when a revision target cannot be resolved as an atom id."""


def _validated_revision_target(operation: str, target: object) -> str | None:
    if target is None:
        return None
    target_id = str(target)
    if operation == "contract" and not (
        target_id.startswith("ps:assertion:") or target_id.startswith("assumption:")
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
    overrides: dict[str, float | str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> WorldlineInputs:
        if data is None:
            return cls()
        return cls.from_document(
            convert_document_value(
                data,
                WorldlineInputsDocument,
                source="worldline:inputs",
            )
        )

    def to_dict(self) -> dict[str, object]:
        data = self.environment.to_dict()
        if self.overrides:
            data["overrides"] = dict(self.overrides)
        return data


@dataclass
class WorldlineRevisionQuery:
    operation: str = ""
    atom: RevisionAtomRef | None = None
    target: str | None = None
    conflicts: RevisionConflictSelection = field(
        default_factory=RevisionConflictSelection
    )
    operator: str | None = None
    merge_operator: str | None = None
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: Mapping[str, object] | None = None
    merge_parent_commits: tuple[str, ...] = ()
    max_alphabet_size: int | None = None

    @classmethod
    def from_dict(cls, data: object) -> WorldlineRevisionQuery | None:
        if data is None:
            return None
        if isinstance(data, Mapping) and not data:
            return None
        return cls.from_document(
            convert_document_value(
                data,
                WorldlineRevisionQueryDocument,
                source="worldline:revision",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"operation": self.operation}
        if self.atom is not None:
            data["atom"] = self.atom.to_dict()
        if self.target is not None:
            data["target"] = self.target
        if self.conflicts.targets_by_atom_id:
            data["conflicts"] = self.conflicts.to_dict()
        if self.operator is not None:
            data["operator"] = self.operator
        if self.merge_operator is not None:
            data["merge_operator"] = self.merge_operator
        if self.profile_atom_ids:
            data["profile_atom_ids"] = [
                list(profile) for profile in self.profile_atom_ids
            ]
        if self.integrity_constraint is not None:
            data["integrity_constraint"] = dict(self.integrity_constraint)
        if self.merge_parent_commits:
            data["merge_parent_commits"] = list(self.merge_parent_commits)
        if self.max_alphabet_size is not None:
            data["max_alphabet_size"] = self.max_alphabet_size
        return data


@dataclass
class WorldlineResult:
    """The materialized results of a worldline query."""

    computed: str = ""
    content_hash: str = ""
    values: dict[str, WorldlineTargetValue] = field(default_factory=dict)
    steps: tuple[WorldlineStep, ...] = ()
    dependencies: WorldlineDependencies = field(default_factory=WorldlineDependencies)
    sensitivity: WorldlineSensitivityReport | None = None
    argumentation: WorldlineArgumentationState | None = None
    revision: WorldlineRevisionState | None = None

    def __post_init__(self) -> None:
        values: dict[str, WorldlineTargetValue] = {}
        for target_name, value in self.values.items():
            if not isinstance(value, WorldlineTargetValue):
                raise TypeError(
                    "WorldlineResult.values entries must be WorldlineTargetValue"
                )
            values[str(target_name)] = value
        self.values = values
        steps: list[WorldlineStep] = []
        for step in self.steps:
            if not isinstance(step, WorldlineStep):
                raise TypeError("WorldlineResult.steps entries must be WorldlineStep")
            steps.append(step)
        self.steps = tuple(steps)
        if not isinstance(self.dependencies, WorldlineDependencies):
            raise TypeError(
                "WorldlineResult.dependencies must be WorldlineDependencies"
            )
        if self.sensitivity is not None and not isinstance(
            self.sensitivity, WorldlineSensitivityReport
        ):
            raise TypeError(
                "WorldlineResult.sensitivity must be WorldlineSensitivityReport or None"
            )
        if self.argumentation is not None and not isinstance(
            self.argumentation, WorldlineArgumentationState
        ):
            raise TypeError(
                "WorldlineResult.argumentation must be WorldlineArgumentationState or None"
            )
        if self.revision is not None and not isinstance(
            self.revision, WorldlineRevisionState
        ):
            raise TypeError(
                "WorldlineResult.revision must be WorldlineRevisionState or None"
            )

    @classmethod
    def from_dict(cls, data: object) -> WorldlineResult | None:
        if data is None:
            return None
        if isinstance(data, Mapping) and not data:
            return None
        return cls.from_document(
            convert_document_value(
                data,
                WorldlineResultDocument,
                source="worldline:results",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
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
    targets: list[str] = field(default_factory=list)
    revision: WorldlineRevisionQuery | None = None
    journal: TransitionJournal | None = None
    results: WorldlineResult | None = None

    @classmethod
    def from_dict(cls, data: object) -> WorldlineDefinition:
        return cls.from_document(
            convert_document_value(
                data,
                WorldlineDefinitionDocument,
                source="worldline:definition",
            )
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"id": self.id}
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
        if self.journal is not None:
            data["journal"] = self.journal.to_dict()
        if self.results is not None:
            data["results"] = self.results.to_dict()
        return data

    def is_stale(self, world: WorldlineStore) -> bool:
        if self.results is None:
            return False

        stored_hash = self.results.content_hash
        if not stored_hash:
            return True

        from propstore.worldline.runner import run_worldline

        current_results = run_worldline(self, world)
        return current_results.content_hash != stored_hash
