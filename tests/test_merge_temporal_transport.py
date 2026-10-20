"""Authored temporal evidence follows its own pinned parent occurrence."""

from pathlib import Path

import msgspec
import pytest

from propstore.app.temporal import temporal_order_between
from propstore.core.lemon.temporal import HappensBeforeAccount, TemporalOrderVerdict
from propstore.families.identity.temporal import (
    happens_before_artifact_id,
    temporal_anchor_artifact_id,
)
from propstore.families.temporal import (
    DescriptionTemporalAnchorDoc,
    HappensBeforeEdgeDoc,
    TemporalFrameDoc,
)
from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.verify import verify_claim_tree
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


@pytest.mark.parametrize("account", tuple(HappensBeforeAccount))
@pytest.mark.parametrize("bounds", [(3.0, 4.0), (3.0, None), (None, None)])
def test_temporal_graph_transport_preserves_incidence_and_query_evidence(
    tmp_path: Path,
    account: HappensBeforeAccount,
    bounds: tuple[float | None, float | None],
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    provenance = Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(ProvenanceWitness(
            asserter="urn:author", timestamp="2026-10-20T00:00:00Z",
            source_artifact_code="urn:evidence", method="authored observation",
        ),),
        graph_name="urn:graph:original", derived_from=("urn:source:original",),
        operations=("original observation",),
    )
    frame = TemporalFrameDoc(frame_id="clock", description="authored clock", provenance=provenance)
    anchor = DescriptionTemporalAnchorDoc(
        anchor_id="anchor", claim_id="c", frame_id="clock", provenance=provenance,
        valid_from=bounds[0], valid_until=bounds[1],
    )
    edge = HappensBeforeEdgeDoc(
        edge_id="edge", earlier_claim_id="s", later_claim_id="c",
        account=account, provenance=provenance,
    )
    repo.families.temporal_frame.save("clock", frame, message="clock")
    repo.families.description_temporal_anchor.save("anchor", anchor, message="anchor")
    repo.families.happens_before_edge.save("edge", edge, message="order")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    for branch, c, s in (("master", 300.0, 110.0), ("peer", 150.0, 90.0)):
        author_param_claim(repo, "c", "x", c, branch=branch)
        author_param_claim(repo, "s", "x", s, branch=branch)
    parents = (git.branch_sha("master"), git.branch_sha("peer"))
    assert all(verify_claim_tree(repo, commit=parent).ok for parent in parents)
    merged = create_merge_commit(repo, "master", "peer")
    assert verify_claim_tree(repo, commit=merged).ok
    manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
    maps = {
        parent: {(image.family, image.source_id): image.target_id
                 for image in manifest.reference_images if image.source_commit == parent}
        for parent in parents
    }
    anchors = tuple(h.document for h in repo.families.description_temporal_anchor.iter_handles(commit=merged))
    edges = tuple(h.document for h in repo.families.happens_before_edge.iter_handles(commit=merged))
    assert len(anchors) == len(edges) == 2
    assert {a.claim_id for a in anchors} == {images["claim", "c"] for images in maps.values()}
    expected_pairs = {(images["claim", "s"], images["claim", "c"]) for images in maps.values()}
    assert {(e.earlier_claim_id, e.later_claim_id) for e in edges} == expected_pairs
    for images in maps.values():
        transported_anchor = repo.families.description_temporal_anchor.require(
            images["description_temporal_anchor", "anchor"], commit=merged,
        )
        assert transported_anchor == msgspec.structs.replace(
            anchor, anchor_id=temporal_anchor_artifact_id(transported_anchor),
            claim_id=images["claim", "c"],
        )
        transported_edge = repo.families.happens_before_edge.require(
            images["happens_before_edge", "edge"], commit=merged,
        )
        assert transported_edge == msgspec.structs.replace(
            edge, edge_id=happens_before_artifact_id(transported_edge),
            earlier_claim_id=images["claim", "s"], later_claim_id=images["claim", "c"],
        )
        # Read the actual merged master through the sidecar/query owners. A
        # foreign-key-valid row that lost its account/provenance is not enough.
        judgment = temporal_order_between(
            repo, images["claim", "s"], images["claim", "c"],
        ).judgment
        assert judgment.verdict is TemporalOrderVerdict.BEFORE
        assert len(judgment.forward_path) == 1
        assert judgment.forward_path[0].edge_id == transported_edge.edge_id
        assert judgment.forward_path[0].account is account
    for parent in parents:
        assert repo.families.description_temporal_anchor.require("anchor", commit=parent) == anchor
        assert repo.families.happens_before_edge.require("edge", commit=parent) == edge
    assert repo.families.temporal_frame.require("clock", commit=merged) == frame


