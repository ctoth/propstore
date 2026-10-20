"""Attack relations follow their own parent's argument and claim occurrences."""

from pathlib import Path

import msgspec
import pytest
from quire.references import ForeignKeyValidationError

from propstore.app.events import (
    CoreferenceClustersReport,
    coreference_clusters,
    propose_coreference_merge_argument,
    record_coreference_attack,
)
from propstore.core.reasoning import ArgumentationSemantics
from propstore.core.render_policy import RenderPolicy
from propstore.families.coreference import (
    CoreferenceMergeArgumentDoc,
    CoreferenceMergeArgumentRepository,
    CoreferenceMergeArgumentRef,
    CoreferenceTransportConflict,
    coreference_proposal_branch,
    derive_coreference_argument_id,
)
from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness
from propstore.verify import verify_claim_tree
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


@pytest.mark.parametrize("shape", ["one_way", "mutual", "self", "cycle3"])
def test_authored_attack_graph_survives_with_correlated_claim_images(tmp_path: Path, shape: str) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    for claim_id, value in (("c", 250.0), ("s", 100.0), ("t", 80.0), ("u", 60.0)):
        author_param_claim(repo, claim_id, "x", value)
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    git.create_branch(proposal, source_commit=git.branch_sha("master"))
    canonical = git.branch_sha(proposal)
    assert repo.families.concept.require("x", commit=canonical).canonical_name == "x"
    assert {h.document.claim_id for h in repo.families.claim.iter_handles(commit=canonical)} == {"c", "s", "t", "u"}
    assert verify_claim_tree(repo, commit=canonical).ok
    supports = (("s", "c"), ("t", "c"), ("u", "c"))
    count = 3 if shape == "cycle3" else 1 if shape == "self" else 2
    ids = []
    for index, members in enumerate(supports[:count]):
        provenance = Provenance(
            status=ProvenanceStatus.STATED,
            witnesses=(ProvenanceWitness(
                asserter=f"urn:author:{index}", timestamp="2026-10-20T00:00:00Z",
                source_artifact_code=f"urn:evidence:{index}", method="authored hypothesis",
            ),),
            graph_name=f"urn:graph:{index}", derived_from=("urn:original",), operations=("original",),
        )
        ids.append(propose_coreference_merge_argument(
            repo, supports=members, description_claim_ids=("c", "s", "t", "u"),
            provenance=provenance, note=f"original hypothesis {index}",
        ).argument_id)
    links = [(0, 1)] if shape == "one_way" else [(0, 1), (1, 0)] if shape == "mutual" else [(0, 0)] if shape == "self" else [(0, 1), (1, 2), (2, 0)]
    for attacker, target in links:
        record_coreference_attack(repo, attacker_id=ids[attacker], target_id=ids[target])
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    source = git.branch_sha(proposal)
    bound = repo.families.proposal_coreference
    originals = tuple(bound.require(CoreferenceMergeArgumentRef(i), commit=source) for i in ids)
    git.create_branch("left", source_commit=source)
    git.create_branch("peer", source_commit=source)
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    parents = (git.branch_sha("left"), git.branch_sha("peer"))
    assert all(verify_claim_tree(repo, commit=parent).ok for parent in parents)
    merged = create_merge_commit(repo, "left", "peer", target_branch=proposal)
    assert verify_claim_tree(repo, commit=merged).ok
    documents = tuple(h.document for h in bound.iter_handles(commit=merged))
    assert len(documents) == 2 * count
    manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
    maps = {
        parent: {(image.family, image.source_id): image.target_id for image in manifest.reference_images
                 if image.source_commit == parent}
        for parent in parents
    }
    for images in maps.values():
        for original in originals:
            mapped_supports = tuple(images.get(("claim", i), i) for i in original.supports)
            expected_id = derive_coreference_argument_id(mapped_supports)
            assert images["proposal_coreference", original.argument_id] == expected_id
            transported = bound.require(CoreferenceMergeArgumentRef(expected_id), commit=merged)
            assert transported == msgspec.structs.replace(
                original, argument_id=expected_id, supports=mapped_supports,
                description_claim_ids=tuple(images.get(("claim", i), i) for i in original.description_claim_ids),
                attacks=tuple(images["proposal_coreference", i] for i in original.attacks),
            )
    assert sum(len(document.attacks) for document in documents) == 2 * len(links)
    # The real fixed-branch -> sidecar -> Dung path must still see the attacks.
    grounded = coreference_clusters(repo, RenderPolicy(semantics=ArgumentationSemantics.GROUNDED))
    assert isinstance(grounded, CoreferenceClustersReport)
    assert bool(grounded.clusters) is (shape == "one_way")
    if shape == "mutual":
        preferred = coreference_clusters(repo, RenderPolicy(semantics=ArgumentationSemantics.PREFERRED))
        assert isinstance(preferred, CoreferenceClustersReport)
        assert preferred.clusters
    for parent in parents:
        for original in originals:
            assert bound.require(CoreferenceMergeArgumentRef(original.argument_id), commit=parent) == original
    assert (git.branch_sha("left"), git.branch_sha("peer")) == parents


