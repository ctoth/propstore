"""Owner-layer world reasoning-report tier (Phase 10-0b).

Typed request/report builders over the :class:`~propstore.world.WorldQuery`
reader — the bulk of the ``pks world`` family's owner core. Each function takes a
``WorldQuery`` (and a :class:`~propstore.world.RenderPolicy` where a render-time
view is involved) and returns a JSON-ready report. No Click / FastAPI here: the
CLI/web adapters construct the request and render the report.

This module is the *reasoning* tier; the low-level ``select_*`` sidecar readers
live alongside it in :mod:`propstore.world.queries` and are untouched. Reports are
retyped over the charter (``Claim`` / ``Concept`` / ``Stance``) directly — there
is no ``*Row`` / ``*Document`` projection-model second spelling.

Honest ignorance: a concept that does not resolve raises
:class:`UnknownConceptError`, a missing claim raises :class:`UnknownClaimError`,
and a resolution that cannot run raises :class:`WorldResolveError` — never a
fabricated value.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import Environment, WorldStore
from propstore.core.scalars import ScalarValue
from propstore.families.claims import Claim, ClaimType
from propstore.reporting import JsonReportMixin
from propstore.world import OverlayWorld, SyntheticClaim, resolve
from propstore.world.bound import BoundWorld
from propstore.world.types import RenderPolicy, ResolutionStrategy

if TYPE_CHECKING:
    from propstore.world import WorldQuery


# ── failures ─────────────────────────────────────────────────────────────────


class WorldQueryError(Exception):
    """Base class for expected world reasoning-report failures."""


class UnknownConceptError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown concept: {target}")
        self.target = target


class UnknownClaimError(WorldQueryError):
    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown claim: {target}")
        self.target = target


class WorldResolveError(WorldQueryError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ── shared display helpers ───────────────────────────────────────────────────


def _value_concept_id(claim: Claim) -> str | None:
    """The concept a claim's value is about: output, else target, else first ref."""

    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return str(candidate)
    return None


def _concept_display_id(world: WorldQuery, concept_id: str) -> str:
    return concept_id


def _concept_canonical_name(world: WorldQuery, concept_id: str) -> str | None:
    concept = world.get_concept(concept_id)
    return None if concept is None else concept.canonical_name


def _claim_value_display(claim: Claim) -> str:
    if claim.unit:
        return f"value={claim.value} {claim.unit}"
    return f"value={claim.value}"


def _active_value_display(active: ActiveClaim, claim: Claim | None) -> str:
    if claim is not None:
        return _claim_value_display(claim)
    return f"value={active.value}"


def _claim_conditions_display(claim: Claim | None) -> str:
    if claim is None or not claim.conditions:
        return "[]"
    return str(list(claim.conditions))


def _resolve_concept_target(world: WorldQuery, target: str) -> str:
    return world.resolve_concept(target) or target


# ── world status ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorldStatusRequest:
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldStatusReport(JsonReportMixin):
    concept_count: int
    visible_claim_count: int
    conflict_count: int
    diagnostic_count: int
    stance_count: int


def get_world_status(
    world: WorldQuery,
    request: WorldStatusRequest,
) -> WorldStatusReport:
    """Aggregate counts for the world under ``request.policy``.

    The visible-claim and diagnostic counts are render-time views (draft/blocked
    and quarantine rows are present in the sidecar but filtered by the default
    policy); the concept/conflict/stance counts are storage totals.
    """

    stats = world.stats()
    return WorldStatusReport(
        concept_count=stats.concepts,
        visible_claim_count=len(world.claims_with_policy(None, request.policy)),
        conflict_count=stats.conflicts,
        diagnostic_count=len(world.build_diagnostics(request.policy)),
        stance_count=len(world.all_claim_stances()),
    )


# ── concept query ────────────────────────────────────────────────────────────


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
class WorldConceptQueryReport(JsonReportMixin):
    canonical_name: str
    concept_display_id: str
    claims: tuple[WorldClaimLine, ...]
    diagnostics: tuple[WorldDiagnosticLine, ...]


