"""Worldline definitions and materialized results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from propstore.world.types import Environment, RenderPolicy


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
    atom: dict[str, Any] | None = None
    target: str | None = None
    conflicts: dict[str, list[str]] = field(default_factory=dict)
    operator: str | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineRevisionQuery | None:
        if not data:
            return None
        raw_conflicts = data.get("conflicts") or {}
        return cls(
            operation=str(data.get("operation", "")),
            atom=dict(data.get("atom") or {}) or None,
            target=data.get("target"),
            conflicts={
                str(atom_id): [str(target_id) for target_id in targets]
                for atom_id, targets in raw_conflicts.items()
            },
            operator=data.get("operator"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"operation": self.operation}
        if self.atom is not None:
            data["atom"] = dict(self.atom)
        if self.target is not None:
            data["target"] = self.target
        if self.conflicts:
            data["conflicts"] = {
                atom_id: list(targets)
                for atom_id, targets in self.conflicts.items()
            }
        if self.operator is not None:
            data["operator"] = self.operator
        return data


@dataclass
class WorldlineResult:
    """The materialized results of a worldline query."""

    computed: str = ""
    content_hash: str = ""
    values: dict[str, dict[str, Any]] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=lambda: {
        "claims": [],
        "stances": [],
        "contexts": [],
    })
    sensitivity: dict[str, Any] | None = None
    argumentation: dict[str, Any] | None = None
    revision: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineResult | None:
        if not data:
            return None
        return cls(
            computed=data.get("computed", ""),
            content_hash=data.get("content_hash", ""),
            values=dict(data.get("values") or {}),
            steps=list(data.get("steps") or []),
            dependencies=data.get("dependencies") or {
                "claims": [],
                "stances": [],
                "contexts": [],
            },
            sensitivity=data.get("sensitivity"),
            argumentation=data.get("argumentation"),
            revision=data.get("revision"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "computed": self.computed,
            "content_hash": self.content_hash,
            "values": self.values,
            "steps": self.steps,
            "dependencies": self.dependencies,
        }
        if self.sensitivity is not None:
            data["sensitivity"] = self.sensitivity
        if self.argumentation is not None:
            data["argumentation"] = self.argumentation
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
