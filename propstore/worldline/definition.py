"""Worldline definitions and materialized results."""

from __future__ import annotations

from dataclasses import dataclass, field

from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
)
from propstore.worldline.revision_types import WorldlineRevisionState


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
