"""Application-layer owner for authored temporal evidence and order queries.

Authoring surfaces write ONLY authored artifacts to canonical storage — a frame,
a description anchor, a happens-before edge (:mod:`propstore.families.temporal`).
The query surface :func:`temporal_order_between` loads ALL stored frames, anchors,
and edges, lowers them to the lemon compute structs, and recomputes the order per
call via :func:`propstore.core.lemon.temporal.temporal_order`. A derived order —
the BFS result, the judgment, any closure — is NEVER written back (CLAUDE.md;
``temporal.py`` docstring; ``docs/event-semantics.md`` §5), so revision that
defeats an edge upstream reaches every verdict at the next query.

This module owns the authoring and query *semantics*; the CLI
(:mod:`propstore.cli.temporal`) is a thin adapter over the typed request/report/
failure objects here. It imports no Click, writes to no stream, and calls no
``sys.exit`` (CLAUDE.md CLI-adapter discipline). The account of a happens-before
edge is mandatory: an unknown account value is a typed
:class:`UnknownHappensBeforeAccount` failure, never a silent default (defaulting
an epistemic commitment would fabricate one).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from quire.sqlalchemy_store import readonly_session

from propstore.core.lemon.temporal import (
    DescriptionTemporalAnchor,
    HappensBeforeAccount,
    HappensBeforeEdge,
    TemporalFrame,
    TemporalOrderJudgment,
    temporal_order,
)
from propstore.families.temporal import (
    DescriptionTemporalAnchorDoc,
    HappensBeforeEdgeDoc,
    TemporalFrameDoc,
    TemporalRepository,
    stated_provenance,
)
from propstore.provenance import Provenance
from propstore.world.queries import (
    select_description_temporal_anchors,
    select_happens_before_edges,
    select_temporal_frames,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


# ── authoring results / failures ─────────────────────────────────────────────


@dataclass(frozen=True)
class TemporalFrameResult:
    """The identity of an authored temporal frame."""

    frame_id: str


@dataclass(frozen=True)
class TemporalAnchorResult:
    """The identity of an authored description-temporal anchor."""

    anchor_id: str


@dataclass(frozen=True)
class HappensBeforeEdgeResult:
    """The identity of an authored happens-before edge."""

    edge_id: str


@dataclass(frozen=True)
class UnknownHappensBeforeAccount:
    """Typed failure: the requested happens-before account is not a known value.

    A happens-before account is mandatory and drawn from
    :class:`~propstore.core.lemon.temporal.HappensBeforeAccount`; an unknown value
    returns this (never a silent default), carrying both the requested value and
    the supported set so the adapter can render an actionable message.
    """

    requested: str
    supported: tuple[str, ...]

    def message(self) -> str:
        supported = ", ".join(self.supported)
        return (
            f"unknown happens-before account '{self.requested}'; "
            f"supported accounts: {supported}"
        )


# ── query report ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TemporalOrderReport:
    """A temporal-order query result: the two claims and the full judgment.

    ``judgment`` is the canonical
    :class:`~propstore.core.lemon.temporal.TemporalOrderJudgment` (verdict plus the
    witnessing forward/backward :class:`~propstore.core.lemon.temporal.OrderingLink`
    paths, ``refuting_frame_id``, and ``proven_frame_id``) — carried whole so the
    audit trail is never flattened to a bare verdict.
    """

    left_claim_id: str
    right_claim_id: str
    judgment: TemporalOrderJudgment


# ── authoring (writes canonical docs, nothing more) ───────────────────────────


def declare_temporal_frame(
    repo: Repository,
    *,
    frame_id: str,
    description: str,
    provenance: Provenance | None = None,
) -> TemporalFrameResult:
    """Author one temporal frame on master; return its id."""

    document = TemporalFrameDoc(
        frame_id=frame_id,
        description=description,
        provenance=provenance if provenance is not None else stated_provenance(),
    )
    _repository(repo).author_frame(
        document, message=f"Declare temporal frame {frame_id}"
    )
    return TemporalFrameResult(frame_id=frame_id)


def anchor_description_claim(
    repo: Repository,
    *,
    anchor_id: str,
    claim_id: str,
    frame_id: str,
    valid_from: float | None = None,
    valid_until: float | None = None,
    provenance: Provenance | None = None,
) -> TemporalAnchorResult:
    """Author one description-temporal anchor on master; return its id.

    An absent bound stays absent (honest ignorance, never a fabricated
    coordinate); a present pair with ``valid_from > valid_until`` is rejected by
    the charter exactly as the lemon struct rejects it.
    """

    document = DescriptionTemporalAnchorDoc(
        anchor_id=anchor_id,
        claim_id=claim_id,
        frame_id=frame_id,
        provenance=provenance if provenance is not None else stated_provenance(),
        valid_from=valid_from,
        valid_until=valid_until,
    )
    _repository(repo).author_anchor(
        document, message=f"Anchor claim {claim_id} in {frame_id}"
    )
    return TemporalAnchorResult(anchor_id=anchor_id)


def assert_happens_before(
    repo: Repository,
    *,
    edge_id: str,
    earlier_claim_id: str,
    later_claim_id: str,
    account: str,
    provenance: Provenance | None = None,
) -> HappensBeforeEdgeResult | UnknownHappensBeforeAccount:
    """Author one happens-before edge on master; return its id.

    The ``account`` is mandatory. An unknown value returns a typed
    :class:`UnknownHappensBeforeAccount` (never a silent default); a valid value
    is stored as the canonical
    :class:`~propstore.core.lemon.temporal.HappensBeforeAccount`.
    """

    resolved = _resolve_account(account)
    if isinstance(resolved, UnknownHappensBeforeAccount):
        return resolved
    document = HappensBeforeEdgeDoc(
        edge_id=edge_id,
        earlier_claim_id=earlier_claim_id,
        later_claim_id=later_claim_id,
        account=resolved,
        provenance=provenance if provenance is not None else stated_provenance(),
    )
    _repository(repo).author_edge(
        document, message=f"Assert {earlier_claim_id} happens-before {later_claim_id}"
    )
    return HappensBeforeEdgeResult(edge_id=edge_id)


# ── query (recomputes the order per call from live rows) ──────────────────────


def temporal_order_between(
    repo: Repository,
    left_claim_id: str,
    right_claim_id: str,
    *,
    assume_complete: bool = False,
) -> TemporalOrderReport:
    """Recompute the happens-before order between two claims from live storage.

    Loads EVERY stored frame, anchor, and edge, lowers them to the lemon compute
    structs, and calls :func:`~propstore.core.lemon.temporal.temporal_order`.
    Nothing is written back: the judgment is recomputed per call, so an edge
    defeated upstream is simply absent next time and the verdict follows.
    """

    _frames, anchors, edges = _load_temporal(repo)
    judgment = temporal_order(
        left_claim_id,
        right_claim_id,
        anchors=anchors,
        edges=edges,
        assume_complete=assume_complete,
    )
    return TemporalOrderReport(
        left_claim_id=left_claim_id,
        right_claim_id=right_claim_id,
        judgment=judgment,
    )


# ── internals ─────────────────────────────────────────────────────────────────


def _repository(repo: Repository) -> TemporalRepository:
    return TemporalRepository(backend=repo.require_git())


def _resolve_account(
    account: str,
) -> HappensBeforeAccount | UnknownHappensBeforeAccount:
    try:
        return HappensBeforeAccount(account)
    except ValueError:
        return UnknownHappensBeforeAccount(
            requested=account,
            supported=tuple(item.value for item in HappensBeforeAccount),
        )


def _load_temporal(
    repo: Repository,
) -> tuple[
    tuple[TemporalFrame, ...],
    tuple[DescriptionTemporalAnchor, ...],
    tuple[HappensBeforeEdge, ...],
]:
    """Read all stored frames/anchors/edges and lower them to the lemon structs.

    Each family is projected into its own single-charter sidecar (the canonical
    family pattern) and read back through the world-query surface. An anchor whose
    frame is not stored is dropped here — it cannot be placed on any timeline
    without fabricating a frame, so lowering it is impossible; this is a
    render-time omission of unusable evidence, not a build-time gate.
    """

    repository = _repository(repo)
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        frame_side = base / "frames.sqlite"
        anchor_side = base / "anchors.sqlite"
        edge_side = base / "edges.sqlite"
        frame_schema = repository.build_frame_sidecar(frame_side)
        anchor_schema = repository.build_anchor_sidecar(anchor_side)
        edge_schema = repository.build_edge_sidecar(edge_side)
        with readonly_session(frame_side, frame_schema) as session:
            frame_docs = select_temporal_frames(session)
        with readonly_session(anchor_side, anchor_schema) as session:
            anchor_docs = select_description_temporal_anchors(session)
        with readonly_session(edge_side, edge_schema) as session:
            edge_docs = select_happens_before_edges(session)

    frames_by_id = {doc.frame_id: _to_frame(doc) for doc in frame_docs}
    anchors = tuple(
        _to_anchor(doc, frames_by_id[doc.frame_id])
        for doc in anchor_docs
        if doc.frame_id in frames_by_id
    )
    edges = tuple(_to_edge(doc) for doc in edge_docs)
    return tuple(frames_by_id.values()), anchors, edges


def _to_frame(document: TemporalFrameDoc) -> TemporalFrame:
    """Lower a stored frame doc to the lemon struct (a construction)."""

    return TemporalFrame(
        frame_id=document.frame_id,
        description=document.description,
        provenance=document.provenance,
    )


def _to_anchor(
    document: DescriptionTemporalAnchorDoc, frame: TemporalFrame
) -> DescriptionTemporalAnchor:
    """Lower a stored anchor doc + its resolved frame to the lemon struct."""

    return DescriptionTemporalAnchor(
        claim_id=document.claim_id,
        frame=frame,
        provenance=document.provenance,
        valid_from=document.valid_from,
        valid_until=document.valid_until,
    )


def _to_edge(document: HappensBeforeEdgeDoc) -> HappensBeforeEdge:
    """Lower a stored edge doc to the lemon struct (a construction)."""

    return HappensBeforeEdge(
        edge_id=document.edge_id,
        earlier_claim_id=document.earlier_claim_id,
        later_claim_id=document.later_claim_id,
        account=HappensBeforeAccount(document.account),
        provenance=document.provenance,
    )
