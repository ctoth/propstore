"""Application-layer semantic neighborhood report (focus = claim).

:func:`build_semantic_neighborhood` renders the argumentative neighborhood of a
focus claim: its supporters and attackers (typed stances incident to it), the
claims sharing its concept, and a per-section :class:`ViewState` with
natural-language sentences. Only ``focus_kind="claim"`` is implemented; concept /
source / worldline focuses raise :class:`SemanticNeighborhoodUnsupportedFocusError`
(honest "not implemented", never a fabricated empty neighborhood). Visibility is
render-time: a focus claim hidden by the policy raises
:class:`ClaimViewBlockedError`, and only policy-visible neighbors are walked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from propstore.app.claim_views import (
    ClaimViewBlockedError,
    ClaimViewUnknownClaimError,
    claim_display_id,
)
from propstore.app.rendering import RenderPolicySummary, summarize_render_policy
from propstore.app.view_state import ViewState
from propstore.families.claims import Claim
from propstore.families.relations import Stance
from propstore.reporting import JsonReportMixin
from propstore.stances import StanceType
from propstore.world import RenderPolicy, WorldQuery

SemanticFocusKind: TypeAlias = Literal["claim", "concept", "source", "worldline"]

_SUPPORT_STANCES = frozenset({StanceType.SUPPORTS, StanceType.EXPLAINS})
_ATTACK_STANCES = frozenset(
    {StanceType.REBUTS, StanceType.UNDERCUTS, StanceType.UNDERMINES}
)


class SemanticNeighborhoodAppError(Exception):
    """Base class for expected semantic-neighborhood failures."""


class SemanticNeighborhoodUnsupportedFocusError(SemanticNeighborhoodAppError):
    def __init__(self, focus_kind: str) -> None:
        super().__init__(f"Semantic neighborhoods for {focus_kind!r} are not implemented.")
        self.focus_kind = focus_kind


@dataclass(frozen=True)
class SemanticFocus:
    kind: str
    focus_id: str
    display_id: str
    sentence: str


@dataclass(frozen=True)
class SemanticFocusStatus:
    state: ViewState
    visible_under_policy: bool
    reason: str


@dataclass(frozen=True)
class SemanticMove:
    kind: str
    target_count: int
    state: ViewState
    sentence: str
    target_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticNode:
    kind: str
    node_id: str
    display_id: str
    sentence: str


@dataclass(frozen=True)
class SemanticEdge:
    source_id: str
    target_id: str
    edge_kind: str
    sentence: str


@dataclass(frozen=True)
class SemanticNeighborhoodRow:
    section: str
    subject_id: str
    relation: str
    object_id: str
    state: ViewState
    sentence: str


@dataclass(frozen=True)
class SemanticNeighborhoodReport(JsonReportMixin):
    focus: SemanticFocus
    status: SemanticFocusStatus
    moves: tuple[SemanticMove, ...]
    nodes: tuple[SemanticNode, ...]
    edges: tuple[SemanticEdge, ...]
    table_rows: tuple[SemanticNeighborhoodRow, ...]
    prose_summary: str
    render_policy: RenderPolicySummary


def build_semantic_neighborhood(
    world: WorldQuery,
    focus_kind: SemanticFocusKind,
    focus_id: str,
    *,
    policy: RenderPolicy,
    limit: int = 50,
) -> SemanticNeighborhoodReport:
    if focus_kind != "claim":
        raise SemanticNeighborhoodUnsupportedFocusError(focus_kind)
    claim = world.get_claim(focus_id)
    if claim is None:
        raise ClaimViewUnknownClaimError(focus_id)
    visible_ids = {str(row.claim_id) for row in world.claims_with_policy(None, policy)}
    focus_claim_id = str(claim.claim_id)
    if focus_claim_id not in visible_ids:
        raise ClaimViewBlockedError(focus_claim_id)

    stances = _visible_incident_stances(world, focus_claim_id, visible_ids)
    supporters = tuple(
        str(stance.source_claim_id)
        for stance in stances
        if str(stance.target_claim_id) == focus_claim_id
        and stance.stance_type in _SUPPORT_STANCES
    )
    attackers = tuple(
        str(stance.source_claim_id)
        for stance in stances
        if str(stance.target_claim_id) == focus_claim_id
        and stance.stance_type in _ATTACK_STANCES
    )
    shared = _shared_concept_ids(world, claim, policy, limit)

    focus = SemanticFocus(
        kind="claim",
        focus_id=focus_claim_id,
        display_id=claim_display_id(claim),
        sentence=f"You are on claim {claim_display_id(claim)}.",
    )
    moves = _moves(claim, supporters, attackers, shared)
    nodes = _nodes(world, claim, stances, shared, limit)
    edges = _edges(world, stances, focus_claim_id, limit)
    rows = _rows(claim, supporters, attackers, shared, edges)
    prose = (
        f"Claim {claim_display_id(claim)} has {len(supporters)} supporters, "
        f"{len(attackers)} attackers, and {len(shared)} visible claims sharing "
        "its concept under the current render policy."
    )
    return SemanticNeighborhoodReport(
        focus=focus,
        status=SemanticFocusStatus(
            state=ViewState.KNOWN,
            visible_under_policy=True,
            reason="Focus claim is visible under the current render policy.",
        ),
        moves=moves,
        nodes=nodes,
        edges=edges,
        table_rows=rows,
        prose_summary=prose,
        render_policy=summarize_render_policy(policy),
    )


def _visible_incident_stances(
    world: WorldQuery, focus_id: str, visible_ids: set[str]
) -> tuple[Stance, ...]:
    incident: list[Stance] = []
    for stance in world.explain(focus_id):
        if stance.stance_type is None:
            continue
        source = stance.source_claim_id
        target = stance.target_claim_id
        if source is None or target is None:
            continue
        if source not in visible_ids or target not in visible_ids:
            continue
        incident.append(stance)
    return tuple(incident)


def _moves(
    claim: Claim,
    supporters: tuple[str, ...],
    attackers: tuple[str, ...],
    shared: tuple[str, ...],
) -> tuple[SemanticMove, ...]:
    has_condition = bool(claim.conditions)
    condition_count = 1 if has_condition else 0
    return (
        SemanticMove(
            kind="supporters",
            target_count=len(supporters),
            state=ViewState.KNOWN,
            sentence=f"{len(supporters)} claims support this claim.",
            target_ids=supporters,
        ),
        SemanticMove(
            kind="attackers",
            target_count=len(attackers),
            state=ViewState.KNOWN,
            sentence=f"{len(attackers)} claims attack this claim.",
            target_ids=attackers,
        ),
        SemanticMove(
            kind="assumptions",
            target_count=0,
            state=ViewState.UNAVAILABLE,
            sentence="Assumption traversal is unavailable in the current neighborhood report.",
        ),
        SemanticMove(
            kind="conditions",
            target_count=condition_count,
            state=ViewState.KNOWN if has_condition else ViewState.VACUOUS,
            sentence=(
                "The claim has an explicit condition expression."
                if has_condition
                else "The claim has vacuous conditions."
            ),
        ),
        SemanticMove(
            kind="provenance",
            target_count=0,
            state=ViewState.MISSING,
            sentence="The claim record carries no provenance.",
        ),
        SemanticMove(
            kind="shared_concept",
            target_count=len(shared),
            state=ViewState.KNOWN,
            sentence=f"{len(shared)} visible claims share this concept.",
            target_ids=shared,
        ),
        SemanticMove(
            kind="policy_alternatives",
            target_count=0,
            state=ViewState.UNAVAILABLE,
            sentence="Policy alternatives are unavailable in the current neighborhood report.",
        ),
    )


def _nodes(
    world: WorldQuery,
    claim: Claim,
    stances: tuple[Stance, ...],
    shared: tuple[str, ...],
    limit: int,
) -> tuple[SemanticNode, ...]:
    ids: list[str] = [str(claim.claim_id)]
    for stance in stances:
        ids.append(str(stance.source_claim_id))
        ids.append(str(stance.target_claim_id))
    ids.extend(shared)

    nodes: list[SemanticNode] = []
    seen: set[str] = set()
    for claim_id in ids:
        if claim_id in seen:
            continue
        seen.add(claim_id)
        display = _display_for_id(world, claim_id)
        nodes.append(
            SemanticNode(
                kind="claim",
                node_id=claim_id,
                display_id=display,
                sentence=f"Claim node {display}.",
            )
        )
        if len(nodes) >= limit:
            break
    return tuple(nodes)


def _edges(
    world: WorldQuery, stances: tuple[Stance, ...], focus_id: str, limit: int
) -> tuple[SemanticEdge, ...]:
    edges: list[SemanticEdge] = []
    for stance in stances:
        if stance.stance_type is None:
            continue
        source_id = str(stance.source_claim_id)
        target_id = str(stance.target_claim_id)
        source_display = _display_for_id(world, source_id)
        target_display = _display_for_id(world, target_id)
        relation = _stance_verb(stance.stance_type)
        if target_id == focus_id:
            sentence = f"Claim {source_display} {relation} the focus claim {target_display}."
        elif source_id == focus_id:
            sentence = f"Focus claim {source_display} {relation} claim {target_display}."
        else:
            sentence = f"Claim {source_display} {relation} claim {target_display}."
        edges.append(
            SemanticEdge(
                source_id=source_id,
                target_id=target_id,
                edge_kind=stance.stance_type.value,
                sentence=sentence,
            )
        )
        if len(edges) >= limit:
            break
    return tuple(edges)


def _rows(
    claim: Claim,
    supporters: tuple[str, ...],
    attackers: tuple[str, ...],
    shared: tuple[str, ...],
    edges: tuple[SemanticEdge, ...],
) -> tuple[SemanticNeighborhoodRow, ...]:
    focus_id = str(claim.claim_id)
    rows: list[SemanticNeighborhoodRow] = []
    for supporter in supporters:
        rows.append(
            SemanticNeighborhoodRow(
                section="supporters",
                subject_id=supporter,
                relation="supports",
                object_id=focus_id,
                state=ViewState.KNOWN,
                sentence=f"Claim {supporter} supports claim {focus_id}.",
            )
        )
    for attacker in attackers:
        rows.append(
            SemanticNeighborhoodRow(
                section="attackers",
                subject_id=attacker,
                relation="attacks",
                object_id=focus_id,
                state=ViewState.KNOWN,
                sentence=f"Claim {attacker} attacks claim {focus_id}.",
            )
        )
    has_condition = bool(claim.conditions)
    rows.append(
        SemanticNeighborhoodRow(
            section="conditions",
            subject_id=focus_id,
            relation="has_conditions",
            object_id="; ".join(claim.conditions) if has_condition else "vacuous",
            state=ViewState.KNOWN if has_condition else ViewState.VACUOUS,
            sentence=(
                f"Claim {focus_id} has condition expression {'; '.join(claim.conditions)}."
                if has_condition
                else f"Claim {focus_id} has vacuous conditions."
            ),
        )
    )
    rows.append(
        SemanticNeighborhoodRow(
            section="provenance",
            subject_id=focus_id,
            relation="has_provenance",
            object_id="missing",
            state=ViewState.MISSING,
            sentence=f"Claim {focus_id} carries no provenance on the claim record.",
        )
    )
    for shared_id in shared:
        rows.append(
            SemanticNeighborhoodRow(
                section="shared_concept",
                subject_id=focus_id,
                relation="shares_concept_with",
                object_id=shared_id,
                state=ViewState.KNOWN,
                sentence=f"Claim {focus_id} shares its concept with claim {shared_id}.",
            )
        )
    for edge in edges:
        rows.append(
            SemanticNeighborhoodRow(
                section="raw_graph_projection",
                subject_id=edge.source_id,
                relation=edge.edge_kind,
                object_id=edge.target_id,
                state=ViewState.KNOWN,
                sentence=edge.sentence,
            )
        )
    return tuple(rows)


def _shared_concept_ids(
    world: WorldQuery, claim: Claim, policy: RenderPolicy, limit: int
) -> tuple[str, ...]:
    if claim.output_concept is None:
        return ()
    related: list[str] = []
    for row in world.claims_with_policy(claim.output_concept, policy):
        claim_id = str(row.claim_id)
        if claim_id != str(claim.claim_id):
            related.append(claim_id)
        if len(related) >= limit:
            break
    return tuple(related)


def _stance_verb(stance_type: StanceType) -> str:
    verbs = {
        StanceType.SUPPORTS: "supports",
        StanceType.EXPLAINS: "explains",
        StanceType.REBUTS: "rebuts",
        StanceType.UNDERCUTS: "undercuts",
        StanceType.UNDERMINES: "undermines",
        StanceType.SUPERSEDES: "supersedes",
        StanceType.ABSTAIN: "abstains from",
        StanceType.PROPER_DEFEATER: "properly defeats",
        StanceType.BLOCKING_DEFEATER: "blocks",
    }
    return verbs.get(stance_type, "has no stance on")


def _display_for_id(world: WorldQuery, claim_id: str) -> str:
    claim = world.get_claim(claim_id)
    return claim_id if claim is None else claim_display_id(claim)
