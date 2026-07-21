"""Temporal order as a happens-before partial order with declared-frame projections.

The temporal layer has two composed pieces:

1. **Happens-before evidence edges** (Lamport 1978). A :class:`HappensBeforeEdge`
   is a provenance-bearing *posit* that one description strictly precedes another
   — a message receive, a human "X then Y", a cross-frame synchronization point.
   It is a claim-shaped piece of evidence, never a global fact; ordering across
   incommensurable clocks exists only insofar as such evidence supplies it.
   Concurrency (provably no invariant order) is a first-class verdict distinct
   from ignorance (insufficient evidence).

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


class DescriptionTemporalAnchor(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
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


class HappensBeforeEdge(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """Provenance-bearing evidence that one description strictly precedes another.

    A happens-before edge (Lamport 1978) is a claim-shaped *posit* — a message
    receive, a human "X then Y", a cross-frame sync point — never a global fact.
    It is the primitive from which cross-frame order is derived, consistent with
    ``docs/event-semantics.md``'s deflationary position: there is no view-from-
    nowhere timeline, only the ordering that evidence supplies.
    """

    edge_id: str
    earlier_claim_id: str
    later_claim_id: str
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.earlier_claim_id == self.later_claim_id:
            raise ValueError(
                "happens-before edge must relate two distinct descriptions"
            )


class TemporalOrderVerdict(StrEnum):
    """Outcome of a happens-before order query between two descriptions.

    ``CONCURRENT`` (provably no invariant order — Lamport 1978) is a DIFFERENT
    verdict from ``UNKNOWN`` (insufficient evidence): the whole point of the
    rebuild. ``CONFLICTED`` means the supplied evidence derives both ``a -> b``
    and ``b -> a``; rival orderings are data (non-commitment principle), surfaced
    rather than silently tie-broken.
    """

    BEFORE = "before"
    AFTER = "after"
    CONCURRENT = "concurrent"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


_RELATION_EXPRESSIONS: dict[AllenRelation, CelExpr] = {
    AllenRelation.BEFORE: CelExpr("left_until < right_from"),
    AllenRelation.MEETS: CelExpr("left_until == right_from"),
    AllenRelation.OVERLAPS: CelExpr(
        "left_from < right_from && right_from < left_until && left_until < right_until"
    ),
    AllenRelation.DURING: CelExpr("right_from < left_from && left_until < right_until"),
    AllenRelation.STARTS: CelExpr("left_from == right_from && left_until < right_until"),
    AllenRelation.FINISHES: CelExpr("right_from < left_from && left_until == right_until"),
    AllenRelation.EQUALS: CelExpr("left_from == right_from && left_until == right_until"),
    AllenRelation.AFTER: CelExpr("right_until < left_from"),
    AllenRelation.MET_BY: CelExpr("right_until == left_from"),
    AllenRelation.OVERLAPPED_BY: CelExpr(
        "right_from < left_from && left_from < right_until && right_until < left_until"
    ),
    AllenRelation.CONTAINS: CelExpr("left_from < right_from && right_until < left_until"),
    AllenRelation.STARTED_BY: CelExpr("left_from == right_from && right_until < left_until"),
    AllenRelation.FINISHED_BY: CelExpr("left_from < right_from && left_until == right_until"),
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


def _transitive_closure(
    edges: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Reflexive step omitted: the transitive closure of directed edges."""

    closure = set(edges)
    changed = True
    while changed:
        changed = False
        for a, b in tuple(closure):
            for c, d in tuple(closure):
                if b == c and (a, d) not in closure:
                    closure.add((a, d))
                    changed = True
    return closure


def temporal_order(
    left_claim_id: str,
    right_claim_id: str,
    *,
    anchors: tuple[DescriptionTemporalAnchor, ...],
    edges: tuple[HappensBeforeEdge, ...],
    assume_complete: bool = False,
) -> TemporalOrderVerdict:
    """Order two descriptions from happens-before evidence and frame-local bounds.

    Same-frame anchor pairs contribute derived happens-before edges through the
    canonical Allen path (a BEFORE that ``HOLDS`` -> a derived ``a -> b`` edge);
    these join the authored edges and the transitive closure is taken. If the
    closure orders the pair both ways -> ``CONFLICTED``; only left->right ->
    ``BEFORE``; only right->left -> ``AFTER``.

    With no ordering derivable, overlapping same-frame bounds that positively rule
    out both BEFORE and AFTER give ``CONCURRENT`` (valid even open-world). Failing
    that, ``assume_complete=True`` is a per-query *declaration* that the supplied
    edge set captures all communication — the vector-clock/Lamport completeness
    assumption made explicit and auditable, exactly like a render-policy
    assumption — and reads the silence as ``CONCURRENT``. The default,
    ``assume_complete=False``, is the open-world honest-ignorance reading and
    returns ``UNKNOWN``.
    """

    directed: set[tuple[str, str]] = {
        (edge.earlier_claim_id, edge.later_claim_id) for edge in edges
    }

    same_frame_pairs = [
        (a, b)
        for a in anchors
        for b in anchors
        if a.claim_id != b.claim_id and a.frame.frame_id == b.frame.frame_id
    ]
    for a, b in same_frame_pairs:
        if description_temporal_relation(a, b, AllenRelation.BEFORE) is AllenVerdict.HOLDS:
            directed.add((a.claim_id, b.claim_id))

    closure = _transitive_closure(directed)
    left_before_right = (left_claim_id, right_claim_id) in closure
    right_before_left = (right_claim_id, left_claim_id) in closure

    if left_before_right and right_before_left:
        return TemporalOrderVerdict.CONFLICTED
    if left_before_right:
        return TemporalOrderVerdict.BEFORE
    if right_before_left:
        return TemporalOrderVerdict.AFTER

    if _bounds_prove_concurrent(left_claim_id, right_claim_id, anchors):
        return TemporalOrderVerdict.CONCURRENT

    if assume_complete:
        return TemporalOrderVerdict.CONCURRENT
    return TemporalOrderVerdict.UNKNOWN


def _bounds_prove_concurrent(
    left_claim_id: str,
    right_claim_id: str,
    anchors: tuple[DescriptionTemporalAnchor, ...],
) -> bool:
    """True iff some same-frame anchor pair positively rules out both orderings.

    Overlapping bounded intervals are positive proof of concurrency (no invariant
    order), so this holds even under the open-world reading.
    """

    lefts = [a for a in anchors if a.claim_id == left_claim_id]
    rights = [a for a in anchors if a.claim_id == right_claim_id]
    for left in lefts:
        for right in rights:
            if left.frame.frame_id != right.frame.frame_id:
                continue
            before = description_temporal_relation(left, right, AllenRelation.BEFORE)
            after = description_temporal_relation(left, right, AllenRelation.AFTER)
            if before is AllenVerdict.FAILS and after is AllenVerdict.FAILS:
                return True
    return False
