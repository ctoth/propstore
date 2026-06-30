"""Merge-side integrity-constraint coverage over a git-backed knowledge store.

This is the **merge-side** :class:`~propstore.merge.IntegrityConstraint` (the layer-2
merge-framework precondition over the emitted arguments) exercised against a real
:class:`~propstore.repository.Repository` merge — distinct from the model-theoretic IC
merge in ``propstore.belief_set.ic_merge`` (Phase 7b-4), which revises belief sets.
Here the constraint filters out forbidden source artifacts and asserts required ones
survive; it never revises a belief, it gates the candidate set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.merge import IntegrityConstraint, IntegrityConstraintViolation
from propstore.merge.merge_commit import build_repository_merge_framework
from propstore.repository import Repository
from tests.merge_commit_helpers import author_obs_claim, init_repo


def _two_branch_repo(tmp_path: Path) -> tuple[Repository, str]:
    repo = init_repo(tmp_path / "knowledge")
    # An anchor commit so both branches share a merge base.
    author_obs_claim(repo, "anchor", "Anchor")
    base_sha = repo.require_git().branch_sha("master")
    assert base_sha is not None
    branch = "paper/right"
    repo.require_git().create_branch(branch, source_commit=base_sha)
    author_obs_claim(repo, "left", "Left")
    author_obs_claim(repo, "right", "Right", branch=branch)
    return repo, branch


def test_integrity_constraint_prunes_forbidden_artifact_ids(tmp_path: Path) -> None:
    repo, branch = _two_branch_repo(tmp_path)

    merge = build_repository_merge_framework(
        repo,
        "master",
        branch,
        integrity_constraint=IntegrityConstraint(
            forbidden_artifact_ids=frozenset({"right"})
        ),
    )

    surviving = {argument.artifact_id for argument in merge.arguments}
    assert "right" not in surviving
    assert {"anchor", "left"} <= surviving


def test_integrity_constraint_required_present_survives(tmp_path: Path) -> None:
    repo, branch = _two_branch_repo(tmp_path)

    merge = build_repository_merge_framework(
        repo,
        "master",
        branch,
        integrity_constraint=IntegrityConstraint(
            required_artifact_ids=frozenset({"left", "right"})
        ),
    )

    assert {"left", "right"} <= {argument.artifact_id for argument in merge.arguments}


def test_integrity_constraint_violation_when_required_missing(tmp_path: Path) -> None:
    repo, branch = _two_branch_repo(tmp_path)

    with pytest.raises(IntegrityConstraintViolation):
        build_repository_merge_framework(
            repo,
            "master",
            branch,
            integrity_constraint=IntegrityConstraint(
                required_artifact_ids=frozenset({"does-not-exist"})
            ),
        )


def test_integrity_constraint_violation_when_forbidden_is_also_required(
    tmp_path: Path,
) -> None:
    """A forbidden artifact pruned away cannot then satisfy a required clause."""

    repo, branch = _two_branch_repo(tmp_path)

    with pytest.raises(IntegrityConstraintViolation):
        build_repository_merge_framework(
            repo,
            "master",
            branch,
            integrity_constraint=IntegrityConstraint(
                required_artifact_ids=frozenset({"right"}),
                forbidden_artifact_ids=frozenset({"right"}),
            ),
        )


def test_nary_merge_preserves_disjoint_branch_additions(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_obs_claim(repo, "anchor", "Anchor")
    base_sha = repo.require_git().branch_sha("master")
    assert base_sha is not None
    right_branch = "paper/right"
    third_branch = "paper/third"
    repo.require_git().create_branch(right_branch, source_commit=base_sha)
    repo.require_git().create_branch(third_branch, source_commit=base_sha)
    author_obs_claim(repo, "left", "Left")
    author_obs_claim(repo, "right", "Right", branch=right_branch)
    author_obs_claim(repo, "third", "Third", branch=third_branch)

    merge = build_repository_merge_framework(
        repo,
        "master",
        right_branch,
        additional_branches=(third_branch,),
    )

    assert {argument.artifact_id for argument in merge.arguments} == {
        "anchor",
        "left",
        "right",
        "third",
    }