@pytest.mark.parametrize("family", ["description_temporal_anchor", "happens_before_edge"])
@pytest.mark.parametrize("different_provenance", [False, True])
def test_equal_temporal_images_coalesce_only_with_identical_evidence(
    tmp_path: Path, family: str, different_provenance: bool,
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    provenance = Provenance(status=ProvenanceStatus.STATED, graph_name="urn:first")
    other_provenance = msgspec.structs.replace(provenance, graph_name="urn:second") if different_provenance else provenance
    bound = repo.families.by_name(family)
    if family == "description_temporal_anchor":
        repo.families.temporal_frame.save(
            "clock", TemporalFrameDoc(frame_id="clock", description="clock", provenance=provenance), message="clock",
        )
        first = DescriptionTemporalAnchorDoc(
            anchor_id="first", claim_id="c", frame_id="clock", provenance=provenance,
            valid_from=1.0, valid_until=2.0,
        )
        second = msgspec.structs.replace(first, anchor_id="second", provenance=other_provenance)
    else:
        first = HappensBeforeEdgeDoc(
            edge_id="first", earlier_claim_id="s", later_claim_id="c",
            account=HappensBeforeAccount.MESSAGE, provenance=provenance,
        )
        second = msgspec.structs.replace(first, edge_id="second", provenance=other_provenance)
    bound.save("first", first, message="first evidence")
    bound.save("second", second, message="second evidence")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    left, right = git.branch_sha("master"), git.branch_sha("peer")
    git.create_branch("result", source_commit=left)
    if different_provenance:
        with pytest.raises(NonClaimMergeConflict):
            create_merge_commit(repo, "master", "peer", target_branch="result")
        assert git.branch_sha("result") == left
    else:
        merged = create_merge_commit(repo, "master", "peer", target_branch="result")
        assert verify_claim_tree(repo, commit=merged).ok
        assert len(tuple(bound.iter_handles(commit=merged))) == 2
        manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
        witnesses = tuple(image for image in manifest.reference_images if image.family == family)
        assert len(witnesses) == 4
        assert {image.source_id for image in witnesses} == {"first", "second"}
        assert {image.source_commit for image in witnesses} == {left, right}
        assert len({image.target_id for image in witnesses}) == 2
    for parent in (left, right):
        assert bound.require("first", commit=parent) == first
        assert bound.require("second", commit=parent) == second
    assert git.branch_sha("master") == left
    assert git.branch_sha("peer") == right


@pytest.mark.parametrize("family", ["description_temporal_anchor", "happens_before_edge"])
@pytest.mark.parametrize("old_id", ["authored-record", "ni:///sha-256;authored-record"])
def test_unchanged_temporal_evidence_keeps_old_identity_and_raw_placement(
    tmp_path: Path, family: str, old_id: str,
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    for claim_id, value in (("c", 250.0), ("s", 100.0), ("u", 80.0)):
        author_param_claim(repo, claim_id, "x", value)
    provenance = Provenance(status=ProvenanceStatus.STATED)
    bound = repo.families.by_name(family)
    if family == "description_temporal_anchor":
        repo.families.temporal_frame.save(
            "clock", TemporalFrameDoc(frame_id="clock", description="clock", provenance=provenance), message="clock",
        )
        document = DescriptionTemporalAnchorDoc(
            anchor_id=old_id, claim_id="s", frame_id="clock", provenance=provenance,
        )
    else:
        document = HappensBeforeEdgeDoc(
            edge_id=old_id, earlier_claim_id="s", later_claim_id="u",
            account=HappensBeforeAccount.STATED, provenance=provenance,
        )
    bound.save(old_id, document, message="prechange evidence")
    git = repo.require_git()
    original = git.branch_sha("master")
    assert bound.require(old_id, commit=original) == document
    git.create_branch("peer", source_commit=original)
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert verify_claim_tree(repo, commit=merged).ok
    assert bound.require(old_id, commit=merged) == document
    handles = tuple(bound.iter_handles(commit=merged))
    assert len(handles) == 1
    assert handles[0].ref == old_id
    assert handles[0].document == document
    assert bound.require(old_id, commit=original) == document


@pytest.mark.parametrize("difference", ["frame", "from", "until", "account", "direction"])
def test_distinct_authored_temporal_content_survives_transport(
    tmp_path: Path, difference: str,
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    provenance = Provenance(status=ProvenanceStatus.STATED)
    if difference in {"frame", "from", "until"}:
        bound = repo.families.description_temporal_anchor
        for frame_id in ("clock", "other-clock"):
            repo.families.temporal_frame.save(
                frame_id, TemporalFrameDoc(frame_id=frame_id, description=frame_id, provenance=provenance),
                message="frame",
            )
        first = DescriptionTemporalAnchorDoc(
            anchor_id="first", claim_id="c", frame_id="clock", provenance=provenance,
            valid_from=1.0, valid_until=2.0,
        )
        second = msgspec.structs.replace(
            first, anchor_id="second",
            frame_id="other-clock" if difference == "frame" else "clock",
            valid_from=None if difference == "from" else 1.0,
            valid_until=None if difference == "until" else 2.0,
        )
    else:
        bound = repo.families.happens_before_edge
        first = HappensBeforeEdgeDoc(
            edge_id="first", earlier_claim_id="s", later_claim_id="c",
            account=HappensBeforeAccount.MESSAGE, provenance=provenance,
        )
        second = msgspec.structs.replace(
            first, edge_id="second",
            account=HappensBeforeAccount.STATED if difference == "account" else first.account,
            earlier_claim_id="c" if difference == "direction" else "s",
            later_claim_id="s" if difference == "direction" else "c",
        )
    bound.save("first", first, message="first evidence")
    bound.save("second", second, message="rival evidence")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    merged = create_merge_commit(repo, "master", "peer")
    assert verify_claim_tree(repo, commit=merged).ok
    documents = tuple(h.document for h in bound.iter_handles(commit=merged))
    assert len(documents) == 4
    if difference in {"frame", "from", "until"}:
        assert {(d.frame_id, d.valid_from, d.valid_until) for d in documents} == {
            (first.frame_id, first.valid_from, first.valid_until),
            (second.frame_id, second.valid_from, second.valid_until),
        }
    else:
        assert {d.account for d in documents} == {first.account, second.account}
        manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
        c_images = {image.target_id for image in manifest.reference_images
                    if image.family == "claim" and image.source_id == "c"}
        for claim_id in c_images:
            judgment = temporal_order_between(repo, "s", claim_id).judgment
            assert judgment.verdict is (
                TemporalOrderVerdict.CONFLICTED if difference == "direction" else TemporalOrderVerdict.BEFORE
            )
            if difference == "direction":
                assert judgment.forward_path and judgment.backward_path
