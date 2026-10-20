"""A merge transports each parent's complete graph with correlated incidence."""

from pathlib import Path

import pytest
import msgspec

from propstore.families.contexts import Context
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.merge.merge_commit import create_merge_commit, NonClaimMergeConflict
from propstore.families.identity.micropubs import micropub_artifact_id, micropub_version_id
from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.identity.justifications import derive_justification_artifact_id
from propstore.families.micropublications import MicropublicationEvidence
from propstore.stances import StanceType
from propstore.verify import verify_claim_tree
from propstore.families.sources import SourceMicropublicationDocument
from propstore.families.temporal import DescriptionTemporalAnchorDoc, HappensBeforeEdgeDoc, TemporalFrameDoc
from propstore.families.coreference import CoreferenceMergeArgumentDoc, CoreferenceMergeArgumentRef
from propstore.provenance import Provenance, ProvenanceStatus
from propstore.core.lemon.temporal import HappensBeforeAccount
from quire.family_transport import UnsupportedFamilyTransportError
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


@pytest.mark.parametrize(
    ("family", "source", "target"),
    [
        ("stance", "c", "s"),
        ("stance", "s", "c"),
        ("justification", "c", "s"),
        ("justification", "s", "c"),
        ("micropublication", "s", "c"),
    ],
)
@pytest.mark.parametrize("existing_target", [False, True])
def test_parent_occurrences_survive_as_reidentified_graph_images(
    tmp_path: Path,
    family: str,
    source: str,
    target: str,
    existing_target: bool,
) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    if family == "stance":
        document = Stance(
            stance_id="edge", source_claim_id=source,
            target_claim_id=target, stance_type=StanceType.SUPPORTS,
        )
        repo.families.stance.save("edge", document, message="support")
    elif family == "justification":
        document = Justification(
            justification_id="edge", conclusion=target, premises=(source,),
        )
        repo.families.justification.save("edge", document, message="justification")
    else:
        repo.families.context.save(
            "ctx", Context(context_id="ctx", name="ctx"), message="context"
        )
        document = Micropublication(
            artifact_id="edge", context_id="ctx", claims=(target,),
            source="urn:source:paper",
        )
        repo.families.micropublication.save("edge", document, message="bundle")

    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    left, right = git.branch_sha("master"), git.branch_sha("peer")
    assert left is not None and right is not None
    assert verify_claim_tree(repo, commit=left).ok
    assert verify_claim_tree(repo, commit=right).ok
    if existing_target:
        git.create_branch("result", source_commit=left)
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert verify_claim_tree(repo, commit=merged).ok
    images = tuple(repo.families.by_name(family).iter_handles(commit=merged))
    assert len(images) == 2
    manifests = tuple(repo.families.merge_manifest.iter_handles(commit=merged))
    witnesses = tuple(i for i in manifests[0].document.reference_images if i.family == family)
    assert {i.source_commit for i in witnesses} == {left, right}
    assert {i.source_id for i in witnesses} == {"edge"}
    assert len({i.target_id for i in witnesses}) == 2
    assert git.branch_sha("result") == merged
    assert git.branch_sha("master") == left
    assert git.branch_sha("peer") == right
    # Both input commits retain the original evidence row and its old identity.
    for commit in (left, right):
        assert repo.families.by_name(family).require("edge", commit=commit) == document


def test_reference_to_one_surviving_claim_identity_still_merges(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    repo.families.stance.save(
        "edge", Stance(stance_id="edge", source_claim_id="c", target_claim_id="c"),
        message="self relation",
    )
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 300.0, branch="peer")
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert verify_claim_tree(repo, commit=merged).ok
    assert repo.families.claim.require("c", commit=merged).value == 300.0
    assert repo.families.stance.require("edge", commit=merged).target_claim_id == "c"


