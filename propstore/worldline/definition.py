"""Worldline definitions and materialized results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

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
)


@dataclass
class WorldlineInputs:
    """The input specification for a worldline query."""

    environment: Environment = field(default_factory=Environment)
    overrides: dict[str, float | str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineInputs:
        if not data:
            return cls()
        return cls(
            environment=Environment.from_dict(data),
            overrides=dict(data.get("overrides") or {}),
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

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineRevisionQuery | None:
        if not data:
            return None
        return cls(
            operation=str(data.get("operation", "")),
            atom=RevisionAtomRef.from_mapping(data.get("atom")),
            target=data.get("target"),
            conflicts=RevisionConflictSelection.from_mapping(data.get("conflicts")),
            operator=data.get("operator"),
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
    revision: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.values = {
            str(target_name): coerce_worldline_target_value(value)
            for target_name, value in self.values.items()
        }
        self.steps = tuple(coerce_worldline_step(step) for step in self.steps)
        if not isinstance(self.dependencies, WorldlineDependencies):
            self.dependencies = WorldlineDependencies.from_mapping(self.dependencies)
        if self.sensitivity is not None and not isinstance(self.sensitivity, WorldlineSensitivityReport):
            self.sensitivity = WorldlineSensitivityReport.from_mapping(self.sensitivity)
        if self.argumentation is not None and not isinstance(self.argumentation, WorldlineArgumentationState):
            self.argumentation = WorldlineArgumentationState.from_mapping(self.argumentation)

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineResult | None:
        if not data:
            return None
        return cls(
            computed=data.get("computed", ""),
            content_hash=data.get("content_hash", ""),
            values={
                str(target_name): WorldlineTargetValue.from_mapping(value)
                for target_name, value in (data.get("values") or {}).items()
                if isinstance(value, dict)
            },
            steps=tuple(
                WorldlineStep.from_mapping(step)
                for step in (data.get("steps") or ())
                if isinstance(step, dict)
            ),
            dependencies=WorldlineDependencies.from_mapping(data.get("dependencies")),
            sensitivity=WorldlineSensitivityReport.from_mapping(data.get("sensitivity")),
            argumentation=WorldlineArgumentationState.from_mapping(data.get("argumentation")),
            revision=data.get("revision"),
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
            data["revision"] = self.revision
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
    results: WorldlineResult | None = None

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

    @classmethod
    def from_file(cls, path: Path) -> WorldlineDefinition:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Worldline file {path} is not a YAML mapping")
        return cls.from_dict(data)

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

    def to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            yaml.dump(
                self.to_dict(),
                handle,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def is_stale(self, world: Any) -> bool:
        if self.results is None:
            return False

        stored_hash = self.results.content_hash
        if not stored_hash:
            return True

        from propstore.worldline.runner import run_worldline

        current_results = run_worldline(self, world)
        return current_results.content_hash != stored_hash