@pytest.mark.parametrize("difference", ["note", "provenance", "descriptions", "attacks"])
def test_same_argument_identity_cannot_discard_different_authored_evidence(tmp_path: Path, difference: str) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    for claim_id, value in (("c", 250.0), ("s", 100.0), ("t", 80.0)):
        author_param_claim(repo, claim_id, "x", value)
    git = repo.require_git()
    git.create_branch(coreference_proposal_branch(), source_commit=git.branch_sha("master"))
    target = propose_coreference_merge_argument(repo, supports=("s", "t")).argument_id
    provenance = Provenance(status=ProvenanceStatus.STATED, graph_name="urn:original")
    first = CoreferenceMergeArgumentDoc(
        argument_id="legacy:first", supports=("s", "c"), description_claim_ids=("s", "c"),
        provenance=provenance, note="original",
    )
    second = msgspec.structs.replace(
        first, argument_id="legacy:second",
        provenance=msgspec.structs.replace(provenance, graph_name="urn:other") if difference == "provenance" else provenance,
        note="other" if difference == "note" else first.note,
        description_claim_ids=("t", "c") if difference == "descriptions" else first.description_claim_ids,
        attacks=(target,) if difference == "attacks" else (),
    )
    bound = repo.families.proposal_coreference
    for document in (first, second):
        bound.save(CoreferenceMergeArgumentRef(document.argument_id), document, message="authored evidence")
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    source = git.branch_sha(proposal)
    git.create_branch("left", source_commit=source)
    git.create_branch("peer", source_commit=source)
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    with pytest.raises(CoreferenceTransportConflict, match="collapse distinct arguments"):
        create_merge_commit(repo, "left", "peer", target_branch=proposal)
    assert git.branch_sha(proposal) == source
    for document in (first, second):
        assert bound.require(CoreferenceMergeArgumentRef(document.argument_id), commit=source) == document


