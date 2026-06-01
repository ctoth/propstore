"""Owner-layer process records for executable epistemic workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any


from propstore.fragility import FragilityReport, FragilityRequest, query_fragility
from propstore.policies import PolicyProfile
from propstore.support_revision.history import (
    EpistemicSnapshot,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.world.types import (
    ATMSConceptInterventionPlan,
    ATMSNodeInterventionPlan,
)

if TYPE_CHECKING:
    from propstore.world.model import WorldQuery


_INVESTIGATION_PLAN_VERSION = "propstore.investigation_plan.v1"
_INTERVENTION_PLAN_VERSION = "propstore.intervention_plan.v1"
_PROCESS_JOB_VERSION = "propstore.process_job.v1"
_PROCESS_MANAGER_VERSION = "propstore.process_manager.v1"
_COMPLETION_VERSION = "propstore.process_completion.v1"


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


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"epistemic process field '{field_name}' must be a mapping")
    return value


def _sequence(value: object, field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, tuple | list):
        raise ValueError(f"epistemic process field '{field_name}' must be a sequence")
    return tuple(value)


def _strings(value: Sequence[object]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)


class JobKind(StrEnum):
    INVESTIGATION = "investigation"
    INTERVENTION = "intervention"
    REVISION = "revision"
    MERGE = "merge"


@dataclass(frozen=True)
class InvestigationPlan:
    objective: str
    analysis_scope: str
    world_fragility: float
    intervention_ids: tuple[str, ...]
    assertion_ids: tuple[str, ...] = ()
    source_report_hash: str | None = None
    schema_version: str = _INVESTIGATION_PLAN_VERSION
    plan_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != _INVESTIGATION_PLAN_VERSION:
            raise ValueError(
                f"unsupported investigation plan version: {self.schema_version}"
            )
        object.__setattr__(self, "objective", str(self.objective))
        object.__setattr__(self, "analysis_scope", str(self.analysis_scope))
        object.__setattr__(self, "world_fragility", float(self.world_fragility))
        object.__setattr__(self, "intervention_ids", _strings(self.intervention_ids))
        object.__setattr__(self, "assertion_ids", _strings(self.assertion_ids))
        if self.source_report_hash is not None:
            object.__setattr__(self, "source_report_hash", str(self.source_report_hash))
        object.__setattr__(
            self, "plan_id", f"urn:propstore:investigation-plan:{self.content_hash}"
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InvestigationPlan:
        plan = cls(
            objective=str(data.get("objective") or ""),
            analysis_scope=str(data.get("analysis_scope") or ""),
            world_fragility=float(data.get("world_fragility") or 0.0),
            intervention_ids=_strings(
                _sequence(data.get("intervention_ids") or (), "intervention_ids")
            ),
            assertion_ids=_strings(
                _sequence(data.get("assertion_ids") or (), "assertion_ids")
            ),
            source_report_hash=(
                None
                if data.get("source_report_hash") is None
                else str(data.get("source_report_hash"))
            ),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_recorded_identity(
            data, plan.plan_id, plan.content_hash, "investigation plan"
        )
        return plan


@dataclass(frozen=True)
class InterventionPlan:
    objective: str
    target: str
    plan_surface: str
    current_status: str
    target_status: str
    result_status: str
    queryable_ids: tuple[str, ...]
    queryable_cels: tuple[str, ...]
    environment: tuple[str, ...]
    consistent: bool
    minimality_basis: str
    assertion_ids: tuple[str, ...] = ()
    schema_version: str = _INTERVENTION_PLAN_VERSION
    plan_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != _INTERVENTION_PLAN_VERSION:
            raise ValueError(
                f"unsupported intervention plan version: {self.schema_version}"
            )
        object.__setattr__(self, "objective", str(self.objective))
        object.__setattr__(self, "target", str(self.target))
        object.__setattr__(self, "plan_surface", str(self.plan_surface))
        object.__setattr__(self, "current_status", str(self.current_status))
        object.__setattr__(self, "target_status", str(self.target_status))
        object.__setattr__(self, "result_status", str(self.result_status))
        object.__setattr__(self, "queryable_ids", _strings(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _strings(self.queryable_cels))
        object.__setattr__(self, "environment", _strings(self.environment))
        object.__setattr__(self, "consistent", bool(self.consistent))
        object.__setattr__(self, "minimality_basis", str(self.minimality_basis))
        object.__setattr__(self, "assertion_ids", _strings(self.assertion_ids))
        object.__setattr__(
            self, "plan_id", f"urn:propstore:intervention-plan:{self.content_hash}"
        )

    @classmethod
    def from_atms_plan(
        cls,
        plan: ATMSNodeInterventionPlan | ATMSConceptInterventionPlan,
        *,
        objective: str,
        assertion_ids: Sequence[str] = (),
    ) -> InterventionPlan:
        if isinstance(plan, ATMSNodeInterventionPlan):
            plan_surface = "atms_node"
            current_status = plan.current_status.value
            target_status = plan.target_status.value
            result_status = plan.result_status.value
            derived_assertions = (
                (plan.node_id,) if plan.node_id.startswith("ps:assertion:") else ()
            )
        else:
            plan_surface = "atms_concept"
            current_status = plan.current_status.value
            target_status = plan.target_status.value
            result_status = plan.result_status.value
            derived_assertions = ()
        return cls(
            objective=objective,
            target=plan.target,
            plan_surface=plan_surface,
            current_status=current_status,
            target_status=target_status,
            result_status=result_status,
            queryable_ids=tuple(str(item) for item in plan.queryable_ids),
            queryable_cels=tuple(str(item) for item in plan.queryable_cels),
            environment=tuple(str(item) for item in plan.environment),
            consistent=bool(plan.consistent),
            minimality_basis=plan.minimality_basis,
            assertion_ids=tuple(assertion_ids) + derived_assertions,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InterventionPlan:
        plan = cls(
            objective=str(data.get("objective") or ""),
            target=str(data.get("target") or ""),
            plan_surface=str(data.get("plan_surface") or ""),
            current_status=str(data.get("current_status") or ""),
            target_status=str(data.get("target_status") or ""),
            result_status=str(data.get("result_status") or ""),
            queryable_ids=_strings(
                _sequence(data.get("queryable_ids") or (), "queryable_ids")
            ),
            queryable_cels=_strings(
                _sequence(data.get("queryable_cels") or (), "queryable_cels")
            ),
            environment=_strings(
                _sequence(data.get("environment") or (), "environment")
            ),
            consistent=bool(data.get("consistent", False)),
            minimality_basis=str(data.get("minimality_basis") or ""),
            assertion_ids=_strings(
                _sequence(data.get("assertion_ids") or (), "assertion_ids")
            ),
            schema_version=str(data.get("schema_version") or ""),
        )
        _check_recorded_identity(
            data, plan.plan_id, plan.content_hash, "intervention plan"
        )
        return plan


def plan_fragility_investigation(
    world: "WorldQuery",
    request: FragilityRequest,
    *,
    objective: str,
    assertion_ids: Sequence[str] = (),
) -> InvestigationPlan:
    report = query_fragility(world, request)
    return InvestigationPlan.from_fragility_report(
        report,
        objective=objective,
        assertion_ids=assertion_ids,
    )


@dataclass(frozen=True)
class ProcessJob:
    kind: JobKind
    snapshot_hash: str
    policy_id: str
    work_item: Mapping[str, Any]
    assertion_ids: tuple[str, ...] = ()
    journal_entry_hashes: tuple[str, ...] = ()
    schema_version: str = _PROCESS_JOB_VERSION
    job_id: str = ""


@dataclass(frozen=True)
class QueuedProcessJob:
    job: ProcessJob
    queue_position: int

    def __post_init__(self) -> None:
        if not isinstance(self.job, ProcessJob):
            raise TypeError("QueuedProcessJob requires a ProcessJob")
        object.__setattr__(self, "queue_position", int(self.queue_position))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> QueuedProcessJob:
        return cls(
            job=ProcessJob.from_dict(_mapping(data.get("job"), "job")),
            queue_position=int(data.get("queue_position") or 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_position": self.queue_position,
            "job": self.job.to_dict(),
        }


@dataclass(frozen=True)
class ProcessCompletionRecord:
    job_id: str
    completed_snapshot_hash: str
    journal_entry_hashes: tuple[str, ...] = ()
    schema_version: str = _COMPLETION_VERSION


@dataclass(frozen=True)
class ProcessReplayReport:
    ok: bool
    queued_job_ids: tuple[str, ...] = ()
    completed_job_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class EpistemicProcessManager:
    queued_jobs: Mapping[str, QueuedProcessJob] = field(default_factory=dict)
    completions: Mapping[str, ProcessCompletionRecord] = field(default_factory=dict)
    schema_version: str = _PROCESS_MANAGER_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _PROCESS_MANAGER_VERSION:
            raise ValueError(
                f"unsupported process manager version: {self.schema_version}"
            )
        object.__setattr__(
            self,
            "queued_jobs",
            {
                str(job_id): queued
                for job_id, queued in sorted(
                    self.queued_jobs.items(),
                    key=lambda item: item[1].queue_position,
                )
            },
        )
        object.__setattr__(
            self,
            "completions",
            {
                str(job_id): completion
                for job_id, completion in sorted(self.completions.items())
            },
        )

    def queue(self, job: ProcessJob) -> EpistemicProcessManager:
        existing = self.queued_jobs.get(job.job_id)
        if existing is not None:
            if existing.job != job:
                raise ValueError(f"conflicting queued job for {job.job_id}")
            return self
        position = len(self.queued_jobs)
        queued_jobs = dict(self.queued_jobs)
        queued_jobs[job.job_id] = QueuedProcessJob(job=job, queue_position=position)
        return EpistemicProcessManager(
            queued_jobs=queued_jobs,
            completions=self.completions,
        )

    def replay(self) -> ProcessReplayReport:
        errors: list[str] = []
        positions: set[int] = set()
        queued_ids: list[str] = []
        for job_id, queued in sorted(
            self.queued_jobs.items(),
            key=lambda item: item[1].queue_position,
        ):
            queued_ids.append(job_id)
            if queued.job.job_id != job_id:
                errors.append(f"queued job key mismatch for {job_id}")
            if queued.queue_position in positions:
                errors.append(f"duplicate queue position {queued.queue_position}")
            positions.add(queued.queue_position)
        for job_id, completion in self.completions.items():
            if job_id not in self.queued_jobs:
                errors.append(f"completion references unqueued job {job_id}")
            if completion.job_id != job_id:
                errors.append(f"completion key mismatch for {job_id}")
        return ProcessReplayReport(
            ok=not errors,
            queued_job_ids=tuple(queued_ids),
            completed_job_ids=tuple(sorted(self.completions)),
            errors=tuple(errors),
        )


__all__ = [
    "EpistemicProcessManager",
    "InterventionPlan",
    "InvestigationPlan",
    "JobKind",
    "ProcessCompletionRecord",
    "ProcessJob",
    "ProcessReplayReport",
    "QueuedProcessJob",
    "plan_fragility_investigation",
]
