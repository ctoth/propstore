"""Two-parent storage merge commit + the formal merge object over a Repository.

Phase 9-2 translation of the reference ``test_repo_merge_object`` onto the rewrite's
charter-shaped, provenance-free storage: claims are authored through the families API
and read back out of the branch trees by ``build_repository_merge_framework``; the
two-parent commit is written by ``create_merge_commit`` via quire ``commit_flat_tree``.
"""

from __future__ import annotations

from pathlib import Path

from propstore.families.claims import Claim
from propstore.families.merge_manifests import MergeManifest
from propstore.merge.merge_commit import (
    build_repository_merge_framework,
    create_merge_commit,
)
from tests.merge_commit_helpers import (
    author_concept,
    author_param_claim,
    init_repo,
)


def _seed_with_base_claim(tmp_path: Path, branch_name: str, base_value: float):
    """Author ``concept_x`` + ``claim1=base_value`` on master, then branch off it."""

    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "concept_x")
    author_param_claim(repo, "claim1", "concept_x", base_value)
    base_sha = repo.require_git().branch_sha("master")
    assert base_sha is not None
    repo.require_git().create_branch(branch_name, source_commit=base_sha)
    return repo


def test_build_merge_framework_conflict_emits_mutual_attack(tmp_path: Path) -> None:
    branch = "paper/conflict"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    author_param_claim(repo, "claim1", "concept_x", 300.0)
    author_param_claim(repo, "claim1", "concept_x", 150.0, branch=branch)

    merge = build_repository_merge_framework(repo, "master", branch)

    assert len(merge.arguments) == 2
    assertion_ids = {argument.assertion_id for argument in merge.arguments}
    assert all(assertion_id.startswith("ps:assertion:") for assertion_id in assertion_ids)
    left_id, right_id = sorted(assertion_ids)
    assert (left_id, right_id) in merge.framework.attacks
    assert (right_id, left_id) in merge.framework.attacks
    assert (left_id, right_id) not in merge.framework.ignorance


def test_build_merge_framework_phi_node_emits_ignorance(tmp_path: Path) -> None:
    branch = "paper/phi"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    author_param_claim(
        repo, "claim1", "concept_x", 300.0, conditions=("temp > 300",)
    )
    author_param_claim(
        repo, "claim1", "concept_x", 150.0, branch=branch, conditions=("temp < 200",)
    )

    merge = build_repository_merge_framework(repo, "master", branch)

    assert len(merge.arguments) == 2
    left_id, right_id = sorted(argument.assertion_id for argument in merge.arguments)
    assert (left_id, right_id) in merge.framework.ignorance
    assert (right_id, left_id) in merge.framework.ignorance
    assert (left_id, right_id) not in merge.framework.attacks


def test_compatible_one_sided_modification_emits_single_argument(tmp_path: Path) -> None:
    branch = "paper/compat"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    # Only the branch modifies claim1; master keeps the base value.
    author_param_claim(repo, "claim1", "concept_x", 999.0, branch=branch)

    merge = build_repository_merge_framework(repo, "master", branch)

    assert len(merge.arguments) == 1
    emitted = merge.arguments[0]
    assert emitted.artifact_id == "claim1"
    assert emitted.claim.claim.value == 999.0
    assert emitted.branch_origins == (branch,)
    assert merge.framework.attacks == frozenset()
    assert merge.framework.ignorance == frozenset()


def test_create_merge_commit_materializes_divergent_versions_as_rivals(
    tmp_path: Path,
) -> None:
    branch = "paper/provenance"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    author_param_claim(repo, "claim1", "concept_x", 300.0)
    author_param_claim(repo, "claim1", "concept_x", 150.0, branch=branch)

    merge_sha = create_merge_commit(repo, "master", branch)

    materialized = [
        handle.document
        for handle in repo.families.claim.iter_handles(commit=merge_sha)
        if isinstance(handle.document, Claim)
    ]
    assert {claim.value for claim in materialized} == {150.0, 300.0}

    manifests = [
        handle.document
        for handle in repo.families.merge_manifest.iter_handles(commit=merge_sha)
        if isinstance(handle.document, MergeManifest)
    ]
    assert len(manifests) == 1
    manifest = manifests[0]
    assert len(manifest.arguments) == 2
    assert all(argument.materialized for argument in manifest.arguments)
    assert {argument.artifact_id for argument in manifest.arguments} == {"claim1"}
    # The two rivals stay distinct (non-commitment): distinct assertion ids.
    assert len({argument.assertion_id for argument in manifest.arguments}) == 2


def test_create_merge_commit_is_two_parent(tmp_path: Path) -> None:
    branch = "paper/two-parent"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    author_param_claim(repo, "claim1", "concept_x", 300.0)
    author_param_claim(repo, "claim1", "concept_x", 150.0, branch=branch)

    git = repo.require_git()
    left_sha = git.branch_sha("master")
    right_sha = git.branch_sha(branch)

    merge_sha = create_merge_commit(repo, "master", branch)

    assert list(git.iter_commit_parent_shas(merge_sha)) == [left_sha, right_sha]
    # The merge advances the target branch (master by default).
    assert git.branch_sha("master") == merge_sha


def test_create_merge_commit_target_branch_override(tmp_path: Path) -> None:
    branch = "paper/target"
    repo = _seed_with_base_claim(tmp_path, branch, 250.0)
    author_param_claim(repo, "claim1", "concept_x", 300.0)
    author_param_claim(repo, "claim1", "concept_x", 150.0, branch=branch)

    git = repo.require_git()
    master_before = git.branch_sha("master")
    branch_before = git.branch_sha(branch)
    git.create_branch("merge/out", source_commit=master_before)

    merge_sha = create_merge_commit(
        repo, "master", branch, target_branch="merge/out"
    )

    assert git.branch_sha("merge/out") == merge_sha
    # The source branches are untouched.
    assert git.branch_sha("master") == master_before
    assert git.branch_sha(branch) == branch_before
    assert list(git.iter_commit_parent_shas(merge_sha)) == [master_before, branch_before]
