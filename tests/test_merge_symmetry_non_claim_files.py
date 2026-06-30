"""A divergent non-claim file is surfaced as a conflict, symmetrically.

Claim divergence is held as rival arguments; a non-claim file (here a concept
document) that differs between the two branches has no rival-alternative semantics,
so ``create_merge_commit`` raises :class:`NonClaimMergeConflict` regardless of merge
direction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from tests.merge_commit_helpers import author_concept, init_repo


def test_non_claim_file_conflict_is_surfaced_symmetrically(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "knowledge")
    author_concept(repo, "anchor")
    base_sha = repo.require_git().branch_sha("master")
    assert base_sha is not None

    branch = "paper/right"
    repo.require_git().create_branch(branch, source_commit=base_sha)
    author_concept(repo, "shared", name="left")
    author_concept(repo, "shared", name="right", branch=branch)

    with pytest.raises(NonClaimMergeConflict) as left_first:
        create_merge_commit(repo, "master", branch, target_branch="merge/lr")
    with pytest.raises(NonClaimMergeConflict) as right_first:
        create_merge_commit(repo, branch, "master", target_branch="merge/rl")

    assert left_first.value.path == "concept/shared.yaml"
    assert right_first.value.path == "concept/shared.yaml"
    assert left_first.value.family == "concept"
    assert left_first.value.left_sha != left_first.value.right_sha
    assert right_first.value.left_sha != right_first.value.right_sha
