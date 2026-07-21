"""Temporal order as a happens-before partial order with declared-frame projections.

The temporal layer has two composed pieces:

1. **Happens-before evidence edges** (Lamport 1978). A :class:`HappensBeforeEdge`
   is a provenance-bearing *posit* that one description strictly precedes another
   — a message receive, a human "X then Y", a cross-frame synchronization point.
   It is a claim-shaped piece of evidence, never a global fact; ordering across
   incommensurable clocks exists only insofar as such evidence supplies it.
   Every edge declares its :class:`HappensBeforeAccount`; transitive chaining is
   licensed only by mechanism-backed accounts (mirroring
   ``causal_transitivity_allowed`` in :mod:`description_kinds`) — a merely STATED
   order never composes, because chaining two tellings would assert an order
   neither teller committed to. Concurrency (provably no invariant order) is a
   first-class verdict distinct from ignorance (insufficient evidence), and the
   two ways of reaching it are distinct verdicts too: ``CONCURRENT_PROVEN``
   (positive proof from bounds — monotone under new edges of the supplied kinds)
   vs ``CONCURRENT_ASSUMED`` (absence of order re-read as concurrency under a
   declared-complete evidence set — defeasible; one new edge destroys it).
   Verdicts are returned inside a :class:`TemporalOrderJudgment` carrying the
   witnessing :class:`OrderingLink` paths, so a reader can always see whether an
   order (or a conflict) rests on frame coordinates, on posits, or on a mixture.

2. **Declared-frame TIMEPOINT projections.** A :class:`TemporalFrame` is the
   declaration that one timeline (one machine's clock, one sensor, one human
   narrative) is totally ordered. Within a single frame, a
   :class:`DescriptionTemporalAnchor` carries optional endpoint bounds and Allen's
   (1983) thirteen interval relations are decided three-valued
   (HOLDS / FAILS / UNDECIDED) by REDUCING each relation to a condition over four
   ``KindType.TIMEPOINT`` variables and discharging it through the ``condition-ir``
   substrate. The single global real line the old module assumed is now a
   *per-frame projection*: bounds are comparable ONLY within one frame, and an
   absent bound is honest ignorance, not a fabricated coordinate.

propstore does NOT reimplement temporal or Z3 logic; it consumes condition-ir's
own types directly (``CelExpr``, ``ConceptInfo``, ``KindType``, ``ConditionSolver``,
``check_condition_ir``, ``SolverUnsat``/``SolverUnknown``) — the boundary is the
import, not an adapter. A ``SolverUnknown`` (Z3 resource failure) is never a
semantic verdict; it propagates as ``Z3UnknownError``.

See ``docs/event-semantics.md`` §5 for the deflationary position this layer
implements: temporal anchoring is a declared-frame projection, not a discovery
about a mind-independent timeline.
"""

from __future__ import annotations

from enum import StrEnum

import msgspec

from condition_ir import (
    CelExpr,
    CheckedCondition,
    ConceptInfo,
    ConditionSolver,
    KindType,
    SolverUnsat,
    Z3UnknownError,
    check_condition_ir,
)
from condition_ir.solver import SolverUnknown

from propstore.provenance import Provenance


class AllenRelation(StrEnum):
    """Allen's thirteen interval relations."""

    BEFORE = "before"
    MEETS = "meets"
    OVERLAPS = "overlaps"
    DURING = "during"
    STARTS = "starts"
    FINISHES = "finishes"
    EQUALS = "equals"
    AFTER = "after"
    MET_BY = "met_by"
    OVERLAPPED_BY = "overlapped_by"
    CONTAINS = "contains"
    STARTED_BY = "started_by"
    FINISHED_BY = "finished_by"


class AllenVerdict(StrEnum):
    """Three-valued outcome of a within-frame Allen query.

    ``UNDECIDED`` is honest ignorance: the supplied (possibly partial) bounds
    neither entail the relation nor its complement. It is distinct from a
    ``FAILS`` that the bounds positively rule out.
    """

    HOLDS = "holds"
    FAILS = "fails"
    UNDECIDED = "undecided"


