"""Typed world query owner APIs.

Request/result/failure types owned here:
- `WorldStatusRequest`
- `WorldStatusReport`
- `WorldQueryError`
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from propstore.world.types import RenderPolicy

if TYPE_CHECKING:
    from propstore.world.model import WorldModel


class WorldQueryError(Exception):
    """Base class for expected world-query failures."""


class UnknownConceptError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown concept: {target}")
        self.target = target


class UnknownClaimError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown claim: {target}")
        self.target = target


@dataclass(frozen=True)
class WorldStatusRequest:
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldStatusReport:
    concept_count: int
    visible_claim_count: int
    conflict_count: int
    diagnostic_count: int


def get_world_status(
    world: WorldModel,
    request: WorldStatusRequest,
) -> WorldStatusReport:
    stats = world.stats()
    visible_claims = len(world.claims_with_policy(None, request.policy))
    diagnostics = world.build_diagnostics(request.policy)
    return WorldStatusReport(
        concept_count=stats.concepts,
        visible_claim_count=visible_claims,
        conflict_count=stats.conflicts,
        diagnostic_count=len(diagnostics),
    )


@dataclass(frozen=True)
class WorldConceptQueryRequest:
    target: str
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldClaimLine:
    display_id: str
    claim_type: str
    value_display: str
    conditions: str


@dataclass(frozen=True)
class WorldDiagnosticLine:
    target: str
    diagnostic_kind: str
    message: str


@dataclass(frozen=True)
class WorldConceptQueryReport:
    canonical_name: str
    concept_display_id: str
    claims: tuple[WorldClaimLine, ...]
    diagnostics: tuple[WorldDiagnosticLine, ...]


@dataclass(frozen=True)
class WorldBindRequest:
    bindings: Mapping[str, str]
    target: str | None = None


@dataclass(frozen=True)
class WorldBindClaimLine:
    display_id: str
    concept_display_id: str | None
    value_display: str
    conditions: str | None
    source: str | None = None


@dataclass(frozen=True)
class WorldBindConceptReport:
    concept_display_id: str
    status: str
    claims: tuple[WorldBindClaimLine, ...]


@dataclass(frozen=True)
class WorldBindActiveReport:
    active_claim_count: int
    claims: tuple[WorldBindClaimLine, ...]


WorldBindReport = WorldBindConceptReport | WorldBindActiveReport


@dataclass(frozen=True)
class WorldExplainRequest:
    claim_id: str


@dataclass(frozen=True)
class WorldStanceLine:
    source_display_id: str
    stance_type: str
    target_display_id: str
    strength: object
    note: object
    nested: bool


@dataclass(frozen=True)
class WorldExplainReport:
    claim_display_id: str
    claim_type: str
    concept_display_id: str
    value: object
    stances: tuple[WorldStanceLine, ...]


@dataclass(frozen=True)
class WorldAlgorithmsRequest:
    stage: str | None = None
    concept: str | None = None


@dataclass(frozen=True)
class WorldAlgorithmLine:
    claim_id: str
    name: str
    stage: str
    concept_id: str


@dataclass(frozen=True)
class WorldAlgorithmsReport:
    algorithms: tuple[WorldAlgorithmLine, ...]


def _maybe_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _format_value_with_si(
    claim: Mapping[str, object],
    world: WorldModel | None = None,
) -> str:
    value = claim.get("value")
    unit = claim.get("unit")
    value_si = claim.get("value_si")
    numeric_value = _maybe_float(value)
    numeric_value_si = _maybe_float(value_si)
    if (
        isinstance(unit, str)
        and numeric_value is not None
        and numeric_value_si is not None
        and numeric_value_si != numeric_value
    ):
        canonical_unit = ""
        if world is not None:
            concept_id = claim.get("concept_id")
            if isinstance(concept_id, str):
                concept = world.get_concept(concept_id)
                if concept is not None:
                    from propstore.core.row_types import coerce_concept_row

                    canonical_unit = str(
                        coerce_concept_row(concept).attributes.get("unit_symbol") or ""
                    )
        si_label = f"{value_si} {canonical_unit}".rstrip()
        return f"value={value} {unit} (SI: {si_label})"
    if isinstance(unit, str):
        return f"value={value} {unit}"
    return f"value={value}"


def resolve_world_target(world: WorldModel, target: str) -> str:
    return world.resolve_concept(target) or target


def world_concept_display_id(world: WorldModel, concept_id: str) -> str:
    from propstore.core.row_types import coerce_concept_row

    concept = world.get_concept(concept_id)
    if concept is None:
        return concept_id
    row = coerce_concept_row(concept)
    logical_id = row.primary_logical_id
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    return str(row.concept_id or concept_id)


def world_claim_display_id(claim: Mapping[str, object] | Any) -> str:
    from propstore.core.row_types import coerce_claim_row

    row = coerce_claim_row(claim)
    logical_id = row.primary_logical_id
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    return str(row.claim_id)


def query_world_concept(
    world: WorldModel,
    request: WorldConceptQueryRequest,
) -> WorldConceptQueryReport:
    from propstore.core.row_types import coerce_claim_row, coerce_concept_row

    resolved = resolve_world_target(world, request.target)
    concept = world.get_concept(resolved)
    if concept is None:
        raise UnknownConceptError(request.target)

    concept_row = coerce_concept_row(concept)
    claims = tuple(
        WorldClaimLine(
            display_id=world_claim_display_id(claim_row),
            claim_type=str(claim_dict["type"]),
            value_display=_format_value_with_si(claim_dict, world),
            conditions=str(claim_dict.get("conditions_cel") or "[]"),
        )
        for claim_row in (
            coerce_claim_row(claim)
            for claim in world.claims_with_policy(resolved, request.policy)
        )
        for claim_dict in (claim_row.to_dict(),)
    )
    diagnostics = tuple(
        WorldDiagnosticLine(
            target=str(row.get("claim_id") or row.get("source_ref") or "?"),
            diagnostic_kind=str(row["diagnostic_kind"]),
            message=str(row["message"]),
        )
        for row in world.build_diagnostics(request.policy)
    )
    return WorldConceptQueryReport(
        canonical_name=concept_row.canonical_name,
        concept_display_id=world_concept_display_id(world, resolved),
        claims=claims,
        diagnostics=diagnostics,
    )


def query_bound_world(
    world: WorldModel,
    request: WorldBindRequest,
) -> WorldBindReport:
    from propstore.core.environment import Environment

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    if request.target is not None:
        resolved = resolve_world_target(world, request.target)
        result = bound.value_of(resolved)
        return WorldBindConceptReport(
            concept_display_id=world_concept_display_id(world, resolved),
            status=str(result.status),
            claims=tuple(
                WorldBindClaimLine(
                    display_id=world_claim_display_id(claim_dict),
                    concept_display_id=None,
                    value_display=_format_value_with_si(claim_dict, world),
                    conditions=None,
                    source=(
                        None
                        if claim_dict.get("source_paper") is None
                        else str(claim_dict.get("source_paper"))
                    ),
                )
                for active_claim in result.claims
                for claim_dict in (active_claim.row.to_dict(),)
            ),
        )

    active_claims = bound.active_claims()
    return WorldBindActiveReport(
        active_claim_count=len(active_claims),
        claims=tuple(
            WorldBindClaimLine(
                display_id=world_claim_display_id(claim_dict),
                concept_display_id=world_concept_display_id(
                    world,
                    str(claim_dict.get("concept_id", "?")),
                ),
                value_display=_format_value_with_si(claim_dict, world),
                conditions=str(claim_dict.get("conditions_cel") or "[]"),
            )
            for active_claim in active_claims
            for claim_dict in (active_claim.row.to_dict(),)
        ),
    )


def explain_world_claim(
    world: WorldModel,
    request: WorldExplainRequest,
) -> WorldExplainReport:
    from propstore.core.row_types import coerce_claim_row

    claim_input = world.get_claim(request.claim_id)
    if claim_input is None:
        raise UnknownClaimError(request.claim_id)
    claim = coerce_claim_row(claim_input)
    claim_display_id = world_claim_display_id(claim)
    stances: list[WorldStanceLine] = []
    for stance in world.explain(str(claim.claim_id)):
        source_id = str(stance.claim_id)
        source_claim = world.get_claim(source_id)
        source_display_id = (
            world_claim_display_id(source_claim) if source_claim else source_id
        )
        target_claim_id = str(stance.target_claim_id)
        target_claim = world.get_claim(target_claim_id)
        target_display_id = (
            world_claim_display_id(target_claim)
            if target_claim
            else target_claim_id
        )
        stances.append(
            WorldStanceLine(
                source_display_id=source_display_id,
                stance_type=str(stance.stance_type),
                target_display_id=target_display_id,
                strength=stance.attributes.get("strength"),
                note=stance.attributes.get("note"),
                nested=source_id != str(claim.claim_id),
            )
        )
    return WorldExplainReport(
        claim_display_id=claim_display_id,
        claim_type=str(claim.claim_type),
        concept_display_id=world_concept_display_id(world, str(claim.concept_id)),
        value=claim.value,
        stances=tuple(stances),
    )


def list_world_algorithms(
    world: WorldModel,
    request: WorldAlgorithmsRequest,
) -> WorldAlgorithmsReport:
    from propstore.core.algorithm_stage import coerce_algorithm_stage
    from propstore.core.claim_types import ClaimType
    from propstore.core.row_types import coerce_claim_row

    claims = [coerce_claim_row(claim) for claim in world.claims_for(None)]
    algorithms = [claim for claim in claims if claim.claim_type is ClaimType.ALGORITHM]
    stage_filter = (
        coerce_algorithm_stage(request.stage)
        if request.stage is not None
        else None
    )
    if stage_filter is not None:
        algorithms = [
            claim for claim in algorithms if claim.algorithm_stage == stage_filter
        ]
    if request.concept:
        algorithms = [
            claim
            for claim in algorithms
            if str(claim.concept_id or "") == request.concept
        ]
    return WorldAlgorithmsReport(
        algorithms=tuple(
            WorldAlgorithmLine(
                claim_id=str(claim.claim_id),
                name=claim.name or (claim.body or "")[:25] or "?",
                stage=str(claim.algorithm_stage)
                if claim.algorithm_stage is not None
                else "-",
                concept_id=str(claim.concept_id)
                if claim.concept_id is not None
                else "-",
            )
            for claim in algorithms
        )
    )
