"""Application-layer epistemic observatory workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from propstore.observatory import (
    EvaluationScenario,
    ObservatoryReport,
    evaluate_scenarios,
)
from propstore.repository import Repository


@dataclass(frozen=True)
class AppObservatoryRunRequest:
    scenarios: tuple[EvaluationScenario, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenarios", tuple(self.scenarios))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AppObservatoryRunRequest:
        raw_scenarios = data.get("scenarios")
        if not isinstance(raw_scenarios, tuple | list):
            raise ValueError("observatory request field 'scenarios' must be a sequence")
        return cls(
            scenarios=tuple(
                EvaluationScenario.from_dict(_mapping(item, "scenario"))
                for item in raw_scenarios
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }


def run_observatory(
    repo: Repository,
    request: AppObservatoryRunRequest,
) -> ObservatoryReport:
    _ = repo
    return evaluate_scenarios(request.scenarios)


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"observatory request field '{field_name}' must be a mapping")
    return value


__all__ = [
    "AppObservatoryRunRequest",
    "run_observatory",
]
