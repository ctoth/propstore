"""Deterministic observatory reports for epistemic workflow behavior."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


_TRACE_VERSION = "propstore.semantic_trace.v1"
_SCENARIO_VERSION = "propstore.evaluation_scenario.v1"
_RESULT_VERSION = "propstore.evaluation_result.v1"
_SUMMARY_VERSION = "propstore.operator_summary.v1"
_REPORT_VERSION = "propstore.observatory_report.v1"


def _plain(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _plain(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"observatory field '{field_name}' must be a mapping")
    return value


def _sequence(value: object, field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, tuple | list):
        raise ValueError(f"observatory field '{field_name}' must be a sequence")
    return tuple(value)


def _strings(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(str(value) for value in values)


@dataclass(frozen=True)
class SemanticTraceRecord:
    source_artifact_id: str
    assertion_id: str
    projection_id: str
    state_hash: str
    journal_entry_hash: str
    schema_version: str = _TRACE_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _TRACE_VERSION:
            raise ValueError(f"unsupported semantic trace version: {self.schema_version}")
        object.__setattr__(self, "source_artifact_id", str(self.source_artifact_id))
        object.__setattr__(self, "assertion_id", str(self.assertion_id))
        object.__setattr__(self, "projection_id", str(self.projection_id))
        object.__setattr__(self, "state_hash", str(self.state_hash))
        object.__setattr__(self, "journal_entry_hash", str(self.journal_entry_hash))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SemanticTraceRecord:
        record = cls(
            source_artifact_id=str(data.get("source_artifact_id") or ""),
            assertion_id=str(data.get("assertion_id") or ""),
            projection_id=str(data.get("projection_id") or ""),
            state_hash=str(data.get("state_hash") or ""),
            journal_entry_hash=str(data.get("journal_entry_hash") or ""),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_hash(data, record.content_hash, "semantic trace")
        return record

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_artifact_id": self.source_artifact_id,
            "assertion_id": self.assertion_id,
            "projection_id": self.projection_id,
            "state_hash": self.state_hash,
            "journal_entry_hash": self.journal_entry_hash,
        }


@dataclass(frozen=True)
class EvaluationScenario:
    scenario_id: str
    operator_family: str
    policy_id: str
    replay_result_hash: str
    falsification_ids: tuple[str, ...] = ()
    trace_records: tuple[SemanticTraceRecord, ...] = ()
    schema_version: str = _SCENARIO_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCENARIO_VERSION:
            raise ValueError(f"unsupported evaluation scenario version: {self.schema_version}")
        object.__setattr__(self, "scenario_id", str(self.scenario_id))
        object.__setattr__(self, "operator_family", str(self.operator_family))
        object.__setattr__(self, "policy_id", str(self.policy_id))
        object.__setattr__(self, "replay_result_hash", str(self.replay_result_hash))
        object.__setattr__(self, "falsification_ids", tuple(sorted(_strings(self.falsification_ids))))
        object.__setattr__(self, "trace_records", tuple(sorted(self.trace_records, key=lambda item: item.content_hash)))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationScenario:
        scenario = cls(
            scenario_id=str(data.get("scenario_id") or ""),
            operator_family=str(data.get("operator_family") or ""),
            policy_id=str(data.get("policy_id") or ""),
            replay_result_hash=str(data.get("replay_result_hash") or ""),
            falsification_ids=_strings(_sequence(data.get("falsification_ids") or (), "falsification_ids")),
            trace_records=tuple(
                SemanticTraceRecord.from_dict(_mapping(item, "trace_record"))
                for item in _sequence(data.get("trace_records") or (), "trace_records")
            ),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_hash(data, scenario.content_hash, "evaluation scenario")
        return scenario

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scenario_id": self.scenario_id,
            "operator_family": self.operator_family,
            "policy_id": self.policy_id,
            "replay_result_hash": self.replay_result_hash,
            "falsification_ids": list(self.falsification_ids),
            "trace_records": [record.to_dict() for record in self.trace_records],
        }


@dataclass(frozen=True)
class ScenarioEvaluation:
    scenario_id: str
    operator_family: str
    policy_id: str
    replay_result_hash: str
    falsification_ids: tuple[str, ...]
    trace_records: tuple[SemanticTraceRecord, ...] = ()
    schema_version: str = _RESULT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _RESULT_VERSION:
            raise ValueError(f"unsupported scenario evaluation version: {self.schema_version}")
        object.__setattr__(self, "scenario_id", str(self.scenario_id))
        object.__setattr__(self, "operator_family", str(self.operator_family))
        object.__setattr__(self, "policy_id", str(self.policy_id))
        object.__setattr__(self, "replay_result_hash", str(self.replay_result_hash))
        object.__setattr__(self, "falsification_ids", tuple(sorted(_strings(self.falsification_ids))))
        object.__setattr__(self, "trace_records", tuple(sorted(self.trace_records, key=lambda item: item.content_hash)))

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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ScenarioEvaluation:
        evaluation = cls(
            scenario_id=str(data.get("scenario_id") or ""),
            operator_family=str(data.get("operator_family") or ""),
            policy_id=str(data.get("policy_id") or ""),
            replay_result_hash=str(data.get("replay_result_hash") or ""),
            falsification_ids=_strings(_sequence(data.get("falsification_ids") or (), "falsification_ids")),
            trace_records=tuple(
                SemanticTraceRecord.from_dict(_mapping(item, "trace_record"))
                for item in _sequence(data.get("trace_records") or (), "trace_records")
            ),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_hash(data, evaluation.content_hash, "scenario evaluation")
        return evaluation

    @property
    def passed(self) -> bool:
        return not self.falsification_ids

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scenario_id": self.scenario_id,
            "operator_family": self.operator_family,
            "policy_id": self.policy_id,
            "replay_result_hash": self.replay_result_hash,
            "falsification_ids": list(self.falsification_ids),
            "passed": self.passed,
            "trace_records": [record.to_dict() for record in self.trace_records],
        }


@dataclass(frozen=True)
class OperatorFamilySummary:
    operator_family: str
    scenario_count: int
    falsification_count: int
    replay_result_hashes: tuple[str, ...]
    schema_version: str = _SUMMARY_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SUMMARY_VERSION:
            raise ValueError(f"unsupported operator summary version: {self.schema_version}")
        object.__setattr__(self, "operator_family", str(self.operator_family))
        object.__setattr__(self, "scenario_count", int(self.scenario_count))
        object.__setattr__(self, "falsification_count", int(self.falsification_count))
        object.__setattr__(self, "replay_result_hashes", tuple(sorted(_strings(self.replay_result_hashes))))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OperatorFamilySummary:
        summary = cls(
            operator_family=str(data.get("operator_family") or ""),
            scenario_count=int(data.get("scenario_count") or 0),
            falsification_count=int(data.get("falsification_count") or 0),
            replay_result_hashes=_strings(_sequence(data.get("replay_result_hashes") or (), "replay_result_hashes")),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_hash(data, summary.content_hash, "operator summary")
        return summary

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operator_family": self.operator_family,
            "scenario_count": self.scenario_count,
            "falsification_count": self.falsification_count,
            "replay_result_hashes": list(self.replay_result_hashes),
        }


@dataclass(frozen=True)
class ObservatoryReport:
    scenario_results: tuple[ScenarioEvaluation, ...]
    operator_summaries: Mapping[str, OperatorFamilySummary]
    schema_version: str = _REPORT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _REPORT_VERSION:
            raise ValueError(f"unsupported observatory report version: {self.schema_version}")
        results = tuple(sorted(self.scenario_results, key=lambda item: item.scenario_id))
        object.__setattr__(self, "scenario_results", results)
        object.__setattr__(
            self,
            "operator_summaries",
            {
                str(key): self.operator_summaries[key]
                for key in sorted(self.operator_summaries)
            },
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ObservatoryReport:
        report = cls(
            scenario_results=tuple(
                ScenarioEvaluation.from_dict(_mapping(item, "scenario_result"))
                for item in _sequence(data.get("scenario_results") or (), "scenario_results")
            ),
            operator_summaries={
                str(item.get("operator_family") or ""): OperatorFamilySummary.from_dict(item)
                for item in (
                    _mapping(raw, "operator_summary")
                    for raw in _sequence(data.get("operator_summaries") or (), "operator_summaries")
                )
            },
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_hash(data, report.content_hash, "observatory report")
        return report

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["content_hash"] = self.content_hash
        return data

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scenario_results": [result.to_dict() for result in self.scenario_results],
            "operator_summaries": [
                summary.to_dict()
                for _, summary in sorted(self.operator_summaries.items())
            ],
        }


def evaluate_scenarios(scenarios: Iterable[EvaluationScenario]) -> ObservatoryReport:
    results = tuple(
        ScenarioEvaluation.from_scenario(scenario)
        for scenario in sorted(scenarios, key=lambda item: item.scenario_id)
    )
    grouped: dict[str, list[ScenarioEvaluation]] = {}
    for result in results:
        grouped.setdefault(result.operator_family, []).append(result)
    summaries = {
        operator_family: OperatorFamilySummary(
            operator_family=operator_family,
            scenario_count=len(items),
            falsification_count=sum(len(item.falsification_ids) for item in items),
            replay_result_hashes=tuple(item.replay_result_hash for item in items),
        )
        for operator_family, items in grouped.items()
    }
    return ObservatoryReport(
        scenario_results=results,
        operator_summaries=summaries,
    )


def _check_hash(data: Mapping[str, Any], expected_hash: str, label: str) -> None:
    recorded_hash = data.get("content_hash")
    if recorded_hash is not None and str(recorded_hash) != expected_hash:
        raise ValueError(f"{label} content_hash does not match payload")


__all__ = [
    "EvaluationScenario",
    "ObservatoryReport",
    "OperatorFamilySummary",
    "ScenarioEvaluation",
    "SemanticTraceRecord",
    "evaluate_scenarios",
]