def test_rival_graphs_keep_endpoint_pairs_principal_and_evidence(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    edge = Stance(
        stance_id="edge", source_claim_id="s", target_claim_id="c",
        stance_type=StanceType.SUPPORTS, resolution_model="authored",
        confidence=0.8, opinion_belief=0.6, opinion_disbelief=0.1,
        opinion_uncertainty=0.3, opinion_base_rate=0.5,
    )
    justification = Justification(
        justification_id="reason", conclusion="c", premises=("s",),
        rule_kind="strict", rule_strength="authored",
    )
    repo.families.stance.save("edge", edge, message="support")
    repo.families.justification.save("reason", justification, message="reason")
    repo.families.context.save("ctx", Context(context_id="ctx", name="ctx"), message="context")
    bundle = Micropublication(
        artifact_id="bundle", context_id="ctx", claims=("s", "c"), principal_claim="c",
        evidence=(MicropublicationEvidence("quotation", "urn:evidence:original"),),
        assumptions=("authored condition",), stance=StanceType.SUPPORTS,
        source="urn:source:original",
    )
    repo.families.micropublication.save("bundle", bundle, message="bundle")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    for branch, c, s in (("master", 300.0, 110.0), ("peer", 150.0, 90.0)):
        author_param_claim(repo, "c", "x", c, branch=branch)
        author_param_claim(repo, "s", "x", s, branch=branch)
    parents = (git.branch_sha("master"), git.branch_sha("peer"))
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert verify_claim_tree(repo, commit=merged).ok
    manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
    maps = {
        parent: {(i.family, i.source_id): i.target_id for i in manifest.reference_images if i.source_commit == parent}
        for parent in parents
    }
    expected_pairs = {(images["claim", "s"], images["claim", "c"]) for images in maps.values()}
    stances = tuple(h.document for h in repo.families.stance.iter_handles(commit=merged))
    assert len(stances) == 2
    assert {(e.source_claim_id, e.target_claim_id) for e in stances} == expected_pairs
    for transported in stances:
        assert transported == msgspec.structs.replace(
            edge, stance_id=transported.stance_id,
            source_claim_id=transported.source_claim_id, target_claim_id=transported.target_claim_id,
        )
        assert transported.stance_id == derive_stance_artifact_id(
            source_claim_id=transported.source_claim_id, target_claim_id=transported.target_claim_id,
            stance_type=transported.stance_type.value,
        )
    reasons = tuple(h.document for h in repo.families.justification.iter_handles(commit=merged))
    assert len(reasons) == 2
    assert {(j.premises[0], j.conclusion) for j in reasons} == expected_pairs
    for reason in reasons:
        assert reason.justification_id == derive_justification_artifact_id(
            conclusion=reason.conclusion, premises=reason.premises,
            rule_kind=reason.rule_kind, rule_strength=reason.rule_strength,
        )
    bundles = tuple(h.document for h in repo.families.micropublication.iter_handles(commit=merged))
    assert len(bundles) == 2
    assert {b.claims for b in bundles} == expected_pairs
    for transported in bundles:
        assert transported.principal_claim == transported.claims[1]
        assert transported.artifact_id == micropub_artifact_id(transported)
        assert transported.version_id == micropub_version_id(transported)
        assert transported == msgspec.structs.replace(
            bundle, artifact_id=transported.artifact_id, version_id=transported.version_id,
            claims=transported.claims, principal_claim=transported.principal_claim,
        )
    for parent in parents:
        assert repo.families.stance.require("edge", commit=parent) == edge
        assert repo.families.micropublication.require("bundle", commit=parent) == bundle


def test_equal_transported_rows_coalesce_without_losing_parent_witnesses(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    edge = Stance(stance_id="first", target_claim_id="c")
    repo.families.stance.save("first", edge, message="first occurrence")
    repo.families.stance.save("second", msgspec.structs.replace(edge, stance_id="second"), message="second occurrence")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    merged = create_merge_commit(repo, "master", "peer", target_branch="result")
    assert len(tuple(repo.families.stance.iter_handles(commit=merged))) == 2
    manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
    witnesses = tuple(i for i in manifest.reference_images if i.family == "stance")
    assert len(witnesses) == 4
    assert {i.source_id for i in witnesses} == {"first", "second"}


def test_identity_collision_with_different_evidence_cannot_overwrite(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    edge = Stance(stance_id="first", target_claim_id="c", resolution_model="first")
    repo.families.stance.save("first", edge, message="first opinion")
    repo.families.stance.save("second", msgspec.structs.replace(edge, stance_id="second", resolution_model="second"), message="second opinion")
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    before = git.branch_sha("master")
    with pytest.raises(NonClaimMergeConflict):
        create_merge_commit(repo, "master", "peer", target_branch="result")
    assert git.branch_sha("result") is None
    assert git.branch_sha("master") == before


def test_micropublication_identity_preserves_source_payload_and_explicit_principal() -> None:
    source = SourceMicropublicationDocument(
        artifact_id="old", context_id="ctx", claims=("c",), source="urn:paper",
    )
    canonical = Micropublication(
        artifact_id="old", context_id="ctx", claims=("c",), source="urn:paper",
    )
    assert micropub_artifact_id(source) == micropub_artifact_id(canonical)
    assert micropub_version_id(source) == micropub_version_id(canonical)
    assert micropub_artifact_id(canonical) != micropub_artifact_id(
        msgspec.structs.replace(canonical, principal_claim="c")
    )


@pytest.mark.parametrize("family", ["description_temporal_anchor", "happens_before_edge", "proposal_coreference"])
def test_unsupported_family_identity_keeps_target_and_input_evidence(tmp_path: Path, family: str) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    provenance = Provenance(status=ProvenanceStatus.STATED)
    bound = repo.families.by_name(family)
    if family == "description_temporal_anchor":
        repo.families.temporal_frame.save(
            "f", TemporalFrameDoc(frame_id="f", description="authored clock", provenance=provenance),
            message="frame",
        )
        document = DescriptionTemporalAnchorDoc(
            anchor_id="e", claim_id="c", frame_id="f", provenance=provenance, valid_from=2.0,
        )
        ref = "e"
    elif family == "happens_before_edge":
        document = HappensBeforeEdgeDoc(
            edge_id="e", earlier_claim_id="s", later_claim_id="c",
            account=HappensBeforeAccount.MESSAGE, provenance=provenance,
        )
        ref = "e"
    else:
        document = CoreferenceMergeArgumentDoc(
            argument_id="e", supports=("s", "c"), description_claim_ids=("s", "c"),
            provenance=provenance, note="authored proposal",
        )
        ref = CoreferenceMergeArgumentRef("e")
    # Fixed proposal placement is authored on its own branch, then the real
    # proposal tree is the starting point for both input instances.
    git = repo.require_git()
    if family == "proposal_coreference":
        git.create_branch("proposal/coreference", source_commit=git.branch_sha("master"))
        bound.save(ref, document, message="evidence")
        source = git.branch_sha("proposal/coreference")
        git.create_branch("left", source_commit=source)
    else:
        bound.save(ref, document, message="evidence")
        git.create_branch("left", source_commit=git.branch_sha("master"))
    git.create_branch("peer", source_commit=git.branch_sha("left"))
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    left, right = git.branch_sha("left"), git.branch_sha("peer")
    git.create_branch("result", source_commit=left)
    with pytest.raises(UnsupportedFamilyTransportError, match=family):
        create_merge_commit(repo, "left", "peer", target_branch="result")
    assert git.branch_sha("result") == left
    for commit in (left, right):
        assert bound.require(ref, commit=commit) == document