class TemporalFrame(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A declared frame of reference whose own timeline is totally ordered.

    A frame IS the declaration that one clock/sensor/narrative is internally
    comparable; endpoint bounds are comparable ONLY within one frame. The single
    global real line the old temporal module assumed is now a per-frame
    projection — cross-frame order comes from :class:`HappensBeforeEdge`
    evidence, not from comparing coordinates across incommensurable clocks.
    """

    frame_id: str
    description: str
    provenance: Provenance


class DescriptionTemporalAnchor(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True
):
    """The validity interval of a description claim within one declared frame.

    Bounds are OPTIONAL: an absent bound is honest ignorance (CLAUDE.md
    honest-ignorance discipline), not a fabricated coordinate. A query against a
    partially-bound anchor is satisfiability given partial knowledge, which is why
    Allen verdicts are three-valued.
    """

    claim_id: str
    frame: TemporalFrame
    provenance: Provenance
    valid_from: float | None = None
    valid_until: float | None = None

    def __post_init__(self) -> None:
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValueError(
                "description temporal anchor requires valid_from <= valid_until"
            )


class HappensBeforeAccount(StrEnum):
    """The kind of evidence a happens-before posit rests on.

    Mirrors :class:`CausalAccount`'s composition discipline
    (``causal_transitivity_allowed`` in :mod:`description_kinds`): transitive
    chaining is licensed only by mechanism-backed accounts. ``MESSAGE`` (a
    send/receive pair) and ``SYNCHRONIZATION`` (an explicit cross-frame sync
    point) compose — they are Lamport's actual relation. ``STATED`` (a telling,
    "X then Y") orders exactly its own endpoints and NEVER participates in a
    chain: composing two tellings would assert an order neither teller committed
    to. To make a telling composable, re-author it under a mechanism-backed
    account and take responsibility for the mechanism.
    """

    STATED = "stated"
    MESSAGE = "message"
    SYNCHRONIZATION = "synchronization"


_COMPOSING_ACCOUNTS = frozenset(
    {HappensBeforeAccount.MESSAGE, HappensBeforeAccount.SYNCHRONIZATION}
)


class HappensBeforeEdge(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Provenance-bearing evidence that one description strictly precedes another.

    A happens-before edge (Lamport 1978) is a claim-shaped *posit* — a message
    receive, a human "X then Y", a cross-frame sync point — never a global fact.
    It is the primitive from which cross-frame order is derived, consistent with
    ``docs/event-semantics.md``'s deflationary position: there is no view-from-
    nowhere timeline, only the ordering that evidence supplies. The mandatory
    ``account`` declares what the posit rests on and thereby whether it may be
    chained (see :class:`HappensBeforeAccount`); there is no default, because
    defaulting an epistemic commitment would fabricate one.
    """

    edge_id: str
    earlier_claim_id: str
    later_claim_id: str
    account: HappensBeforeAccount
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.earlier_claim_id == self.later_claim_id:
            raise ValueError(
                "happens-before edge must relate two distinct descriptions"
            )


class TemporalOrderVerdict(StrEnum):
    """Outcome of a happens-before order query between two descriptions.

    Concurrency and ignorance are distinct, and so are the two BASES for
    concurrency — because belief revision treats them differently:

    - ``CONCURRENT_PROVEN``: positive proof (same-frame bounds rule out both
      orderings). Monotone: adding edges cannot retract the bounds; it can only
      CONTRADICT them, which surfaces as ``CONFLICTED``, never as a silent flip.
    - ``CONCURRENT_ASSUMED``: absence of order re-read as concurrency under a
      per-query ``assume_complete`` declaration. Defeasible: one new edge
      destroys it.

    ``CONFLICTED`` means rival orderings — either the evidence derives both
    ``a -> b`` and ``b -> a``, or a derived order is positively refuted by frame
    coordinates. Rival orderings are data (non-commitment principle), surfaced
    with their witnessing paths rather than silently tie-broken.
    """

    BEFORE = "before"
    AFTER = "after"
    CONCURRENT_PROVEN = "concurrent_proven"
    CONCURRENT_ASSUMED = "concurrent_assumed"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


class OrderingEvidenceKind(StrEnum):
    """What one link in a witnessing path is grounded in.

    ``COORDINATE_DERIVED`` links are grounded in comparable bounds within one
    declared frame; ``AUTHORED_POSIT`` links are happens-before evidence edges.
    These are epistemically different arrows — a conflict between them is a
    different animal from a conflict between two posits, and the judgment keeps
    the difference visible instead of laundering it through a closure.
    """

    COORDINATE_DERIVED = "coordinate_derived"
    AUTHORED_POSIT = "authored_posit"


