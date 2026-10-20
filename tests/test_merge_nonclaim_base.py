"""Base-relative ordinary versions must survive family occurrence transport."""

from pathlib import Path

import msgspec
import pytest
import yaml
from click.testing import CliRunner
from quire.git_store import AmbiguousMergeBaseError
from quire.references import ForeignKeyValidationError

from propstore.app.merge import MergeCommitRequest, commit_merge
from propstore.cli import cli
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from propstore.stances import StanceType
from propstore.verify import verify_claim_tree
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


def _seed(tmp_path: Path, family: str):
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    if family == "concept":
        ref = "ordinary"
        document = Concept(concept_id=ref, canonical_name="ordinary")
    elif family == "stance":
        ref = "edge"
        document = Stance(stance_id=ref, source_claim_id="c", target_claim_id="c", stance_type=StanceType.SUPPORTS, confidence=0.4)
    else:
        repo.families.context.save("ctx", Context(context_id="ctx", name="ctx"), message="context")
        ref = "ni:///bundle/evidence"
        document = Micropublication(artifact_id=ref, context_id="ctx", claims=("c",), source="urn:paper:base")
    bound = repo.families.by_name(family)
    base = bound.save(ref, document, message="base ordinary evidence")
    repo.require_git().create_branch("peer", source_commit=base)
    return repo, bound, ref, document, base


def _changed(document):
    if isinstance(document, Concept):
        return msgspec.structs.replace(document, canonical_name="updated")
    if isinstance(document, Stance):
        return msgspec.structs.replace(document, confidence=0.8)
    return msgspec.structs.replace(document, source="urn:paper:updated")


@pytest.mark.parametrize("family", ["concept", "stance", "micropublication"])
@pytest.mark.parametrize("reverse", [False, True])
def test_unchanged_peer_does_not_resurrect_deleted_family(tmp_path, family, reverse):
    repo, bound, ref, original, base = _seed(tmp_path, family)
    deleted = bound.delete(ref, message="explicit deletion", branch="master")
    git = repo.require_git()
    assert verify_claim_tree(repo, commit=deleted).ok
    assert verify_claim_tree(repo, commit=base).ok
    assert bound.load(ref, commit=deleted) is None
    sources = ("peer", "master") if reverse else ("master", "peer")
    merged = create_merge_commit(repo, *sources, target_branch="result")
    actual = bound.load(ref, commit=merged)
    assert actual is None
    assert verify_claim_tree(repo, commit=merged).ok
    assert list(git.iter_commit_parent_shas(merged)) == ([base, deleted] if reverse else [deleted, base])
    assert bound.require(ref, commit=base) == original
    assert git.branch_sha("master") == deleted
    assert git.branch_sha("peer") == base


@pytest.mark.parametrize("family", ["concept", "stance", "micropublication"])
@pytest.mark.parametrize("reverse", [False, True])
def test_modify_delete_conflict_keeps_target_and_parent_evidence(tmp_path, family, reverse):
    repo, bound, ref, original, base = _seed(tmp_path, family)
    modified_document = _changed(original)
    modified = bound.save(ref, modified_document, message="changed evidence", branch="master")
    deleted = bound.delete(ref, message="competing deletion", branch="peer")
    git = repo.require_git()
    git.create_branch("result", source_commit=base)
    sources = ("peer", "master") if reverse else ("master", "peer")
    with pytest.raises(NonClaimMergeConflict) as caught:
        create_merge_commit(repo, *sources, target_branch="result")
    assert caught.value.family == family
    stored_path = next(handle.address.require_path() for handle in bound.iter_handles(commit=base) if handle.document == original)
    assert caught.value.path == stored_path
    assert git.branch_sha("result") == base
    assert (git.branch_sha("master"), git.branch_sha("peer")) == (modified, deleted)
    assert bound.require(ref, commit=modified) == modified_document
    assert bound.load(ref, commit=deleted) is None


@pytest.mark.parametrize("family", ["concept", "stance", "micropublication"])
@pytest.mark.parametrize("reverse", [False, True])
def test_one_sided_ordinary_modification_uses_selected_parent_document(tmp_path, family, reverse):
    repo, bound, ref, original, base = _seed(tmp_path, family)
    changed = _changed(original)
    modified = bound.save(ref, changed, message="one-sided edit", branch="master")
    sources = ("peer", "master") if reverse else ("master", "peer")
    merged = create_merge_commit(repo, *sources, target_branch="result")
    assert bound.require(ref, commit=merged) == changed
    assert bound.require(ref, commit=base) == original
    assert repo.require_git().branch_sha("master") == modified
    assert verify_claim_tree(repo, commit=merged).ok


@pytest.mark.parametrize("family", ["stance", "micropublication"])
@pytest.mark.parametrize("entrypoint", ["app", "cli"])
def test_app_and_cli_keep_deletion_and_both_parent_snapshots(tmp_path, family, entrypoint):
    repo, bound, ref, original, base = _seed(tmp_path, family)
    deleted = bound.delete(ref, message="explicit deletion", branch="master")
    if entrypoint == "app":
        report = commit_merge(repo, MergeCommitRequest("master", "peer", target_branch="result"))
        merged = report.commit_sha
    else:
        result = CliRunner().invoke(cli, ["-C", str(repo.root), "merge", "commit", "master", "peer", "--target-branch", "result"])
        assert result.exit_code == 0, result.output
        merged = yaml.safe_load(result.output)["commit_sha"]
    git = repo.require_git()
    assert bound.load(ref, commit=merged) is None
    assert bound.require(ref, commit=base) == original
    assert bound.load(ref, commit=deleted) is None
    assert list(git.iter_commit_parent_shas(merged)) == [deleted, base]
    assert verify_claim_tree(repo, commit=merged).ok


