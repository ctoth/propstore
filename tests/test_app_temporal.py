"""App-layer temporal order queries over authored evidence.

Drives the production query path: author frames/anchors/edges through the owner
surfaces, then recompute the happens-before order per query. Covers account-
sensitive chaining (message chains, stated does not), positive concurrency from
frame bounds, assumed concurrency under a completeness declaration, rival cycles
surfacing as CONFLICTED, the typed unknown-account failure, and the hard
architectural invariant: a query writes NO derived rows back to storage.
"""

from __future__ import annotations

from pathlib import Path

from propstore.app.temporal import (
    UnknownHappensBeforeAccount,
    anchor_description_claim,
    assert_happens_before,
    declare_temporal_frame,
    temporal_order_between,
)
from propstore.core.lemon.temporal import (
    OrderingEvidenceKind,
    TemporalOrderVerdict,
)
from propstore.families.temporal import TemporalRepository
from propstore.repository import Repository


def _edge(
    repo: Repository, edge_id: str, earlier: str, later: str, account: str
) -> None:
    result = assert_happens_before(
        repo,
        edge_id=edge_id,
        earlier_claim_id=earlier,
        later_claim_id=later,
        account=account,
    )
    assert not isinstance(result, UnknownHappensBeforeAccount), result


def test_message_edges_chain_to_before_with_path(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _edge(repo, "e1", "c1", "c2", "message")
    _edge(repo, "e2", "c2", "c3", "message")

    report = temporal_order_between(repo, "c1", "c3")
    assert report.judgment.verdict is TemporalOrderVerdict.BEFORE
    # Two-hop witnessing path, each hop an authored message posit.
    path = report.judgment.forward_path
    assert tuple(link.later_claim_id for link in path) == ("c2", "c3")
    assert all(link.kind is OrderingEvidenceKind.AUTHORED_POSIT for link in path)


def test_stated_edges_order_endpoints_but_do_not_chain(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _edge(repo, "e1", "c1", "c2", "stated")
    _edge(repo, "e2", "c2", "c3", "stated")

    # A stated telling orders exactly its own endpoints.
    endpoints = temporal_order_between(repo, "c1", "c2")
    assert endpoints.judgment.verdict is TemporalOrderVerdict.BEFORE
    # But two tellings never compose: c1..c3 is UNKNOWN, not BEFORE.
    chained = temporal_order_between(repo, "c1", "c3")
    assert chained.judgment.verdict is TemporalOrderVerdict.UNKNOWN


def test_same_frame_overlap_is_concurrent_proven(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    declare_temporal_frame(repo, frame_id="f1", description="clock")
    anchor_description_claim(
        repo,
        anchor_id="a1",
        claim_id="c1",
        frame_id="f1",
        valid_from=0.0,
        valid_until=10.0,
    )
    anchor_description_claim(
        repo,
        anchor_id="a2",
        claim_id="c2",
        frame_id="f1",
        valid_from=5.0,
        valid_until=15.0,
    )

    report = temporal_order_between(repo, "c1", "c2")
    assert report.judgment.verdict is TemporalOrderVerdict.CONCURRENT_PROVEN
    assert report.judgment.proven_frame_id == "f1"


def test_assume_complete_reads_silence_as_concurrent_assumed(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    # No edges, no bounds: open-world silence.
    default = temporal_order_between(repo, "c1", "c2")
    assert default.judgment.verdict is TemporalOrderVerdict.UNKNOWN
    assumed = temporal_order_between(repo, "c1", "c2", assume_complete=True)
    assert assumed.judgment.verdict is TemporalOrderVerdict.CONCURRENT_ASSUMED


def test_rival_cyclic_edges_are_conflicted_with_both_paths(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _edge(repo, "fwd", "c1", "c2", "message")
    _edge(repo, "bwd", "c2", "c1", "message")

    report = temporal_order_between(repo, "c1", "c2")
    assert report.judgment.verdict is TemporalOrderVerdict.CONFLICTED
    assert report.judgment.forward_path
    assert report.judgment.backward_path


def test_unknown_account_is_a_typed_failure(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    result = assert_happens_before(
        repo,
        edge_id="e1",
        earlier_claim_id="c1",
        later_claim_id="c2",
        account="telepathy",
    )
    assert isinstance(result, UnknownHappensBeforeAccount)
    assert "telepathy" in result.message()
    # Nothing was authored for the rejected posit.
    repository = TemporalRepository(backend=repo.require_git())
    assert list(repository.iter_edges()) == []


def test_order_query_writes_no_derived_rows(tmp_path: Path) -> None:
    """The judgment is recomputed per query; storage holds only authored rows."""

    repo = Repository.init(tmp_path)
    declare_temporal_frame(repo, frame_id="f1", description="clock")
    anchor_description_claim(
        repo,
        anchor_id="a1",
        claim_id="c1",
        frame_id="f1",
        valid_from=0.0,
        valid_until=1.0,
    )
    _edge(repo, "e1", "c1", "c2", "message")
    _edge(repo, "e2", "c2", "c3", "message")

    repository = TemporalRepository(backend=repo.require_git())
    before = (
        len(list(repository.iter_frames())),
        len(list(repository.iter_anchors())),
        len(list(repository.iter_edges())),
    )

    # Run several queries, including one that derives a multi-hop order.
    temporal_order_between(repo, "c1", "c3")
    temporal_order_between(repo, "c1", "c2", assume_complete=True)

    repository_after = TemporalRepository(backend=repo.require_git())
    after = (
        len(list(repository_after.iter_frames())),
        len(list(repository_after.iter_anchors())),
        len(list(repository_after.iter_edges())),
    )
    assert before == after == (1, 1, 2)
