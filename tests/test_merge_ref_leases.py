"""Deterministic authoring interleavings at real merge planning boundaries."""

from pathlib import Path

import pytest
from quire.git_store import HeadMismatchError

from propstore.merge import merge_commit
from tests.merge_commit_helpers import author_concept, author_param_claim, init_repo


@pytest.mark.parametrize("boundary", ["read", "publish"])
@pytest.mark.parametrize("source", ["master", "peer"])
def test_merge_rejects_source_advanced_during_planning(tmp_path, monkeypatch, boundary, source):
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    author_param_claim(repo, "c", "x", 300.0)
    author_param_claim(repo, "c", "x", 150.0, branch="peer")
    expected = git.branch_sha(source)
    advanced = None
    original = getattr(merge_commit, "_read_branch_merge_claims" if boundary == "read" else "_transport_family_occurrences")

    def interleave(*args, **kwargs):
        nonlocal advanced
        result = original(*args, **kwargs)
        if advanced is None:
            advanced = author_param_claim(repo, "late", "x", 123.0, branch=source)
        return result

    monkeypatch.setattr(merge_commit, "_read_branch_merge_claims" if boundary == "read" else "_transport_family_occurrences", interleave)
    with pytest.raises(HeadMismatchError) as caught:
        merge_commit.create_merge_commit(repo, "master", "peer", target_branch="result")
    assert caught.value.branch == source
    assert caught.value.expected_head == expected
    assert caught.value.actual_head == advanced
    assert git.branch_sha(source) == advanced
    assert git.branch_sha("result") is None


@pytest.mark.parametrize("existing_target", [False, True])
def test_merge_preserves_target_changed_after_planning(tmp_path: Path, monkeypatch, existing_target):
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    author_param_claim(repo, "c", "x", 250.0)
    git = repo.require_git()
    git.create_branch("peer", source_commit=git.branch_sha("master"))
    if existing_target:
        git.create_branch("result", source_commit=git.branch_sha("master"))
    expected = git.branch_sha("result")
    parents = (git.branch_sha("master"), git.branch_sha("peer"))
    concurrent = None
    original = merge_commit._transport_family_occurrences

    def interleave(*args, **kwargs):
        nonlocal concurrent
        result = original(*args, **kwargs)
        if not existing_target:
            git.create_branch("result", source_commit=parents[0])
        concurrent = author_param_claim(repo, "concurrent", "x", 99.0, branch="result")
        return result

    monkeypatch.setattr(merge_commit, "_transport_family_occurrences", interleave)
    with pytest.raises(HeadMismatchError) as caught:
        merge_commit.create_merge_commit(repo, "master", "peer", target_branch="result")
    assert caught.value.branch == "result"
    assert caught.value.expected_head == expected
    assert caught.value.actual_head == concurrent
    assert git.branch_sha("result") == concurrent
    document = repo.families.claim.load("concurrent", commit=concurrent)
    assert document is not None and document.value == 99.0
    assert (git.branch_sha("master"), git.branch_sha("peer")) == parents


def test_framework_reads_claims_and_base_from_captured_commits(tmp_path, monkeypatch):
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    base = author_param_claim(repo, "c", "x", 250.0)
    git = repo.require_git()
    git.create_branch("peer", source_commit=base)
    left = author_param_claim(repo, "c", "x", 300.0)
    right = author_param_claim(repo, "c", "x", 150.0, branch="peer")
    reads = []
    original = merge_commit._read_branch_merge_claims

    def interleave(repo, branch, commit):
        result = original(repo, branch, commit)
        reads.append((branch, commit))
        if len(reads) == 1:
            author_param_claim(repo, "late", "x", 99.0, branch="peer")
        return result

    monkeypatch.setattr(merge_commit, "_read_branch_merge_claims", interleave)
    framework = merge_commit.build_repository_merge_framework(
        repo, "master", "peer", branch_commits={"master": left, "peer": right}
    )
    assert reads == [("master", left), ("peer", right), ("master", base)]
    assert {argument.claim.claim.value for argument in framework.arguments} == {300.0, 150.0}
    assert {argument.artifact_id for argument in framework.arguments} == {"c"}


@pytest.mark.parametrize("target", ["master", "peer", "new-result"])
def test_merge_with_unchanged_leases_keeps_exact_parents_and_rivals(tmp_path, target):
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "x")
    base = author_param_claim(repo, "c", "x", 250.0)
    git = repo.require_git()
    git.create_branch("peer", source_commit=base)
    left = author_param_claim(repo, "c", "x", 300.0)
    right = author_param_claim(repo, "c", "x", 150.0, branch="peer")
    merged = merge_commit.create_merge_commit(repo, "master", "peer", target_branch=target)
    assert git.branch_sha(target) == merged
    assert list(git.iter_commit_parent_shas(merged)) == [left, right]
    assert {h.document.value for h in repo.families.claim.iter_handles(commit=merged)} == {300.0, 150.0}
    for branch, commit in (("master", left), ("peer", right)):
        if branch != target:
            assert git.branch_sha(branch) == commit