def query_world_concept(
    world: WorldQuery,
    request: WorldConceptQueryRequest,
) -> WorldConceptQueryReport:
    """The policy-visible claims and quarantine diagnostics about one concept."""

    resolved = world.resolve_concept(request.target)
    if resolved is None:
        raise UnknownConceptError(request.target)
    concept = world.get_concept(resolved)
    if concept is None:
        raise UnknownConceptError(request.target)
    claims = tuple(
        WorldClaimLine(
            display_id=str(claim.claim_id),
            claim_type=str(claim.claim_type or ClaimType.UNKNOWN),
            value_display=_claim_value_display(claim),
            conditions=_claim_conditions_display(claim),
        )
        for claim in world.claims_with_policy(resolved, request.policy)
    )
    diagnostics = tuple(
        WorldDiagnosticLine(
            target=str(diagnostic.claim_id or diagnostic.source_ref or "?"),
            diagnostic_kind=str(diagnostic.diagnostic_kind),
            message=str(diagnostic.message),
        )
        for diagnostic in world.build_diagnostics(request.policy)
    )
    return WorldConceptQueryReport(
        canonical_name=concept.canonical_name,
        concept_display_id=_concept_display_id(world, resolved),
        claims=claims,
        diagnostics=diagnostics,
    )


# ── bound world ──────────────────────────────────────────────────────────────


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


@dataclass(frozen=True)
class WorldBindConceptReport(JsonReportMixin):
    concept_display_id: str
    status: str
    claims: tuple[WorldBindClaimLine, ...]


@dataclass(frozen=True)
class WorldBindActiveReport(JsonReportMixin):
    active_claim_count: int
    claims: tuple[WorldBindClaimLine, ...]


WorldBindReport = WorldBindConceptReport | WorldBindActiveReport


def query_bound_world(
    world: WorldQuery,
    request: WorldBindRequest,
) -> WorldBindReport:
    """Bind the world to ``request.bindings`` and report active claims.

    With a ``target`` concept, reports that concept's value status and the active
    claims backing it; without one, reports every active claim under the bindings.
    """

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    if request.target is not None:
        resolved = _resolve_concept_target(world, request.target)
        result = bound.value_of(resolved)
        return WorldBindConceptReport(
            concept_display_id=_concept_display_id(world, resolved),
            status=str(result.status),
            claims=tuple(_bind_line(world, active) for active in result.claims),
        )

    active_claims = bound.active_claims()
    return WorldBindActiveReport(
        active_claim_count=len(active_claims),
        claims=tuple(_bind_line(world, active) for active in active_claims),
    )


def _bind_line(world: WorldQuery, active: ActiveClaim) -> WorldBindClaimLine:
    claim = world.get_claim(str(active.claim_id))
    concept_id = None if claim is None else _value_concept_id(claim)
    return WorldBindClaimLine(
        display_id=str(active.claim_id),
        concept_display_id=(
            None if concept_id is None else _concept_display_id(world, concept_id)
        ),
        value_display=_active_value_display(active, claim),
        conditions=_claim_conditions_display(claim),
    )


# ── explain ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorldExplainRequest:
    claim_id: str


@dataclass(frozen=True)
class WorldStanceLine:
    source_display_id: str
    stance_type: str
    target_display_id: str
    confidence: float | None
    nested: bool


@dataclass(frozen=True)
class WorldExplainReport(JsonReportMixin):
    claim_display_id: str
    claim_type: str
    concept_display_id: str | None
    value: ScalarValue | None
    stances: tuple[WorldStanceLine, ...]


def explain_world_claim(
    world: WorldQuery,
    request: WorldExplainRequest,
) -> WorldExplainReport:
    """The claim's value, focus concept, and the stances incident to it."""

    claim = world.get_claim(request.claim_id)
    if claim is None:
        raise UnknownClaimError(request.claim_id)
    claim_id = str(claim.claim_id)
    concept_id = _value_concept_id(claim)
    stances: list[WorldStanceLine] = []
    for stance in world.explain(claim_id):
        source_id = str(stance.source_claim_id)
        target_id = str(stance.target_claim_id)
        stances.append(
            WorldStanceLine(
                source_display_id=source_id,
                stance_type=str(stance.stance_type),
                target_display_id=target_id,
                confidence=stance.confidence,
                nested=source_id != claim_id,
            )
        )
    return WorldExplainReport(
        claim_display_id=claim_id,
        claim_type=str(claim.claim_type or ClaimType.UNKNOWN),
        concept_display_id=(
            None if concept_id is None else _concept_display_id(world, concept_id)
        ),
        value=claim.value,
        stances=tuple(stances),
    )


# ── algorithms ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorldAlgorithmsRequest:
    concept: str | None = None


@dataclass(frozen=True)
class WorldAlgorithmLine:
    claim_id: str
    name: str
    concept_id: str