@pytest.mark.parametrize("family", ["stance", "micropublication"])
def test_cli_modify_delete_renders_conflict_and_keeps_target(tmp_path, family):
    repo, bound, ref, original, base = _seed(tmp_path, family)
    modified = bound.save(ref, _changed(original), message="modify", branch="master")
    deleted = bound.delete(ref, message="delete", branch="peer")
    git = repo.require_git()
    git.create_branch("result", source_commit=base)
    result = CliRunner().invoke(cli, ["-C", str(repo.root), "merge", "commit", "master", "peer", "--target-branch", "result"])
    assert result.exit_code == 1
    assert "non-claim merge conflict" in result.output
    assert f"family {family!r}" in result.output
    assert "FrozenInstanceError" not in result.output
    assert git.branch_sha("result") == base
    assert (git.branch_sha("master"), git.branch_sha("peer")) == (modified, deleted)


@pytest.mark.parametrize("reverse", [False, True])
def test_selected_stance_edit_follows_only_its_own_rival_claim_version(tmp_path, reverse):
    repo, bound, ref, original, base = _seed(tmp_path, "stance")
    author_param_claim(repo, "c", "x", 300.0, branch="master")
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    changed = _changed(original)
    left = bound.save(ref, changed, message="one-sided stance edit", branch="master")
    right = repo.require_git().branch_sha("peer")
    sources = ("peer", "master") if reverse else ("master", "peer")
    merged = create_merge_commit(repo, *sources, target_branch="result")
    claims = {h.document.claim_id: h.document for h in repo.families.claim.iter_handles(commit=merged)}
    assert {document.value for document in claims.values()} == {300.0, 150.0}
    stances = tuple(bound.iter_handles(commit=merged))
    assert len(stances) == 1
    stance = stances[0].document
    assert stance.confidence == 0.8
    assert claims[stance.source_claim_id].value == 300.0
    assert claims[stance.target_claim_id].value == 300.0
    manifest = next(repo.families.merge_manifest.iter_handles(commit=merged)).document
    assert {image.source_commit for image in manifest.reference_images if image.family == "stance"} == {left}
    assert bound.require(ref, commit=right) == original
    assert bound.require(ref, commit=left) == changed
    assert verify_claim_tree(repo, commit=merged).ok


@pytest.mark.parametrize("reverse", [False, True])
def test_combined_reference_violation_rejects_valid_parents_before_publication(tmp_path, reverse):
    repo = init_repo(tmp_path / "knowledge")
    base = author_concept(repo, "x")
    git = repo.require_git()
    git.create_branch("peer", source_commit=base)
    removed = repo.families.concept.delete("x", message="remove unused concept", branch="master")
    added = author_param_claim(repo, "c", "x", 250.0, branch="peer")
    assert verify_claim_tree(repo, commit=removed).ok
    assert verify_claim_tree(repo, commit=added).ok
    git.create_branch("result", source_commit=base)
    sources = ("peer", "master") if reverse else ("master", "peer")
    with pytest.raises(ForeignKeyValidationError):
        create_merge_commit(repo, *sources, target_branch="result")
    assert git.branch_sha("result") == base
    assert (git.branch_sha("master"), git.branch_sha("peer")) == (removed, added)
    assert repo.families.concept.require("x", commit=base).concept_id == "x"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("existing_target", [False, True])
@pytest.mark.parametrize("entrypoint", ["owner", "app", "cli"])
def test_criss_cross_opposite_concept_resolutions_refuse_before_writes(tmp_path, reverse, existing_target, entrypoint):
    repo = init_repo(tmp_path / "knowledge")
    origin = author_concept(repo, "x", name="O")
    git = repo.require_git()
    git.create_branch("left", source_commit=origin)
    git.create_branch("right", source_commit=origin)
    a = author_concept(repo, "x", name="A", branch="left")
    b = author_concept(repo, "x", name="B", branch="right")
    left = git.commit_flat_tree(dict(git.iter_flat_tree_entries(a)), "retain A", parents=[a, b], branch="left")
    right = git.commit_flat_tree(dict(git.iter_flat_tree_entries(b)), "retain B", parents=[b, a], branch="right")
    if existing_target:
        git.create_branch("result", source_commit=origin)
    refs_before = git.raw_repo.refs.as_dict()
    objects_before = set(git.raw_repo.object_store)
    sources = ("right", "left") if reverse else ("left", "right")
    assert set(git.iter_merge_bases(left, right)) == {a, b}
    if entrypoint == "cli":
        result = CliRunner().invoke(cli, ["-C", str(repo.root), "merge", "commit", *sources, "--target-branch", "result"])
        assert result.exit_code == 1
        assert "Multiple best merge bases" in result.output
        assert a in result.output and b in result.output
    else:
        with pytest.raises(AmbiguousMergeBaseError) as caught:
            if entrypoint == "owner":
                create_merge_commit(repo, *sources, target_branch="result")
            else:
                commit_merge(repo, MergeCommitRequest(*sources, target_branch="result"))
        assert set(caught.value.base_shas) == {a, b}
        assert (caught.value.left_sha, caught.value.right_sha) == ((right, left) if reverse else (left, right))
    assert git.raw_repo.refs.as_dict() == refs_before
    assert set(git.raw_repo.object_store) == objects_before
    assert repo.families.concept.require("x", commit=left).canonical_name == "A"
    assert repo.families.concept.require("x", commit=right).canonical_name == "B"