class OrderingLink(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One auditable step in a witnessing path.

    ``edge_id``/``account`` are set iff the link is an authored posit;
    ``frame_id`` is set iff the link is derived from one frame's coordinates.
    """

    earlier_claim_id: str
    later_claim_id: str
    kind: OrderingEvidenceKind
    edge_id: str | None = None
    account: HappensBeforeAccount | None = None
    frame_id: str | None = None


class TemporalOrderJudgment(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A temporal-order verdict together with the evidence that witnesses it.

    ``forward_path`` witnesses left-before-right, ``backward_path`` witnesses
    right-before-left (present when the corresponding order was derived, which
    for ``CONFLICTED`` may be both, or one path plus ``refuting_frame_id`` — the
    frame whose coordinates positively rule the derived direction out).
    ``proven_frame_id`` is the frame whose bounds prove ``CONCURRENT_PROVEN``.
    Nothing here is ever persisted: the judgment is recomputed per query from
    live anchors and edges, so revision that defeats an edge upstream reaches
    every verdict that leaned on it at the next query — there is no snapshotted
    closure to go stale.
    """

    verdict: TemporalOrderVerdict
    forward_path: tuple[OrderingLink, ...] = ()
    backward_path: tuple[OrderingLink, ...] = ()
    refuting_frame_id: str | None = None
    proven_frame_id: str | None = None


_RELATION_EXPRESSIONS: dict[AllenRelation, CelExpr] = {
    AllenRelation.BEFORE: CelExpr("left_until < right_from"),
    AllenRelation.MEETS: CelExpr("left_until == right_from"),
    AllenRelation.OVERLAPS: CelExpr(
        "left_from < right_from && right_from < left_until && left_until < right_until"
    ),
    AllenRelation.DURING: CelExpr("right_from < left_from && left_until < right_until"),
    AllenRelation.STARTS: CelExpr(
        "left_from == right_from && left_until < right_until"
    ),
    AllenRelation.FINISHES: CelExpr(
        "right_from < left_from && left_until == right_until"
    ),
    AllenRelation.EQUALS: CelExpr(
        "left_from == right_from && left_until == right_until"
    ),
    AllenRelation.AFTER: CelExpr("right_until < left_from"),
    AllenRelation.MET_BY: CelExpr("right_until == left_from"),
    AllenRelation.OVERLAPPED_BY: CelExpr(
        "right_from < left_from && left_from < right_until && right_until < left_until"
    ),
    AllenRelation.CONTAINS: CelExpr(
        "left_from < right_from && right_until < left_until"
    ),
    AllenRelation.STARTED_BY: CelExpr(
        "left_from == right_from && right_until < left_until"
    ),
    AllenRelation.FINISHED_BY: CelExpr(
        "left_from < right_from && left_until == right_until"
    ),
}


def _description_temporal_registry() -> dict[str, ConceptInfo]:
    """The four interval-endpoint timepoints as TIMEPOINT concepts for condition-ir.

    The ``_from``/``_until`` suffix naming lets condition-ir's
    ``temporal_ordering_constraints`` auto-inject ``X_from <= X_until`` so a
    partially-bound interval is still constrained to be well-formed.
    """

    return {
        name: ConceptInfo(
            id=f"ps:concept:{name}",
            canonical_name=name,
            kind=KindType.TIMEPOINT,
        )
        for name in ("left_from", "left_until", "right_from", "right_until")
    }


def _bindings_for(
    left: DescriptionTemporalAnchor, right: DescriptionTemporalAnchor
) -> dict[str, float]:
    """Bind ONLY the present bounds; absent bounds stay free in the solver."""

    bindings: dict[str, float] = {}
    if left.valid_from is not None:
        bindings["left_from"] = left.valid_from
    if left.valid_until is not None:
        bindings["left_until"] = left.valid_until
    if right.valid_from is not None:
        bindings["right_from"] = right.valid_from
    if right.valid_until is not None:
        bindings["right_until"] = right.valid_until
    return bindings


def _is_unsatisfiable(
    solver: ConditionSolver,
    condition: CheckedCondition,
    bindings: dict[str, float],
) -> bool:
    """True iff ``condition`` is UNSAT under ``bindings``; ``SolverUnknown`` propagates."""

    result = solver.is_condition_satisfied_result(condition, bindings)
    if isinstance(result, SolverUnsat):
        return True
    if isinstance(result, SolverUnknown):
        # Z3 resource failure (e.g. timeout) is not a semantic verdict.
        raise Z3UnknownError(result)
    return False


def description_temporal_relation(
    left: DescriptionTemporalAnchor,
    right: DescriptionTemporalAnchor,
    relation: AllenRelation,
) -> AllenVerdict:
    """Decide an Allen ``relation`` three-valued within a single frame.

    Raises ``ValueError`` if the two anchors are in different frames: Allen
    relations are frame-local, and asking for one of the thirteen interval
    relations across incommensurable clocks is a category error, not an unknown.
    Use :func:`temporal_order` for cross-frame queries.

    With both anchors fully bound this reproduces the classical Allen answers
    (BEFORE -> HOLDS, etc.). With bounds omitted the query is satisfiability given
    partial knowledge: UNSAT of the relation -> ``FAILS``; else UNSAT of its
    complement -> ``HOLDS``; both satisfiable -> ``UNDECIDED``.
    """

    if left.frame.frame_id != right.frame.frame_id:
        raise ValueError(
            "Allen relations are frame-local; anchors "
            f"{left.claim_id!r} ({left.frame.frame_id!r}) and "
            f"{right.claim_id!r} ({right.frame.frame_id!r}) live in different "
            "frames. Use temporal_order for cross-frame queries."
        )

    registry = _description_temporal_registry()
    solver = ConditionSolver(registry)
    bindings = _bindings_for(left, right)

    relation_expr = str(_RELATION_EXPRESSIONS[relation])
    relation_condition = check_condition_ir(relation_expr, registry)
    if _is_unsatisfiable(solver, relation_condition, bindings):
        return AllenVerdict.FAILS

    complement_condition = check_condition_ir(f"!({relation_expr})", registry)
    if _is_unsatisfiable(solver, complement_condition, bindings):
        return AllenVerdict.HOLDS

    return AllenVerdict.UNDECIDED


def _link_sort_key(link: OrderingLink) -> tuple[str, str, str]:
    return (link.later_claim_id, link.kind.value, link.edge_id or "")


def _build_links(
    anchors: tuple[DescriptionTemporalAnchor, ...],
    edges: tuple[HappensBeforeEdge, ...],
) -> tuple[OrderingLink, ...]:
    """All ordering links: coordinate-derived (same-frame Allen BEFORE that
    HOLDS, through the canonical Allen path — never a hand-rolled float compare)
    plus one link per authored posit.

    Derived-link construction is quadratic in same-frame anchors and each pair
    costs a solver query; a log-scale consumer should supply authored MESSAGE
    edges rather than thousands of bounded anchors.
    """

    links: list[OrderingLink] = []
    for a in anchors:
        for b in anchors:
            if a.claim_id == b.claim_id or a.frame.frame_id != b.frame.frame_id:
                continue
            if (
                description_temporal_relation(a, b, AllenRelation.BEFORE)
                is AllenVerdict.HOLDS
            ):
                links.append(
                    OrderingLink(
                        earlier_claim_id=a.claim_id,
                        later_claim_id=b.claim_id,
                        kind=OrderingEvidenceKind.COORDINATE_DERIVED,
                        frame_id=a.frame.frame_id,
                    )
                )
    for edge in edges:
        links.append(
            OrderingLink(
                earlier_claim_id=edge.earlier_claim_id,
                later_claim_id=edge.later_claim_id,
                kind=OrderingEvidenceKind.AUTHORED_POSIT,
                edge_id=edge.edge_id,
                account=edge.account,
            )
        )
    return tuple(links)


def _link_composes(link: OrderingLink) -> bool:
    """Whether a link may participate in a chain (see HappensBeforeAccount)."""

    if link.kind is OrderingEvidenceKind.COORDINATE_DERIVED:
        return True
    return link.account in _COMPOSING_ACCOUNTS


def _find_path(
    start: str,
    goal: str,
    links: tuple[OrderingLink, ...],
) -> tuple[OrderingLink, ...] | None:
    """A witnessing path start -> goal, or None.

    BFS (shortest, deterministic by sorted link keys) over COMPOSABLE links
    only; a non-composing (STATED) link can witness the pair solely as a direct,
    length-one path. No closure is materialized anywhere — reachability is
    answered per query in O(links), and the path itself is the audit trail.
    """

    adjacency: dict[str, list[OrderingLink]] = {}
    for link in sorted(filter(_link_composes, links), key=_link_sort_key):
        adjacency.setdefault(link.earlier_claim_id, []).append(link)

    parent: dict[str, OrderingLink] = {}
    visited = {start}
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node == goal:
            path: list[OrderingLink] = []
            while node != start:
                link = parent[node]
                path.append(link)
                node = link.earlier_claim_id
            return tuple(reversed(path))
        for link in adjacency.get(node, ()):
            if link.later_claim_id not in visited:
                visited.add(link.later_claim_id)
                parent[link.later_claim_id] = link
                queue.append(link.later_claim_id)

    direct_stated = sorted(
        (
            link
            for link in links
            if not _link_composes(link)
            and link.earlier_claim_id == start
            and link.later_claim_id == goal
        ),
        key=_link_sort_key,
    )
    if direct_stated:
        return (direct_stated[0],)
    return None


def _bounds_refutations(
    left_claim_id: str,
    right_claim_id: str,
    anchors: tuple[DescriptionTemporalAnchor, ...],
) -> tuple[str | None, str | None, str | None]:
    """(frame refuting left-before, frame refuting left-after, frame refuting both).

    A same-frame anchor pair whose bounds make BEFORE (resp. AFTER) FAIL is a
    positive, coordinate-grounded refutation of that ordering. A pair failing
    both is positive proof of concurrency (no invariant order), valid even
    open-world. First witnessing frame in anchor order wins (deterministic).
    """

    refutes_before: str | None = None
    refutes_after: str | None = None
    refutes_both: str | None = None
    lefts = [a for a in anchors if a.claim_id == left_claim_id]
    rights = [a for a in anchors if a.claim_id == right_claim_id]
    for left in lefts:
        for right in rights:
            if left.frame.frame_id != right.frame.frame_id:
                continue
            before = description_temporal_relation(left, right, AllenRelation.BEFORE)
            after = description_temporal_relation(left, right, AllenRelation.AFTER)
            if before is AllenVerdict.FAILS and refutes_before is None:
                refutes_before = left.frame.frame_id
            if after is AllenVerdict.FAILS and refutes_after is None:
                refutes_after = left.frame.frame_id
            if (
                before is AllenVerdict.FAILS
                and after is AllenVerdict.FAILS
                and refutes_both is None
            ):
                refutes_both = left.frame.frame_id
    return refutes_before, refutes_after, refutes_both


def temporal_order(
    left_claim_id: str,
    right_claim_id: str,
    *,
    anchors: tuple[DescriptionTemporalAnchor, ...],
    edges: tuple[HappensBeforeEdge, ...],
    assume_complete: bool = False,
) -> TemporalOrderJudgment:
    """Order two descriptions from happens-before evidence and frame-local bounds.

    Pure per-query function: links are rebuilt and paths re-searched from the
    supplied ``anchors``/``edges`` on every call. Nothing persists a derived
    order — an edge defeated upstream is simply absent from the next call, so
    revision reaches every verdict. Storage, when it exists, holds only
    AUTHORED edges; a derived order must never be written back.

    Verdict logic: a witnessing path each way (composable links chain; STATED
    posits witness only their own endpoints); both ways -> ``CONFLICTED``; a
    path positively refuted by some frame's coordinates -> ``CONFLICTED`` (a
    posit contradicting comparable bounds is a rival ordering, not a winner);
    one unrefuted path -> ``BEFORE``/``AFTER``. With no path: bounds failing
    both orderings in one frame -> ``CONCURRENT_PROVEN``; else
    ``assume_complete=True`` — the per-query, auditable vector-clock/Lamport
    completeness declaration — reads silence as ``CONCURRENT_ASSUMED``; else
    ``UNKNOWN`` (open-world honest ignorance, the default).
    """

    links = _build_links(anchors, edges)
    forward = _find_path(left_claim_id, right_claim_id, links)
    backward = _find_path(right_claim_id, left_claim_id, links)
    refutes_before, refutes_after, refutes_both = _bounds_refutations(
        left_claim_id, right_claim_id, anchors
    )

    if forward is not None and backward is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.CONFLICTED,
            forward_path=forward,
            backward_path=backward,
        )
    if forward is not None and refutes_before is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.CONFLICTED,
            forward_path=forward,
            refuting_frame_id=refutes_before,
        )
    if backward is not None and refutes_after is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.CONFLICTED,
            backward_path=backward,
            refuting_frame_id=refutes_after,
        )
    if forward is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.BEFORE, forward_path=forward
        )
    if backward is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.AFTER, backward_path=backward
        )
    if refutes_both is not None:
        return TemporalOrderJudgment(
            verdict=TemporalOrderVerdict.CONCURRENT_PROVEN,
            proven_frame_id=refutes_both,
        )
    if assume_complete:
        return TemporalOrderJudgment(verdict=TemporalOrderVerdict.CONCURRENT_ASSUMED)
    return TemporalOrderJudgment(verdict=TemporalOrderVerdict.UNKNOWN)
