"""Application-layer semantic neighborhood reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from propstore.app.claim_views import ClaimViewBlockedError, ClaimViewUnknownClaimError
from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicySummary,
    build_render_policy,
    summarize_render_policy,
)
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    repository_view_label,
)
from propstore.app.world import open_app_world_model
from propstore.repository import Repository
from propstore.stances import StanceType

SemanticFocusKind: TypeAlias = Literal["claim", "concept", "source", "worldline"]
SemanticState: TypeAlias = Literal[
    "known",
    "unknown",
    "vacuous",
    "blocked",
    "unavailable",
]


class SemanticNeighborhoodAppError(Exception):
    """Base class for expected semantic-neighborhood failures."""


class SemanticNeighborhoodUnsupportedFocusError(SemanticNeighborhoodAppError):
    def __init__(self, focus_kind: str) -> None:
        super().__init__(f"Semantic neighborhoods for {focus_kind!r} are not implemented.")
        self.focus_kind = focus_kind


@dataclass(frozen=True)
class SemanticNeighborhoodRequest:
    focus_kind: SemanticFocusKind
    focus_id: str
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)
    repository_view: AppRepositoryViewRequest = field(default_factory=AppRepositoryViewRequest)
    limit: int = 50


@dataclass(frozen=True)
class SemanticFocus:
    kind: SemanticFocusKind
    focus_id: str
    display_id: str
    sentence: str


@dataclass(frozen=True)
class SemanticFocusStatus:
    state: SemanticState
    visible_under_policy: bool
    reason: str


@dataclass(frozen=True)
class SemanticMove:
    kind: str
    target_count: int
    state: SemanticState
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
    state: SemanticState
    sentence: str


@dataclass(frozen=True)
class SemanticNeighborhoodReport:
    focus: SemanticFocus
    render_policy: RenderPolicySummary
    status: SemanticFocusStatus
    moves: tuple[SemanticMove, ...]
    nodes: tuple[SemanticNode, ...]
    edges: tuple[SemanticEdge, ...]
    table_rows: tuple[SemanticNeighborhoodRow, ...]
    prose_summary: str


def build_semantic_neighborhood(
    repo: Repository,
    request: SemanticNeighborhoodRequest,
) -> SemanticNeighborhoodReport:
    if request.focus_kind != "claim":
        raise SemanticNeighborhoodUnsupportedFocusError(request.focus_kind)
    _ = repository_view_label(request.repository_view)
    policy = build_render_policy(request.render_policy)
    with open_app_world_model(repo) as world:
        claim = world.get_claim(request.focus_id)
        if claim is None:
            raise ClaimViewUnknownClaimError(request.focus_id)
        visible_ids = {str(row.claim_id) for row in world.claims_with_policy(None, policy)}
        focus_id = str(claim.claim_id)
        if focus_id not in visible_ids:
            raise ClaimViewBlockedError(focus_id)
        focus = SemanticFocus(
            kind="claim",
            focus_id=focus_id,
            display_id=_claim_display_id(claim),
            sentence=f"You are on claim {_claim_display_id(claim)}.",
        )
        status = _focus_status(True)
        stances = world.claim_stances_with_policy(focus_id, policy)
        supporters = tuple(
            str(stance.claim_id)
            for stance in stances
            if str(stance.target_claim_id) == focus_id
            and stance.stance_type in {StanceType.SUPPORTS, StanceType.EXPLAINS}
        )
        attackers = tuple(
            str(stance.claim_id)
            for stance in stances
            if str(stance.target_claim_id) == focus_id
            and stance.stance_type
            in {StanceType.REBUTS, StanceType.UNDERCUTS, StanceType.UNDERMINES}
        )
        shared_concept_ids = _shared_concept_ids(world, claim, policy, request.limit)
        moves = _moves(claim, supporters, attackers, shared_concept_ids)
        nodes = _nodes(world, claim, stances, shared_concept_ids, request.limit)
        edges = _edges(world, stances, focus_id, request.limit)
        rows = _rows(claim, supporters, attackers, shared_concept_ids, edges)
        prose = (
            f"Claim {_claim_display_id(claim)} has {len(supporters)} supporters, "
            f"{len(attackers)} attackers, and {len(shared_concept_ids)} visible claims "
            "sharing its concept under the current render policy."
        )
        return SemanticNeighborhoodReport(
            focus=focus,
            render_policy=summarize_render_policy(policy),
            status=status,
            moves=moves,
            nodes=nodes,
            edges=edges,
            table_rows=rows,
            prose_summary=prose,
        )


def _focus_status(visible: bool) -> SemanticFocusStatus:
    if visible:
        return SemanticFocusStatus(
            state="known",
            visible_under_policy=True,
            reason="Focus claim is visible under the current render policy.",
        )
    return SemanticFocusStatus(
        state="blocked",
        visible_under_policy=False,
        reason="Focus claim is blocked under the current render policy.",
    )


def _moves(
    claim,
    supporters: tuple[str, ...],
    attackers: tuple[str, ...],
    shared_concept_ids: tuple[str, ...],
) -> tuple[SemanticMove, ...]:
    condition_state: SemanticState = "known" if claim.conditions_cel else "vacuous"
    provenance_state: SemanticState = "known" if claim.provenance is not None else "unknown"
    provenance_count = 1 if claim.provenance is not None else 0
    condition_count = 1 if claim.conditions_cel else 0
    return (
        SemanticMove(
            kind="supporters",
            target_count=len(supporters),
            state="known",
            sentence=f"{len(supporters)} claims support this claim.",
            target_ids=supporters,
        ),
        SemanticMove(
            kind="attackers",
            target_count=len(attackers),
            state="known",
            sentence=f"{len(attackers)} claims attack this claim.",
            target_ids=attackers,
        ),
        SemanticMove(
            kind="assumptions",
            target_count=0,
            state="unavailable",
            sentence="Assumption traversal is unavailable in the current neighborhood report.",
        ),
        SemanticMove(
            kind="conditions",
            target_count=condition_count,
            state=condition_state,
            sentence=(
                "The claim has an explicit condition expression."
                if claim.conditions_cel
                else "The claim has vacuous conditions."
            ),
        ),
        SemanticMove(
            kind="provenance",
            target_count=provenance_count,
            state=provenance_state,
            sentence=(
                "The claim has provenance."
                if claim.provenance is not None
                else "The claim provenance is unknown."
            ),
        ),
        SemanticMove(
            kind="shared_concept",
            target_count=len(shared_concept_ids),
            state="known",
            sentence=f"{len(shared_concept_ids)} visible claims share this concept.",
            target_ids=shared_concept_ids,
        ),
        SemanticMove(
            kind="policy_alternatives",
            target_count=0,
            state="unavailable",
            sentence="Policy alternatives are unavailable in the current neighborhood report.",
        ),
    )


def _nodes(
    world,
    claim,
    stances,
    shared_concept_ids: tuple[str, ...],
    limit: int,
) -> tuple[SemanticNode, ...]:
    ids = [str(claim.claim_id)]
    for stance in stances:
        ids.append(str(stance.claim_id))
        ids.append(str(stance.target_claim_id))
    ids.extend(shared_concept_ids)

    nodes: list[SemanticNode] = []
    seen: set[str] = set()
    for claim_id in ids:
        if claim_id in seen:
            continue
        seen.add(claim_id)
        row = world.get_claim(claim_id)
        display_id = claim_id if row is None else _claim_display_id(row)
        nodes.append(
            SemanticNode(
                kind="claim",
                node_id=claim_id,
                display_id=display_id,
                sentence=f"Claim node {display_id}.",
            )
        )
        if len(nodes) >= limit:
            break
    return tuple(nodes)


def _edges(world, stances, focus_id: str, limit: int) -> tuple[SemanticEdge, ...]:
    edges: list[SemanticEdge] = []
    for stance in stances:
        source_id = str(stance.claim_id)
        target_id = str(stance.target_claim_id)
        source_display = _display_for_id(world, source_id)
        target_display = _display_for_id(world, target_id)
        stance_type = stance.stance_type.value
        relation = _stance_sentence_verb(stance.stance_type)
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
                edge_kind=stance_type,
                sentence=sentence,
            )
        )
        if len(edges) >= limit:
            break
    return tuple(edges)


def _rows(
    claim,
    supporters: tuple[str, ...],
    attackers: tuple[str, ...],
    shared_concept_ids: tuple[str, ...],
    edges: tuple[SemanticEdge, ...],
) -> tuple[SemanticNeighborhoodRow, ...]:
    rows: list[SemanticNeighborhoodRow] = []
    focus_id = str(claim.claim_id)
    for supporter in supporters:
        rows.append(
            SemanticNeighborhoodRow(
                section="supporters",
                subject_id=supporter,
                relation="supports",
                object_id=focus_id,
                state="known",
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
                state="known",
                sentence=f"Claim {attacker} attacks claim {focus_id}.",
            )
        )
    rows.append(
        SemanticNeighborhoodRow(
            section="conditions",
            subject_id=focus_id,
            relation="has_conditions",
            object_id=claim.conditions_cel or "vacuous",
            state="known" if claim.conditions_cel else "vacuous",
            sentence=(
                f"Claim {focus_id} has condition expression {claim.conditions_cel}."
                if claim.conditions_cel
                else f"Claim {focus_id} has vacuous conditions."
            ),
        )
    )
    provenance_state: SemanticState = "known" if claim.provenance is not None else "unknown"
    rows.append(
        SemanticNeighborhoodRow(
            section="provenance",
            subject_id=focus_id,
            relation="has_provenance",
            object_id="known" if claim.provenance is not None else "unknown",
            state=provenance_state,
            sentence=(
                f"Claim {focus_id} has provenance."
                if claim.provenance is not None
                else f"Claim {focus_id} provenance is unknown."
            ),
        )
    )
    for shared_id in shared_concept_ids:
        rows.append(
            SemanticNeighborhoodRow(
                section="shared_concept",
                subject_id=focus_id,
                relation="shares_concept_with",
                object_id=shared_id,
                state="known",
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
                state="known",
                sentence=edge.sentence,
            )
        )
    return tuple(rows)


def _shared_concept_ids(world, claim, policy, limit: int) -> tuple[str, ...]:
    if claim.value_concept_id is None:
        return ()
    related: list[str] = []
    for row in world.claims_with_policy(str(claim.value_concept_id), policy):
        claim_id = str(row.claim_id)
        if claim_id != str(claim.claim_id):
            related.append(claim_id)
        if len(related) >= limit:
            break
    return tuple(related)


def _stance_sentence_verb(stance_type: StanceType) -> str:
    if stance_type is StanceType.SUPPORTS:
        return "supports"
    if stance_type is StanceType.EXPLAINS:
        return "explains"
    if stance_type is StanceType.REBUTS:
        return "rebuts"
    if stance_type is StanceType.UNDERCUTS:
        return "undercuts"
    if stance_type is StanceType.UNDERMINES:
        return "undermines"
    if stance_type is StanceType.SUPERSEDES:
        return "supersedes"
    if stance_type is StanceType.ABSTAIN:
        return "abstains from"
    return "has no stance on"


def _display_for_id(world, claim_id: str) -> str:
    claim = world.get_claim(claim_id)
    return claim_id if claim is None else _claim_display_id(claim)


def _claim_display_id(claim) -> str:
    return claim.primary_logical_value or str(claim.claim_id)
