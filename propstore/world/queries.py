"""Typed world query owner APIs.

Request/result/failure types owned here:
- `WorldStatusRequest`
- `WorldStatusReport`
- `WorldQueryError`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from propstore.core.algorithm_stage import AlgorithmStage
from propstore.reporting import JsonReportMixin
from propstore.families.claims.declaration import Claim
from propstore.families.concepts.declaration import (
    ConceptSearchQuerySyntaxError,
)
from propstore.world.types import BeliefSpace, RenderPolicy

if TYPE_CHECKING:
    from propstore.world.model import WorldQuery
    from propstore.world.overlay import OverlayWorld


class WorldQueryError(Exception):
    """Base class for expected world-query failures."""


class UnknownConceptError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown concept: {target}")
        self.target = target


class AmbiguousConceptError(WorldQueryError):
    def __init__(
        self,
        target: str,
        candidates: tuple[WorldConceptResolutionCandidate, ...],
    ) -> None:
        super().__init__(f"Ambiguous concept: {target}")
        self.target = target
        self.candidates = candidates


class UnknownClaimError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown claim: {target}")
        self.target = target


@dataclass(frozen=True)
class WorldStatusRequest:
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldStatusReport(JsonReportMixin):
    concept_count: int
    visible_claim_count: int
    conflict_count: int
    diagnostic_count: int
    source_count: int = 0
    context_count: int = 0
    predicate_count: int = 0
    rule_count: int = 0
    authored_justification_count: int = 0
    stance_count: int = 0


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
        authored_justification_count=world.authored_justification_count(),
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
class WorldConceptResolutionCandidate:
    concept_id: str
    display_id: str
    canonical_name: str


@dataclass(frozen=True)
class WorldConceptQueryReport(JsonReportMixin):
    canonical_name: str
    concept_display_id: str
    claims: tuple[WorldClaimLine, ...]
    diagnostics: tuple[WorldDiagnosticLine, ...]
    resolved_from: str | None = None


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
class WorldBindConceptReport(JsonReportMixin):
    concept_display_id: str
    status: str
    claims: tuple[WorldBindClaimLine, ...]


@dataclass(frozen=True)
class WorldBindActivationReport(JsonReportMixin):
    active_claim_count: int
    claims: tuple[WorldBindClaimLine, ...]


WorldBindReport = WorldBindConceptReport | WorldBindActivationReport


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
class WorldExplainReport(JsonReportMixin):
    claim_display_id: str
    claim_type: str
    concept_display_id: str
    value: object
    stances: tuple[WorldStanceLine, ...]


@dataclass(frozen=True)
class WorldAlgorithmsRequest:
    stage: AlgorithmStage | None = None
    concept: str | None = None


@dataclass(frozen=True)
class WorldAlgorithmLine:
    claim_id: str
    name: str
    stage: str
    concept_id: str


@dataclass(frozen=True)
class WorldAlgorithmsReport(JsonReportMixin):
    algorithms: tuple[WorldAlgorithmLine, ...]


@dataclass(frozen=True)
class WorldDeriveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldDeriveReport(JsonReportMixin):
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
class WorldHypotheticalExtensionCounts:
    active: int
    accepted: int
    defeated: int
    undecided: int


@dataclass(frozen=True)
class WorldHypotheticalExtensionTransition:
    from_status: str
    to_status: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorldHypotheticalExtensionDiff:
    before: WorldHypotheticalExtensionCounts
    after: WorldHypotheticalExtensionCounts
    unchanged: bool
    transitions: tuple[WorldHypotheticalExtensionTransition, ...]


@dataclass(frozen=True)
class WorldHypotheticalReport(JsonReportMixin):
    changes: tuple[WorldHypotheticalChangeLine, ...]
    extension_diff: WorldHypotheticalExtensionDiff


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
class WorldResolveReport(JsonReportMixin):
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
class WorldChainReport(JsonReportMixin):
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


def resolve_world_target(world: WorldQuery, target: str) -> str:
    concept = world.get_concept(target)
    return str(concept.id) if concept is not None else target


def _fts_phrase(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _concept_resolution_candidate(
    world: WorldQuery,
    concept_id: str,
) -> WorldConceptResolutionCandidate | None:
    concept = world.get_concept(concept_id)
    if concept is None:
        return None
    return WorldConceptResolutionCandidate(
        concept_id=concept_id,
        display_id=world_concept_display_id(world, concept_id),
        canonical_name=concept.canonical_name,
    )


def _resolve_world_query_target(
    world: WorldQuery,
    target: str,
) -> tuple[str, str | None]:
    concept = world.get_concept(target)
    if concept is not None:
        return str(concept.id), None

    try:
        hits = world.search(_fts_phrase(target))
    except ConceptSearchQuerySyntaxError:
        hits = []
    candidate_ids = tuple(dict.fromkeys(str(hit.concept_id) for hit in hits))
    candidates = tuple(
        candidate
        for concept_id in candidate_ids
        for candidate in (_concept_resolution_candidate(world, concept_id),)
        if candidate is not None
    )
    if len(candidates) == 1:
        return candidates[0].concept_id, target
    if len(candidates) > 1:
        raise AmbiguousConceptError(target, candidates)
    return target, None


def world_concept_display_id(world: WorldQuery, concept_id: str) -> str:
    concept = world.get_concept(concept_id)
    if concept is None:
        return concept_id
    logical_id = concept.primary_logical_id
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    return str(concept.concept_id or concept_id)


def world_claim_display_id(claim: Claim) -> str:
    logical_id = claim.primary_logical_id
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    return str(claim.id)


def _world_chain_concept_line(
    world: WorldQuery,
    concept_id: str,
) -> WorldChainConceptLine:
    concept = world.get_concept(concept_id)
    canonical_name = concept.canonical_name if concept is not None else None
    return WorldChainConceptLine(
        display_id=world_concept_display_id(world, concept_id),
        canonical_name=canonical_name,
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
    from propstore.families.claims.types import ClaimType
    from propstore.core.environment import Environment
    from propstore.core.id_types import ConceptId
    from propstore.world.overlay import OverlayWorld
    from propstore.world.types import SyntheticClaim

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    synthetics = [
        SyntheticClaim(
            id=spec.claim_id,
            concept_id=ConceptId(spec.concept_id),
            type=ClaimType(spec.claim_type),
            value=spec.value,
            conditions=list(to_cel_exprs(spec.conditions)),
        )
        for spec in request.add_claims
    ]
    resolved_remove = [
        str(claim.id) if (claim := world.get_claim(claim_id)) is not None else claim_id
        for claim_id in request.remove_claim_ids
    ]
    overlay = OverlayWorld(
        bound,
        remove=resolved_remove,
        add=synthetics,
    )
    diff = overlay.diff()
    return WorldHypotheticalReport(
        changes=tuple(
            WorldHypotheticalChangeLine(
                concept_display_id=world_concept_display_id(world, concept_id),
                base_status=base.status,
                hypothetical_status=hypothetical.status,
            )
            for concept_id, (base, hypothetical) in diff.items()
        ),
        extension_diff=_diff_grounded_extension(world, bound, overlay),
    )


@dataclass(frozen=True)
class _GroundedExtensionSnapshot:
    counts: WorldHypotheticalExtensionCounts
    labels_by_claim_id: dict[str, str]


def _grounded_extension_snapshot(
    store,
    active_claim_ids: set[str],
) -> _GroundedExtensionSnapshot:
    from argumentation.dung import grounded_extension, range_of
    from propstore.claim_graph import build_argumentation_framework

    framework = build_argumentation_framework(store, active_claim_ids)
    accepted = set(grounded_extension(framework))
    defeated = set(range_of(frozenset(accepted), framework.defeats)) - accepted
    undecided = set(framework.arguments) - accepted - defeated
    labels_by_claim_id = {
        **{claim_id: "accepted" for claim_id in accepted},
        **{claim_id: "defeated" for claim_id in defeated},
        **{claim_id: "undecided" for claim_id in undecided},
    }
    return _GroundedExtensionSnapshot(
        counts=WorldHypotheticalExtensionCounts(
            active=len(framework.arguments),
            accepted=len(accepted),
            defeated=len(defeated),
            undecided=len(undecided),
        ),
        labels_by_claim_id=labels_by_claim_id,
    )


def _diff_grounded_extension(
    world: WorldQuery,
    bound: BeliefSpace,
    overlay: OverlayWorld,
) -> WorldHypotheticalExtensionDiff:
    base_active_ids = {str(claim.id) for claim in bound.active_claims()}
    hypothetical_active_ids = {str(claim.id) for claim in overlay.active_claims()}
    before = _grounded_extension_snapshot(world, base_active_ids)
    after = _grounded_extension_snapshot(overlay, hypothetical_active_ids)

    grouped: dict[tuple[str, str], list[str]] = {}
    for claim_id in sorted(base_active_ids | hypothetical_active_ids):
        before_status = before.labels_by_claim_id.get(claim_id, "absent")
        after_status = after.labels_by_claim_id.get(claim_id, "absent")
        if before_status == after_status:
            continue
        grouped.setdefault((before_status, after_status), []).append(
            _hypothetical_claim_display_id(world, overlay, claim_id)
        )

    transitions = tuple(
        WorldHypotheticalExtensionTransition(
            from_status=from_status,
            to_status=to_status,
            claim_ids=tuple(claim_ids),
        )
        for (from_status, to_status), claim_ids in sorted(grouped.items())
    )
    return WorldHypotheticalExtensionDiff(
        before=before.counts,
        after=after.counts,
        unchanged=not transitions,
        transitions=transitions,
    )


def _hypothetical_claim_display_id(
    world: WorldQuery,
    overlay: OverlayWorld,
    claim_id: str,
) -> str:
    claim = world.get_claim(claim_id)
    if claim is None:
        claim = overlay.get_claim(claim_id)
    if claim is None:
        return claim_id
    return world_claim_display_id(claim)


def resolve_world_value(
    world: WorldQuery,
    request: WorldResolveRequest,
) -> WorldResolveReport:
    from propstore.core.environment import Environment
    from propstore.world.resolution import resolve

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
    from propstore.world.types import DerivedResult, ResolutionStrategy

    resolved = resolve_world_target(world, request.concept_id)
    strategy = ResolutionStrategy(request.strategy) if request.strategy else None
    result = world.chain_query(resolved, strategy=strategy, **dict(request.bindings))
    value = (
        result.result.value
        if isinstance(result.result, DerivedResult) and result.result.value is not None
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