@dataclass(frozen=True)
class WorldAlgorithmsReport(JsonReportMixin):
    algorithms: tuple[WorldAlgorithmLine, ...]


def list_world_algorithms(
    world: WorldQuery,
    request: WorldAlgorithmsRequest,
) -> WorldAlgorithmsReport:
    """Every authored algorithm claim, optionally filtered to one focus concept."""

    concept_filter = (
        None
        if request.concept is None
        else _resolve_concept_target(world, request.concept)
    )
    algorithms = [
        claim
        for claim in world.claims_for(None)
        if claim.claim_type is ClaimType.ALGORITHM
        and (concept_filter is None or _value_concept_id(claim) == concept_filter)
    ]
    return WorldAlgorithmsReport(
        algorithms=tuple(
            WorldAlgorithmLine(
                claim_id=str(claim.claim_id),
                name=claim.name or (claim.body or "")[:25] or "?",
                concept_id=_value_concept_id(claim) or "-",
            )
            for claim in algorithms
        )
    )


# ── derive ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorldDeriveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldDeriveReport(JsonReportMixin):
    concept_id: str
    status: str
    value: float | None
    formula: str | None
    input_values: dict[str, float]
    exactness: str | None


def derive_world_value(
    world: WorldQuery,
    request: WorldDeriveRequest,
) -> WorldDeriveReport:
    """Derive a concept's value from its parameterization under the bindings."""

    resolved = _resolve_concept_target(world, request.concept_id)
    bound = world.bind(
        Environment(bindings=dict(request.bindings)),
        policy=request.policy,
    )
    result = bound.derived_value(resolved)
    return WorldDeriveReport(
        concept_id=resolved,
        status=str(result.status),
        value=result.value,
        formula=result.formula,
        input_values={str(key): value for key, value in result.input_values.items()},
        exactness=None if result.exactness is None else result.exactness.value,
    )


# ── resolve ──────────────────────────────────────────────────────────────────


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
    status: str
    value: ScalarValue | None
    winning_claim_display_id: str | None
    strategy: str | None
    reason: str | None
    acceptance_probs: tuple[WorldAcceptanceProbabilityLine, ...]


def resolve_world_value(
    world: WorldQuery,
    request: WorldResolveRequest,
) -> WorldResolveReport:
    """Resolve a (possibly conflicted) concept under the request's render policy."""

    resolved = _resolve_concept_target(world, request.concept_id)
    bound = world.bind(Environment(bindings=dict(request.bindings)))
    try:
        result = resolve(bound, resolved, policy=request.policy, world=world)
    except (ValueError, NotImplementedError) as exc:
        raise WorldResolveError(str(exc)) from exc

    winner_id = (
        None if result.winning_claim_id is None else str(result.winning_claim_id)
    )
    acceptance = (
        tuple(
            WorldAcceptanceProbabilityLine(claim_id=str(claim_id), probability=prob)
            for claim_id, prob in sorted(result.acceptance_probs.items())
        )
        if result.acceptance_probs
        else ()
    )
    return WorldResolveReport(
        concept_display_id=_concept_display_id(world, resolved),
        status=str(result.status),
        value=result.value,
        winning_claim_display_id=winner_id,
        strategy=result.strategy,
        reason=result.reason,
        acceptance_probs=acceptance,
    )


# ── chain ────────────────────────────────────────────────────────────────────


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
    value: ScalarValue | None
    source: str


@dataclass(frozen=True)
class WorldChainReport(JsonReportMixin):
    target: WorldChainConceptLine
    status: str
    value: float | None
    steps: tuple[WorldChainStepLine, ...]


def _chain_concept_line(world: WorldQuery, concept_id: str) -> WorldChainConceptLine:
    return WorldChainConceptLine(
        display_id=_concept_display_id(world, concept_id),
        canonical_name=_concept_canonical_name(world, concept_id),
    )


def query_world_chain(
    world: WorldQuery,
    request: WorldChainRequest,
) -> WorldChainReport:
    """Backward-chain a target concept's value through its parameterization graph."""

    from propstore.world.types import DerivedResult

    resolved = _resolve_concept_target(world, request.concept_id)
    strategy = (
        ResolutionStrategy(request.strategy) if request.strategy is not None else None
    )
    result = world.chain_query(resolved, strategy, **dict(request.bindings))
    value = result.result.value if isinstance(result.result, DerivedResult) else None
    return WorldChainReport(
        target=_chain_concept_line(world, resolved),
        status=str(result.result.status),
        value=value,
        steps=tuple(
            WorldChainStepLine(
                concept=_chain_concept_line(world, str(step.concept_id)),
                value=step.value,
                source=step.source,
            )
            for step in result.steps
        ),
    )


