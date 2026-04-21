"""Application-layer ATMS world inspection workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, cast

from propstore.app.world import (
    open_app_world_model,
    resolve_world_target,
)
from propstore.repository import Repository


class WorldAtmsAppError(Exception):
    """Base class for expected ATMS app failures."""


class WorldAtmsValidationError(WorldAtmsAppError):
    pass


class _StatusCarrier(Protocol):
    status: object


@dataclass(frozen=True)
class AppAtmsViewRequest:
    bindings: Mapping[str, str]
    concept_id: str | None = None
    context: str | None = None


@dataclass(frozen=True)
class AppAtmsTargetRequest:
    target: str
    bindings: Mapping[str, str]
    queryables: tuple[str, ...] = ()
    limit: int = 8
    context: str | None = None


@dataclass(frozen=True)
class AppAtmsInterventionRequest:
    target: str
    bindings: Mapping[str, str]
    target_status: str
    queryables: tuple[str, ...]
    limit: int = 8
    context: str | None = None


@dataclass(frozen=True)
class AtmsClaimStatusLine:
    claim_id: str
    status: str
    support_quality: str | None = None
    essential_support: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class AtmsStatusReport:
    claims: tuple[AtmsClaimStatusLine, ...]


@dataclass(frozen=True)
class AtmsContextReport:
    environment: tuple[str, ...]
    claims: tuple[AtmsClaimStatusLine, ...]


@dataclass(frozen=True)
class AtmsVerifyReport:
    ok: bool
    sections: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class AtmsFutureLine:
    queryable_cels: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class AtmsClaimFutureReport:
    target: str
    current_status: str
    could_become_in: object
    could_become_out: object
    futures: tuple[AtmsFutureLine, ...]


@dataclass(frozen=True)
class AtmsConceptFutureReport:
    claims: tuple[AtmsClaimFutureReport, ...]


AtmsFutureReport = AtmsClaimFutureReport | AtmsConceptFutureReport


@dataclass(frozen=True)
class AtmsClaimWhyOutReport:
    target: str
    out_kind: str
    future_activatable: object
    candidate_queryables: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class AtmsConceptWhyOutReport:
    target: str
    value_status: object
    supported_claim_ids: tuple[str, ...]
    claim_reasons: tuple[AtmsClaimWhyOutReport, ...]


AtmsWhyOutReport = AtmsClaimWhyOutReport | AtmsConceptWhyOutReport


@dataclass(frozen=True)
class AtmsStabilityReport:
    target: str
    current_status: object
    stable: object
    consistent_future_count: object
    witnesses: tuple[AtmsFutureLine, ...]


@dataclass(frozen=True)
class AtmsRelevancePairLine:
    queryable_cel: str
    without_queryables: tuple[str, ...]
    without_status: str
    with_queryables: tuple[str, ...]
    with_status: str


@dataclass(frozen=True)
class AtmsRelevanceReport:
    target: str
    current_status: object
    relevant_queryables: tuple[str, ...]
    witness_pairs: tuple[AtmsRelevancePairLine, ...]


@dataclass(frozen=True)
class AtmsPlanLine:
    queryable_cels: tuple[str, ...]
    result_status: str


@dataclass(frozen=True)
class AtmsInterventionsReport:
    plans: tuple[AtmsPlanLine, ...]


@dataclass(frozen=True)
class AtmsNextQueryLine:
    queryable_cel: str
    plan_count: object
    smallest_plan_size: object


@dataclass(frozen=True)
class AtmsNextQueryReport:
    suggestions: tuple[AtmsNextQueryLine, ...]


def _status_value(status: object) -> str:
    if isinstance(status, str):
        return status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def _support_ids(support: object) -> tuple[str, ...]:
    assumption_ids = getattr(support, "assumption_ids", ())
    return tuple(str(assumption_id) for assumption_id in assumption_ids)


def _mapping_sequence(value: object, *, field_name: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, tuple | list):
        raise WorldAtmsValidationError(f"{field_name} must be a sequence")
    result: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise WorldAtmsValidationError(f"{field_name} entries must be mappings")
        result.append(item)
    return tuple(result)


def _string_sequence(value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple | list):
        raise WorldAtmsValidationError(f"{field_name} must be a sequence")
    return tuple(str(item) for item in value)


def _queryables(queryables: tuple[str, ...]):
    from propstore.world.types import coerce_queryable_assumptions

    return list(coerce_queryable_assumptions(queryables))


def _bind_atms(repo: Repository, request: AppAtmsViewRequest):
    from propstore.world.atms_workflows import ATMSBindRequest, bind_atms_world

    world = open_app_world_model(repo)
    wm = world.__enter__()
    try:
        bindings = dict(request.bindings)
        bound = bind_atms_world(wm, ATMSBindRequest(bindings, request.context))
        return world, wm, bound, bindings, request.concept_id
    except Exception:
        world.__exit__(None, None, None)
        raise


def _claim_future_report(target: str, report: Mapping[str, object]) -> AtmsClaimFutureReport:
    return AtmsClaimFutureReport(
        target=target,
        current_status=_status_value(cast(_StatusCarrier, report["current"]).status),
        could_become_in=report["could_become_in"],
        could_become_out=report["could_become_out"],
        futures=tuple(
            AtmsFutureLine(
                queryable_cels=_string_sequence(
                    future["queryable_cels"],
                    field_name="future.queryable_cels",
                ),
                status=_status_value(future["status"]),
            )
            for future in _mapping_sequence(report["futures"], field_name="futures")
        ),
    )


def world_atms_status(repo: Repository, request: AppAtmsViewRequest) -> AtmsStatusReport:
    manager, wm, bound, _bindings, concept_id = _bind_atms(repo, request)
    try:
        resolved = None if concept_id is None else resolve_world_target(wm, concept_id)
        active_claims = sorted(
            bound.active_claims(resolved),
            key=lambda claim: str(claim.claim_id),
        )
        return AtmsStatusReport(
            claims=tuple(
                AtmsClaimStatusLine(
                    claim_id=str(claim.claim_id),
                    status=_status_value(inspection.status),
                    support_quality=_status_value(inspection.support_quality),
                    essential_support=_support_ids(inspection.essential_support),
                    reason=str(inspection.reason),
                )
                for claim in active_claims
                for inspection in (bound.claim_status(str(claim.claim_id)),)
            )
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_context(repo: Repository, request: AppAtmsViewRequest) -> AtmsContextReport:
    manager, wm, bound, _bindings, concept_id = _bind_atms(repo, request)
    try:
        environment = tuple(
            str(assumption.assumption_id)
            for assumption in bound._environment.assumptions
        )
        claim_ids = bound.claims_in_environment(environment)
        if concept_id:
            resolved = resolve_world_target(wm, concept_id)
            allowed = {
                str(claim.claim_id)
                for claim in bound.active_claims(resolved)
            }
            claim_ids = [claim_id for claim_id in claim_ids if claim_id in allowed]
        return AtmsContextReport(
            environment=environment,
            claims=tuple(
                AtmsClaimStatusLine(
                    claim_id=str(claim_id),
                    status=_status_value(inspection.status),
                    essential_support=_support_ids(inspection.essential_support),
                )
                for claim_id in sorted(claim_ids)
                for inspection in (bound.claim_status(claim_id),)
            ),
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_verify(repo: Repository, request: AppAtmsViewRequest) -> AtmsVerifyReport:
    manager, _wm, bound, _bindings, _concept_id = _bind_atms(repo, request)
    try:
        raw = bound.atms_engine().verify_labels()
        sections = {
            section: tuple(str(error) for error in raw.get(section) or ())
            for section in (
                "consistency_errors",
                "minimality_errors",
                "soundness_errors",
                "completeness_errors",
            )
        }
        return AtmsVerifyReport(ok=bool(raw["ok"]), sections=sections)
    finally:
        manager.__exit__(None, None, None)


def world_atms_futures(repo: Repository, request: AppAtmsTargetRequest) -> AtmsFutureReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            return _claim_future_report(
                request.target,
                bound.claim_future_statuses(
                    request.target,
                    queryables,
                    limit=request.limit,
                ),
            )
        resolved = resolve_world_target(wm, request.target)
        concept_report = bound.concept_future_statuses(
            resolved,
            queryables,
            limit=request.limit,
        )
        return AtmsConceptFutureReport(
            claims=tuple(
                _claim_future_report(str(claim_id), concept_report[claim_id])
                for claim_id in sorted(concept_report)
            )
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_why_out(repo: Repository, request: AppAtmsTargetRequest) -> AtmsWhyOutReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            report = bound.atms_engine().why_out(
                f"claim:{request.target}",
                queryables=queryables,
                limit=request.limit,
            )
            return AtmsClaimWhyOutReport(
                target=request.target,
                out_kind=(
                    "none"
                    if report["out_kind"] is None
                    else _status_value(report["out_kind"])
                ),
                future_activatable=report["future_activatable"],
                candidate_queryables=tuple(
                    ", ".join(str(value) for value in item)
                    for item in report["candidate_queryable_cels"]
                ),
                reason=str(report["reason"]),
            )
        resolved = resolve_world_target(wm, request.target)
        concept_report = bound.why_concept_out(
            resolved,
            queryables,
            limit=request.limit,
        )
        return AtmsConceptWhyOutReport(
            target=resolved,
            value_status=concept_report["value_status"],
            supported_claim_ids=tuple(
                str(claim_id) for claim_id in concept_report["supported_claim_ids"]
            ),
            claim_reasons=tuple(
                AtmsClaimWhyOutReport(
                    target=str(claim_id),
                    out_kind=(
                        "none"
                        if report["out_kind"] is None
                        else _status_value(report["out_kind"])
                    ),
                    future_activatable=report["future_activatable"],
                    candidate_queryables=(),
                    reason=str(report.get("reason", "")),
                )
                for claim_id, report in sorted(concept_report["claim_reasons"].items())
            ),
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_stability(repo: Repository, request: AppAtmsTargetRequest) -> AtmsStabilityReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            report = bound.claim_stability(
                request.target,
                queryables,
                limit=request.limit,
            )
            return AtmsStabilityReport(
                target=request.target,
                current_status=_status_value(report["current"].status),
                stable=report["stable"],
                consistent_future_count=report["consistent_future_count"],
                witnesses=tuple(
                    AtmsFutureLine(
                        queryable_cels=tuple(str(value) for value in witness["queryable_cels"]),
                        status=_status_value(witness["status"]),
                    )
                    for witness in report["witnesses"]
                ),
            )
        resolved = resolve_world_target(wm, request.target)
        report = bound.concept_stability(resolved, queryables, limit=request.limit)
        return AtmsStabilityReport(
            target=resolved,
            current_status=report["current_status"],
            stable=report["stable"],
            consistent_future_count=report["consistent_future_count"],
            witnesses=tuple(
                AtmsFutureLine(
                    queryable_cels=tuple(str(value) for value in witness["queryable_cels"]),
                    status=_status_value(witness["status"]),
                )
                for witness in report["witnesses"]
            ),
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_relevance(repo: Repository, request: AppAtmsTargetRequest) -> AtmsRelevanceReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            raw = bound.claim_relevance(request.target, queryables, limit=request.limit)
            target = request.target
            current_status = _status_value(raw["current"].status)
        else:
            target = resolve_world_target(wm, request.target)
            raw = bound.concept_relevance(target, queryables, limit=request.limit)
            current_status = raw["current_status"]
        pairs: list[AtmsRelevancePairLine] = []
        for queryable_cel, raw_pairs in sorted(raw["witness_pairs"].items()):
            for pair in raw_pairs:
                pairs.append(
                    AtmsRelevancePairLine(
                        queryable_cel=str(queryable_cel),
                        without_queryables=tuple(
                            str(value)
                            for value in pair["without"]["queryable_cels"]
                        ),
                        without_status=_status_value(pair["without"]["status"]),
                        with_queryables=tuple(
                            str(value)
                            for value in pair["with"]["queryable_cels"]
                        ),
                        with_status=_status_value(pair["with"]["status"]),
                    )
                )
        return AtmsRelevanceReport(
            target=target,
            current_status=current_status,
            relevant_queryables=tuple(str(value) for value in raw["relevant_queryables"]),
            witness_pairs=tuple(pairs),
        )
    finally:
        manager.__exit__(None, None, None)


def _target_status_for_claim(target_status: str):
    from propstore.world.types import ATMSNodeStatus

    try:
        return ATMSNodeStatus(target_status)
    except ValueError as exc:
        raise WorldAtmsValidationError(str(exc)) from exc


def _target_status_for_concept(target_status: str):
    from propstore.world.types import coerce_value_status

    try:
        typed_status = coerce_value_status(target_status)
    except ValueError as exc:
        raise WorldAtmsValidationError(str(exc)) from exc
    if typed_status is None:
        raise WorldAtmsValidationError("target status is required")
    return typed_status


def world_atms_interventions(
    repo: Repository,
    request: AppAtmsInterventionRequest,
) -> AtmsInterventionsReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            plans = bound.claim_interventions(
                request.target,
                queryables,
                _target_status_for_claim(request.target_status),
                limit=request.limit,
            )
        else:
            plans = bound.concept_interventions(
                resolve_world_target(wm, request.target),
                queryables,
                _target_status_for_concept(request.target_status),
                limit=request.limit,
            )
        return AtmsInterventionsReport(
            plans=tuple(
                AtmsPlanLine(
                    queryable_cels=tuple(str(value) for value in plan["queryable_cels"]),
                    result_status=_status_value(plan["result_status"]),
                )
                for plan in plans
            )
        )
    finally:
        manager.__exit__(None, None, None)


def world_atms_next_query(
    repo: Repository,
    request: AppAtmsInterventionRequest,
) -> AtmsNextQueryReport:
    manager, wm, bound, _bindings, _concept_id = _bind_atms(
        repo,
        AppAtmsViewRequest(bindings=request.bindings, context=request.context),
    )
    try:
        queryables = _queryables(request.queryables)
        claim = wm.get_claim(request.target)
        if claim is not None:
            suggestions = bound.claim_next_queryables(
                request.target,
                queryables,
                _target_status_for_claim(request.target_status),
                limit=request.limit,
            )
        else:
            suggestions = bound.concept_next_queryables(
                resolve_world_target(wm, request.target),
                queryables,
                _target_status_for_concept(request.target_status),
                limit=request.limit,
            )
        return AtmsNextQueryReport(
            suggestions=tuple(
                AtmsNextQueryLine(
                    queryable_cel=str(suggestion["queryable_cel"]),
                    plan_count=suggestion["plan_count"],
                    smallest_plan_size=suggestion["smallest_plan_size"],
                )
                for suggestion in suggestions
            )
        )
    finally:
        manager.__exit__(None, None, None)
