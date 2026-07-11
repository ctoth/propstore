"""Deterministic observatory reports for epistemic workflow behavior."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import msgspec
from quire.canonical import canonical_json_bytes


_TRACE_VERSION = "propstore.semantic_trace.v2"
_SCENARIO_VERSION = "propstore.evaluation_scenario.v2"
_RESULT_VERSION = "propstore.evaluation_result.v2"
_SUMMARY_VERSION = "propstore.operator_summary.v2"
_REPORT_VERSION = "propstore.observatory_report.v2"


class SemanticTraceRecord(
    msgspec.Struct, kw_only=True, frozen=True, forbid_unknown_fields=True
):
    source_artifact_id: str
    assertion_id: str
    projection_id: str
    state_hash: str
    journal_entry_hash: str
    schema_version: str = _TRACE_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _TRACE_VERSION:
            raise ValueError(
                f"unsupported semantic trace version: {self.schema_version}"
            )

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self)).hexdigest()


class EvaluationScenario(
    msgspec.Struct, kw_only=True, frozen=True, forbid_unknown_fields=True
):
    scenario_id: str
    operator_family: str
    policy_id: str
    replay_result_hash: str
    falsification_ids: tuple[str, ...] = ()
    trace_records: tuple[SemanticTraceRecord, ...] = ()
    schema_version: str = _SCENARIO_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCENARIO_VERSION:
            raise ValueError(
                f"unsupported evaluation scenario version: {self.schema_version}"
            )
        object.__setattr__(
            self, "falsification_ids", tuple(sorted(self.falsification_ids))
        )
        object.__setattr__(
            self,
            "trace_records",
            tuple(sorted(self.trace_records, key=lambda item: item.content_hash)),
        )

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self)).hexdigest()


class ScenarioEvaluation(
    msgspec.Struct, kw_only=True, frozen=True, forbid_unknown_fields=True
):
    scenario_id: str
    operator_family: str
    policy_id: str
    replay_result_hash: str
    falsification_ids: tuple[str, ...]
    trace_records: tuple[SemanticTraceRecord, ...] = ()
    schema_version: str = _RESULT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _RESULT_VERSION:
            raise ValueError(
                f"unsupported scenario evaluation version: {self.schema_version}"
            )
        object.__setattr__(
            self, "falsification_ids", tuple(sorted(self.falsification_ids))
        )
        object.__setattr__(
            self,
            "trace_records",
            tuple(sorted(self.trace_records, key=lambda item: item.content_hash)),
        )

    @classmethod
    def from_scenario(cls, scenario: EvaluationScenario) -> ScenarioEvaluation:
        return cls(
            scenario_id=scenario.scenario_id,
            operator_family=scenario.operator_family,
            policy_id=scenario.policy_id,
            replay_result_hash=scenario.replay_result_hash,
            falsification_ids=scenario.falsification_ids,
            trace_records=scenario.trace_records,
        )

    @property
    def passed(self) -> bool:
        return not self.falsification_ids

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self)).hexdigest()


class OperatorFamilySummary(
    msgspec.Struct, kw_only=True, frozen=True, forbid_unknown_fields=True
):
    operator_family: str
    scenario_count: int
    falsification_count: int
    replay_result_hashes: tuple[str, ...]
    schema_version: str = _SUMMARY_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SUMMARY_VERSION:
            raise ValueError(
                f"unsupported operator summary version: {self.schema_version}"
            )
        object.__setattr__(
            self, "replay_result_hashes", tuple(sorted(self.replay_result_hashes))
        )

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self)).hexdigest()


class ObservatoryReport(
    msgspec.Struct, kw_only=True, frozen=True, forbid_unknown_fields=True
):
    scenario_results: tuple[ScenarioEvaluation, ...]
    operator_summaries: tuple[OperatorFamilySummary, ...]
    schema_version: str = _REPORT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _REPORT_VERSION:
            raise ValueError(
                f"unsupported observatory report version: {self.schema_version}"
            )
        object.__setattr__(
            self,
            "scenario_results",
            tuple(sorted(self.scenario_results, key=lambda item: item.scenario_id)),
        )
        object.__setattr__(
            self,
            "operator_summaries",
            tuple(
                sorted(self.operator_summaries, key=lambda item: item.operator_family)
            ),
        )

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self)).hexdigest()


def evaluate_scenarios(scenarios: Iterable[EvaluationScenario]) -> ObservatoryReport:
    results = tuple(
        ScenarioEvaluation.from_scenario(scenario)
        for scenario in sorted(scenarios, key=lambda item: item.scenario_id)
    )
    grouped: dict[str, list[ScenarioEvaluation]] = {}
    for result in results:
        grouped.setdefault(result.operator_family, []).append(result)
    summaries = tuple(
        OperatorFamilySummary(
            operator_family=operator_family,
            scenario_count=len(items),
            falsification_count=sum(len(item.falsification_ids) for item in items),
            replay_result_hashes=tuple(item.replay_result_hash for item in items),
        )
        for operator_family, items in grouped.items()
    )
    return ObservatoryReport(
        scenario_results=results,
        operator_summaries=summaries,
    )


__all__ = [
    "EvaluationScenario",
    "ObservatoryReport",
    "OperatorFamilySummary",
    "ScenarioEvaluation",
    "SemanticTraceRecord",
    "evaluate_scenarios",
]