# ── hypothetical diff ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorldHypotheticalSyntheticClaimSpec:
    claim_id: str
    concept_id: str
    claim_type: str = "parameter"
    value: ScalarValue | None = None
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorldHypotheticalRequest:
    bindings: Mapping[str, str]
    remove_claim_ids: tuple[str, ...] = ()
    add_claims: tuple[WorldHypotheticalSyntheticClaimSpec, ...] = ()


@dataclass(frozen=True)
class WorldHypotheticalChangeLine:
    concept_display_id: str
    base_status: str
    hypothetical_status: str


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


def diff_hypothetical_world(
    world: WorldQuery,
    request: WorldHypotheticalRequest,
) -> WorldHypotheticalReport:
    """Overlay synthetic/removed claims and report the value + grounded changes.

    Overlay semantics, not a Pearl intervention: the parameterization graph is
    preserved and conflict resolution decides winners. ``changes`` are the
    concepts whose value status/values move; ``extension_diff`` is the grounded
    Dung extension before vs after the overlay.
    """

    from condition_ir import to_cel_exprs

    from propstore.core.id_types import to_concept_id

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    synthetics = [
        SyntheticClaim(
            id=spec.claim_id,
            concept_id=to_concept_id(spec.concept_id),
            type=ClaimType(spec.claim_type),
            value=spec.value,
            conditions=list(to_cel_exprs(spec.conditions)),
        )
        for spec in request.add_claims
    ]
    resolved_remove = [
        world.resolve_claim(claim_id) or claim_id
        for claim_id in request.remove_claim_ids
    ]
    overlay = OverlayWorld(bound, remove=resolved_remove, add=synthetics)
    diff = overlay.diff()
    changes = tuple(
        WorldHypotheticalChangeLine(
            concept_display_id=_concept_display_id(world, concept_id),
            base_status=str(base.status),
            hypothetical_status=str(hypothetical.status),
        )
        for concept_id, (base, hypothetical) in diff.items()
    )
    return WorldHypotheticalReport(
        changes=changes,
        extension_diff=_diff_grounded_extension(world, bound, overlay),
    )


@dataclass(frozen=True)
class _GroundedExtensionSnapshot:
    counts: WorldHypotheticalExtensionCounts
    labels_by_claim_id: dict[str, str]


def _grounded_extension_snapshot(
    store: WorldStore,
    active_claim_ids: set[str],
) -> _GroundedExtensionSnapshot:
    from argumentation.core.dung import grounded_extension, range_of

    from propstore.claim_graph import build_argumentation_framework

    framework = build_argumentation_framework(store, active_claim_ids)
    accepted = grounded_extension(framework)
    defeated = range_of(accepted, framework.defeats) - accepted
    undecided = framework.arguments - accepted - defeated
    labels: dict[str, str] = {}
    for claim_id in accepted:
        labels[claim_id] = "accepted"
    for claim_id in defeated:
        labels[claim_id] = "defeated"
    for claim_id in undecided:
        labels[claim_id] = "undecided"
    return _GroundedExtensionSnapshot(
        counts=WorldHypotheticalExtensionCounts(
            active=len(framework.arguments),
            accepted=len(accepted),
            defeated=len(defeated),
            undecided=len(undecided),
        ),
        labels_by_claim_id=labels,
    )


def _diff_grounded_extension(
    world: WorldQuery,
    bound: BoundWorld,
    overlay: OverlayWorld,
) -> WorldHypotheticalExtensionDiff:
    base_active_ids = {str(claim.claim_id) for claim in bound.active_claims()}
    hypothetical_active_ids = {str(claim.claim_id) for claim in overlay.active_claims()}
    before = _grounded_extension_snapshot(world, base_active_ids)
    after = _grounded_extension_snapshot(overlay.store, hypothetical_active_ids)

    grouped: dict[tuple[str, str], list[str]] = {}
    for claim_id in sorted(base_active_ids | hypothetical_active_ids):
        before_status = before.labels_by_claim_id.get(claim_id, "absent")
        after_status = after.labels_by_claim_id.get(claim_id, "absent")
        if before_status == after_status:
            continue
        grouped.setdefault((before_status, after_status), []).append(claim_id)

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
