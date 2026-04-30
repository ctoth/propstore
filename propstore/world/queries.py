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
    from propstore.world.model import WorldQuery


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
    world: WorldQuery,
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


@dataclass(frozen=True)
class WorldDeriveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldDeriveReport:
    concept_id: str
    status: object
    value: object
    formula: object
    input_values: object
    exactness: object


@dataclass(frozen=True)
class WorldHypotheticalSyntheticClaimSpec:
    claim_id: str
    concept_id: str
    claim_type: object = "parameter"
    value: float | str | None = None
    conditions: tuple[object, ...] = ()


@dataclass(frozen=True)
class WorldHypotheticalRequest:
    bindings: Mapping[str, str]
    remove_claim_ids: tuple[str, ...] = ()
    add_claims: tuple[WorldHypotheticalSyntheticClaimSpec, ...] = ()


@dataclass(frozen=True)
class WorldHypotheticalChangeLine:
    concept_display_id: str
    base_status: object
    hypothetical_status: object


@dataclass(frozen=True)
class WorldHypotheticalReport:
    changes: tuple[WorldHypotheticalChangeLine, ...]


class WorldResolveError(WorldQueryError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class WorldResolveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldAcceptanceProbabilityLine:
    claim_id: str
    probability: float


@dataclass(frozen=True)
class WorldResolveReport:
    concept_display_id: str
    status: object
    value: object
    winning_claim_display_id: str | None
    strategy: object
    reason: object
    acceptance_probs: tuple[WorldAcceptanceProbabilityLine, ...]


@dataclass(frozen=True)
class WorldChainRequest:
    concept_id: str
    bindings: Mapping[str, str]
    strategy: str | None = None


@dataclass(frozen=True)
class WorldChainConceptLine:
    display_id: str
    canonical_name: str | None


@dataclass(frozen=True)
class WorldChainStepLine:
    concept: WorldChainConceptLine
    value: object
    source: str


@dataclass(frozen=True)
class WorldChainReport:
    target: WorldChainConceptLine
    status: object
    value: object
    steps: tuple[WorldChainStepLine, ...]


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
    world: WorldQuery | None = None,
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


def resolve_world_target(world: WorldQuery, target: str) -> str:
    return world.resolve_concept(target) or target


def world_concept_display_id(world: WorldQuery, concept_id: str) -> str:
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


def _world_chain_concept_line(
    world: WorldQuery,
    concept_id: str,
) -> WorldChainConceptLine:
    from propstore.core.row_types import coerce_concept_row

    concept = world.get_concept(concept_id)
    canonical_name = (
        coerce_concept_row(concept).canonical_name
        if concept is not None
        else None
    )
    return WorldChainConceptLine(
        display_id=world_concept_display_id(world, concept_id),
        canonical_name=canonical_name,
    )


def query_world_concept(
    world: WorldQuery,
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
    world: WorldQuery,
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
    world: WorldQuery,
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
        concept_display_id=world_concept_display_id(world, str(claim.value_concept_id)),
        value=claim.value,
        stances=tuple(stances),
    )


def list_world_algorithms(
    world: WorldQuery,
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
            if str(claim.output_concept_id or "") == request.concept
        ]
    return WorldAlgorithmsReport(
        algorithms=tuple(
            WorldAlgorithmLine(
                claim_id=str(claim.claim_id),
                name=claim.name or (claim.body or "")[:25] or "?",
                stage=str(claim.algorithm_stage)
                if claim.algorithm_stage is not None
                else "-",
                concept_id=str(claim.output_concept_id)
                if claim.output_concept_id is not None
                else "-",
            )
            for claim in algorithms
        )
    )


def derive_world_value(
    world: WorldQuery,
    request: WorldDeriveRequest,
) -> WorldDeriveReport:
    from propstore.core.environment import Environment

    resolved = resolve_world_target(world, request.concept_id)
    bound = world.bind(
        Environment(bindings=dict(request.bindings)),
        policy=request.policy,
    )
    result = bound.derived_value(resolved)
    return WorldDeriveReport(
        concept_id=resolved,
        status=result.status,
        value=result.value,
        formula=result.formula,
        input_values=result.input_values,
        exactness=result.exactness,
    )


def diff_hypothetical_world(
    world: WorldQuery,
    request: WorldHypotheticalRequest,
) -> WorldHypotheticalReport:
    from propstore.cel_types import to_cel_exprs
    from propstore.core.claim_types import ClaimType, coerce_claim_type
    from propstore.core.environment import Environment
    from propstore.core.id_types import to_concept_id
    from propstore.world import OverlayWorld, SyntheticClaim

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    synthetics = [
        SyntheticClaim(
            id=spec.claim_id,
            concept_id=to_concept_id(spec.concept_id),
            type=coerce_claim_type(spec.claim_type) or ClaimType.PARAMETER,
            value=spec.value,
            conditions=list(to_cel_exprs(spec.conditions)),
        )
        for spec in request.add_claims
    ]
    resolved_remove = [
        world.resolve_claim(claim_id) or claim_id
        for claim_id in request.remove_claim_ids
    ]
    diff = OverlayWorld(
        bound,
        remove=resolved_remove,
        add=synthetics,
    ).diff()
    return WorldHypotheticalReport(
        changes=tuple(
            WorldHypotheticalChangeLine(
                concept_display_id=world_concept_display_id(world, concept_id),
                base_status=base.status,
                hypothetical_status=hypothetical.status,
            )
            for concept_id, (base, hypothetical) in diff.items()
        )
    )


def resolve_world_value(
    world: WorldQuery,
    request: WorldResolveRequest,
) -> WorldResolveReport:
    from propstore.core.environment import Environment
    from propstore.world import resolve

    resolved = resolve_world_target(world, request.concept_id)
    bound = world.bind(Environment(bindings=dict(request.bindings)))
    try:
        result = resolve(bound, resolved, policy=request.policy, world=world)
    except (ValueError, NotImplementedError) as exc:
        raise WorldResolveError(str(exc)) from exc

    winner_id = None
    if result.winning_claim_id:
        winning_claim = world.get_claim(result.winning_claim_id)
        winner_id = (
            world_claim_display_id(winning_claim)
            if winning_claim
            else result.winning_claim_id
        )
    return WorldResolveReport(
        concept_display_id=world_concept_display_id(world, resolved),
        status=result.status,
        value=result.value,
        winning_claim_display_id=winner_id,
        strategy=result.strategy,
        reason=result.reason,
        acceptance_probs=tuple(
            WorldAcceptanceProbabilityLine(claim_id=str(claim_id), probability=prob)
            for claim_id, prob in sorted(result.acceptance_probs.items())
        )
        if result.acceptance_probs
        else (),
    )


def query_world_chain(
    world: WorldQuery,
    request: WorldChainRequest,
) -> WorldChainReport:
    from propstore.world import DerivedResult, ResolutionStrategy

    resolved = resolve_world_target(world, request.concept_id)
    strategy = ResolutionStrategy(request.strategy) if request.strategy else None
    result = world.chain_query(resolved, strategy=strategy, **dict(request.bindings))
    value = (
        result.result.value
        if isinstance(result.result, DerivedResult)
        and result.result.value is not None
        else None
    )
    return WorldChainReport(
        target=_world_chain_concept_line(world, resolved),
        status=result.result.status,
        value=value,
        steps=tuple(
            WorldChainStepLine(
                concept=_world_chain_concept_line(world, step.concept_id),
                value=step.value,
                source=step.source,
            )
            for step in result.steps
        ),
    )
