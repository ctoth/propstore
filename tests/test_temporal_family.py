"""Temporal storage families: charter round-trips, invariants, non-committal projection.

Proves the storage half of the happens-before path: frames, description anchors,
and happens-before edges round-trip through git, their invariants (optional
bounds, ordered bounds, mandatory valid account) hold at the charter, and EVERY
row — including two rival cyclic edges — reaches the sidecar (non-commitment; the
order verdict is a render-time decision tested at the app layer).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from quire.git_store import GitStore
from quire.sqlalchemy_store import readonly_session
from sqlalchemy import select

from propstore.families.registry import registered_family_names
from propstore.families.temporal import (
    DescriptionTemporalAnchorDoc,
    HappensBeforeEdgeDoc,
    TemporalFrameDoc,
    TemporalRepository,
    stated_provenance,
)
from propstore.provenance import ProvenanceStatus


def test_families_are_registered() -> None:
    names = set(registered_family_names())
    assert {
        "temporal_frame",
        "description_temporal_anchor",
        "happens_before_edge",
    } <= names


def test_frame_anchor_edge_round_trip() -> None:
    repository = TemporalRepository(backend=GitStore.init_memory())
    repository.author_frame(
        TemporalFrameDoc(frame_id="f1", description="machine clock", provenance=stated_provenance()),
        message="declare f1",
    )
    # An anchor with only ONE bound: the other stays absent (honest ignorance).
    repository.author_anchor(
        DescriptionTemporalAnchorDoc(
            anchor_id="a1",
            claim_id="c1",
            frame_id="f1",
            provenance=stated_provenance(),
            valid_from=3.0,
        ),
        message="anchor c1",
    )
    repository.author_edge(
        HappensBeforeEdgeDoc(
            edge_id="e1",
            earlier_claim_id="c1",
            later_claim_id="c2",
            account="message",
            provenance=stated_provenance(),
        ),
        message="assert e1",
    )

    frame = repository.get_frame("f1")
    assert frame is not None and frame.description == "machine clock"
    anchor = repository.get_anchor("a1")
    assert anchor is not None
    assert anchor.valid_from == 3.0
    assert anchor.valid_until is None
    assert anchor.provenance.status is ProvenanceStatus.STATED
    edge = repository.get_edge("e1")
    assert edge is not None and edge.account == "message"


def test_misordered_bounds_are_rejected() -> None:
    with pytest.raises(ValueError, match="valid_from <= valid_until"):
        DescriptionTemporalAnchorDoc(
            anchor_id="a2",
            claim_id="c1",
            frame_id="f1",
            provenance=stated_provenance(),
            valid_from=9.0,
            valid_until=1.0,
        )


def test_bogus_account_is_rejected() -> None:
    with pytest.raises(ValueError):
        HappensBeforeEdgeDoc(
            edge_id="e2",
            earlier_claim_id="c1",
            later_claim_id="c2",
            account="whenever",
            provenance=stated_provenance(),
        )


def test_self_edge_is_rejected() -> None:
    with pytest.raises(ValueError, match="two distinct descriptions"):
        HappensBeforeEdgeDoc(
            edge_id="e3",
            earlier_claim_id="c1",
            later_claim_id="c1",
            account="message",
            provenance=stated_provenance(),
        )


def test_edge_sidecar_projects_every_rival_of_a_cycle(tmp_path: Path) -> None:
    repository = TemporalRepository(backend=GitStore.init_memory())
    repository.author_edge(
        HappensBeforeEdgeDoc(
            edge_id="fwd",
            earlier_claim_id="c1",
            later_claim_id="c2",
            account="message",
            provenance=stated_provenance(),
        ),
        message="c1->c2",
    )
    repository.author_edge(
        HappensBeforeEdgeDoc(
            edge_id="bwd",
            earlier_claim_id="c2",
            later_claim_id="c1",
            account="message",
            provenance=stated_provenance(),
        ),
        message="c2->c1",
    )

    sidecar = tmp_path / "edges.sqlite"
    schema = repository.build_edge_sidecar(sidecar)
    model = schema.model("happens_before_edge")
    with readonly_session(sidecar, schema) as session:
        rows = {row.edge_id for row in session.scalars(select(model))}
    assert rows == {"fwd", "bwd"}


def test_repo_backed_repository_authors_to_master(tmp_path: Path) -> None:
    from propstore.repository import Repository

    repo = Repository.init(tmp_path)
    repository = TemporalRepository(backend=repo.require_git())
    repository.author_frame(
        TemporalFrameDoc(frame_id="f1", description="clock", provenance=stated_provenance()),
        message="declare f1",
    )
    assert {frame.frame_id for frame in repository.iter_frames()} == {"f1"}
    assert repository.get_frame("f1") is not None