def test_unchanged_support_attacker_cannot_combine_different_parent_attack_images(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    for claim_id, value in (("c", 250.0), ("s", 100.0), ("t", 80.0)):
        author_param_claim(repo, claim_id, "x", value)
    git = repo.require_git()
    git.create_branch(coreference_proposal_branch(), source_commit=git.branch_sha("master"))
    attacker = propose_coreference_merge_argument(repo, supports=("s", "t")).argument_id
    target = propose_coreference_merge_argument(repo, supports=("s", "c")).argument_id
    record_coreference_attack(repo, attacker_id=attacker, target_id=target)
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    source = git.branch_sha(proposal)
    git.create_branch("left", source_commit=source)
    git.create_branch("peer", source_commit=source)
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    with pytest.raises(NonClaimMergeConflict):
        create_merge_commit(repo, "left", "peer", target_branch=proposal)
    assert git.branch_sha(proposal) == source
    assert repo.families.proposal_coreference.require(CoreferenceMergeArgumentRef(attacker), commit=source).attacks == (target,)


def test_unchanged_legacy_cycle_retains_nominal_ids_and_raw_reads(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    for claim_id, value in (("c", 250.0), ("s", 100.0), ("t", 80.0), ("u", 60.0)):
        author_param_claim(repo, claim_id, "x", value)
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    git.create_branch(proposal, source_commit=git.branch_sha("master"))
    provenance = Provenance(status=ProvenanceStatus.STATED)
    ids = ("cma:legacy-one", "ni:///sha-256;legacy-two")
    documents = (
        CoreferenceMergeArgumentDoc(argument_id=ids[0], supports=("s", "t"), description_claim_ids=("s", "t"), attacks=(ids[1],), provenance=provenance),
        CoreferenceMergeArgumentDoc(argument_id=ids[1], supports=("t", "u"), description_claim_ids=("t", "u"), attacks=(ids[0],), provenance=provenance),
    )
    bound = repo.families.proposal_coreference
    with repo.families.transact(message="legacy records", branch=proposal) as transaction:
        for document in documents:
            transaction.by_name("proposal_coreference").save(CoreferenceMergeArgumentRef(document.argument_id), document)
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    source = git.branch_sha(proposal)
    git.create_branch("left", source_commit=source)
    git.create_branch("peer", source_commit=source)
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    merged = create_merge_commit(repo, "left", "peer", target_branch=proposal)
    assert verify_claim_tree(repo, commit=merged).ok
    assert {h.ref.argument_id for h in bound.iter_handles(commit=merged)} == set(ids)
    for document in documents:
        for commit in (source, merged):
            assert bound.require(CoreferenceMergeArgumentRef(document.argument_id), commit=commit) == document


def test_unresolved_legacy_attack_remains_readable_but_cannot_silently_merge(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    git = repo.require_git()
    git.create_branch(coreference_proposal_branch(), source_commit=git.branch_sha("master"))
    provenance = Provenance(status=ProvenanceStatus.STATED)
    document = CoreferenceMergeArgumentDoc(
        argument_id="legacy", supports=("c",), description_claim_ids=("c",),
        attacks=("missing-argument",), provenance=provenance,
    )
    bound = repo.families.proposal_coreference
    CoreferenceMergeArgumentRepository(backend=git).author(document, message="legacy unresolved attack")
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    source = git.branch_sha(proposal)
    git.create_branch("peer", source_commit=source)
    assert bound.require(CoreferenceMergeArgumentRef("legacy"), commit=source) == document
    with pytest.raises(ForeignKeyValidationError, match="coreference_attacks.*does not resolve"):
        create_merge_commit(repo, proposal, "peer", target_branch=proposal)
    assert git.branch_sha(proposal) == source


def test_legacy_mutual_arguments_cannot_collapse_to_self_attack(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    author_param_claim(repo, "s", "x", 100.0)
    git = repo.require_git()
    proposal = coreference_proposal_branch()
    git.create_branch(proposal, source_commit=git.branch_sha("master"))
    provenance = Provenance(status=ProvenanceStatus.STATED)
    first = CoreferenceMergeArgumentDoc(
        argument_id="legacy:A", supports=("s", "c"), description_claim_ids=("s", "c"),
        attacks=("legacy:B",), provenance=provenance, note="same evidence",
    )
    second = msgspec.structs.replace(first, argument_id="legacy:B", attacks=("legacy:A",))
    bound = repo.families.proposal_coreference
    with repo.families.transact(message="valid legacy mutual attack", branch=proposal) as transaction:
        for document in (first, second):
            transaction.by_name("proposal_coreference").save(CoreferenceMergeArgumentRef(document.argument_id), document)
    source = git.branch_sha(proposal)
    for document in (first, second):
        assert bound.require(CoreferenceMergeArgumentRef(document.argument_id), commit=source) == document
    assert verify_claim_tree(repo, commit=source).ok
    before = coreference_clusters(repo, RenderPolicy(semantics=ArgumentationSemantics.PREFERRED))
    assert isinstance(before, CoreferenceClustersReport)
    assert before.clusters
    git.create_branch("left", source_commit=source)
    git.create_branch("peer", source_commit=source)
    author_param_claim(repo, "c", "x", 300.0, branch="left")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    parents = (git.branch_sha("left"), git.branch_sha("peer"))
    assert all(verify_claim_tree(repo, commit=parent).ok for parent in parents)
    with pytest.raises(CoreferenceTransportConflict, match="collapse distinct arguments"):
        create_merge_commit(repo, "left", "peer", target_branch=proposal)
    assert git.branch_sha(proposal) == source
    assert (git.branch_sha("left"), git.branch_sha("peer")) == parents
    for parent in (source, *parents):
        for document in (first, second):
            assert bound.require(CoreferenceMergeArgumentRef(document.argument_id), commit=parent) == document
    after = coreference_clusters(repo, RenderPolicy(semantics=ArgumentationSemantics.PREFERRED))
    assert isinstance(after, CoreferenceClustersReport)
    assert after == before
